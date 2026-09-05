"""add exam rubric grading ai usage kind

Revision ID: 202609050002
Revises: 202609050001
Create Date: 2026-09-05 00:02:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "202609050002"
down_revision: str | None = "202609050001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE ai_usage_kind ADD VALUE IF NOT EXISTS 'exam_rubric_grading'")


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE - removing an enum member
    # means rebuilding the type from scratch, which isn't worth doing for a
    # downgrade path nothing else depends on.
    pass
