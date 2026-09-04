"""Roadmap, lesson player and progress endpoints.

Curriculum is read-only from the API's side - it arrives through the seed
loader, not through HTTP - so the only writes here are the ones that record
what a student did.

Routes address lessons and steps by slug rather than id. Slugs are the stable
identity of authored content (see `models`), which means a lesson URL is the
same in every environment and can be linked to from a lesson's own prose.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.domains.learning.schemas import (
    LessonCompleteRead,
    LessonRead,
    ProgressSummary,
    QuizAnswerRequest,
    QuizAnswerResult,
    RoadmapRead,
    StepSeenRead,
)
from app.domains.learning.service import (
    LessonNotFoundError,
    StepKindError,
    StepNotFoundError,
    answer_quiz,
    complete_lesson,
    get_lesson,
    get_progress_summary,
    get_roadmap,
    mark_step_seen,
)
from app.domains.users.models import User

router = APIRouter(prefix="/learning", tags=["learning"])

_lesson_not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found.")
_step_not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step not found.")


@router.get("/roadmap", response_model=RoadmapRead)
async def read_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapRead:
    """Every stage and lesson, with this student's status on each.

    Returns the whole path in one response, locked to nothing: lessons the
    student hasn't reached come back exactly like the ones they have, marked
    `not_started`. The client draws the recommended order; it doesn't
    enforce it.
    """
    return await get_roadmap(db, current_user.id)


@router.get("/lessons/{lesson_slug}", response_model=LessonRead)
async def read_lesson(
    lesson_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonRead:
    """One lesson and its ordered steps.

    Quiz steps come back without their answer key - see `_public_step` in
    the service, where that stripping is enforced by the response type
    rather than by remembering to delete a field.

    A read, and only a read: opening a lesson doesn't start it. Progress
    begins when the student advances past a step.
    """
    try:
        return await get_lesson(db, current_user.id, lesson_slug)
    except LessonNotFoundError as exc:
        raise _lesson_not_found from exc


@router.post("/lessons/{lesson_slug}/steps/{step_slug}/answer", response_model=QuizAnswerResult)
async def answer_quiz_step(
    lesson_slug: str,
    step_slug: str,
    payload: QuizAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuizAnswerResult:
    """Grades one multiple-choice answer.

    The correct choice and the explanation come back whether the answer was
    right or wrong. Retries are unlimited and unpenalised, so there is
    nothing to protect by withholding them - and a student who got it wrong
    is exactly the one who needs the explanation.
    """
    try:
        return await answer_quiz(db, current_user.id, lesson_slug, step_slug, payload.choice_index)
    except LessonNotFoundError as exc:
        raise _lesson_not_found from exc
    except StepNotFoundError as exc:
        raise _step_not_found from exc
    except StepKindError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/lessons/{lesson_slug}/steps/{step_slug}/seen", response_model=StepSeenRead)
async def mark_step_seen_endpoint(
    lesson_slug: str,
    step_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StepSeenRead:
    """Records that the student has reached this step.

    The player calls this as each step comes into view, including the first,
    which is what moves a lesson from `not_started` to `in_progress` and
    what "continue where you left off" reads later.
    """
    try:
        return await mark_step_seen(db, current_user.id, lesson_slug, step_slug)
    except LessonNotFoundError as exc:
        raise _lesson_not_found from exc
    except StepNotFoundError as exc:
        raise _step_not_found from exc


@router.post("/lessons/{lesson_slug}/complete", response_model=LessonCompleteRead)
async def complete_lesson_endpoint(
    lesson_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonCompleteRead:
    """Marks a lesson complete and points at the next one.

    Idempotent: completing a finished lesson returns the original completion
    time rather than resetting it.
    """
    try:
        return await complete_lesson(db, current_user.id, lesson_slug)
    except LessonNotFoundError as exc:
        raise _lesson_not_found from exc


@router.get("/progress", response_model=ProgressSummary)
async def read_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgressSummary:
    """Totals per stage, plus the lesson to pick back up."""
    return await get_progress_summary(db, current_user.id)
