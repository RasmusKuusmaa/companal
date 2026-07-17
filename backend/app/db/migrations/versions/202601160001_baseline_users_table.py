"""baseline: create users table

Revision ID: 202601160001
Revises:
Create Date: 2026-01-16 00:00:01

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "202601160001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None

user_role = postgresql.ENUM("student", "teacher", "admin", name="user_role")

# Same enum, but `create_type=False`: op.create_table() below would
# otherwise try to CREATE TYPE a second time for this column (it doesn't
# check-first on its own), colliding with the explicit, checkfirst=True
# creation a few lines down.
user_role_column_type = postgresql.ENUM(
    "student", "teacher", "admin", name="user_role", create_type=False
)


def upgrade() -> None:
    user_role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_column_type, nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    user_role.drop(op.get_bind(), checkfirst=True)
