"""AI commentary on top of a deterministic exercise grade.

Mirrors `feedback.ai_service` in shape - a single narrow function so the
rest of the domain can depend on its signature without a real
`ANTHROPIC_API_KEY` or network access - but scoped to one exercise rather
than a whole composition, and given the requirement checklist as ground
truth rather than being asked to judge correctness itself (see
`ai_prompts.py`). Reuses `feedback.schemas.CompositionFeedback` as the
structured-output shape: the two are the same kind of response - a
narrative summary, strengths, taught issues, suggestions - and inventing a
second identical schema here would just be two names for one thing.
"""

from functools import lru_cache
from typing import Any

import anthropic

from app.core.config import settings
from app.domains.billing.service import AiCallUsage
from app.domains.feedback.models import SkillLevel
from app.domains.feedback.schemas import CompositionFeedback
from app.domains.notation.ai_prompts import build_system_prompt, build_user_prompt
from app.domains.notation.requirements import RequirementResult


class AIGradingError(Exception):
    """Raised when AI commentary can't be generated - missing configuration,
    a failed API call, or a response that could not be parsed."""


class AIGradingUnavailableError(AIGradingError):
    """Raised specifically because no API key is configured - see
    `feedback.ai_service.AIServiceUnavailableError`, which this mirrors."""


@lru_cache
def _get_client() -> anthropic.Anthropic:
    if not settings.ANTHROPIC_API_KEY:
        raise AIGradingUnavailableError(
            "AI grading is not configured (ANTHROPIC_API_KEY is unset)."
        )
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def generate_exercise_feedback(
    lesson_title: str,
    brief: str,
    requirement_results: list[RequirementResult],
    analysis_bundle: dict[str, Any],
    skill_level: SkillLevel,
) -> tuple[CompositionFeedback, AiCallUsage]:
    """Calls Claude to comment on one already-graded exercise submission.

    Returns the parsed feedback alongside the call's token usage, so callers
    can record it to the `AiUsage` ledger without a second round trip.
    """
    client = _get_client()
    try:
        response = client.messages.parse(
            model=settings.AI_MODEL,
            max_tokens=4096,
            system=build_system_prompt(skill_level),
            messages=[
                {
                    "role": "user",
                    "content": build_user_prompt(
                        lesson_title, brief, requirement_results, analysis_bundle
                    ),
                }
            ],
            output_format=CompositionFeedback,
        )
    except anthropic.APIError as exc:
        raise AIGradingError(f"AI grading request failed: {exc}") from exc

    if response.stop_reason == "refusal":
        raise AIGradingError("The AI declined to grade this submission.")
    if response.parsed_output is None:
        raise AIGradingError("The AI response could not be parsed into feedback.")

    usage = AiCallUsage(
        model=response.model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    return response.parsed_output, usage
