"""Refresh-token session state.

JWTs are stateless by design, which is exactly the problem for a refresh
token: a 30-day-lived credential that can't be revoked if it leaks is a
real liability. Every issued refresh token gets a row here (hash only,
never the raw token) so a session can be revoked, and so token *reuse*
after rotation - the standard signal that a refresh token was stolen and
replayed - can be detected. See app.domains.auth.service for how these
rows get consumed.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # SHA-256 hex digest of the JWT, not the token itself - a leaked DB
    # backup must not hand out usable credentials.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
