"""Generates and stores AI feedback for a composition's latest analyzed version.

Feedback is built from the *stored* `CompositionAnalysis`, not the raw
MusicXML file - so a composition has to be analyzed (via the projects
analyze endpoint) before feedback can be generated for it.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domains.billing import service as billing_service
from app.domains.billing.models import AiUsageKind
from app.domains.feedback.ai_service import generate_feedback
from app.domains.feedback.models import Feedback, SkillLevel
from app.domains.projects.models import CompositionAnalysis
from app.domains.projects.service import get_composition


class AnalysisNotFoundError(Exception):
    """Raised when the composition has no stored analysis to give feedback on."""


class FeedbackNotFoundError(Exception):
    """Raised when no feedback has been generated yet for this skill level."""


def _bundle_from_analysis(analysis: CompositionAnalysis) -> dict[str, object]:
    return {
        "melody_analysis": analysis.melody_analysis,
        "harmony_analysis": analysis.harmony_analysis,
        "rhythm_analysis": analysis.rhythm_analysis,
        "overall_score": analysis.overall_score,
        "unavailable": analysis.unavailable,
    }


async def _latest_analysis(db: AsyncSession, composition_id: uuid.UUID) -> CompositionAnalysis:
    analysis = await db.scalar(
        select(CompositionAnalysis)
        .where(CompositionAnalysis.composition_id == composition_id)
        .order_by(CompositionAnalysis.updated_at.desc())
        .limit(1)
    )
    if analysis is None:
        raise AnalysisNotFoundError
    return analysis


async def generate_composition_feedback(
    db: AsyncSession, owner_id: uuid.UUID, composition_id: uuid.UUID, skill_level: SkillLevel
) -> Feedback:
    """Generates (or regenerates) AI feedback for a composition's latest analysis.

    One row per `(version_id, skill_level)`: regenerating overwrites in
    place, matching how `CompositionAnalysis` handles re-analysis.
    """
    await get_composition(db, owner_id, composition_id)
    analysis = await _latest_analysis(db, composition_id)

    content, usage = generate_feedback(_bundle_from_analysis(analysis), skill_level)
    await billing_service.record_ai_usage(db, owner_id, AiUsageKind.COMPOSITION_FEEDBACK, usage)

    feedback = await db.scalar(
        select(Feedback).where(
            Feedback.version_id == analysis.version_id, Feedback.skill_level == skill_level
        )
    )
    if feedback is None:
        feedback = Feedback(
            composition_id=composition_id, version_id=analysis.version_id, skill_level=skill_level
        )
        db.add(feedback)

    feedback.summary = content.summary
    feedback.strengths = content.strengths
    feedback.issues = [issue.model_dump(mode="json") for issue in content.issues]
    feedback.suggestions = content.suggestions
    feedback.model = settings.AI_MODEL
    feedback.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(feedback)
    return feedback


async def get_composition_feedback(
    db: AsyncSession, owner_id: uuid.UUID, composition_id: uuid.UUID, skill_level: SkillLevel
) -> Feedback:
    """Returns previously generated feedback for the latest version without
    calling the AI again."""
    await get_composition(db, owner_id, composition_id)
    analysis = await _latest_analysis(db, composition_id)

    feedback = await db.scalar(
        select(Feedback).where(
            Feedback.version_id == analysis.version_id, Feedback.skill_level == skill_level
        )
    )
    if feedback is None:
        raise FeedbackNotFoundError
    return feedback
