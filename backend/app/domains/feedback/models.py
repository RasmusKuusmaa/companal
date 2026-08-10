"""AI-generated composition feedback, stored per version and skill level.

One row per `(version_id, skill_level)`: like `CompositionAnalysis`, this is a
cache of an AI call rather than a history log - regenerating feedback for the
same version and skill level overwrites the row instead of growing a list of
near-duplicates.
"""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SkillLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("version_id", "skill_level"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    composition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compositions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("composition_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_level: Mapped[SkillLevel] = mapped_column(
        Enum(
            SkillLevel,
            name="feedback_skill_level",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    # Each a list of plain JSON objects/strings - see
    # app.domains.feedback.schemas.CompositionFeedback for the shape written
    # here, which is also exactly what the API returns.
    strengths: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    suggestions: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    model: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
