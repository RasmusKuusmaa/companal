from pathlib import Path

import pytest
from httpx import AsyncClient

_FIXTURES = Path(__file__).parent / "fixtures"
SIMPLE_SCORE = (_FIXTURES / "simple_score.musicxml").read_bytes()


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


class TestAnalyzeUpload:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/analysis", files={"file": ("piece.musicxml", SIMPLE_SCORE, "application/xml")}
        )
        assert response.status_code == 401

    async def test_returns_the_structured_analysis(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/analysis",
            headers=headers,
            files={"file": ("piece.musicxml", SIMPLE_SCORE, "application/xml")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["key"] == "C major"
        assert body["tempo"] == 90
        assert body["time_signature"] == "4/4"
        assert len(body["measures"]) == 2
        assert body["chords"] == []

    async def test_rejects_an_empty_file(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/analysis",
            headers=headers,
            files={"file": ("piece.musicxml", b"", "application/xml")},
        )

        assert response.status_code == 400

    async def test_rejects_unparseable_content(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/analysis",
            headers=headers,
            files={"file": ("piece.musicxml", b"not xml", "application/xml")},
        )

        assert response.status_code == 400

    async def test_rejects_a_file_over_the_size_limit(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("app.domains.analysis.router.settings.MAX_UPLOAD_SIZE_BYTES", 10)
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/analysis",
            headers=headers,
            files={"file": ("piece.musicxml", SIMPLE_SCORE, "application/xml")},
        )

        assert response.status_code == 413
