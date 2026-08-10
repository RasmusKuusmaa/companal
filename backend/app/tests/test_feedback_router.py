from pathlib import Path
from typing import Any, cast

import pytest
from httpx import AsyncClient

from app.domains.feedback.ai_service import AIServiceError
from app.domains.feedback.schemas import CompositionFeedback, FeedbackIssue, TheoryLesson

_FIXTURES = Path(__file__).parent / "fixtures"
SATB = (_FIXTURES / "harmony_satb.musicxml").read_bytes()

_FAKE_FEEDBACK = CompositionFeedback(
    summary="A solid draft with one voice-leading issue to fix.",
    strengths=["Clear melodic contour"],
    issues=[
        FeedbackIssue(
            problem="Parallel fifths in measure 4.",
            explanation="Two voices move in parallel perfect fifths.",
            suggestion="Move one voice by a different interval.",
            theory=TheoryLesson(
                concept="Parallel fifths",
                lesson="Avoid two voices moving in parallel perfect fifths.",
            ),
        )
    ],
    suggestions=["Vary the accompaniment rhythm for more interest."],
)


def _mock_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.domains.feedback.service.generate_feedback",
        lambda *_args, **_kwargs: _FAKE_FEEDBACK,
    )


async def _auth_headers(client: AsyncClient, email: str = "composer@example.com") -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct horse battery staple", "full_name": "Composer"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "correct horse battery staple"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_composition(
    client: AsyncClient, headers: dict[str, str], title: str = "Sonata No. 1"
) -> dict[str, Any]:
    response = await client.post("/api/v1/projects", json={"title": title}, headers=headers)
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


async def _analyzed_composition(client: AsyncClient, headers: dict[str, str]) -> dict[str, Any]:
    composition = await _create_composition(client, headers)
    await client.post(
        f"/api/v1/projects/{composition['id']}/versions",
        headers=headers,
        files={"file": ("piece.musicxml", SATB, "application/xml")},
    )
    response = await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)
    assert response.status_code == 200
    return composition


class TestCreateFeedback:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000/feedback"
        )
        assert response.status_code == 401

    async def test_returns_404_for_an_unknown_composition(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_ai(monkeypatch)
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000/feedback", headers=headers
        )

        assert response.status_code == 404

    async def test_returns_404_for_another_users_composition(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_ai(monkeypatch)
        headers_a = await _auth_headers(client, "a@example.com")
        headers_b = await _auth_headers(client, "b@example.com")
        composition = await _analyzed_composition(client, headers_a)

        response = await client.post(
            f"/api/v1/projects/{composition['id']}/feedback", headers=headers_b
        )

        assert response.status_code == 404

    async def test_returns_404_when_not_yet_analyzed(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)

        response = await client.post(
            f"/api/v1/projects/{composition['id']}/feedback", headers=headers
        )

        assert response.status_code == 404

    async def test_generates_feedback_for_the_requested_skill_level(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_ai(monkeypatch)
        headers = await _auth_headers(client)
        composition = await _analyzed_composition(client, headers)

        response = await client.post(
            f"/api/v1/projects/{composition['id']}/feedback",
            headers=headers,
            params={"skill_level": "beginner"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["skill_level"] == "beginner"
        assert body["summary"] == _FAKE_FEEDBACK.summary
        assert body["strengths"] == _FAKE_FEEDBACK.strengths
        assert body["issues"][0]["theory"]["concept"] == "Parallel fifths"
        assert body["suggestions"] == _FAKE_FEEDBACK.suggestions
        assert body["composition_id"] == composition["id"]

    async def test_defaults_to_intermediate_skill_level(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_ai(monkeypatch)
        headers = await _auth_headers(client)
        composition = await _analyzed_composition(client, headers)

        response = await client.post(
            f"/api/v1/projects/{composition['id']}/feedback", headers=headers
        )

        assert response.status_code == 200
        assert response.json()["skill_level"] == "intermediate"

    async def test_returns_503_when_the_ai_service_fails(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(*_args: Any, **_kwargs: Any) -> CompositionFeedback:
            raise AIServiceError("AI feedback is not configured (ANTHROPIC_API_KEY is unset).")

        monkeypatch.setattr("app.domains.feedback.service.generate_feedback", _raise)
        headers = await _auth_headers(client)
        composition = await _analyzed_composition(client, headers)

        response = await client.post(
            f"/api/v1/projects/{composition['id']}/feedback", headers=headers
        )

        assert response.status_code == 503


class TestReadFeedback:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000/feedback"
        )
        assert response.status_code == 401

    async def test_returns_404_when_none_generated_yet(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _analyzed_composition(client, headers)

        response = await client.get(
            f"/api/v1/projects/{composition['id']}/feedback", headers=headers
        )

        assert response.status_code == 404

    async def test_returns_previously_generated_feedback(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_ai(monkeypatch)
        headers = await _auth_headers(client)
        composition = await _analyzed_composition(client, headers)
        await client.post(
            f"/api/v1/projects/{composition['id']}/feedback",
            headers=headers,
            params={"skill_level": "advanced"},
        )

        response = await client.get(
            f"/api/v1/projects/{composition['id']}/feedback",
            headers=headers,
            params={"skill_level": "advanced"},
        )

        assert response.status_code == 200
        assert response.json()["summary"] == _FAKE_FEEDBACK.summary
