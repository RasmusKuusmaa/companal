"""Composition submission: grading round-trip, storage, and the API shape.

Three layers, each tested at the layer where it actually lives:

* `notation.grading.grade_submission` - pure, no database, no storage.
* `learning.service.submit_composition` - the database and storage
  integration: a `StepAttempt` row, a MusicXML file, progress starting.
* the router - auth, status codes, the response shape a client sees.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef
from app.domains.learning.models import StepAttempt
from app.domains.learning.seeding import seed_curriculum
from app.domains.learning.service import (
    LessonNotFoundError,
    StepKindError,
    StepNotFoundError,
    submit_composition,
)
from app.domains.notation.grading import grade_submission
from app.domains.notation.requirements import KeyRequirement, MeasureCountRequirement
from app.domains.notation.schemas import NotationDocument
from app.domains.users.models import User

SUBMIT_URL = "/api/v1/learning/lessons/single-note/steps/single-note-task/submit"


def _note(step: str, octave: int = 4, duration: str = "whole") -> dict[str, object]:
    return {
        "id": "n",
        "step": step,
        "octave": octave,
        "alter": 0,
        "duration": duration,
        "dots": 0,
        "is_rest": False,
        "tied_to_next": False,
    }


def _document(measure_count: int = 1) -> NotationDocument:
    return NotationDocument.model_validate(
        {
            "fifths": 0,
            "mode": "major",
            "time": {"beats": 4, "beat_type": 4},
            "tempo": 90,
            "staves": [
                {
                    "id": "s1",
                    "clef": "treble",
                    "measures": [
                        {"id": f"m{i}", "voices": [{"id": "1", "notes": [_note("C")]}]}
                        for i in range(measure_count)
                    ],
                }
            ],
        }
    )


def _curriculum() -> list[CourseDef]:
    return [
        CourseDef(
            slug="fundamentals",
            title="Fundamentals",
            description="d",
            level="beginner",
            lessons=[
                LessonDef(
                    slug="single-note",
                    title="Single note",
                    summary="s",
                    steps=[
                        StepDef(
                            slug="single-note-task",
                            kind="composition",
                            payload={
                                "brief": "Write one whole note in C major.",
                                "requirements": [
                                    {"type": "key", "key": "C major"},
                                    {"type": "measure_count", "count": 1},
                                ],
                            },
                        ),
                        StepDef(
                            slug="a-reading",
                            kind="reading",
                            payload={"markdown": "# Not a composition step"},
                        ),
                    ],
                )
            ],
        )
    ]


async def _seed(db_session: AsyncSession) -> None:
    await seed_curriculum(db_session, topics=[], courses=_curriculum())


async def _make_user(db_session: AsyncSession, email: str = "composer@example.com") -> User:
    user = User(email=email, hashed_password="not-a-real-hash", full_name="Composer")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _auth_headers(client: AsyncClient, email: str = "composer@example.com") -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct horse battery staple", "full_name": "Composer"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "correct horse battery staple"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


class TestGradeSubmission:
    """Pure - no database, no storage."""

    def test_a_passing_submission(self) -> None:
        grade, musicxml = grade_submission(
            _document(measure_count=1),
            [KeyRequirement(key="C major"), MeasureCountRequirement(count=1)],
        )
        assert grade.passed is True
        assert all(result.passed for result in grade.requirement_results)
        assert musicxml.startswith(b"<?xml")

    def test_a_failing_submission_still_returns_a_full_checklist(self) -> None:
        grade, _musicxml = grade_submission(
            _document(measure_count=1),
            [KeyRequirement(key="C major"), MeasureCountRequirement(count=8)],
        )
        assert grade.passed is False
        assert len(grade.requirement_results) == 2
        # Every requirement is checked, not just the first failure - a
        # partial checklist would leave the student guessing what else
        # might be wrong.
        assert grade.requirement_results[0].passed is True
        assert grade.requirement_results[1].passed is False

    def test_an_empty_requirement_list_always_passes(self) -> None:
        grade, _musicxml = grade_submission(_document(), [])
        assert grade.passed is True
        assert grade.requirement_results == []

    def test_the_musicxml_returned_is_what_was_graded(self) -> None:
        _grade, musicxml = grade_submission(_document(measure_count=3), [])
        from app.domains.analysis.service import analyze

        reparsed = analyze(musicxml, "check.musicxml")
        assert reparsed.measure_count == 3


class TestSubmitCompositionService:
    async def test_creates_an_attempt_and_stores_the_musicxml(
        self, db_session: AsyncSession
    ) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        result = await submit_composition(
            db_session, user.id, "single-note", "single-note-task", _document()
        )

        assert result.passed is True
        attempt = await db_session.get(StepAttempt, result.attempt_id)
        assert attempt is not None
        assert attempt.passed is True
        assert attempt.payload["document"]["fifths"] == 0

        storage_key = attempt.result["storage_key"]
        content = await storage.read_file(storage_key)
        assert content.startswith(b"<?xml")

    async def test_every_retry_is_kept_as_its_own_attempt(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        first = await submit_composition(
            db_session, user.id, "single-note", "single-note-task", _document()
        )
        second = await submit_composition(
            db_session, user.id, "single-note", "single-note-task", _document()
        )

        assert first.attempt_id != second.attempt_id
        attempts = (
            await db_session.scalars(select(StepAttempt).where(StepAttempt.user_id == user.id))
        ).all()
        assert len(attempts) == 2

    async def test_submitting_starts_the_lesson(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        await submit_composition(
            db_session, user.id, "single-note", "single-note-task", _document()
        )

        from app.domains.learning.service import get_lesson

        lesson = await get_lesson(db_session, user.id, "single-note")
        assert lesson.status.value == "in_progress"

    async def test_rejects_submission_to_a_non_composition_step(
        self, db_session: AsyncSession
    ) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        with pytest.raises(StepKindError, match="reading"):
            await submit_composition(db_session, user.id, "single-note", "a-reading", _document())

    async def test_unknown_lesson_raises(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        with pytest.raises(LessonNotFoundError):
            await submit_composition(db_session, user.id, "no-such-lesson", "x", _document())

    async def test_unknown_step_raises(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        with pytest.raises(StepNotFoundError):
            await submit_composition(
                db_session, user.id, "single-note", "no-such-step", _document()
            )

    async def test_a_failing_submission_is_still_recorded(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        # Wrong key - the requirement fails, but the attempt is kept anyway.
        wrong_key_doc = _document()
        wrong_key_doc.fifths = 2

        result = await submit_composition(
            db_session, user.id, "single-note", "single-note-task", wrong_key_doc
        )
        assert result.passed is False
        attempt = await db_session.get(StepAttempt, result.attempt_id)
        assert attempt is not None
        assert attempt.passed is False


class TestSubmitCompositionRouter:
    async def test_requires_a_token(self, client: AsyncClient) -> None:
        response = await client.post(SUBMIT_URL, json={"document": _document().model_dump()})
        assert response.status_code == 401

    async def test_submits_and_returns_the_grade(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _seed(db_session)
        headers = await _auth_headers(client)

        response = await client.post(
            SUBMIT_URL, json={"document": _document().model_dump()}, headers=headers
        )

        assert response.status_code == 200
        body = response.json()
        assert body["passed"] is True
        assert uuid.UUID(body["attempt_id"])
        assert {r["requirement"]["type"] for r in body["requirement_results"]} == {
            "key",
            "measure_count",
        }

    async def test_ai_feedback_is_null_without_a_configured_key(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _seed(db_session)
        headers = await _auth_headers(client)

        response = await client.post(
            SUBMIT_URL,
            json={"document": _document().model_dump(), "with_ai_feedback": True},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["ai_feedback"] is None

    async def test_wrong_step_kind_is_a_400(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _seed(db_session)
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/learning/lessons/single-note/steps/a-reading/submit",
            json={"document": _document().model_dump()},
            headers=headers,
        )
        assert response.status_code == 400

    async def test_unknown_step_is_a_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _seed(db_session)
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/learning/lessons/single-note/steps/no-such-step/submit",
            json={"document": _document().model_dump()},
            headers=headers,
        )
        assert response.status_code == 404
