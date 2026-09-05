"""Exams: one assessment per course stage, plus a comprehensive final.

`ExamQuestion` deliberately parallels `learning.models.LessonStep` - a
`kind` discriminator with a per-kind JSONB `payload`, the same reasoning
about authoring content without a migration - but lives in its own table
rather than reusing `LessonStep`. An exam attempt needs scoring semantics
(`attempt_number`, `score`, `max_score`, answers held until submission)
that a lesson step attempt has no use for, and mixing the two would mean
every lesson-player query filtering out exam content it never wanted.
"""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExamQuestionKind(str, enum.Enum):
    """What an exam question asks of the student.

    Narrower than `learning.models.StepKind` on purpose - an exam is an
    assessment, not a lesson, so there is no `READING` question to answer.
    """

    QUIZ = "quiz"
    COMPOSITION = "composition"


class Exam(Base):
    """One assessment: one per course stage, plus a comprehensive final
    that spans everything and isn't scoped to a single stage.
    """

    __tablename__ = "exams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Null for the comprehensive final. SET NULL rather than CASCADE: a
    # stage being removed shouldn't take its exam's history down with it.
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ExamQuestion(Base):
    """One question within one exam - the MCQ or composition task that
    contributes to the attempt's score. See the module docstring for why
    this isn't `LessonStep`.
    """

    __tablename__ = "exam_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    kind: Mapped[ExamQuestionKind] = mapped_column(
        Enum(
            ExamQuestionKind,
            name="exam_question_kind",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # The question and answer key for a quiz; the brief and requirement
    # rules for a composition task - shaped like `LessonStep.payload`, and
    # validated the same way (see `exams.schemas`).
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_exam_questions_exam_id_position", "exam_id", "position"),)


class ExamAttempt(Base):
    """One student's attempt at one exam.

    `attempt_number` (1, 2, 3, ...) rather than relying on `started_at`
    ordering, because "retake as often as you like" means the ordinal
    itself is shown to the student - "your 3rd attempt" - not just derived
    for sorting. `score`/`max_score`/`submitted_at` stay null until the
    attempt is submitted: answers are held back and graded together (see
    `ExamAnswer`), not scored one at a time as the student goes.
    """

    __tablename__ = "exam_attempts"
    __table_args__ = (UniqueConstraint("user_id", "exam_id", "attempt_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)

    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ExamAnswer(Base):
    """One question's answer within one attempt.

    Held rather than graded on arrival - `score`/`max_score`/`result` stay
    null until the attempt is submitted, the same "grade the whole thing
    together, once" rule `ExamAttempt` describes. `payload` mirrors
    `StepAttempt.payload`: a `{"choice_index": 2}` for a quiz question, the
    submitted notation document for a composition one.
    """

    __tablename__ = "exam_answers"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exam_questions.id", ondelete="CASCADE"), nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
