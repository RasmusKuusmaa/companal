"""Schemas for exams: sectioned assessments built from the same quiz and
composition payloads a lesson step uses (see `learning.schemas`) - see
`exams.models` for why an exam question doesn't reuse `LessonStep` itself -
with their own attempt and scoring shapes layered on top.
"""

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from app.domains.exams.models import ExamQuestionKind
from app.domains.feedback.models import SkillLevel
from app.domains.learning.schemas import CompositionPayload, QuizPayload
from app.domains.notation.requirements import Requirement
from app.domains.notation.schemas import NotationDocument

__all__ = [
    "ExamQuestionKind",
    "ExamQuestionPayload",
    "PAYLOAD_BY_KIND",
    "ExamQuizQuestionRead",
    "ExamCompositionQuestionRead",
    "ExamQuestionRead",
    "ExamSummary",
    "ExamRead",
    "ExamAttemptStartRead",
    "ExamQuizAnswerPayload",
    "ExamCompositionAnswerPayload",
    "ExamAnswerPayload",
    "ExamAnswerSubmission",
    "ExamAnswerRead",
    "ExamQuestionResultRead",
    "ExamAttemptResultRead",
    "ExamAttemptSummary",
    "ExamAttemptHistoryRead",
    "ExamSubmitRequest",
]


# --------------------------------------------------------------------------- #
# Question payloads - the authored side. Reused from the lesson step ones
# rather than redefined: an exam question and a lesson step ask exactly the
# same two things of a student (a multiple-choice check or a composition
# task), so the payload shape and its validation shouldn't have two copies
# to drift apart.
# --------------------------------------------------------------------------- #

ExamQuestionPayload = QuizPayload | CompositionPayload

PAYLOAD_BY_KIND: dict[ExamQuestionKind, type[ExamQuestionPayload]] = {
    ExamQuestionKind.QUIZ: QuizPayload,
    ExamQuestionKind.COMPOSITION: CompositionPayload,
}


# --------------------------------------------------------------------------- #
# Question reads - the served side
# --------------------------------------------------------------------------- #


class _ExamQuestionBase(BaseModel):
    id: uuid.UUID
    slug: str
    position: int


class ExamQuizQuestionRead(_ExamQuestionBase):
    """A quiz question as the student receives it - no `answer_index`, the
    same stripping `learning.schemas.QuizStepRead` does and for the same
    reason: there is no field here for the answer to leak through.
    """

    kind: Literal[ExamQuestionKind.QUIZ] = ExamQuestionKind.QUIZ
    question: str
    choices: list[str]


class ExamCompositionQuestionRead(_ExamQuestionBase):
    kind: Literal[ExamQuestionKind.COMPOSITION] = ExamQuestionKind.COMPOSITION
    brief: str
    requirements: list[Requirement]
    starter_notation: NotationDocument | None = None
    locked_staff_indices: list[int] = Field(default_factory=list)


ExamQuestionRead = Annotated[
    ExamQuizQuestionRead | ExamCompositionQuestionRead,
    Field(discriminator="kind"),
]


# --------------------------------------------------------------------------- #
# Exam overview
# --------------------------------------------------------------------------- #


class ExamSummary(BaseModel):
    """One exam on the exam list - scope and identity, no questions."""

    id: uuid.UUID
    slug: str
    title: str
    description: str
    # None for the comprehensive final, which isn't scoped to one stage.
    course_slug: str | None
    question_count: int


class ExamRead(ExamSummary):
    """One exam with its full question set - what starting or resuming an
    attempt is answered against."""

    questions: list[ExamQuestionRead]


# --------------------------------------------------------------------------- #
# Attempts - answers are held, not graded, until the attempt is submitted
# --------------------------------------------------------------------------- #


class ExamAttemptStartRead(BaseModel):
    """What starting a new attempt hands back: its identity and ordinal,
    plus the exam it's an attempt at."""

    attempt_id: uuid.UUID
    attempt_number: int
    exam: ExamRead
    started_at: datetime


class ExamQuizAnswerPayload(BaseModel):
    kind: Literal["quiz"] = "quiz"
    choice_index: int = Field(ge=0)


class ExamCompositionAnswerPayload(BaseModel):
    kind: Literal["composition"] = "composition"
    document: NotationDocument


ExamAnswerPayload = Annotated[
    ExamQuizAnswerPayload | ExamCompositionAnswerPayload,
    Field(discriminator="kind"),
]


class ExamAnswerSubmission(BaseModel):
    """One held answer. Submitting again for the same question replaces
    what was held - see `exams.service.answer_question` - since nothing is
    graded until the whole attempt is submitted.
    """

    answer: ExamAnswerPayload


class ExamAnswerRead(BaseModel):
    """Confirms one answer was held, without grading it."""

    question_id: uuid.UUID
    answered: bool


# --------------------------------------------------------------------------- #
# Grading
# --------------------------------------------------------------------------- #


class ExamQuestionResultRead(BaseModel):
    """One question's graded result within a submitted attempt.

    `detail` is shaped like `StepAttempt.result` - a quiz's correctness and
    explanation, or a composition's deterministic grade (and, for premium,
    AI rubric commentary) - see `exams.service.grade_attempt`.
    """

    question_id: uuid.UUID
    kind: ExamQuestionKind
    score: float
    max_score: float
    detail: dict[str, Any]


class ExamAttemptResultRead(BaseModel):
    """The verdict on one submitted attempt."""

    attempt_id: uuid.UUID
    attempt_number: int
    score: float
    max_score: float
    submitted_at: datetime
    question_results: list[ExamQuestionResultRead]


class ExamAttemptSummary(BaseModel):
    """One past attempt, for the side-by-side history view."""

    attempt_id: uuid.UUID
    attempt_number: int
    score: float | None
    max_score: float | None
    started_at: datetime
    submitted_at: datetime | None


class ExamAttemptHistoryRead(BaseModel):
    exam_slug: str
    attempts: list[ExamAttemptSummary]


class ExamSubmitRequest(BaseModel):
    """What the client sends to grade an attempt.

    `with_ai_feedback` is opt-in and additive, the same convention as
    `learning.schemas.CompositionSubmissionRequest`: the deterministic
    grade is computed either way, and asking for AI commentary can only add
    to the response. Whether a free user is even allowed to ask is enforced
    by the route (`Feature.AI_EXAM_RUBRIC_GRADING`), not by this schema.
    """

    with_ai_feedback: bool = False
    skill_level: SkillLevel = SkillLevel.BEGINNER
