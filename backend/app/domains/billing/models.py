"""What a user is allowed, and what Stripe (eventually) says about it.

One `Subscription` row per user, created lazily rather than at signup - see
`service.get_or_create_subscription`. A user with no row is free by
definition, which means the free tier needs no backfill migration and a
user who never subscribes never gets a row at all.

The Stripe columns are here now, unpopulated, so that wiring Stripe in
later (CLAUDE.md's premium-system phase) is a service change, not a schema
change - `service.py` already has somewhere to put the customer and
subscription ids the moment a webhook hands them over.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    tier: Mapped[Tier] = mapped_column(
        Enum(Tier, name="subscription_tier", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=Tier.FREE,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(
            SubscriptionStatus,
            name="subscription_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Unpopulated until Stripe is wired in - see the module docstring.
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
