import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.exams.definitions import ExamDef, ExamQuestionDef
from app.domains.exams.seeding import seed_exams
from app.domains.exams.service import start_attempt

HISTORY_URL = "/api/v1/exams/final-exam/history"


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
                questions=[
                    ExamQuestionDef(
                        slug="q1",
                        kind="quiz",
                        payload={
                            "question": "2+2?",
                            "choices": ["3", "4"],
                            "answer_index": 1,
                            "explanation": "math",
                        },
                    )
                ],
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
