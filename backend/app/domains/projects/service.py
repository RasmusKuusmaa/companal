"""Composition/version CRUD, MusicXML upload validation, and file retrieval.

Every read/write is scoped to `owner_id` - there's no cross-user access yet
(no collaborators, no teacher/admin override), so a composition that
exists but belongs to someone else is indistinguishable from one that
doesn't exist at all: both raise `CompositionNotFoundError`, which the
router maps to a 404. That avoids leaking which composition ids are in use
by other accounts.

Upload validation is deliberately shallow: enough to reject obviously-wrong
files (wrong extension, malformed XML, a `.mxl` that isn't actually a zip)
without parsing musical content - that's the analysis domain's job, not
this one's.
"""

import io
import uuid
import zipfile
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.core.config import settings
from app.domains.projects.models import Composition, Version
from app.domains.projects.schemas import CompositionCreate, CompositionUpdate

_MUSICXML_ROOT_TAGS = {"score-partwise", "score-timewise"}
_ALLOWED_EXTENSIONS = {".xml", ".musicxml", ".mxl"}


class ProjectError(Exception):
    """Base class for project-domain failures; the router maps these to HTTP responses."""


class CompositionNotFoundError(ProjectError):
    pass


class VersionNotFoundError(ProjectError):
    pass


class InvalidMusicXmlFileError(ProjectError):
    pass


class FileTooLargeError(ProjectError):
    pass


class VersionConflictError(ProjectError):
    pass


async def _get_owned_composition(
    db: AsyncSession, composition_id: uuid.UUID, owner_id: uuid.UUID
) -> Composition:
    composition = await db.scalar(
        select(Composition).where(
            Composition.id == composition_id, Composition.owner_id == owner_id
        )
    )
    if composition is None:
        raise CompositionNotFoundError
    return composition


def _validate_musicxml(filename: str, content: bytes) -> str:
    """Returns the normalized (lowercased) file extension, or raises
    `InvalidMusicXmlFileError`."""
    if not content:
        raise InvalidMusicXmlFileError("The uploaded file is empty.")

    extension = Path(filename).suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        raise InvalidMusicXmlFileError(
            "Unsupported file type. Upload a .musicxml, .xml, or .mxl file."
        )

    if extension == ".mxl":
        buffer = io.BytesIO(content)
        if not zipfile.is_zipfile(buffer):
            raise InvalidMusicXmlFileError("The .mxl file is not a valid compressed archive.")
        with zipfile.ZipFile(buffer) as archive:
            if "META-INF/container.xml" not in archive.namelist():
                raise InvalidMusicXmlFileError(
                    "The .mxl archive is missing its META-INF/container.xml manifest."
                )
        return extension

    # Parsed with defusedxml, not stdlib ElementTree - this is untrusted
    # user input, and a plain XML parser is vulnerable to entity-expansion
    # ("billion laughs") and external-entity attacks.
    try:
        root = ElementTree.fromstring(content)
    except (ElementTree.ParseError, DefusedXmlException) as exc:
        raise InvalidMusicXmlFileError("The file is not well-formed XML.") from exc

    if root.tag not in _MUSICXML_ROOT_TAGS:
        raise InvalidMusicXmlFileError(
            "The file's root element is not <score-partwise> or <score-timewise>."
        )
    return extension


async def create_composition(
    db: AsyncSession, owner_id: uuid.UUID, payload: CompositionCreate
) -> Composition:
    composition = Composition(owner_id=owner_id, title=payload.title)
    db.add(composition)
    await db.commit()
    await db.refresh(composition)
    return composition


async def list_compositions(db: AsyncSession, owner_id: uuid.UUID) -> Sequence[Composition]:
    result = await db.scalars(
        select(Composition)
        .where(Composition.owner_id == owner_id)
        .order_by(Composition.updated_at.desc())
    )
    return result.all()


async def get_composition(
    db: AsyncSession, owner_id: uuid.UUID, composition_id: uuid.UUID
) -> Composition:
    return await _get_owned_composition(db, composition_id, owner_id)


async def rename_composition(
    db: AsyncSession,
    owner_id: uuid.UUID,
    composition_id: uuid.UUID,
    payload: CompositionUpdate,
) -> Composition:
    composition = await _get_owned_composition(db, composition_id, owner_id)
    composition.title = payload.title
    await db.commit()
    await db.refresh(composition)
    return composition


async def delete_composition(
    db: AsyncSession, owner_id: uuid.UUID, composition_id: uuid.UUID
) -> None:
    composition = await _get_owned_composition(db, composition_id, owner_id)
    await db.delete(composition)
    await db.commit()
    # Best-effort: the DB row (source of truth) is already gone either way.
    await storage.delete_directory(str(composition_id))


async def list_versions(
    db: AsyncSession, owner_id: uuid.UUID, composition_id: uuid.UUID
) -> Sequence[Version]:
    await _get_owned_composition(db, composition_id, owner_id)
    result = await db.scalars(
        select(Version)
        .where(Version.composition_id == composition_id)
        .order_by(Version.version_number.desc())
    )
    return result.all()


async def add_version(
    db: AsyncSession,
    owner_id: uuid.UUID,
    composition_id: uuid.UUID,
    filename: str,
    content: bytes,
) -> Version:
    composition = await _get_owned_composition(db, composition_id, owner_id)

    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLargeError

    extension = _validate_musicxml(filename, content)

    next_number = composition.version_count + 1
    version_id = uuid.uuid4()
    storage_key = f"{composition_id}/{version_id}{extension}"

    # Written before the DB commit: if the write fails, we've lost nothing
    # but a disk write; if the commit failed after the write instead, we'd
    # have a Version row pointing at a file that doesn't exist.
    await storage.save_file(storage_key, content)

    version = Version(
        id=version_id,
        composition_id=composition.id,
        version_number=next_number,
        original_filename=filename[:255],
        storage_key=storage_key,
        file_size=len(content),
    )
    composition.version_count = next_number
    composition.updated_at = datetime.now(UTC)
    db.add(version)
    try:
        await db.commit()
    except IntegrityError as exc:
        # TOCTOU: two uploads for the same composition racing on
        # `next_number` (e.g. two tabs). Extremely unlikely given
        # single-owner access, but the unique constraint on
        # (composition_id, version_number) catches it if it happens.
        await db.rollback()
        await storage.delete_file(storage_key)
        raise VersionConflictError from exc

    await db.refresh(version)
    return version


async def get_version_file(
    db: AsyncSession,
    owner_id: uuid.UUID,
    composition_id: uuid.UUID,
    version_id: uuid.UUID,
) -> tuple[Version, bytes]:
    await _get_owned_composition(db, composition_id, owner_id)
    version = await db.scalar(
        select(Version).where(
            Version.id == version_id, Version.composition_id == composition_id
        )
    )
    if version is None:
        raise VersionNotFoundError

    content = await storage.read_file(version.storage_key)
    return version, content
