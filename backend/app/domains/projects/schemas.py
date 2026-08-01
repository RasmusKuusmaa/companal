import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domains.analysis.schemas import AnalysisBundle


class CompositionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class CompositionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class CompositionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    version_count: int
    created_at: datetime
    updated_at: datetime


class VersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    composition_id: uuid.UUID
    version_number: int
    original_filename: str
    file_size: int
    created_at: datetime


class CompositionAnalysisRead(AnalysisBundle):
    """A stored combined analysis, as returned by the analyze endpoint.

    Extends the engine bundle (`melody_analysis`, `harmony_analysis`,
    `rhythm_analysis`, `overall_score`, `unavailable`) with the identity of
    the version that was analyzed, since an analysis always belongs to one
    specific upload rather than to the composition as a whole.
    """

    composition_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    analyzed_at: datetime
