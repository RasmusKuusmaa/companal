from typing import Any, cast

from httpx import AsyncClient

REGISTER_PAYLOAD = {
    "email": "grace@example.com",
    "password": "correct horse battery staple",
    "full_name": "Grace Hopper",
}


async def _register(client: AsyncClient, **overrides: str) -> dict[str, Any]:
    response = await client.post("/api/v1/auth/register", json={**REGISTER_PAYLOAD, **overrides})
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


async def _login(
    client: AsyncClient,
    email: str = REGISTER_PAYLOAD["email"],
    password: str = REGISTER_PAYLOAD["password"],
) -> dict[str, Any]:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return cast(dict[str, Any], response.json())


class TestRegister:
    async def test_returns_the_created_user_without_the_password(self, client: AsyncClient) -> None:
        body = await _register(client)

        assert body["email"] == REGISTER_PAYLOAD["email"]
        assert body["full_name"] == REGISTER_PAYLOAD["full_name"]
        assert body["role"] == "student"
        assert body["is_active"] is True
        assert "password" not in body
        assert "hashed_password" not in body

    async def test_rejects_duplicate_email(self, client: AsyncClient) -> None:
        await _register(client)

        response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

        assert response.status_code == 409

    async def test_rejects_a_password_below_the_minimum_length(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register", json={**REGISTER_PAYLOAD, "password": "short"}
        )

        assert response.status_code == 422

    async def test_ignores_a_client_supplied_role(self, client: AsyncClient) -> None:
        # RegisterRequest has no `role` field at all - self-registration can
        # never grant teacher/admin privileges, no matter what's in the body.
        response = await client.post(
            "/api/v1/auth/register", json={**REGISTER_PAYLOAD, "role": "admin"}
        )

        assert response.status_code == 201
        assert response.json()["role"] == "student"


class TestLogin:
    async def test_returns_tokens_for_correct_credentials(self, client: AsyncClient) -> None:
        await _register(client)

        body = await _login(client)

        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["refresh_token"]

    async def test_rejects_wrong_password_and_unknown_email_identically(
        self, client: AsyncClient
    ) -> None:
        await _register(client)

        wrong_password = await client.post(
            "/api/v1/auth/login",
            json={"email": REGISTER_PAYLOAD["email"], "password": "not the password"},
        )
        unknown_email = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "irrelevant"},
        )

        assert wrong_password.status_code == 401
        assert unknown_email.status_code == 401
        assert wrong_password.json()["detail"] == unknown_email.json()["detail"]


class TestMe:
    async def test_requires_a_bearer_token(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_returns_the_authenticated_user(self, client: AsyncClient) -> None:
        await _register(client)
        tokens = await _login(client)

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == REGISTER_PAYLOAD["email"]

    async def test_rejects_a_garbage_token(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert response.status_code == 401

    async def test_rejects_a_refresh_token_used_as_an_access_token(
        self, client: AsyncClient
    ) -> None:
        await _register(client)
        tokens = await _login(client)

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
        )

        assert response.status_code == 401


class TestRefresh:
    async def test_rotates_tokens_and_retires_the_old_refresh_token(
        self, client: AsyncClient
    ) -> None:
        await _register(client)
        tokens = await _login(client)

        rotated = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert rotated.status_code == 200
        new_tokens = rotated.json()
        assert new_tokens["refresh_token"] != tokens["refresh_token"]

        reused = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert reused.status_code == 401

    async def test_rejects_an_invalid_token(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "garbage"})
        assert response.status_code == 401


class TestLogout:
    async def test_revokes_the_refresh_token(self, client: AsyncClient) -> None:
        await _register(client)
        tokens = await _login(client)

        logout_response = await client.post(
            "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
        )
        assert logout_response.status_code == 204

        refresh_response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_response.status_code == 401


class TestFullFlow:
    async def test_register_login_me_refresh_logout(self, client: AsyncClient) -> None:
        await _register(client)
        tokens = await _login(client)

        me_response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me_response.status_code == 200

        refresh_response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        refreshed = refresh_response.json()

        me_again = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {refreshed['access_token']}"}
        )
        assert me_again.status_code == 200

        logout_response = await client.post(
            "/api/v1/auth/logout", json={"refresh_token": refreshed["refresh_token"]}
        )
        assert logout_response.status_code == 204
