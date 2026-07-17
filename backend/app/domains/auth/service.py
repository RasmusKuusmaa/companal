"""Registration, authentication, and refresh-token lifecycle.

Two security properties this module is deliberately built around:

1. **Login doesn't leak whether an email is registered.** Both "no such
   user" and "wrong password" raise the same `InvalidCredentialsError`
   with no distinguishing detail, and the non-existent-user path still
   runs a password hash so response timing doesn't give away the
   difference either (`_TIMING_SAFE_DUMMY_HASH`).
2. **Refresh tokens are rotated and reuse is treated as theft.** Every
   refresh consumes the presented token (marks it revoked) and issues a
   new one. If a token already marked revoked is presented again - the
   signature of a stolen token being replayed after the legitimate
   client already rotated past it - every session for that user is
   revoked, not just the one token.
"""

import hashlib
import uuid
from datetime import UTC, datetime
from typing import NamedTuple

import jwt
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domains.auth.models import RefreshToken
from app.domains.auth.schemas import RegisterRequest
from app.domains.users.models import User

_TIMING_SAFE_DUMMY_HASH = hash_password(uuid.uuid4().hex)


class AuthError(Exception):
    """Base class for auth-domain failures; the router maps these to HTTP responses."""


class EmailAlreadyRegisteredError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass


class TokenPair(NamedTuple):
    access_token: str
    refresh_token: str


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise EmailAlreadyRegisteredError

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        # Closes the TOCTOU gap between the check above and the insert: two
        # concurrent registrations for the same email can both pass the
        # SELECT before either commits.
        await db.rollback()
        raise EmailAlreadyRegisteredError from exc
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        verify_password(password, _TIMING_SAFE_DUMMY_HASH)
        raise InvalidCredentialsError
    if not verify_password(password, user.hashed_password) or not user.is_active:
        raise InvalidCredentialsError
    return user


def _new_refresh_token_row(user_id: uuid.UUID, token: str) -> RefreshToken:
    payload = decode_token(token)
    return RefreshToken(
        user_id=user_id,
        token_hash=_hash_token(token),
        expires_at=datetime.fromtimestamp(payload.exp, tz=UTC),
    )


async def issue_tokens(db: AsyncSession, user: User) -> TokenPair:
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    db.add(_new_refresh_token_row(user.id, refresh_token))
    await db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


async def _revoke_all_for_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()


async def rotate_refresh_token(db: AsyncSession, presented_token: str) -> TokenPair:
    try:
        payload = decode_token(presented_token)
    except (jwt.InvalidTokenError, ValidationError) as exc:
        raise InvalidRefreshTokenError from exc

    if payload.type is not TokenType.REFRESH:
        raise InvalidRefreshTokenError

    row = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == _hash_token(presented_token))
    )
    if row is None:
        raise InvalidRefreshTokenError

    if row.revoked_at is not None:
        await _revoke_all_for_user(db, row.user_id)
        raise InvalidRefreshTokenError

    if row.expires_at < datetime.now(UTC):
        raise InvalidRefreshTokenError

    user = await db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise InvalidRefreshTokenError

    row.revoked_at = datetime.now(UTC)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    db.add(_new_refresh_token_row(user.id, refresh_token))
    await db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


async def revoke_refresh_token(db: AsyncSession, presented_token: str) -> None:
    row = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == _hash_token(presented_token))
    )
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)
        await db.commit()
