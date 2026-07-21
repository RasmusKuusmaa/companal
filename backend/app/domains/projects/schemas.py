import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
