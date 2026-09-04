"""Roadmap, lesson player and progress endpoints.

Curriculum is read-only from the API's side - it arrives through the seed
loader, not through HTTP - so the only writes here are the ones that record
what a student did.

Routes address lessons and steps by slug rather than id. Slugs are the stable
identity of authored content (see `models`), which means a lesson URL is the
same in every environment and can be linked to from a lesson's own prose.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.domains.learning.schemas import RoadmapRead
from app.domains.learning.service import get_roadmap
from app.domains.users.models import User

router = APIRouter(prefix="/learning", tags=["learning"])


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
