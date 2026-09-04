"""Shared FastAPI dependencies: DB session, JWT-authenticated user, and
feature gating."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.features import Feature, tier_has_feature
from app.core.security import TokenPayload, TokenType, decode_token
from app.db.session import AsyncSessionLocal
from app.domains.billing import service as billing_service
from app.domains.users.models import User

# tokenUrl points at where the (not-yet-built) login endpoint will live;
# used only for OpenAPI's "Authorize" button, not for routing.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_token_payload(
    token: str | None = Depends(oauth2_scheme),
) -> TokenPayload:
    if token is None:
        raise _credentials_exception
    try:
        payload = decode_token(token)
    except (jwt.InvalidTokenError, ValidationError) as exc:
        raise _credentials_exception from exc
    if payload.type is not TokenType.ACCESS:
        raise _credentials_exception
    return payload


async def get_current_user(
    payload: TokenPayload = Depends(get_current_token_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError as exc:
        raise _credentials_exception from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise _credentials_exception
    return user


def require_feature(feature: Feature) -> Callable[..., Awaitable[User]]:
    """Dependency factory gating a route behind a feature the caller's tier
    must have. Raises 402 with a payload the frontend can turn straight into
    an upgrade prompt, rather than a bare "forbidden".

    When no `ANTHROPIC_API_KEY` is configured at all, every AI feature is
    unavailable regardless of tier - raising the usual 402 there would tell
    a user to upgrade for something upgrading can't fix, so this raises 404
    instead: the same "doesn't exist here" signal already used for a missing
    resource, not an upgrade prompt and not a 503.
    """

    async def _require_feature(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        if not settings.ANTHROPIC_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This feature is not available in this deployment.",
            )

        tier = await billing_service.get_tier(db, user.id)
        if not tier_has_feature(tier, feature):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "upgrade_required",
                    "feature": feature.value,
                    "tier": tier.value,
                },
            )
        return user

    return _require_feature
