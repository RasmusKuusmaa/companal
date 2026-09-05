"""The shape of authored exam content - mirrors
`learning.curriculum.definitions` for the same reason: an exam's questions
are written as Python data, not rows in a table, so editing one is a normal,
reviewable commit rather than an admin-UI action nobody has asked for.
"""

from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.domains.exams.models import ExamQuestionKind
from app.domains.exams.schemas import PAYLOAD_BY_KIND


class ExamQuestionDef(BaseModel):
    """One authored exam question.

    `payload` is validated against the model for this question's `kind` and
    normalised in place, the same way `learning.curriculum.definitions.
    StepDef` validates a lesson step's payload at seed time rather than
    when a student happens to open the exam.
    """

    slug: str = Field(min_length=1, max_length=120)
    kind: ExamQuestionKind
    payload: dict[str, Any]

    @model_validator(mode="after")
    def _validate_payload(self) -> "ExamQuestionDef":
        model = PAYLOAD_BY_KIND[self.kind].model_validate(self.payload)
        self.payload = model.model_dump(mode="json")
        return self


class ExamDef(BaseModel):
    """One authored exam and its questions."""

    slug: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    # None for the comprehensive final, which isn't scoped to one stage.
    course_slug: str | None = None
    questions: list[ExamQuestionDef] = Field(default_factory=list)
