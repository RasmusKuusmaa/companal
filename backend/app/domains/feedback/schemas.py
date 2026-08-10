"""Pydantic schemas for AI-generated composition feedback.

`CompositionFeedback` doubles as the structured-output schema handed to the
Anthropic API (see `app.domains.feedback.ai_service`) and the shape stored on
the `Feedback` row - the AI's response *is* the row content, unmodified.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domains.feedback.models import SkillLevel

__all__ = ["SkillLevel", "TheoryLesson", "FeedbackIssue", "CompositionFeedback", "FeedbackRead"]


class TheoryLesson(BaseModel):
    """A theory concept connected to one specific problem in the score."""

    concept: str = Field(description="Short name of the theory concept, e.g. 'parallel fifths'.")
    lesson: str = Field(description="A short, self-contained explanation of the concept.")


class FeedbackIssue(BaseModel):
    """One weakness in the composition, explained and connected to a lesson."""

    problem: str = Field(
        description="What is wrong, stated plainly, e.g. 'Parallel fifths in m.4'."
    )
    explanation: str = Field(
        description="Why this is a problem, in language matching the skill level."
    )
    suggestion: str = Field(
        description="A concrete, actionable way the student could fix or improve this themselves."
    )
    theory: TheoryLesson


class CompositionFeedback(BaseModel):
    """The AI teacher's full response for one composition and skill level."""

    summary: str = Field(description="A short overall narrative summary of the feedback.")
    strengths: list[str] = Field(description="What the composition does well.")
    issues: list[FeedbackIssue] = Field(description="Problems found, each explained and taught.")
    suggestions: list[str] = Field(
        description="General next-step suggestions not tied to one specific issue."
    )


class FeedbackRead(CompositionFeedback):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    composition_id: uuid.UUID
    version_id: uuid.UUID
    skill_level: SkillLevel
    model: str
    created_at: datetime
    updated_at: datetime
