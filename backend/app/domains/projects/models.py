"""Composition, Version and CompositionAnalysis ORM models.

A `Composition` is the project shell (title, ownership); each upload of a
MusicXML file creates a `Version` row under it. `version_count` on
`Composition` is denormalized rather than computed via a join/count on every
list request - it's maintained by `service.add_version` in the same
transaction that inserts the new `Version` row, so it never drifts.

A `CompositionAnalysis` caches the combined melody/harmony/rhythm analysis of
one `Version`.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Composition(Base):
    __tablename__ = "compositions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Version(Base):
    __tablename__ = "composition_versions"
    __table_args__ = (UniqueConstraint("composition_id", "version_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    composition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compositions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # Relative key into app.core.storage, not a filesystem path - see that
    # module for why the distinction matters.
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CompositionAnalysis(Base):
    """The stored result of analyzing one version of a composition.

    One row per version, not one per run: the engines are deterministic, so
    re-analyzing a version can only reproduce what is already here, and
    `service.analyze_composition` overwrites in place rather than growing a
    history of identical rows.

    Each engine's full report is kept as JSONB so the stored analysis matches
    the API response exactly, while the four scores are also lifted into
    columns of their own so they can be filtered and ordered on without
    unpacking the documents. A score is null when that engine could not run
    against the version - `unavailable` records why.
    """

    __tablename__ = "composition_analyses"
    __table_args__ = (UniqueConstraint("version_id"),)

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

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    melody_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    harmony_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rhythm_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # none_as_null: without it SQLAlchemy stores a missing analysis as the
    # JSON value 'null' rather than SQL NULL, so `WHERE harmony_analysis IS
    # NULL` would never match an engine that could not run - defeating the
    # point of making these queryable alongside the score columns.
    melody_analysis: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True),  # type: ignore[no-untyped-call]
        nullable=True,
    )
    harmony_analysis: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True),  # type: ignore[no-untyped-call]
        nullable=True,
    )
    rhythm_analysis: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True),  # type: ignore[no-untyped-call]
        nullable=True,
    )
    unavailable: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
