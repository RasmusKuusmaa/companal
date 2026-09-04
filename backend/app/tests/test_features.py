from app.core.features import TIER_MONTHLY_AI_QUOTA, Feature, tier_has_feature
from app.domains.billing.models import Tier


class TestTierHasFeature:
    def test_free_tier_has_the_two_always_on_ai_features(self) -> None:
        assert tier_has_feature(Tier.FREE, Feature.AI_COMPOSITION_FEEDBACK)
        assert tier_has_feature(Tier.FREE, Feature.AI_EXERCISE_GRADING)

    def test_free_tier_does_not_have_the_exam_rubric_feature(self) -> None:
        assert not tier_has_feature(Tier.FREE, Feature.AI_EXAM_RUBRIC_GRADING)

    def test_premium_tier_has_every_feature(self) -> None:
        for feature in Feature:
            assert tier_has_feature(Tier.PREMIUM, feature)


class TestTierMonthlyAiQuota:
    def test_free_tier_has_a_finite_quota(self) -> None:
        assert TIER_MONTHLY_AI_QUOTA[Tier.FREE] == 5

    def test_premium_tier_is_unlimited(self) -> None:
        assert TIER_MONTHLY_AI_QUOTA[Tier.PREMIUM] is None
