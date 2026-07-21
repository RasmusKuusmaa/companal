import io
import uuid
import zipfile

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.projects.schemas import CompositionCreate, CompositionUpdate
from app.domains.projects.service import (
    CompositionNotFoundError,
    FileTooLargeError,
    InvalidMusicXmlFileError,
    VersionNotFoundError,
    add_version,
    create_composition,
    delete_composition,
    get_composition,
    get_version_file,
    list_compositions,
    list_versions,
    rename_composition,
)
from app.domains.users.models import User

VALID_MUSICXML = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Music</part-name></score-part></part-list>
  <part id="P1"><measure number="1"><note><rest/><duration>4</duration></note></measure></part>
</score-partwise>
"""


def _valid_mxl() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("META-INF/container.xml", "<container/>")
        archive.writestr("score.xml", VALID_MUSICXML.decode())
    return buffer.getvalue()


async def _make_user(db_session: AsyncSession, email: str = "composer@example.com") -> User:
    user = User(email=email, hashed_password="not-a-real-hash", full_name="Composer")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestCreateComposition:
    async def test_creates_with_zero_versions(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)

        composition = await create_composition(
            db_session, owner.id, CompositionCreate(title="Sonata No. 1")
        )

        assert composition.title == "Sonata No. 1"
        assert composition.version_count == 0
        assert composition.owner_id == owner.id


class TestListCompositions:
    async def test_scopes_to_owner(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session, "owner@example.com")
        other = await _make_user(db_session, "other@example.com")
        await create_composition(db_session, owner.id, CompositionCreate(title="Mine"))
        await create_composition(db_session, other.id, CompositionCreate(title="Not mine"))

        compositions = await list_compositions(db_session, owner.id)

        assert [c.title for c in compositions] == ["Mine"]


class TestGetComposition:
    async def test_raises_for_another_owner(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session, "owner@example.com")
        other = await _make_user(db_session, "other@example.com")
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        with pytest.raises(CompositionNotFoundError):
            await get_composition(db_session, other.id, composition.id)


class TestRenameComposition:
    async def test_updates_title(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="Old"))

        renamed = await rename_composition(
            db_session, owner.id, composition.id, CompositionUpdate(title="New")
        )

        assert renamed.title == "New"

    async def test_raises_for_another_owner(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session, "owner@example.com")
        other = await _make_user(db_session, "other@example.com")
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        with pytest.raises(CompositionNotFoundError):
            await rename_composition(
                db_session, other.id, composition.id, CompositionUpdate(title="Hijacked")
            )


class TestDeleteComposition:
    async def test_removes_the_composition(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        await delete_composition(db_session, owner.id, composition.id)

        with pytest.raises(CompositionNotFoundError):
            await get_composition(db_session, owner.id, composition.id)

    async def test_raises_for_another_owner(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session, "owner@example.com")
        other = await _make_user(db_session, "other@example.com")
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        with pytest.raises(CompositionNotFoundError):
            await delete_composition(db_session, other.id, composition.id)


class TestAddVersion:
    async def test_first_upload_is_version_one(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        version = await add_version(
            db_session, owner.id, composition.id, "piece.musicxml", VALID_MUSICXML
        )

        assert version.version_number == 1
        assert version.file_size == len(VALID_MUSICXML)
        await db_session.refresh(composition)
        assert composition.version_count == 1

    async def test_second_upload_increments_the_version_number(
        self, db_session: AsyncSession
    ) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))
        await add_version(db_session, owner.id, composition.id, "v1.musicxml", VALID_MUSICXML)

        second = await add_version(
            db_session, owner.id, composition.id, "v2.musicxml", VALID_MUSICXML
        )

        assert second.version_number == 2

    async def test_accepts_a_valid_mxl_archive(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        version = await add_version(db_session, owner.id, composition.id, "piece.mxl", _valid_mxl())

        assert version.original_filename == "piece.mxl"

    async def test_rejects_an_unsupported_extension(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        with pytest.raises(InvalidMusicXmlFileError):
            await add_version(db_session, owner.id, composition.id, "piece.pdf", b"not xml")

    async def test_rejects_malformed_xml(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        with pytest.raises(InvalidMusicXmlFileError):
            await add_version(db_session, owner.id, composition.id, "piece.xml", b"<not-closed>")

    async def test_rejects_well_formed_xml_with_the_wrong_root_element(
        self, db_session: AsyncSession
    ) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        with pytest.raises(InvalidMusicXmlFileError):
            await add_version(
                db_session, owner.id, composition.id, "piece.xml", b"<not-musicxml/>"
            )

    async def test_rejects_a_zip_missing_its_container_manifest(
        self, db_session: AsyncSession
    ) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("score.xml", "not a real container")

        with pytest.raises(InvalidMusicXmlFileError):
            await add_version(db_session, owner.id, composition.id, "piece.mxl", buffer.getvalue())

    async def test_rejects_a_file_over_the_size_limit(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("app.domains.projects.service.settings.MAX_UPLOAD_SIZE_BYTES", 10)
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        with pytest.raises(FileTooLargeError):
            await add_version(
                db_session, owner.id, composition.id, "piece.musicxml", VALID_MUSICXML
            )

    async def test_raises_for_another_owner(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session, "owner@example.com")
        other = await _make_user(db_session, "other@example.com")
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        with pytest.raises(CompositionNotFoundError):
            await add_version(
                db_session, other.id, composition.id, "piece.musicxml", VALID_MUSICXML
            )


class TestListVersions:
    async def test_orders_newest_first(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))
        await add_version(db_session, owner.id, composition.id, "v1.musicxml", VALID_MUSICXML)
        await add_version(db_session, owner.id, composition.id, "v2.musicxml", VALID_MUSICXML)

        versions = await list_versions(db_session, owner.id, composition.id)

        assert [v.version_number for v in versions] == [2, 1]


class TestGetVersionFile:
    async def test_returns_the_uploaded_bytes(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))
        uploaded = await add_version(
            db_session, owner.id, composition.id, "piece.musicxml", VALID_MUSICXML
        )

        version, content = await get_version_file(
            db_session, owner.id, composition.id, uploaded.id
        )

        assert content == VALID_MUSICXML
        assert version.id == uploaded.id

    async def test_raises_for_an_unknown_version(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        composition = await create_composition(db_session, owner.id, CompositionCreate(title="X"))

        with pytest.raises(VersionNotFoundError):
            await get_version_file(db_session, owner.id, composition.id, uuid.uuid4())
