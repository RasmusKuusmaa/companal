import hashlib
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.domains.auth.models import RefreshToken
from app.domains.auth.schemas import RegisterRequest
from app.domains.auth.service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    authenticate_user,
    issue_tokens,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.domains.users.models import User


def _register_payload(email: str = "ada@example.com") -> RegisterRequest:
    return RegisterRequest(email=email, password="correct horse battery staple", full_name="Ada")


async def _registered_user(db_session: AsyncSession, email: str = "ada@example.com") -> User:
    return await register_user(db_session, _register_payload(email))


class TestRegisterUser:
    async def test_creates_user_with_hashed_password(self, db_session: AsyncSession) -> None:
        user = await _registered_user(db_session)

        assert user.email == "ada@example.com"
        assert user.is_active is True
        assert user.hashed_password != "correct horse battery staple"

    async def test_rejects_duplicate_email(self, db_session: AsyncSession) -> None:
        await _registered_user(db_session)

        with pytest.raises(EmailAlreadyRegisteredError):
            await _registered_user(db_session)


class TestAuthenticateUser:
    async def test_succeeds_with_correct_credentials(self, db_session: AsyncSession) -> None:
        await _registered_user(db_session)

        user = await authenticate_user(
            db_session, "ada@example.com", "correct horse battery staple"
        )

        assert user.email == "ada@example.com"

    async def test_rejects_wrong_password(self, db_session: AsyncSession) -> None:
        await _registered_user(db_session)

        with pytest.raises(InvalidCredentialsError):
            await authenticate_user(db_session, "ada@example.com", "wrong password")

    async def test_rejects_unknown_email_with_the_same_error_as_wrong_password(
        self, db_session: AsyncSession
    ) -> None:
        # Deliberately not distinguishing "no such user" from "wrong
        # password" - both must raise the identical exception so a caller
        # (and the HTTP layer above it) can't be used to enumerate
        # registered emails.
        with pytest.raises(InvalidCredentialsError):
            await authenticate_user(db_session, "nobody@example.com", "whatever")

    async def test_rejects_inactive_user(self, db_session: AsyncSession) -> None:
        user = await _registered_user(db_session)
        user.is_active = False
        await db_session.commit()

        with pytest.raises(InvalidCredentialsError):
            await authenticate_user(db_session, "ada@example.com", "correct horse battery staple")


class TestIssueTokens:
    async def test_persists_a_hashed_refresh_token_row(self, db_session: AsyncSession) -> None:
        user = await _registered_user(db_session)

        tokens = await issue_tokens(db_session, user)

        expected_hash = hashlib.sha256(tokens.refresh_token.encode()).hexdigest()
        row = await db_session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == expected_hash)
        )
        assert row is not None
        assert row.user_id == user.id
        assert row.revoked_at is None
        assert row.expires_at > datetime.now(UTC)


class TestRotateRefreshToken:
    async def test_rotation_issues_new_tokens_and_revokes_the_old_row(
        self, db_session: AsyncSession
    ) -> None:
        user = await _registered_user(db_session)
        original = await issue_tokens(db_session, user)

        rotated = await rotate_refresh_token(db_session, original.refresh_token)

        assert rotated.refresh_token != original.refresh_token
        assert rotated.access_token != original.access_token

        original_hash = hashlib.sha256(original.refresh_token.encode()).hexdigest()
        original_row = await db_session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == original_hash)
        )
        assert original_row is not None
        assert original_row.revoked_at is not None

    async def test_reusing_a_rotated_token_revokes_every_session_for_that_user(
        self, db_session: AsyncSession
    ) -> None:
        user = await _registered_user(db_session)
        session_a = await issue_tokens(db_session, user)
        session_b = await issue_tokens(db_session, user)

        rotated_a = await rotate_refresh_token(db_session, session_a.refresh_token)

        # Replaying the now-consumed session_a token is the reuse signal.
        with pytest.raises(InvalidRefreshTokenError):
            await rotate_refresh_token(db_session, session_a.refresh_token)

        # Fallout: not just session_a, but its rotated replacement AND the
        # unrelated, still-otherwise-valid session_b must all be dead too.
        for token in (rotated_a.refresh_token, session_b.refresh_token):
            with pytest.raises(InvalidRefreshTokenError):
                await rotate_refresh_token(db_session, token)

    async def test_rejects_a_malformed_token(self, db_session: AsyncSession) -> None:
        with pytest.raises(InvalidRefreshTokenError):
            await rotate_refresh_token(db_session, "not-a-jwt")

    async def test_rejects_an_access_token_presented_as_a_refresh_token(
        self, db_session: AsyncSession
    ) -> None:
        user = await _registered_user(db_session)
        access_token = create_access_token(user.id)

        with pytest.raises(InvalidRefreshTokenError):
            await rotate_refresh_token(db_session, access_token)


class TestRevokeRefreshToken:
    async def test_revokes_the_matching_row(self, db_session: AsyncSession) -> None:
        user = await _registered_user(db_session)
        tokens = await issue_tokens(db_session, user)

        await revoke_refresh_token(db_session, tokens.refresh_token)

        with pytest.raises(InvalidRefreshTokenError):
            await rotate_refresh_token(db_session, tokens.refresh_token)

    async def test_is_idempotent(self, db_session: AsyncSession) -> None:
        user = await _registered_user(db_session)
        tokens = await issue_tokens(db_session, user)

        await revoke_refresh_token(db_session, tokens.refresh_token)
        await revoke_refresh_token(db_session, tokens.refresh_token)
