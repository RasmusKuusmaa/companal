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
from app.domains.learning.schemas import LessonRead, RoadmapRead
from app.domains.learning.service import (
    LessonNotFoundError,
    get_lesson,
    get_roadmap,
)
from app.domains.users.models import User

router = APIRouter(prefix="/learning", tags=["learning"])

_lesson_not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found.")


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
