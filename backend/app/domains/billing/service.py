"""Subscription lookups and lazy creation.

See `models.py`'s module docstring for why a missing row means free tier.
Reads that only need the tier go through `get_tier`, which never writes -
that's what keeps the free tier backfill-free. `get_or_create_subscription`
is for the few callers that need a real row to update (the Stripe webhook,
billing endpoints).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.features import TIER_MONTHLY_AI_QUOTA
from app.domains.billing.models import AiUsage, Subscription, SubscriptionStatus, Tier


class QuotaExceededError(Exception):
    """Raised when a user has used up their tier's monthly AI quota."""


async def get_tier(db: AsyncSession, user_id: uuid.UUID) -> Tier:
    subscription = await db.scalar(select(Subscription).where(Subscription.user_id == user_id))
    return subscription.tier if subscription is not None else Tier.FREE


async def get_or_create_subscription(db: AsyncSession, user_id: uuid.UUID) -> Subscription:
    subscription = await db.scalar(select(Subscription).where(Subscription.user_id == user_id))
    if subscription is not None:
        return subscription

    subscription = Subscription(user_id=user_id, tier=Tier.FREE, status=SubscriptionStatus.ACTIVE)
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


def _current_period_start() -> datetime:
    """Start of the current calendar month, UTC.

    Free tier has no `current_period_end` of its own, and nothing outside
    this quota check reads a period yet, so the calendar month is the
    obvious default - premium's Stripe-driven period can replace it later
    if a billing-anniversary quota ever matters.
    """
    now = datetime.now(UTC)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def ai_usage_this_period(db: AsyncSession, user_id: uuid.UUID) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(AiUsage)
        .where(AiUsage.user_id == user_id, AiUsage.created_at >= _current_period_start())
    )
    return count or 0


async def enforce_ai_quota(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Raises `QuotaExceededError` once the user's tier's monthly cap is used up.

    A no-op for tiers with no cap (`TIER_MONTHLY_AI_QUOTA[tier] is None`).
    """
    tier = await get_tier(db, user_id)
    quota = TIER_MONTHLY_AI_QUOTA[tier]
    if quota is None:
        return

    used = await ai_usage_this_period(db, user_id)
    if used >= quota:
        raise QuotaExceededError
