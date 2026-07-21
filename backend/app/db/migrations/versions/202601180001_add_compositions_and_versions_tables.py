"""add compositions and composition_versions tables

Revision ID: 202601180001
Revises: 202601170001
Create Date: 2026-01-18 00:00:01

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "202601180001"
down_revision: str | None = "202601170001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "compositions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("version_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_compositions_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_compositions")),
    )
    op.create_index(op.f("ix_compositions_owner_id"), "compositions", ["owner_id"])

    op.create_table(
        "composition_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("composition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["composition_id"],
            ["compositions.id"],
            name=op.f("fk_composition_versions_composition_id_compositions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_composition_versions")),
        sa.UniqueConstraint(
            "composition_id",
            "version_number",
            name=op.f("uq_composition_versions_composition_id"),
        ),
    )
    op.create_index(
        op.f("ix_composition_versions_composition_id"), "composition_versions", ["composition_id"]
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_composition_versions_composition_id"), table_name="composition_versions"
    )
    op.drop_table("composition_versions")
    op.drop_index(op.f("ix_compositions_owner_id"), table_name="compositions")
    op.drop_table("compositions")
