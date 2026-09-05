"""Exam endpoints.

Exams are addressed by slug, the same reasoning as `learning.router`: a
slug is the stable identity of authored content, so an exam's URL survives
a fresh database and can be linked to from its own prose. Attempts and
their questions are addressed by id instead - they're never linked to from
anywhere but the exam session that created them.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.features import Feature, tier_has_feature
from app.domains.billing import service as billing_service
from app.domains.exams.schemas import (
    ExamAnswerRead,
    ExamAnswerSubmission,
    ExamAttemptHistoryRead,
    ExamAttemptResultRead,
    ExamAttemptStartRead,
    ExamSubmitRequest,
    ExamSummary,
)
from app.domains.exams.service import (
    ExamAnswerKindMismatchError,
    ExamAttemptAlreadySubmittedError,
    ExamAttemptNotFoundError,
    ExamNotFoundError,
    ExamQuestionNotFoundError,
    answer_question,
    get_attempt_history,
    grade_attempt,
    list_exams,
    start_attempt,
)
from app.domains.users.models import User

router = APIRouter(prefix="/exams", tags=["exams"])

_exam_not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found.")
_attempt_not_found = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found."
)
_question_not_found = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Question not found."
)
_already_submitted = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="This attempt has already been submitted."
)


@router.get("", response_model=list[ExamSummary])
async def read_exams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ExamSummary]:
    """Every exam, in position order - one per stage, plus the final."""
    return await list_exams(db)


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


@router.post("/{exam_slug}/attempts", response_model=ExamAttemptStartRead)
async def start_attempt_endpoint(
    exam_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExamAttemptStartRead:
    """Starts a new attempt - always a fresh one, never a resume of an
    earlier one at the same exam (see `service.start_attempt`)."""
    try:
        return await start_attempt(db, current_user.id, exam_slug)
    except ExamNotFoundError as exc:
        raise _exam_not_found from exc


@router.post(
    "/attempts/{attempt_id}/questions/{question_id}/answer", response_model=ExamAnswerRead
)
async def answer_question_endpoint(
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: ExamAnswerSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExamAnswerRead:
    """Holds one answer. Nothing is graded until the attempt is submitted,
    and answering the same question again replaces what was held."""
    try:
        return await answer_question(
            db, current_user.id, attempt_id, question_id, payload.answer
        )
    except ExamAttemptNotFoundError as exc:
        raise _attempt_not_found from exc
    except ExamQuestionNotFoundError as exc:
        raise _question_not_found from exc
    except ExamAttemptAlreadySubmittedError as exc:
        raise _already_submitted from exc
    except ExamAnswerKindMismatchError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/attempts/{attempt_id}/submit", response_model=ExamAttemptResultRead)
async def submit_attempt_endpoint(
    attempt_id: uuid.UUID,
    payload: ExamSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExamAttemptResultRead:
    """Grades every held answer and marks the attempt submitted.

    `with_ai_feedback` is a hard tier gate, not a quota - unlike lesson
    composition feedback, free tier never gets the exam rubric writeup
    regardless of usage (see `core.features`), so asking for it without
    premium is rejected here rather than silently coming back empty.
    """
    if payload.with_ai_feedback:
        tier = await billing_service.get_tier(db, current_user.id)
        if not tier_has_feature(tier, Feature.AI_EXAM_RUBRIC_GRADING):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "upgrade_required",
                    "feature": Feature.AI_EXAM_RUBRIC_GRADING.value,
                    "tier": tier.value,
                },
            )

    try:
        return await grade_attempt(
            db,
            current_user.id,
            attempt_id,
            with_ai_feedback=payload.with_ai_feedback,
            skill_level=payload.skill_level,
        )
    except ExamAttemptNotFoundError as exc:
        raise _attempt_not_found from exc
    except ExamAttemptAlreadySubmittedError as exc:
        raise _already_submitted from exc
