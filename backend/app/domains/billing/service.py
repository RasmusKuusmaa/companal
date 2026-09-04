"""Subscription lookups and lazy creation.

See `models.py`'s module docstring for why a missing row means free tier.
Reads that only need the tier go through `get_tier`, which never writes -
that's what keeps the free tier backfill-free. `get_or_create_subscription`
is for the few callers that need a real row to update (the Stripe webhook,
billing endpoints).
"""

import uuid
from datetime import UTC, datetime
from typing import NamedTuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.features import TIER_MONTHLY_AI_QUOTA
from app.domains.billing.models import AiUsage, AiUsageKind, Subscription, SubscriptionStatus, Tier
from app.domains.billing.schemas import SubscriptionSummary

# Anthropic's published per-model rate, USD per million tokens (input, output).
# A model missing here costs $0 in the ledger rather than a guessed number -
# that's immediately visible as "0.00" and prompts updating this table,
# instead of silently under- or over-billing against a stale rate.
_MODEL_RATES_USD_PER_MILLION_TOKENS: dict[str, tuple[float, float]] = {
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


class AiCallUsage(NamedTuple):
    """What a single Claude call cost, as reported by the API response
    itself - the resolved `model` (not the possibly-aliased one requested)
    and the token counts `estimate_cost_usd` prices."""

    model: str
    input_tokens: int
    output_tokens: int


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_rate, output_rate = _MODEL_RATES_USD_PER_MILLION_TOKENS.get(model, (0.0, 0.0))
    return (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000


class QuotaExceededError(Exception):
    """Raised when a user has used up their tier's monthly AI quota."""


class GlobalSpendCapExceededError(Exception):
    """Raised when the whole app's monthly AI spend has hit its configured cap."""


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


async def record_ai_usage(
    db: AsyncSession, user_id: uuid.UUID, kind: AiUsageKind, usage: AiCallUsage
) -> AiUsage:
    """Appends one row to the never-updated `AiUsage` ledger. Call this once
    per successful Claude call, after the response comes back - a failed or
    refused call was never billed by Anthropic and shouldn't count against
    the user's quota either."""
    record = AiUsage(
        user_id=user_id,
        kind=kind,
        model=usage.model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        estimated_cost_usd=estimate_cost_usd(usage.model, usage.input_tokens, usage.output_tokens),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


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


async def global_ai_spend_this_period(db: AsyncSession) -> float:
    total = await db.scalar(
        select(func.coalesce(func.sum(AiUsage.estimated_cost_usd), 0.0)).where(
            AiUsage.created_at >= _current_period_start()
        )
    )
    return float(total or 0.0)


async def enforce_global_spend_cap(db: AsyncSession) -> None:
    """Raises `GlobalSpendCapExceededError` once the app-wide monthly spend
    cap is hit. A no-op when `GLOBAL_AI_MONTHLY_SPEND_CAP_USD` is unset -
    the default, so local dev is never blocked by it.
    """
    cap = settings.GLOBAL_AI_MONTHLY_SPEND_CAP_USD
    if cap is None:
        return

    spent = await global_ai_spend_this_period(db)
    if spent >= cap:
        raise GlobalSpendCapExceededError


async def get_subscription_summary(db: AsyncSession, user_id: uuid.UUID) -> SubscriptionSummary:
    """Reads the caller's tier and quota standing without ever creating a
    `Subscription` row - a plain `GET` shouldn't backfill one for a free
    user who has never needed one (see `models.py`'s module docstring).
    """
    subscription = await db.scalar(select(Subscription).where(Subscription.user_id == user_id))
    tier = subscription.tier if subscription is not None else Tier.FREE
    status = subscription.status if subscription is not None else SubscriptionStatus.ACTIVE
    period_end = subscription.current_period_end if subscription is not None else None

    quota = TIER_MONTHLY_AI_QUOTA[tier]
    used = await ai_usage_this_period(db, user_id)
    remaining = None if quota is None else max(quota - used, 0)

    return SubscriptionSummary(
        tier=tier,
        status=status,
        current_period_end=period_end,
        ai_quota=quota,
        ai_quota_used=used,
        ai_quota_remaining=remaining,
    )
