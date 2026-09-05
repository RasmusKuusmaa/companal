import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.exams.definitions import ExamDef, ExamQuestionDef
from app.domains.exams.seeding import seed_exams
from app.domains.exams.service import start_attempt

EXAMS_URL = "/api/v1/exams"
HISTORY_URL = "/api/v1/exams/final-exam/history"


def _quiz_question(slug: str = "q1") -> ExamQuestionDef:
    return ExamQuestionDef(
        slug=slug,
        kind="quiz",
        payload={
            "question": "2+2?",
            "choices": ["3", "4"],
            "answer_index": 1,
            "explanation": "math",
        },
    )


def _composition_question(slug: str = "c1") -> ExamQuestionDef:
    return ExamQuestionDef(
        slug=slug, kind="composition", payload={"brief": "Write something.", "requirements": []}
    )


def _note() -> dict[str, object]:
    return {
        "id": "n",
        "step": "C",
        "octave": 4,
        "alter": 0,
        "duration": "whole",
        "dots": 0,
        "is_rest": False,
        "tied_to_next": False,
    }


def _document() -> dict[str, object]:
    return {
        "fifths": 0,
        "mode": "major",
        "time": {"beats": 4, "beat_type": 4},
        "tempo": 90,
        "staves": [
            {
                "id": "s1",
                "clef": "treble",
                "measures": [{"id": "m0", "voices": [{"id": "1", "notes": [_note()]}]}],
            }
        ],
    }


async def _auth_headers(client: AsyncClient, email: str = "examer@example.com") -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct horse battery staple", "full_name": "Examer"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "correct horse battery staple"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _user_id(client: AsyncClient, headers: dict[str, str]) -> uuid.UUID:
    me = await client.get("/api/v1/auth/me", headers=headers)
    return uuid.UUID(me.json()["id"])


@pytest.fixture
async def seeded(db_session: AsyncSession) -> None:
    await seed_exams(
        db_session,
        exams=[
            ExamDef(
                slug="final-exam",
                title="Final",
                description="d",
                questions=[_quiz_question(), _composition_question()],
            )
        ],
    )


class TestAuthentication:
    async def test_requires_a_token(self, client: AsyncClient, seeded: None) -> None:
        response = await client.get(HISTORY_URL)
        assert response.status_code == 401


