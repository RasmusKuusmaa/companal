"""add feedback table

Revision ID: 202601200001
Revises: 202601190001
Create Date: 2026-01-20 00:00:01

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "202601200001"
down_revision: str | None = "202601190001"
branch_labels: str | None = None
depends_on: str | None = None

_skill_level = postgresql.ENUM("beginner", "intermediate", "advanced", name="feedback_skill_level")

# Same enum, but `create_type=False`: op.create_table() below would otherwise
# try to CREATE TYPE a second time for this column (it doesn't check-first on
# its own), colliding with the explicit, checkfirst=True creation below.
_skill_level_column_type = postgresql.ENUM(
    "beginner", "intermediate", "advanced", name="feedback_skill_level", create_type=False
)


def upgrade() -> None:
    _skill_level.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("composition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_level", _skill_level_column_type, nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "strengths", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column(
            "issues", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column(
            "suggestions", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["composition_id"],
            ["compositions.id"],
            name=op.f("fk_feedback_composition_id_compositions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["composition_versions.id"],
            name=op.f("fk_feedback_version_id_composition_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback")),
        # One stored feedback per version and skill level: regenerating
        # overwrites in place rather than growing near-duplicate rows.
        sa.UniqueConstraint("version_id", "skill_level", name=op.f("uq_feedback_version_id")),
    )
    op.create_index(op.f("ix_feedback_composition_id"), "feedback", ["composition_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_feedback_composition_id"), table_name="feedback")
    op.drop_table("feedback")
    _skill_level.drop(op.get_bind(), checkfirst=True)
