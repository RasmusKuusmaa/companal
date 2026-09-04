"""Converting between the editor's notation document and MusicXML.

Nothing here is persisted - this is a pure conversion boundary, used both
for the editor's own "preview as engraved notation" (export) and for
opening an uploaded score in the editor (import, added alongside
`importer.py`). Composition submissions go through the same conversion
internally, but as part of the learning domain's grading flow, not this
router.
"""

import asyncio

from fastapi import APIRouter, Depends, Response

from app.core.dependencies import get_current_user
from app.domains.notation.builder import to_musicxml_bytes
from app.domains.notation.schemas import NotationDocument
from app.domains.users.models import User

router = APIRouter(prefix="/notation", tags=["notation"])

_MUSICXML_CONTENT_TYPE = "application/vnd.recordare.musicxml+xml"


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
