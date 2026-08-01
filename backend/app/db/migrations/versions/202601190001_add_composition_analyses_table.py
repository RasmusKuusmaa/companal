"""add composition_analyses table

Revision ID: 202601190001
Revises: 202601180001
Create Date: 2026-01-19 00:00:01

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "202601190001"
down_revision: str | None = "202601180001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "composition_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("composition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        # Null when that engine could not run against this version; the
        # reason is recorded in `unavailable`.
        sa.Column("melody_score", sa.Float(), nullable=True),
        sa.Column("harmony_score", sa.Float(), nullable=True),
        sa.Column("rhythm_score", sa.Float(), nullable=True),
        sa.Column("melody_analysis", postgresql.JSONB(), nullable=True),
        sa.Column("harmony_analysis", postgresql.JSONB(), nullable=True),
        sa.Column("rhythm_analysis", postgresql.JSONB(), nullable=True),
        sa.Column(
            "unavailable", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["composition_id"],
            ["compositions.id"],
            name=op.f("fk_composition_analyses_composition_id_compositions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["composition_versions.id"],
            name=op.f("fk_composition_analyses_version_id_composition_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_composition_analyses")),
        # One analysis per version: the engines are deterministic, so a
        # re-run is an overwrite rather than a new row.
        sa.UniqueConstraint("version_id", name=op.f("uq_composition_analyses_version_id")),
    )
    op.create_index(
        op.f("ix_composition_analyses_composition_id"),
        "composition_analyses",
        ["composition_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_composition_analyses_composition_id"), table_name="composition_analyses"
    )
    op.drop_table("composition_analyses")
