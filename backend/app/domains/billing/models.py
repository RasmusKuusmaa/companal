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

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
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


class AiUsageKind(str, enum.Enum):
    """What the call was for - the two things that currently spend AI money."""

    COMPOSITION_FEEDBACK = "composition_feedback"
    EXERCISE_GRADING = "exercise_grading"


class AiUsage(Base):
    """One row per Claude call, ever - the ledger everything else reads.

    Never updated, never deleted: the monthly quota (`billing.service`) and
    the global spend cap both work by summing this table over a window, and
    a ledger that could be edited after the fact wouldn't be trustworthy for
    either. `estimated_cost_usd` is computed at call time from the token
    counts and the model's published rate, not looked up again later - a
    rate change tomorrow shouldn't rewrite what a call cost yesterday.
    """

    __tablename__ = "ai_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[AiUsageKind] = mapped_column(
        Enum(AiUsageKind, name="ai_usage_kind", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
