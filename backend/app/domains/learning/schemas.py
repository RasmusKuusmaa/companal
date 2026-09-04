"""Schemas for the roadmap, the lesson player, and progress.

Two families of step schema live here, and the split is the point:

* the `*Payload` models are what a `LessonStep.payload` holds - authored
  content, validated when the seed loader writes it, answer keys included;
* the `*StepRead` models are what the API hands the browser.

They are not the same shape. A quiz's payload carries the correct choice; the
step the student is served must not, or the answer is one devtools tab away.
Keeping the two apart in the type system means the stripping isn't a step
someone can forget - there is simply no field to leak.

The payload models deliberately don't carry a `kind` field of their own: the
step row already has a `kind` column, and that column is the discriminator
(see `PAYLOAD_BY_KIND`). Storing the kind twice invites the two copies to
disagree.
"""

import enum
import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.learning.models import CourseLevel, StepKind

__all__ = [
    "CourseLevel",
    "StepKind",
    "LessonProgressStatus",
    "ReadingPayload",
    "QuizPayload",
    "CompositionPayload",
    "StepPayload",
    "PAYLOAD_BY_KIND",
    "ReadingStepRead",
    "QuizStepRead",
    "CompositionStepRead",
    "LessonStepRead",
    "CourseRef",
    "LessonSummary",
    "CourseSummary",
    "CourseWithLessons",
    "RoadmapRead",
    "LessonRead",
    "QuizAnswerRequest",
    "QuizAnswerResult",
    "StepSeenRead",
    "LessonCompleteRead",
    "CourseProgress",
    "ProgressSummary",
]


class LessonProgressStatus(str, enum.Enum):
    """Where the student stands on one lesson, from the API's point of view.

    Wider than the database's `LessonStatus`, which has no "not started"
    member because it doesn't need one - the absence of a `UserProgress` row
    *is* not-started. The UI does need to say it out loud, so the API-facing
    enum names all three states.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# --------------------------------------------------------------------------- #
# Step payloads - the authored side
# --------------------------------------------------------------------------- #


class ReadingPayload(BaseModel):
    """Prose to read. Markdown, rendered client-side."""

    markdown: str = Field(min_length=1)


class QuizPayload(BaseModel):
    """A multiple-choice check with its answer key and teaching explanation."""

    question: str = Field(min_length=1)
    choices: list[str] = Field(min_length=2)
    answer_index: int = Field(ge=0)
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def _answer_index_in_range(self) -> "QuizPayload":
        if self.answer_index >= len(self.choices):
            raise ValueError(
                f"answer_index {self.answer_index} is out of range for {len(self.choices)} choices"
            )
        return self


class CompositionPayload(BaseModel):
    """A task the student answers by writing music.

    `requirements` stays an opaque mapping until Phase D gives the rule
    language a schema of its own - the validator that reads these rules
    doesn't exist yet, and inventing a shape here that the validator then has
    to honour would be guessing. `starter_notation` is the same: the notation
    document format is defined by the editor, so this holds it untyped until
    there is an editor to define it.
    """

    brief: str = Field(min_length=1)
    requirements: dict[str, Any] = Field(default_factory=dict)
    starter_notation: dict[str, Any] | None = None


StepPayload = ReadingPayload | QuizPayload | CompositionPayload

PAYLOAD_BY_KIND: dict[StepKind, type[StepPayload]] = {
    StepKind.READING: ReadingPayload,
    StepKind.QUIZ: QuizPayload,
    StepKind.COMPOSITION: CompositionPayload,
}


# --------------------------------------------------------------------------- #
# Step reads - the served side
# --------------------------------------------------------------------------- #


class _StepBase(BaseModel):
    id: uuid.UUID
    slug: str
    position: int


class ReadingStepRead(_StepBase):
    kind: Literal[StepKind.READING] = StepKind.READING
    markdown: str


class QuizStepRead(_StepBase):
    """A quiz as the student receives it - no `answer_index`, by construction."""

    kind: Literal[StepKind.QUIZ] = StepKind.QUIZ
    question: str
    choices: list[str]


class CompositionStepRead(_StepBase):
    kind: Literal[StepKind.COMPOSITION] = StepKind.COMPOSITION
    brief: str
    requirements: dict[str, Any]
    starter_notation: dict[str, Any] | None = None


LessonStepRead = Annotated[
    ReadingStepRead | QuizStepRead | CompositionStepRead,
    Field(discriminator="kind"),
]


# --------------------------------------------------------------------------- #
# Roadmap
# --------------------------------------------------------------------------- #


class CourseRef(BaseModel):
    """Just enough course identity to render a breadcrumb."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str


