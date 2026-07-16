"""Shared FastAPI dependencies: DB session and JWT-authenticated user."""

import uuid
from collections.abc import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import TokenPayload, TokenType, decode_token
from app.db.session import AsyncSessionLocal
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
