"""Pydantic schemas for the subscription and usage endpoints."""

from datetime import datetime

from pydantic import BaseModel

from app.domains.billing.models import SubscriptionStatus, Tier


class SubscriptionSummary(BaseModel):
    """The caller's current tier and quota standing - what the billing
    endpoint and the frontend's usage meter both need in one call.

    Built from `Subscription` plus the `AiUsage` ledger, not read straight
    off one row - a free user with no `Subscription` row still gets a
    summary (see `billing.service.get_subscription_summary`).
    """

    tier: Tier
    status: SubscriptionStatus
    current_period_end: datetime | None
    ai_quota: int | None  # None means unlimited.
    ai_quota_used: int
    ai_quota_remaining: int | None  # None means unlimited.