class LessonSummary(BaseModel):
    """One lesson on the roadmap - everything a card needs, no step content."""

    id: uuid.UUID
    slug: str
    title: str
    summary: str
    position: int
    estimated_minutes: int
    step_count: int
    status: LessonProgressStatus
    completed_at: datetime | None = None


class CourseSummary(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    description: str
    level: CourseLevel
    position: int
    lesson_count: int
    completed_lesson_count: int


class CourseWithLessons(CourseSummary):
    lessons: list[LessonSummary]


class RoadmapRead(BaseModel):
    """The whole path in one response.

    Nothing here is gated: every lesson of every course is returned with its
    status, and the client renders the recommended order without locking
    anything. The totals ride along so the page doesn't have to re-derive
    them by summing courses.
    """

    courses: list[CourseWithLessons]
    lesson_count: int
    completed_lesson_count: int
    in_progress_lesson_count: int


# --------------------------------------------------------------------------- #
# Lesson detail and answering
# --------------------------------------------------------------------------- #


class LessonRead(BaseModel):
    """A lesson with its ordered steps - what the lesson player runs on."""

    id: uuid.UUID
    slug: str
    title: str
    summary: str
    position: int
    estimated_minutes: int
    course: CourseRef
    status: LessonProgressStatus
    current_step_id: uuid.UUID | None
    completed_at: datetime | None
    steps: list[LessonStepRead]
    # Slugs rather than ids: these become router links, and the player
    # shouldn't need a second request to turn an id into a URL.
    previous_lesson_slug: str | None = None
    next_lesson_slug: str | None = None


class QuizAnswerRequest(BaseModel):
    choice_index: int = Field(ge=0)


class QuizAnswerResult(BaseModel):
    """The verdict on one quiz answer.

    The correct choice and the explanation come back either way, right or
    wrong. Retries are unlimited, so withholding them would only turn a
    wrong answer into a guessing game - and the explanation is the part
    that actually teaches. Retrying a quiz later is revision, not a second
    guess at a hidden answer.
    """

    attempt_id: uuid.UUID
    is_correct: bool
    correct_index: int
    explanation: str


class StepSeenRead(BaseModel):
    """Acknowledges that the student advanced past a step."""

    lesson_id: uuid.UUID
    current_step_id: uuid.UUID | None
    status: LessonProgressStatus


class LessonCompleteRead(BaseModel):
    lesson_id: uuid.UUID
    status: LessonProgressStatus
    completed_at: datetime
    next_lesson_slug: str | None = None


# --------------------------------------------------------------------------- #
# Progress
# --------------------------------------------------------------------------- #


class CourseProgress(BaseModel):
    course_id: uuid.UUID
    course_slug: str
    course_title: str
    lesson_count: int
    completed_lesson_count: int
    in_progress_lesson_count: int


class ProgressSummary(BaseModel):
    """Cross-course progress, plus where to pick back up.

    `continue_lesson_slug` is the lesson the dashboard's "continue" button
    points at: the one in progress, or failing that the first not yet
    started, in roadmap order.
    """

    lesson_count: int
    completed_lesson_count: int
    in_progress_lesson_count: int
    by_course: list[CourseProgress]
    continue_lesson_slug: str | None = None
