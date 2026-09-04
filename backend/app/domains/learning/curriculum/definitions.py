"""The shape of authored curriculum content.

Curriculum is written as Python data (see this package's `__init__`), not
rows in a table and not a migration: a lesson's text is edited far more often
than any schema, and making that edit a normal commit - reviewable as a diff,
revertable like anything else - is worth more than the flexibility of an
admin UI nobody has asked for.

`position` appears nowhere here on purpose. Order comes from list order, so
inserting a lesson in the middle of a stage is inserting a list element, not
renumbering everything after it.
"""

from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.domains.learning.models import CourseLevel, StepKind
from app.domains.learning.schemas import PAYLOAD_BY_KIND


class TopicDef(BaseModel):
    """One skill-map topic."""

    slug: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=255)
    area: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1)


class StepDef(BaseModel):
    """One authored step, with the topics it exercises.

    `payload` is validated against the model for this step's `kind` and
    normalised in place, so a malformed quiz (an `answer_index` past the end
    of `choices`, say) fails at seed time with a clear error rather than at
    3am when a student happens to open that lesson.
    """

    slug: str = Field(min_length=1, max_length=120)
    kind: StepKind
    payload: dict[str, Any]
    topics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_payload(self) -> "StepDef":
        model = PAYLOAD_BY_KIND[self.kind].model_validate(self.payload)
        self.payload = model.model_dump(mode="json")
        return self


class LessonDef(BaseModel):
    slug: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    estimated_minutes: int = Field(gt=0, default=10)
    steps: list[StepDef] = Field(default_factory=list)


class CourseDef(BaseModel):
    """One stage of the roadmap and everything in it."""

    slug: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    level: CourseLevel
    lessons: list[LessonDef] = Field(default_factory=list)
