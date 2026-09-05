"""Exam endpoints.

Exams are addressed by slug, the same reasoning as `learning.router`: a
slug is the stable identity of authored content, so an exam's URL survives
a fresh database and can be linked to from its own prose.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.domains.exams.schemas import ExamAttemptHistoryRead
from app.domains.exams.service import ExamNotFoundError, get_attempt_history
from app.domains.users.models import User

router = APIRouter(prefix="/exams", tags=["exams"])

_exam_not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found.")


@router.get("/{exam_slug}/history", response_model=ExamAttemptHistoryRead)
async def read_attempt_history(
    exam_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExamAttemptHistoryRead:
    """Every attempt this student has made at this exam, newest first."""
    try:
        return await get_attempt_history(db, current_user.id, exam_slug)
    except ExamNotFoundError as exc:
        raise _exam_not_found from exc
