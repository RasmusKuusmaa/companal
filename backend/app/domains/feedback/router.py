"""AI composition feedback endpoints.

Nested under a composition, like the analyze endpoints in `projects.router`:
feedback always describes one composition's latest analyzed version, never
stands alone.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.domains.feedback.ai_service import AIServiceError, AIServiceUnavailableError
from app.domains.feedback.models import SkillLevel
from app.domains.feedback.schemas import FeedbackRead
from app.domains.feedback.service import (
    AnalysisNotFoundError,
    FeedbackNotFoundError,
    generate_composition_feedback,
    get_composition_feedback,
)
from app.domains.projects.service import CompositionNotFoundError
from app.domains.users.models import User

router = APIRouter(prefix="/projects/{composition_id}/feedback", tags=["feedback"])

_composition_not_found = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Composition not found."
)
_analysis_not_found = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="This composition has not been analyzed yet.",
)


@router.post("", response_model=FeedbackRead)
async def create_feedback(
    composition_id: uuid.UUID,
    skill_level: SkillLevel = SkillLevel.INTERMEDIATE,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedbackRead:
    """Generates (or regenerates) AI feedback for the composition's newest
    analyzed version, at the requested skill level."""
    try:
        feedback = await generate_composition_feedback(
            db, current_user.id, composition_id, skill_level
        )
    except CompositionNotFoundError as exc:
        raise _composition_not_found from exc
    except AnalysisNotFoundError as exc:
        raise _analysis_not_found from exc
    except AIServiceUnavailableError as exc:
        # Not configured, not broken: treat a missing API key as the
        # feature not existing in this deployment, not as an outage.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI feedback is not available in this deployment.",
        ) from exc
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return FeedbackRead.model_validate(feedback)


@router.get("", response_model=FeedbackRead)
async def read_feedback(
    composition_id: uuid.UUID,
    skill_level: SkillLevel = SkillLevel.INTERMEDIATE,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedbackRead:
    """Returns previously generated feedback without calling the AI again."""
    try:
        feedback = await get_composition_feedback(db, current_user.id, composition_id, skill_level)
    except CompositionNotFoundError as exc:
        raise _composition_not_found from exc
    except AnalysisNotFoundError as exc:
        raise _analysis_not_found from exc
    except FeedbackNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No feedback has been generated yet for this skill level.",
        ) from exc
    return FeedbackRead.model_validate(feedback)
