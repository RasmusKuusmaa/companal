"""Subscription lookups and lazy creation.

See `models.py`'s module docstring for why a missing row means free tier.
Reads that only need the tier go through `get_tier`, which never writes -
that's what keeps the free tier backfill-free. `get_or_create_subscription`
is for the few callers that need a real row to update (the Stripe webhook,
billing endpoints).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.billing.models import Subscription, SubscriptionStatus, Tier


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
