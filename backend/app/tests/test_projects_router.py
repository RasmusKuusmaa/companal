from typing import Any, cast

import pytest
from httpx import AsyncClient

VALID_MUSICXML = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Music</part-name></score-part></part-list>
  <part id="P1"><measure number="1"><note><rest/><duration>4</duration></note></measure></part>
</score-partwise>
"""


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


async def _upload_version(
    client: AsyncClient,
    headers: dict[str, str],
    composition_id: str,
    filename: str = "piece.musicxml",
    content: bytes = VALID_MUSICXML,
) -> Any:
    return await client.post(
        f"/api/v1/projects/{composition_id}/versions",
        headers=headers,
        files={"file": (filename, content, "application/xml")},
    )


class TestCreateProject:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/projects", json={"title": "X"})
        assert response.status_code == 401

    async def test_creates_a_composition(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)

        body = await _create_composition(client, headers, "Fugue in D minor")

        assert body["title"] == "Fugue in D minor"
        assert body["version_count"] == 0

    async def test_rejects_a_blank_title(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)

        response = await client.post("/api/v1/projects", json={"title": ""}, headers=headers)

        assert response.status_code == 422


class TestListProjects:
    async def test_scopes_to_the_authenticated_user(self, client: AsyncClient) -> None:
        headers_a = await _auth_headers(client, "a@example.com")
        headers_b = await _auth_headers(client, "b@example.com")
        await _create_composition(client, headers_a, "Mine")
        await _create_composition(client, headers_b, "Not mine")

        response = await client.get("/api/v1/projects", headers=headers_a)

        assert response.status_code == 200
        titles = [c["title"] for c in response.json()]
        assert titles == ["Mine"]


class TestGetProject:
    async def test_returns_404_for_an_unknown_id(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)

        response = await client.get(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000", headers=headers
        )

        assert response.status_code == 404

    async def test_returns_404_for_another_users_composition(self, client: AsyncClient) -> None:
        headers_a = await _auth_headers(client, "a@example.com")
        headers_b = await _auth_headers(client, "b@example.com")
        composition = await _create_composition(client, headers_a)

        response = await client.get(f"/api/v1/projects/{composition['id']}", headers=headers_b)

        assert response.status_code == 404


class TestRenameProject:
    async def test_updates_the_title(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers, "Old Title")

        response = await client.patch(
            f"/api/v1/projects/{composition['id']}", json={"title": "New Title"}, headers=headers
        )

        assert response.status_code == 200
        assert response.json()["title"] == "New Title"


class TestDeleteProject:
    async def test_removes_the_composition(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)

        delete_response = await client.delete(
            f"/api/v1/projects/{composition['id']}", headers=headers
        )
        assert delete_response.status_code == 204

        get_response = await client.get(f"/api/v1/projects/{composition['id']}", headers=headers)
        assert get_response.status_code == 404


class TestUploadVersion:
    async def test_uploads_the_first_version(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)

        response = await _upload_version(client, headers, composition["id"])

        assert response.status_code == 201
        body = response.json()
        assert body["version_number"] == 1
        assert body["original_filename"] == "piece.musicxml"

    async def test_rejects_a_non_musicxml_file(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)

        response = await _upload_version(
            client, headers, composition["id"], "notes.pdf", b"%PDF-1.4"
        )

        assert response.status_code == 400

    async def test_rejects_a_file_over_the_size_limit(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("app.domains.projects.service.settings.MAX_UPLOAD_SIZE_BYTES", 10)
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)

        response = await _upload_version(client, headers, composition["id"])

        assert response.status_code == 413

    async def test_returns_404_for_another_users_composition(self, client: AsyncClient) -> None:
        headers_a = await _auth_headers(client, "a@example.com")
        headers_b = await _auth_headers(client, "b@example.com")
        composition = await _create_composition(client, headers_a)

        response = await _upload_version(client, headers_b, composition["id"])

        assert response.status_code == 404


class TestListVersions:
    async def test_orders_newest_first(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        await _upload_version(client, headers, composition["id"], "v1.musicxml")
        await _upload_version(client, headers, composition["id"], "v2.musicxml")

        response = await client.get(
            f"/api/v1/projects/{composition['id']}/versions", headers=headers
        )

        assert response.status_code == 200
        assert [v["version_number"] for v in response.json()] == [2, 1]


class TestDownloadVersion:
    async def test_returns_the_uploaded_content(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        uploaded = (await _upload_version(client, headers, composition["id"])).json()

        response = await client.get(
            f"/api/v1/projects/{composition['id']}/versions/{uploaded['id']}/file",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.content == VALID_MUSICXML
        assert "piece.musicxml" in response.headers["content-disposition"]

    async def test_returns_404_for_an_unknown_version(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)

        response = await client.get(
            f"/api/v1/projects/{composition['id']}/versions/"
            "00000000-0000-0000-0000-000000000000/file",
            headers=headers,
        )

        assert response.status_code == 404
