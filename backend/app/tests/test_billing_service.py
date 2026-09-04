import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domains.billing import service as billing_service
from app.domains.billing.models import AiUsage, AiUsageKind, Tier
from app.domains.billing.service import GlobalSpendCapExceededError, QuotaExceededError
from app.domains.users.models import User


async def _make_user(db_session: AsyncSession) -> User:
    user = User(
        email=f"{uuid.uuid4()}@example.com", hashed_password="not-a-real-hash", full_name="U"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _add_usage(
    db_session: AsyncSession, user_id: uuid.UUID, count: int, cost_each: float = 0.01
) -> None:
    for _ in range(count):
        db_session.add(
            AiUsage(
                user_id=user_id,
                kind=AiUsageKind.EXERCISE_GRADING,
                model="claude-opus-5",
                input_tokens=100,
                output_tokens=50,
                estimated_cost_usd=cost_each,
            )
        )
    await db_session.commit()


class TestEnforceAiQuota:
    async def test_under_the_free_quota_does_not_raise(self, db_session: AsyncSession) -> None:
        user = await _make_user(db_session)
        await _add_usage(db_session, user.id, 4)  # free quota is 5

        await billing_service.enforce_ai_quota(db_session, user.id)

    async def test_at_the_free_quota_raises(self, db_session: AsyncSession) -> None:
        user = await _make_user(db_session)
        await _add_usage(db_session, user.id, 5)

        with pytest.raises(QuotaExceededError):
            await billing_service.enforce_ai_quota(db_session, user.id)

    async def test_over_the_free_quota_raises(self, db_session: AsyncSession) -> None:
        user = await _make_user(db_session)
        await _add_usage(db_session, user.id, 8)

        with pytest.raises(QuotaExceededError):
            await billing_service.enforce_ai_quota(db_session, user.id)

    async def test_premium_tier_has_no_cap(self, db_session: AsyncSession) -> None:
        user = await _make_user(db_session)
        await _add_usage(db_session, user.id, 50)
        subscription = await billing_service.get_or_create_subscription(db_session, user.id)
        subscription.tier = Tier.PREMIUM
        await db_session.commit()

        await billing_service.enforce_ai_quota(db_session, user.id)

    async def test_does_not_depend_on_a_configured_api_key(self, db_session: AsyncSession) -> None:
        # The test environment never sets ANTHROPIC_API_KEY - quota
        # enforcement reads only the AiUsage ledger and must not care.
        assert not settings.ANTHROPIC_API_KEY
        user = await _make_user(db_session)
        await _add_usage(db_session, user.id, 5)

        with pytest.raises(QuotaExceededError):
            await billing_service.enforce_ai_quota(db_session, user.id)


class TestEnforceGlobalSpendCap:
    async def test_unset_cap_never_trips(self, db_session: AsyncSession) -> None:
        user = await _make_user(db_session)
        await _add_usage(db_session, user.id, 100, cost_each=10.0)

        await billing_service.enforce_global_spend_cap(db_session)

    async def test_cap_trips_once_spend_reaches_it(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "GLOBAL_AI_MONTHLY_SPEND_CAP_USD", 1.0)
        user = await _make_user(db_session)
        await _add_usage(db_session, user.id, 5, cost_each=0.25)  # totals 1.25

        with pytest.raises(GlobalSpendCapExceededError):
            await billing_service.enforce_global_spend_cap(db_session)

    async def test_cap_does_not_trip_under_the_threshold(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "GLOBAL_AI_MONTHLY_SPEND_CAP_USD", 10.0)
        user = await _make_user(db_session)
        await _add_usage(db_session, user.id, 2, cost_each=1.0)  # totals 2.0

        await billing_service.enforce_global_spend_cap(db_session)
