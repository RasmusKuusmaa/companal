"""Converting between the editor's notation document and MusicXML.

Nothing here is persisted - this is a pure conversion boundary, used both
for the editor's own "preview as engraved notation" (export) and for
opening an uploaded score in the editor (import, added alongside
`importer.py`). Composition submissions go through the same conversion
internally, but as part of the learning domain's grading flow, not this
router.
"""

import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.domains.notation.builder import to_musicxml_bytes
from app.domains.notation.importer import (
    NotationImportError,
    import_musicxml,
    validate_musicxml_upload,
)
from app.domains.notation.schemas import NotationDocument
from app.domains.users.models import User

router = APIRouter(prefix="/notation", tags=["notation"])

_MUSICXML_CONTENT_TYPE = "application/vnd.recordare.musicxml+xml"


async def _read_upload(file: UploadFile) -> bytes:
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty."
        )
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the maximum allowed upload size.",
        )
    return content


@router.post("/musicxml")
async def export_musicxml(
    document: NotationDocument,
    current_user: User = Depends(get_current_user),
) -> Response:
    """Renders a notation document to MusicXML.

    Used for the editor's own preview (rendering through OpenSheetMusicDisplay
    the same way an uploaded score is shown) and as the first step of
    grading a submission, called directly rather than over HTTP in that path.
    """
    content = await asyncio.to_thread(to_musicxml_bytes, document)
    return Response(content=content, media_type=_MUSICXML_CONTENT_TYPE)


@router.post("/import", response_model=NotationDocument)
async def import_score(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> NotationDocument:
    """Opens an uploaded score in the editor.

    Only what the editor can represent comes back - see `importer.py` for
    exactly what that excludes (tuplets, chords, anything past a double
    sharp/flat). A file outside that is a 400, not a best-effort guess.

    Validated with the same `validate_musicxml_upload` a composition
    version upload goes through (`projects.service`) before music21 ever
    sees the bytes - wrong extension, a `.mxl` that isn't really a zip, and
    malformed XML all get the same clear rejection here that they do there.
    """
    filename = file.filename or "upload.musicxml"
    content = await _read_upload(file)
    try:
        validate_musicxml_upload(filename, content)
        return await asyncio.to_thread(import_musicxml, content, filename)
    except NotationImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
