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
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.feedback.models import SkillLevel
from app.domains.feedback.schemas import CompositionFeedback
from app.domains.learning.models import CourseLevel, MasteryStatus, StepKind
from app.domains.notation.grading import DeterministicGrade
from app.domains.notation.requirements import Requirement
from app.domains.notation.schemas import NotationDocument

__all__ = [
    "CourseLevel",
    "StepKind",
    "MasteryStatus",
    "LessonProgressStatus",
    "Requirement",
    "NotationDocument",
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
    "CompositionSubmissionRequest",
    "CompositionSubmissionRead",
    "CourseProgress",
    "ProgressSummary",
    "TopicLessonRef",
    "TopicMasteryRead",
    "SkillMapRead",
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

    `requirements` is the declarative rule language `notation.requirements`
    defines and `notation.validation` grades against - what used to be an
    opaque mapping here, before that module existed. `starter_notation` is
    a full `NotationDocument` for the same reason: a given soprano line or a
    cantus firmus the student writes against, in the exact shape the editor
    itself edits.

    `locked_staff_indices` names which of `starter_notation`'s staves are
    the given material rather than a mere starting point - indices into
    `starter_notation.staves`, not into the whole document's voices, since a
    lock is a per-staff, not per-voice, concept (see the editor's
    `useNotationEditor` on the frontend, which is where this is actually
    enforced; the backend never re-checks it, the same way it never
    re-checks that the student didn't resize the canvas).
    """

    brief: str = Field(min_length=1)
    requirements: list[Requirement] = Field(default_factory=list)
    starter_notation: NotationDocument | None = None
    locked_staff_indices: list[int] = Field(default_factory=list)


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
    requirements: list[Requirement]
    starter_notation: NotationDocument | None = None
    locked_staff_indices: list[int] = Field(default_factory=list)


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


class CompositionSubmissionRequest(BaseModel):
    """What the editor sends when a student submits a composition task.

    `with_ai_feedback` is opt-in and additive: the deterministic checklist
    and analysis are computed and returned either way, so asking for AI
    commentary can only add to the response, never gate it. Requesting it
    without AI configured (or once a quota exists, without one available)
    is not an error - `ai_feedback` simply comes back `None`.
    """

    document: NotationDocument
    skill_level: SkillLevel = SkillLevel.BEGINNER
    with_ai_feedback: bool = False


class CompositionSubmissionRead(DeterministicGrade):
    """A graded submission, kept as a `StepAttempt` - see `service.py`'s
    `submit_composition`. Extends `DeterministicGrade` rather than wrapping
    it, so the checklist and analysis a student sees is exactly what was
    computed, with just the attempt's own identity and any AI commentary
    riding along."""

    attempt_id: uuid.UUID
    created_at: datetime
    ai_feedback: CompositionFeedback | None = None


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
    started, in roadmap order. Its title rides along so that card is
    self-sufficient - otherwise every dashboard would have to fetch the
    entire roadmap to render one line of text.
    """

    lesson_count: int
    completed_lesson_count: int
    in_progress_lesson_count: int
    by_course: list[CourseProgress]
    continue_lesson_slug: str | None = None
    continue_lesson_title: str | None = None


# --------------------------------------------------------------------------- #
# Skill map
# --------------------------------------------------------------------------- #


class TopicLessonRef(BaseModel):
    """One lesson that exercises a topic - what "coverage" means at the
    topic level, and what a topic detail panel links out to."""

    slug: str
    title: str


class TopicMasteryRead(BaseModel):
    """One topic's mastery, as the skill map renders it.

    Present for every topic in the curriculum, whether or not the student
    has touched it - an untouched topic comes back with `status=untouched`
    and zeroed counts rather than being omitted, so the heatmap can show
    the whole curriculum rather than only what's been attempted.
    """

    id: uuid.UUID
    slug: str
    name: str
    area: str
    description: str
    status: MasteryStatus
    attempt_count: int
    correct_count: int
    accuracy: float
    # Oldest first, capped at ten - see `models.TopicMastery`'s own
    # docstring. What a topic detail panel renders as "your attempt
    # history" without a second request.
    recent_results: list[bool]
    last_seen_at: datetime | None
    lessons: list[TopicLessonRef]


class SkillMapRead(BaseModel):
    """Every topic in the curriculum, this student's mastery of each, and
    the totals a coverage summary is built from."""

    topics: list[TopicMasteryRead]
    topic_count: int
    touched_topic_count: int
