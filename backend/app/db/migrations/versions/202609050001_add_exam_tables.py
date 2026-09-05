"""add exam tables

Revision ID: 202609050001
Revises: 202609040002
Create Date: 2026-09-05 00:01:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "202609050001"
down_revision: str | None = "202609040002"
branch_labels: str | None = None
depends_on: str | None = None

_question_kind = postgresql.ENUM("quiz", "composition", name="exam_question_kind")
_question_kind_column = postgresql.ENUM(
    "quiz", "composition", name="exam_question_kind", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    _question_kind.create(bind, checkfirst=True)

    op.create_table(
        "exams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name=op.f("fk_exams_course_id_courses"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exams")),
        sa.UniqueConstraint("slug", name=op.f("uq_exams_slug")),
    )
    op.create_index(op.f("ix_exams_course_id"), "exams", ["course_id"])

    op.create_table(
        "exam_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("kind", _question_kind_column, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["exam_id"],
            ["exams.id"],
            name=op.f("fk_exam_questions_exam_id_exams"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exam_questions")),
        sa.UniqueConstraint("slug", name=op.f("uq_exam_questions_slug")),
    )
    op.create_index(op.f("ix_exam_questions_exam_id"), "exam_questions", ["exam_id"])
    op.create_index(
        "ix_exam_questions_exam_id_position", "exam_questions", ["exam_id", "position"]
    )

    op.create_table(
        "exam_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_exam_attempts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["exam_id"],
            ["exams.id"],
            name=op.f("fk_exam_attempts_exam_id_exams"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exam_attempts")),
        sa.UniqueConstraint(
            "user_id", "exam_id", "attempt_number", name=op.f("uq_exam_attempts_user_id")
        ),
    )
    op.create_index(op.f("ix_exam_attempts_user_id"), "exam_attempts", ["user_id"])
    op.create_index(op.f("ix_exam_attempts_exam_id"), "exam_attempts", ["exam_id"])

    op.create_table(
        "exam_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["exam_attempts.id"],
            name=op.f("fk_exam_answers_attempt_id_exam_attempts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["exam_questions.id"],
            name=op.f("fk_exam_answers_question_id_exam_questions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exam_answers")),
        sa.UniqueConstraint(
            "attempt_id", "question_id", name=op.f("uq_exam_answers_attempt_id")
        ),
    )
    op.create_index(op.f("ix_exam_answers_attempt_id"), "exam_answers", ["attempt_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_exam_answers_attempt_id"), table_name="exam_answers")
    op.drop_table("exam_answers")

    op.drop_index(op.f("ix_exam_attempts_exam_id"), table_name="exam_attempts")
    op.drop_index(op.f("ix_exam_attempts_user_id"), table_name="exam_attempts")
    op.drop_table("exam_attempts")

    op.drop_index("ix_exam_questions_exam_id_position", table_name="exam_questions")
    op.drop_index(op.f("ix_exam_questions_exam_id"), table_name="exam_questions")
    op.drop_table("exam_questions")

    op.drop_index(op.f("ix_exams_course_id"), table_name="exams")
    op.drop_table("exams")

    bind = op.get_bind()
    _question_kind.drop(bind, checkfirst=True)
