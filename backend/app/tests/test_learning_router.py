import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learning.seeding import seed_curriculum
from app.tests.test_learning_service import TOPICS, _curriculum

ROADMAP = "/api/v1/learning/roadmap"
LESSON = "/api/v1/learning/lessons/intervals"
QUIZ_ANSWER = "/api/v1/learning/lessons/intervals/steps/intervals-quiz/answer"


async def _auth_headers(client: AsyncClient, email: str = "student@example.com") -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct horse battery staple", "full_name": "Student"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "correct horse battery staple"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def seeded(db_session: AsyncSession) -> None:
    await seed_curriculum(db_session, topics=TOPICS, courses=_curriculum())


class TestAuthentication:
    @pytest.mark.parametrize(
        ("method", "url"),
        [
            ("get", ROADMAP),
            ("get", LESSON),
            ("get", "/api/v1/learning/progress"),
            ("post", QUIZ_ANSWER),
            ("post", "/api/v1/learning/lessons/intervals/steps/intervals-quiz/seen"),
            ("post", "/api/v1/learning/lessons/intervals/complete"),
        ],
    )
    async def test_requires_a_token(self, client: AsyncClient, method: str, url: str) -> None:
        # `request` rather than `client.get(...)`: httpx's GET helper takes no
        # `json`, and every route here is checked with the same call.
        response = await client.request(method, url, json={"choice_index": 0})
        assert response.status_code == 401


class TestRoadmap:
    async def test_returns_every_stage(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.get(ROADMAP, headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert [course["slug"] for course in body["courses"]] == ["fundamentals", "harmony"]
        assert body["lesson_count"] == 3

    async def test_nothing_is_locked(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        body = (await client.get(ROADMAP, headers=headers)).json()
        lessons = [lesson for course in body["courses"] for lesson in course["lessons"]]

        # Every lesson is served in full whatever the student has done - the
        # only thing that varies is its status.
        assert all(lesson["status"] == "not_started" for lesson in lessons)
        assert all(lesson["step_count"] > 0 for lesson in lessons)


class TestLessonDetail:
    async def test_returns_ordered_steps(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.get(LESSON, headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert [step["slug"] for step in body["steps"]] == [
            "intervals-reading",
            "intervals-quiz",
        ]
        assert body["steps"][1]["kind"] == "quiz"

    async def test_answer_key_never_reaches_the_client(
        self, client: AsyncClient, seeded: None
    ) -> None:
        headers = await _auth_headers(client)

        response = await client.get(LESSON, headers=headers)

        # Against the raw body, not the parsed step: this is the assertion
        # that would catch an answer key smuggled in anywhere at all.
        assert "answer_index" not in response.text
        assert "Seven - count them" not in response.text

    async def test_unknown_lesson_is_404(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.get("/api/v1/learning/lessons/no-such-lesson", headers=headers)

        assert response.status_code == 404


class TestQuizAnswers:
    async def test_correct_answer(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.post(QUIZ_ANSWER, json={"choice_index": 1}, headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["is_correct"] is True
        assert body["correct_index"] == 1
        assert "Seven" in body["explanation"]

    async def test_wrong_answer_is_still_a_200(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.post(QUIZ_ANSWER, json={"choice_index": 0}, headers=headers)

        # Being wrong is a normal outcome, not a client error.
        assert response.status_code == 200
        assert response.json()["is_correct"] is False

    async def test_retries_are_unlimited(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        for choice in (0, 2, 0, 1):
            response = await client.post(
                QUIZ_ANSWER, json={"choice_index": choice}, headers=headers
            )
            assert response.status_code == 200

    async def test_answering_a_reading_step_is_rejected(
        self, client: AsyncClient, seeded: None
    ) -> None:
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/learning/lessons/intervals/steps/intervals-reading/answer",
            json={"choice_index": 0},
            headers=headers,
        )

        assert response.status_code == 400

    async def test_unknown_step_is_404(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/learning/lessons/intervals/steps/no-such-step/answer",
            json={"choice_index": 0},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_choice_index_must_be_positive(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)

        response = await client.post(QUIZ_ANSWER, json={"choice_index": -1}, headers=headers)

        assert response.status_code == 422


class TestProgress:
    async def test_marking_a_step_seen_starts_the_lesson(
        self, client: AsyncClient, seeded: None
    ) -> None:
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/learning/lessons/intervals/steps/intervals-reading/seen", headers=headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

    async def test_completion_is_idempotent(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)
        url = "/api/v1/learning/lessons/intervals/complete"

        first = await client.post(url, headers=headers)
        second = await client.post(url, headers=headers)

        assert first.status_code == second.status_code == 200
        assert first.json()["completed_at"] == second.json()["completed_at"]
        assert second.json()["next_lesson_slug"] == "scales"

    async def test_progress_summary(self, client: AsyncClient, seeded: None) -> None:
        headers = await _auth_headers(client)
        await client.post("/api/v1/learning/lessons/intervals/complete", headers=headers)

        response = await client.get("/api/v1/learning/progress", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["completed_lesson_count"] == 1
        assert body["continue_lesson_slug"] == "scales"

    async def test_progress_is_not_shared_between_students(
        self, client: AsyncClient, seeded: None
    ) -> None:
        mine = await _auth_headers(client, "one@example.com")
        theirs = await _auth_headers(client, "two@example.com")
        await client.post("/api/v1/learning/lessons/intervals/complete", headers=mine)

        response = await client.get("/api/v1/learning/progress", headers=theirs)

        assert response.json()["completed_lesson_count"] == 0

    async def test_completing_an_unknown_lesson_is_404(
        self, client: AsyncClient, seeded: None
    ) -> None:
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/learning/lessons/no-such-lesson/complete", headers=headers
        )

        assert response.status_code == 404
