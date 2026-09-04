"""add learning tables

Revision ID: 202609040001
Revises: 202601200001
Create Date: 2026-09-04 00:00:01

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "202609040001"
down_revision: str | None = "202601200001"
branch_labels: str | None = None
depends_on: str | None = None

# Each enum is declared twice for the same reason as the feedback migration:
# the first object owns the CREATE TYPE (run explicitly, checkfirst=True), the
# `create_type=False` twin is what the column references so op.create_table()
# doesn't try to create the type a second time.
_course_level = postgresql.ENUM("beginner", "intermediate", "advanced", name="course_level")
_course_level_column = postgresql.ENUM(
    "beginner", "intermediate", "advanced", name="course_level", create_type=False
)

_step_kind = postgresql.ENUM("reading", "quiz", "composition", name="lesson_step_kind")
_step_kind_column = postgresql.ENUM(
    "reading", "quiz", "composition", name="lesson_step_kind", create_type=False
)

_lesson_status = postgresql.ENUM("in_progress", "completed", name="lesson_status")
_lesson_status_column = postgresql.ENUM(
    "in_progress", "completed", name="lesson_status", create_type=False
)

# "untouched" is part of the type even though no row ever holds it - a topic
# with no mastery row is untouched by definition. Keeping the member here
# means the database can represent every state the API describes.
_mastery_status = postgresql.ENUM(
    "untouched", "learning", "solid", "needs_practice", name="mastery_status"
)
_mastery_status_column = postgresql.ENUM(
    "untouched", "learning", "solid", "needs_practice", name="mastery_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    _course_level.create(bind, checkfirst=True)
    _step_kind.create(bind, checkfirst=True)
    _lesson_status.create(bind, checkfirst=True)
    _mastery_status.create(bind, checkfirst=True)

    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("level", _course_level_column, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_courses")),
        sa.UniqueConstraint("slug", name=op.f("uq_courses_slug")),
    )

    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("area", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_topics")),
        sa.UniqueConstraint("slug", name=op.f("uq_topics_slug")),
    )

    op.create_table(
        "lessons",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name=op.f("fk_lessons_course_id_courses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lessons")),
        sa.UniqueConstraint("slug", name=op.f("uq_lessons_slug")),
    )
    op.create_index(op.f("ix_lessons_course_id"), "lessons", ["course_id"])

    op.create_table(
        "lesson_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("kind", _step_kind_column, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lessons.id"],
            name=op.f("fk_lesson_steps_lesson_id_lessons"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lesson_steps")),
        sa.UniqueConstraint("slug", name=op.f("uq_lesson_steps_slug")),
    )
    op.create_index(op.f("ix_lesson_steps_lesson_id"), "lesson_steps", ["lesson_id"])

    op.create_table(
        "lesson_step_topics",
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["step_id"],
            ["lesson_steps.id"],
            name=op.f("fk_lesson_step_topics_step_id_lesson_steps"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            name=op.f("fk_lesson_step_topics_topic_id_topics"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("step_id", "topic_id", name=op.f("pk_lesson_step_topics")),
    )
    op.create_index(op.f("ix_lesson_step_topics_topic_id"), "lesson_step_topics", ["topic_id"])

    op.create_table(
        "step_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_step_attempts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["step_id"],
            ["lesson_steps.id"],
            name=op.f("fk_step_attempts_step_id_lesson_steps"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_step_attempts")),
    )
    op.create_index("ix_step_attempts_user_id_step_id", "step_attempts", ["user_id", "step_id"])

    op.create_table(
        "user_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", _lesson_status_column, nullable=False),
        sa.Column("current_step_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_progress_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lessons.id"],
            name=op.f("fk_user_progress_lesson_id_lessons"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["current_step_id"],
            ["lesson_steps.id"],
            name=op.f("fk_user_progress_current_step_id_lesson_steps"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_progress")),
        sa.UniqueConstraint("user_id", "lesson_id", name=op.f("uq_user_progress_user_id")),
    )
    op.create_index(op.f("ix_user_progress_user_id"), "user_progress", ["user_id"])
    op.create_index(op.f("ix_user_progress_lesson_id"), "user_progress", ["lesson_id"])

    op.create_table(
        "topic_mastery",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("recent_results", postgresql.JSONB(), nullable=False),
        sa.Column("status", _mastery_status_column, nullable=False),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_topic_mastery_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            name=op.f("fk_topic_mastery_topic_id_topics"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_topic_mastery")),
        sa.UniqueConstraint("user_id", "topic_id", name=op.f("uq_topic_mastery_user_id")),
    )
    op.create_index(op.f("ix_topic_mastery_user_id"), "topic_mastery", ["user_id"])
    op.create_index(op.f("ix_topic_mastery_topic_id"), "topic_mastery", ["topic_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_topic_mastery_topic_id"), table_name="topic_mastery")
    op.drop_index(op.f("ix_topic_mastery_user_id"), table_name="topic_mastery")
    op.drop_table("topic_mastery")

    op.drop_index(op.f("ix_user_progress_lesson_id"), table_name="user_progress")
    op.drop_index(op.f("ix_user_progress_user_id"), table_name="user_progress")
    op.drop_table("user_progress")

    op.drop_index("ix_step_attempts_user_id_step_id", table_name="step_attempts")
    op.drop_table("step_attempts")

    op.drop_index(op.f("ix_lesson_step_topics_topic_id"), table_name="lesson_step_topics")
    op.drop_table("lesson_step_topics")

    op.drop_index(op.f("ix_lesson_steps_lesson_id"), table_name="lesson_steps")
    op.drop_table("lesson_steps")

    op.drop_index(op.f("ix_lessons_course_id"), table_name="lessons")
    op.drop_table("lessons")

    op.drop_table("topics")
    op.drop_table("courses")

    bind = op.get_bind()
    _mastery_status.drop(bind, checkfirst=True)
    _lesson_status.drop(bind, checkfirst=True)
    _step_kind.drop(bind, checkfirst=True)
    _course_level.drop(bind, checkfirst=True)
