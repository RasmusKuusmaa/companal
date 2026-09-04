"""Free vs premium capability matrix - the single source of truth for what a
tier can do.

Two independent things live here, because they answer different questions:

- `tier_has_feature` - a hard yes/no. Most of the app doesn't consult this at
  all, because per Cadence's design, no theory content is ever paywalled;
  only AI features are gated, and today that's just the exam rubric writeup
  (Phase I), which free tier never gets regardless of quota.
- `TIER_MONTHLY_AI_QUOTA` - a soft cap for features both tiers *have*.
  Composition feedback and exercise grading are available to everyone, free
  users just run out after `FREE_MONTHLY_AI_QUOTA` calls a month (`None`
  means no cap). Enforcing the cap against the `AiUsage` ledger is
  `billing.service`'s job, not this module's.
"""

import enum

from app.domains.billing.models import Tier

FREE_MONTHLY_AI_QUOTA = 5


class Feature(str, enum.Enum):
    AI_COMPOSITION_FEEDBACK = "ai_composition_feedback"
    AI_EXERCISE_GRADING = "ai_exercise_grading"
    AI_EXAM_RUBRIC_GRADING = "ai_exam_rubric_grading"


_TIER_FEATURES: dict[Tier, frozenset[Feature]] = {
    Tier.FREE: frozenset({Feature.AI_COMPOSITION_FEEDBACK, Feature.AI_EXERCISE_GRADING}),
    Tier.PREMIUM: frozenset(Feature),
}

TIER_MONTHLY_AI_QUOTA: dict[Tier, int | None] = {
    Tier.FREE: FREE_MONTHLY_AI_QUOTA,
    Tier.PREMIUM: None,
}


def tier_has_feature(tier: Tier, feature: Feature) -> bool:
    return feature in _TIER_FEATURES[tier]
