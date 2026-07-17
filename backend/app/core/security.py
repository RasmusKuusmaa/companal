"""Password hashing and JWT creation/verification.

Decoupled from any specific ORM model: tokens carry a subject (`sub`, the
user id as a string) and a type (`access` vs `refresh`). Resolving `sub` to
an actual user row is the caller's job (see core/dependencies.py).
"""

import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from pydantic import BaseModel

from app.core.config import settings

_password_hasher = PasswordHasher()


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(BaseModel):
    sub: str
    type: TokenType
    iat: int
    exp: int
    jti: str


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False


def _create_token(subject: uuid.UUID | str, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        # Without a per-token nonce, two tokens for the same subject
        # issued within the same second (same iat, same fixed
        # expires_delta -> same exp) are byte-identical JWTs. That's a
        # real case, not just a testing artifact - e.g. issuing refresh
        # tokens for the same user from two tabs within the same second -
        # and it broke the DB's uniqueness constraint on the refresh
        # token's hash.
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: uuid.UUID | str) -> str:
    return _create_token(
        subject, TokenType.ACCESS, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(subject: uuid.UUID | str) -> str:
    return _create_token(
        subject, TokenType.REFRESH, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str) -> TokenPayload:
    """Raises jwt.InvalidTokenError (or a subclass) on a bad/expired token."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    return TokenPayload(**payload)
