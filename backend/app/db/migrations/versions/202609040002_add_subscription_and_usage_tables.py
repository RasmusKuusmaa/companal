"""add subscription and usage tables

Revision ID: 202609040002
Revises: 202609040001
Create Date: 2026-09-04 00:02:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "202609040002"
down_revision: str | None = "202609040001"
branch_labels: str | None = None
depends_on: str | None = None

_tier = postgresql.ENUM("free", "premium", name="subscription_tier")
_tier_column_type = postgresql.ENUM(
    "free", "premium", name="subscription_tier", create_type=False
)

_status = postgresql.ENUM("active", "canceled", "past_due", name="subscription_status")
_status_column_type = postgresql.ENUM(
    "active", "canceled", "past_due", name="subscription_status", create_type=False
)

_usage_kind = postgresql.ENUM(
    "composition_feedback", "exercise_grading", name="ai_usage_kind"
)
_usage_kind_column_type = postgresql.ENUM(
    "composition_feedback", "exercise_grading", name="ai_usage_kind", create_type=False
)


def upgrade() -> None:
    _tier.create(op.get_bind(), checkfirst=True)
    _status.create(op.get_bind(), checkfirst=True)
    _usage_kind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tier", _tier_column_type, nullable=False),
        sa.Column("status", _status_column_type, nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_subscriptions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscriptions")),
        sa.UniqueConstraint("user_id", name=op.f("uq_subscriptions_user_id")),
        sa.UniqueConstraint(
            "stripe_customer_id", name=op.f("uq_subscriptions_stripe_customer_id")
        ),
        sa.UniqueConstraint(
            "stripe_subscription_id", name=op.f("uq_subscriptions_stripe_subscription_id")
        ),
    )

    op.create_table(
        "ai_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", _usage_kind_column_type, nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_ai_usage_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_usage")),
    )
    op.create_index(op.f("ix_ai_usage_user_id"), "ai_usage", ["user_id"])
    op.create_index(op.f("ix_ai_usage_created_at"), "ai_usage", ["created_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_usage_created_at"), table_name="ai_usage")
    op.drop_index(op.f("ix_ai_usage_user_id"), table_name="ai_usage")
    op.drop_table("ai_usage")
    op.drop_table("subscriptions")

    _usage_kind.drop(op.get_bind(), checkfirst=True)
    _status.drop(op.get_bind(), checkfirst=True)
    _tier.drop(op.get_bind(), checkfirst=True)
