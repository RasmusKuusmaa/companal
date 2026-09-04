"""AI service layer: turns a structured music analysis into feedback text.

Kept as a single narrow function so the rest of the domain - and tests - can
depend on its signature (`AnalysisBundle JSON, skill level -> CompositionFeedback`)
without needing a real `ANTHROPIC_API_KEY` or network access.
"""

from functools import lru_cache
from typing import Any

import anthropic

from app.core.config import settings
from app.domains.billing.service import AiCallUsage
from app.domains.feedback.models import SkillLevel
from app.domains.feedback.prompts import build_system_prompt, build_user_prompt
from app.domains.feedback.schemas import CompositionFeedback


class AIServiceError(Exception):
    """Raised when AI feedback cannot be generated - missing configuration,
    a failed API call, or a response that could not be parsed."""


@lru_cache
def _get_client() -> anthropic.Anthropic:
    if not settings.ANTHROPIC_API_KEY:
        raise AIServiceError("AI feedback is not configured (ANTHROPIC_API_KEY is unset).")
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def generate_feedback(
    analysis_bundle: dict[str, Any], skill_level: SkillLevel
) -> tuple[CompositionFeedback, AiCallUsage]:
    """Calls Claude to turn one structured analysis into educational feedback.

    Returns the parsed feedback alongside the call's token usage, so callers
    can record it to the `AiUsage` ledger without a second round trip.
    """
    client = _get_client()
    try:
        response = client.messages.parse(
            model=settings.AI_MODEL,
            max_tokens=4096,
            system=build_system_prompt(skill_level),
            messages=[{"role": "user", "content": build_user_prompt(analysis_bundle)}],
            output_format=CompositionFeedback,
        )
    except anthropic.APIError as exc:
        raise AIServiceError(f"AI feedback request failed: {exc}") from exc

    if response.stop_reason == "refusal":
        raise AIServiceError("The AI declined to generate feedback for this composition.")
    if response.parsed_output is None:
        raise AIServiceError("The AI response could not be parsed into feedback.")

    usage = AiCallUsage(
        model=response.model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    return response.parsed_output, usage
