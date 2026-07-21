"""Composition/version endpoints.

Every route is scoped to the authenticated user via `get_current_user`; the
service layer treats "exists but belongs to someone else" the same as
"doesn't exist" (see projects/service.py), so all not-found/not-yours cases
surface here as a plain 404.
"""

import re
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.domains.projects.schemas import (
    CompositionCreate,
    CompositionRead,
    CompositionUpdate,
    VersionRead,
)
from app.domains.projects.service import (
    CompositionNotFoundError,
    FileTooLargeError,
    InvalidMusicXmlFileError,
    VersionConflictError,
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

router = APIRouter(prefix="/projects", tags=["projects"])

_CONTENT_TYPES = {
    ".xml": "application/vnd.recordare.musicxml+xml",
    ".musicxml": "application/vnd.recordare.musicxml+xml",
    ".mxl": "application/vnd.recordare.musicxml",
}

_UNSAFE_HEADER_CHARS = re.compile(r'[\r\n"\\]')

_composition_not_found = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Composition not found."
)


def _content_disposition(filename: str) -> str:
    """Builds a `Content-Disposition` header from a user-supplied filename.

    The filename is untrusted (it's whatever the uploader's browser sent),
    so it's never interpolated into the header raw: an ASCII fallback with
    quotes/backslashes/CR/LF stripped guards against header injection for
    old clients, and an RFC 5987 percent-encoded `filename*` gives modern
    browsers the real (possibly non-ASCII) name.
    """
    ascii_name = filename.encode("ascii", "replace").decode("ascii")
    ascii_fallback = _UNSAFE_HEADER_CHARS.sub("_", ascii_name)
    encoded = quote(filename, safe="")
    return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded}'


@router.post("", response_model=CompositionRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: CompositionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompositionRead:
    composition = await create_composition(db, current_user.id, payload)
    return CompositionRead.model_validate(composition)


@router.get("", response_model=list[CompositionRead])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CompositionRead]:
    compositions = await list_compositions(db, current_user.id)
    return [CompositionRead.model_validate(c) for c in compositions]


@router.get("/{composition_id}", response_model=CompositionRead)
async def get_project(
    composition_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompositionRead:
    try:
        composition = await get_composition(db, current_user.id, composition_id)
    except CompositionNotFoundError as exc:
        raise _composition_not_found from exc
    return CompositionRead.model_validate(composition)


@router.patch("/{composition_id}", response_model=CompositionRead)
async def rename_project(
    composition_id: uuid.UUID,
    payload: CompositionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompositionRead:
    try:
        composition = await rename_composition(db, current_user.id, composition_id, payload)
    except CompositionNotFoundError as exc:
        raise _composition_not_found from exc
    return CompositionRead.model_validate(composition)


@router.delete("/{composition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    composition_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await delete_composition(db, current_user.id, composition_id)
    except CompositionNotFoundError as exc:
        raise _composition_not_found from exc


@router.get("/{composition_id}/versions", response_model=list[VersionRead])
async def list_project_versions(
    composition_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VersionRead]:
    try:
        versions = await list_versions(db, current_user.id, composition_id)
    except CompositionNotFoundError as exc:
        raise _composition_not_found from exc
    return [VersionRead.model_validate(v) for v in versions]


@router.post(
    "/{composition_id}/versions",
    response_model=VersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_project_version(
    composition_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VersionRead:
    content = await file.read()
    try:
        version = await add_version(
            db, current_user.id, composition_id, file.filename or "upload.musicxml", content
        )
    except CompositionNotFoundError as exc:
        raise _composition_not_found from exc
    except InvalidMusicXmlFileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the maximum allowed upload size.",
        ) from exc
    except VersionConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not save this version, please retry the upload.",
        ) from exc
    return VersionRead.model_validate(version)


@router.get("/{composition_id}/versions/{version_id}/file")
async def download_project_version(
    composition_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        version, content = await get_version_file(db, current_user.id, composition_id, version_id)
    except CompositionNotFoundError as exc:
        raise _composition_not_found from exc
    except VersionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Version not found."
        ) from exc

    extension = Path(version.storage_key).suffix.lower()
    media_type = _CONTENT_TYPES.get(extension, "application/octet-stream")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": _content_disposition(version.original_filename)},
    )
