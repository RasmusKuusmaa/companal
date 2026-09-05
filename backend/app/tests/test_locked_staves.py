"""Server-side enforcement of a composition step's given (locked) material.

The frontend editor is what actually stops a student from editing a locked
staff - see `useNotationEditor`'s `lockedStaffIndices` on the frontend -
but nothing stops a request straight to the submit endpoint from carrying
an edited one anyway. `_apply_locked_staves` is what makes that pointless:
grading always runs against the pristine given material, regardless of
what the client actually sent.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef
from app.domains.learning.models import StepAttempt
from app.domains.learning.seeding import seed_curriculum
from app.domains.learning.service import submit_composition
from app.domains.notation.schemas import NotationDocument
from app.domains.users.models import User

LESSON_SLUG = "cantus-firmus"
STEP_SLUG = "write-against-the-given-bass"


def _note(step: str) -> dict[str, object]:
    return {
        "id": "n",
        "step": step,
        "octave": 4,
        "alter": 0,
        "duration": "whole",
        "dots": 0,
        "is_rest": False,
        "tied_to_next": False,
    }


def _document(given_step: str, student_step: str) -> dict[str, object]:
    return {
        "fifths": 0,
        "mode": "major",
        "time": {"beats": 4, "beat_type": 4},
        "tempo": 90,
        "staves": [
            {
                "id": "given",
                "clef": "bass",
                "measures": [{"id": "m0", "voices": [{"id": "1", "notes": [_note(given_step)]}]}],
            },
            {
                "id": "student",
                "clef": "treble",
                "measures": [
                    {"id": "m0", "voices": [{"id": "2", "notes": [_note(student_step)]}]}
                ],
            },
        ],
    }


def _curriculum(given_step: str) -> list[CourseDef]:
    return [
        CourseDef(
            slug="counterpoint",
            title="Counterpoint",
            description="d",
            level="beginner",
            lessons=[
                LessonDef(
                    slug=LESSON_SLUG,
                    title="Cantus firmus",
                    summary="s",
                    steps=[
                        StepDef(
                            slug=STEP_SLUG,
                            kind="composition",
                            payload={
                                "brief": "Write a counterpoint against the given bass.",
                                "requirements": [],
                                "starter_notation": _document(given_step, "C"),
                                "locked_staff_indices": [0],
                            },
                        )
                    ],
                )
            ],
        )
    ]


async def _make_user(db_session: AsyncSession) -> User:
    user = User(email="cf@example.com", hashed_password="not-a-real-hash", full_name="Student")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestLockedStaves:
    async def test_tampered_locked_staff_is_restored_before_grading(
        self, db_session: AsyncSession
    ) -> None:
        await seed_curriculum(db_session, topics=[], courses=_curriculum(given_step="C"))
        user = await _make_user(db_session)

        # The submitted document has changed the given bass from C to G -
        # simulating a client that bypassed the editor's own lock.
        tampered = NotationDocument.model_validate(_document(given_step="G", student_step="D"))

        result = await submit_composition(db_session, user.id, LESSON_SLUG, STEP_SLUG, tampered)

        attempt = await db_session.get(StepAttempt, result.attempt_id)
        assert attempt is not None
        stored = attempt.payload["document"]["staves"]
        assert stored[0]["measures"][0]["voices"][0]["notes"][0]["step"] == "C"
        assert stored[1]["measures"][0]["voices"][0]["notes"][0]["step"] == "D"

    async def test_untampered_submission_is_unaffected(self, db_session: AsyncSession) -> None:
        await seed_curriculum(db_session, topics=[], courses=_curriculum(given_step="C"))
        user = await _make_user(db_session)

        untouched = NotationDocument.model_validate(_document(given_step="C", student_step="E"))
        result = await submit_composition(db_session, user.id, LESSON_SLUG, STEP_SLUG, untouched)

        attempt = await db_session.get(StepAttempt, result.attempt_id)
        assert attempt is not None
        stored = attempt.payload["document"]["staves"]
        assert stored[0]["measures"][0]["voices"][0]["notes"][0]["step"] == "C"
        assert stored[1]["measures"][0]["voices"][0]["notes"][0]["step"] == "E"

    async def test_no_locked_indices_leaves_the_document_untouched(
        self, db_session: AsyncSession
    ) -> None:
        courses = _curriculum(given_step="C")
        courses[0].lessons[0].steps[0].payload["locked_staff_indices"] = []
        await seed_curriculum(db_session, topics=[], courses=courses)
        user = await _make_user(db_session)

        edited_given = NotationDocument.model_validate(_document(given_step="A", student_step="E"))
        result = await submit_composition(db_session, user.id, LESSON_SLUG, STEP_SLUG, edited_given)

        attempt = await db_session.get(StepAttempt, result.attempt_id)
        assert attempt is not None
        stored = attempt.payload["document"]["staves"]
        # Nothing locked - the "given" staff is just a normal staff here.
        assert stored[0]["measures"][0]["voices"][0]["notes"][0]["step"] == "A"


async def test_seeding_persists_locked_staff_indices(db_session: AsyncSession) -> None:
    await seed_curriculum(db_session, topics=[], courses=_curriculum(given_step="C"))

    from app.domains.learning.models import LessonStep

    step = await db_session.scalar(select(LessonStep).where(LessonStep.slug == STEP_SLUG))
    assert step is not None
    assert step.payload["locked_staff_indices"] == [0]
