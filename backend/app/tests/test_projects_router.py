import uuid
from pathlib import Path
from typing import Any, cast

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.projects.models import CompositionAnalysis

_FIXTURES = Path(__file__).parent / "fixtures"
# Four real parts, so all three engines have something to read.
SATB = (_FIXTURES / "harmony_satb.musicxml").read_bytes()
# One line: melody and rhythm run, harmony has no chords to read.
MELODY_LINE = (_FIXTURES / "melody_line.musicxml").read_bytes()

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


class TestAnalyzeVersion:
    async def test_returns_the_structured_analysis(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        uploaded = (await _upload_version(client, headers, composition["id"])).json()

        response = await client.get(
            f"/api/v1/projects/{composition['id']}/versions/{uploaded['id']}/analysis",
            headers=headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["part_count"] == 1
        assert body["measures"][0]["notes"][0]["is_rest"] is True

    async def test_returns_404_for_an_unknown_version(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)

        response = await client.get(
            f"/api/v1/projects/{composition['id']}/versions/"
            "00000000-0000-0000-0000-000000000000/analysis",
            headers=headers,
        )

        assert response.status_code == 404

    async def test_returns_404_for_another_users_composition(self, client: AsyncClient) -> None:
        headers_a = await _auth_headers(client, "a@example.com")
        headers_b = await _auth_headers(client, "b@example.com")
        composition = await _create_composition(client, headers_a)
        uploaded = (await _upload_version(client, headers_a, composition["id"])).json()

        response = await client.get(
            f"/api/v1/projects/{composition['id']}/versions/{uploaded['id']}/analysis",
            headers=headers_b,
        )

        assert response.status_code == 404


class TestAnalyzeComposition:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000/analyze"
        )
        assert response.status_code == 401

    async def test_returns_404_for_an_unknown_composition(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)

        response = await client.post(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000/analyze", headers=headers
        )

        assert response.status_code == 404

    async def test_returns_404_for_another_users_composition(self, client: AsyncClient) -> None:
        headers_a = await _auth_headers(client, "a@example.com")
        headers_b = await _auth_headers(client, "b@example.com")
        composition = await _create_composition(client, headers_a)
        await _upload_version(client, headers_a, composition["id"], content=SATB)

        response = await client.post(
            f"/api/v1/projects/{composition['id']}/analyze", headers=headers_b
        )

        assert response.status_code == 404

    async def test_returns_404_when_nothing_has_been_uploaded(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)

        response = await client.post(
            f"/api/v1/projects/{composition['id']}/analyze", headers=headers
        )

        assert response.status_code == 404
        assert "no uploaded versions" in response.json()["detail"]

    async def test_returns_all_three_analyses_and_an_overall_score(
        self, client: AsyncClient
    ) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        uploaded = (await _upload_version(client, headers, composition["id"], content=SATB)).json()

        response = await client.post(
            f"/api/v1/projects/{composition['id']}/analyze", headers=headers
        )

        assert response.status_code == 200
        body = response.json()
        assert body["melody_analysis"] is not None
        assert body["harmony_analysis"] is not None
        assert body["rhythm_analysis"] is not None
        assert body["unavailable"] == []
        assert 0.0 <= body["overall_score"] <= 100.0
        # Each engine's own report comes through whole.
        assert set(body["melody_analysis"]) == {"score", "strengths", "issues", "technical_data"}
        assert body["harmony_analysis"]["technical_data"]["key"] == "C major"
        # ...alongside the identity of the version that was analyzed.
        assert body["composition_id"] == composition["id"]
        assert body["version_id"] == uploaded["id"]
        assert body["version_number"] == 1

    async def test_overall_score_is_the_mean_of_the_engine_scores(
        self, client: AsyncClient
    ) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        await _upload_version(client, headers, composition["id"], content=SATB)

        body = (
            await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)
        ).json()

        scores = [
            body["melody_analysis"]["score"],
            body["harmony_analysis"]["score"],
            body["rhythm_analysis"]["score"],
        ]
        assert body["overall_score"] == pytest.approx(sum(scores) / 3, abs=0.05)

    async def test_analyzes_the_newest_version(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        await _upload_version(client, headers, composition["id"], content=MELODY_LINE)
        second = (await _upload_version(client, headers, composition["id"], content=SATB)).json()

        body = (
            await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)
        ).json()

        assert body["version_id"] == second["id"]
        assert body["version_number"] == 2
        # The SATB upload has harmony; the earlier single line did not.
        assert body["harmony_analysis"] is not None

    async def test_reports_an_engine_that_cannot_read_the_score(self, client: AsyncClient) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        await _upload_version(client, headers, composition["id"], content=MELODY_LINE)

        body = (
            await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)
        ).json()

        assert body["melody_analysis"] is not None
        assert body["rhythm_analysis"] is not None
        assert body["harmony_analysis"] is None
        assert [u["engine"] for u in body["unavailable"]] == ["harmony"]
        # The absent engine is left out of the mean, not counted as zero.
        ran = [body["melody_analysis"]["score"], body["rhythm_analysis"]["score"]]
        assert body["overall_score"] == pytest.approx(sum(ran) / 2, abs=0.05)

    async def test_returns_422_when_no_engine_can_analyze_the_file(
        self, client: AsyncClient
    ) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        # The shared fixture is a single whole rest - nothing to analyze.
        await _upload_version(client, headers, composition["id"], content=VALID_MUSICXML)

        response = await client.post(
            f"/api/v1/projects/{composition['id']}/analyze", headers=headers
        )

        assert response.status_code == 422

    async def test_stores_the_analysis(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        uploaded = (await _upload_version(client, headers, composition["id"], content=SATB)).json()

        body = (
            await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)
        ).json()

        stored = (
            await db_session.scalars(
                select(CompositionAnalysis).where(
                    CompositionAnalysis.version_id == uuid.UUID(uploaded["id"])
                )
            )
        ).all()
        assert len(stored) == 1
        row = stored[0]
        assert row.overall_score == body["overall_score"]
        assert row.melody_score == body["melody_analysis"]["score"]
        assert row.harmony_score == body["harmony_analysis"]["score"]
        assert row.rhythm_score == body["rhythm_analysis"]["score"]
        # The stored documents are the same JSON the endpoint returned.
        assert row.harmony_analysis == body["harmony_analysis"]
        assert row.unavailable == []

    async def test_stores_a_null_score_for_an_engine_that_could_not_run(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        await _upload_version(client, headers, composition["id"], content=MELODY_LINE)

        await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)

        row = await db_session.scalar(select(CompositionAnalysis))
        assert row is not None
        assert row.harmony_score is None
        assert row.harmony_analysis is None
        assert row.melody_score is not None
        assert [u["engine"] for u in row.unavailable] == ["harmony"]

        # Stored as SQL NULL, not the JSON value 'null' - otherwise this
        # IS NULL filter silently matches nothing.
        missing = await db_session.scalar(
            select(CompositionAnalysis).where(CompositionAnalysis.harmony_analysis.is_(None))
        )
        assert missing is not None
        assert missing.id == row.id

    async def test_re_analysing_overwrites_rather_than_adding_a_row(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        await _upload_version(client, headers, composition["id"], content=SATB)

        first = (
            await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)
        ).json()
        second = (
            await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)
        ).json()

        rows = (await db_session.scalars(select(CompositionAnalysis))).all()
        assert len(rows) == 1
        # The engines are deterministic, so a re-run reproduces the analysis.
        assert first["overall_score"] == second["overall_score"]

    async def test_keeps_one_analysis_per_version(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        await _upload_version(client, headers, composition["id"], content=MELODY_LINE)
        await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)

        await _upload_version(client, headers, composition["id"], content=SATB)
        await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)

        rows = (await db_session.scalars(select(CompositionAnalysis))).all()
        assert len(rows) == 2
        assert {r.harmony_score is None for r in rows} == {True, False}

    async def test_deleting_the_composition_removes_its_analyses(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        headers = await _auth_headers(client)
        composition = await _create_composition(client, headers)
        await _upload_version(client, headers, composition["id"], content=SATB)
        await client.post(f"/api/v1/projects/{composition['id']}/analyze", headers=headers)

        await client.delete(f"/api/v1/projects/{composition['id']}", headers=headers)

        rows = (await db_session.scalars(select(CompositionAnalysis))).all()
        assert rows == []
