"""Standalone MusicXML upload + analysis.

Unlike `projects`, nothing here is persisted - the file is parsed in memory
and the structured analysis is returned directly. Parsing runs via
`asyncio.to_thread`: music21 is synchronous and CPU-bound, and blocking the
event loop for the time it takes to analyze a large score would stall every
other in-flight request.
"""

import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.domains.analysis.schemas import ScoreAnalysis
from app.domains.analysis.service import AnalysisError, analyze
from app.domains.users.models import User

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("", response_model=ScoreAnalysis)
async def analyze_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> ScoreAnalysis:
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

    try:
        return await asyncio.to_thread(analyze, content, file.filename or "upload.musicxml")
    except AnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