class TestAttemptHistory:
    async def test_returns_no_attempts_before_any_are_started(
        self, client: AsyncClient, seeded: None
    ) -> None:
        headers = await _auth_headers(client)

        response = await client.get(HISTORY_URL, headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["exam_slug"] == "final-exam"
        assert body["attempts"] == []

    async def test_lists_attempts_newest_first(
        self, client: AsyncClient, db_session: AsyncSession, seeded: None
    ) -> None:
        headers = await _auth_headers(client, "one@example.com")
        user_id = await _user_id(client, headers)

        await start_attempt(db_session, user_id, "final-exam")
        await start_attempt(db_session, user_id, "final-exam")

        response = await client.get(HISTORY_URL, headers=headers)

        assert response.status_code == 200
        attempts = response.json()["attempts"]
        assert [a["attempt_number"] for a in attempts] == [2, 1]
        assert attempts[0]["submitted_at"] is None
        assert attempts[0]["score"] is None

    async def test_history_is_not_shared_between_students(
        self, client: AsyncClient, db_session: AsyncSession, seeded: None
    ) -> None:
        mine = await _auth_headers(client, "mine@example.com")
        theirs = await _auth_headers(client, "theirs@example.com")
        my_id = await _user_id(client, mine)

        await start_attempt(db_session, my_id, "final-exam")

        response = await client.get(HISTORY_URL, headers=theirs)

        assert response.status_code == 200
        assert response.json()["attempts"] == []

    async def test_unknown_exam_slug_is_a_404(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.get("/api/v1/exams/no-such-exam/history", headers=headers)

        assert response.status_code == 404


class TestListExams:
    async def test_requires_a_token(self, client: AsyncClient, seeded: None) -> None:
        response = await client.get(EXAMS_URL)
        assert response.status_code == 401

    async def test_lists_every_exam(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.get(EXAMS_URL, headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["slug"] == "final-exam"
        assert body[0]["question_count"] == 2
        assert body[0]["course_slug"] is None


class TestStartAttemptEndpoint:
    async def test_starts_a_fresh_attempt(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.post("/api/v1/exams/final-exam/attempts", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["attempt_number"] == 1
        assert len(body["exam"]["questions"]) == 2

    async def test_unknown_exam_slug_is_a_404(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.post("/api/v1/exams/no-such-exam/attempts", headers=headers)

        assert response.status_code == 404


class TestAnswerEndpoint:
    async def _attempt(self, client: AsyncClient, headers: dict[str, str]) -> dict[str, object]:
        start = await client.post("/api/v1/exams/final-exam/attempts", headers=headers)
        body: dict[str, object] = start.json()
        return body

    async def test_holds_a_quiz_answer(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)
        attempt = await self._attempt(client, headers)
        attempt_id = attempt["attempt_id"]
        question_id = attempt["exam"]["questions"][0]["id"]  # type: ignore[index]

        response = await client.post(
            f"/api/v1/exams/attempts/{attempt_id}/questions/{question_id}/answer",
            json={"answer": {"kind": "quiz", "choice_index": 1}},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["answered"] is True

    async def test_holds_a_composition_answer(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)
        attempt = await self._attempt(client, headers)
        attempt_id = attempt["attempt_id"]
        question_id = attempt["exam"]["questions"][1]["id"]  # type: ignore[index]

        response = await client.post(
            f"/api/v1/exams/attempts/{attempt_id}/questions/{question_id}/answer",
            json={"answer": {"kind": "composition", "document": _document()}},
            headers=headers,
        )

        assert response.status_code == 200

    async def test_a_kind_mismatch_is_a_400(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)
        attempt = await self._attempt(client, headers)
        attempt_id = attempt["attempt_id"]
        quiz_question_id = attempt["exam"]["questions"][0]["id"]  # type: ignore[index]

        response = await client.post(
            f"/api/v1/exams/attempts/{attempt_id}/questions/{quiz_question_id}/answer",
            json={"answer": {"kind": "composition", "document": _document()}},
            headers=headers,
        )

        assert response.status_code == 400

    async def test_unknown_attempt_is_a_404(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)
        attempt = await self._attempt(client, headers)
        question_id = attempt["exam"]["questions"][0]["id"]  # type: ignore[index]

        response = await client.post(
            f"/api/v1/exams/attempts/{uuid.uuid4()}/questions/{question_id}/answer",
            json={"answer": {"kind": "quiz", "choice_index": 0}},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_unknown_question_is_a_404(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)
        attempt = await self._attempt(client, headers)
        attempt_id = attempt["attempt_id"]

        response = await client.post(
            f"/api/v1/exams/attempts/{attempt_id}/questions/{uuid.uuid4()}/answer",
            json={"answer": {"kind": "quiz", "choice_index": 0}},
            headers=headers,
        )

        assert response.status_code == 404


class TestSubmitEndpoint:
    async def test_grades_the_attempt(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)
        start = await client.post("/api/v1/exams/final-exam/attempts", headers=headers)
        attempt_id = start.json()["attempt_id"]
        question_id = start.json()["exam"]["questions"][0]["id"]
        await client.post(
            f"/api/v1/exams/attempts/{attempt_id}/questions/{question_id}/answer",
            json={"answer": {"kind": "quiz", "choice_index": 1}},
            headers=headers,
        )

        response = await client.post(
            f"/api/v1/exams/attempts/{attempt_id}/submit", json={}, headers=headers
        )

        assert response.status_code == 200
        body = response.json()
        assert body["score"] == 1.0
        assert body["max_score"] == 2.0

    async def test_submitting_twice_is_a_400(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)
        start = await client.post("/api/v1/exams/final-exam/attempts", headers=headers)
        attempt_id = start.json()["attempt_id"]
        await client.post(
            f"/api/v1/exams/attempts/{attempt_id}/submit", json={}, headers=headers
        )

        response = await client.post(
            f"/api/v1/exams/attempts/{attempt_id}/submit", json={}, headers=headers
        )

        assert response.status_code == 400

    async def test_unknown_attempt_is_a_404(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.post(
            f"/api/v1/exams/attempts/{uuid.uuid4()}/submit", json={}, headers=headers
        )

        assert response.status_code == 404

    async def test_ai_feedback_is_gated_behind_premium(
        self, client: AsyncClient, seeded: None
    ) -> None:
        headers = await _auth_headers(client)
        start = await client.post("/api/v1/exams/final-exam/attempts", headers=headers)
        attempt_id = start.json()["attempt_id"]

        response = await client.post(
            f"/api/v1/exams/attempts/{attempt_id}/submit",
            json={"with_ai_feedback": True},
            headers=headers,
        )

        assert response.status_code == 402
        assert response.json()["detail"]["feature"] == "ai_exam_rubric_grading"
