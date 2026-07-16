"""Pydantic schemas for the users domain.

Just the read model needed to type `get_current_user`'s return value for
now — create/update schemas arrive with the registration endpoint.
"""

import uuid

from pydantic import BaseModel, ConfigDict

from app.domains.users.models import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
