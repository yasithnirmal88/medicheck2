from __future__ import annotations

from typing import Any

from httpx import AsyncClient

from app.infrastructure.persistence.repositories.sql_user_repository import (
    SQLUserRepository,
)


class TestAuthAPI:
    async def test_health_check(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data
        assert "timestamp" in data

    async def test_register_success(self, client: AsyncClient, db_session: Any) -> None:
        payload = {
            "firebase_token": "test-firebase-token",
            "full_name": "Test User",
            "email": "test@example.com",
        }
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
        assert "id" in data
        assert "firebase_uid" in data

    async def test_register_duplicate_firebase_uid(
        self, client: AsyncClient, db_session: Any
    ) -> None:
        payload1 = {
            "firebase_token": "duplicate-token",
            "full_name": "User One",
            "email": "one@example.com",
        }
        response1 = await client.post("/api/v1/auth/register", json=payload1)
        assert response1.status_code == 201

        payload2 = {
            "firebase_token": "duplicate-token",
            "full_name": "User Two",
            "email": "two@example.com",
        }
        response2 = await client.post("/api/v1/auth/register", json=payload2)
        assert response2.status_code == 409
        data = response2.json()
        assert "already" in data.get("error", {}).get("message", "").lower() or "already" in str(data).lower()

    async def test_login_creates_new_user(
        self, client: AsyncClient, db_session: Any
    ) -> None:
        payload = {"firebase_token": "new-login-token"}
        response = await client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] is not None
        assert data["user"]["is_active"] is True

    async def test_login_existing_user(
        self, client: AsyncClient, db_session: Any
    ) -> None:
        register_payload = {
            "firebase_token": "existing-login-token",
            "full_name": "Existing User",
            "email": "existing@example.com",
        }
        await client.post("/api/v1/auth/register", json=register_payload)

        login_payload = {"firebase_token": "existing-login-token"}
        response = await client.post("/api/v1/auth/login", json=login_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "existing@example.com"
        assert data["user"]["full_name"] == "Existing User"

    async def test_get_me_authenticated(
        self, client: AsyncClient, db_session: Any
    ) -> None:
        register_payload = {
            "firebase_token": "me-test-token",
            "full_name": "Me User",
            "email": "me@example.com",
        }
        reg_response = await client.post("/api/v1/auth/register", json=register_payload)
        assert reg_response.status_code == 201

        headers = {"Authorization": "Bearer me-test-token"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["full_name"] == "Me User"

    async def test_get_me_unauthenticated(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_delete_account(self, client: AsyncClient, db_session: Any) -> None:
        register_payload = {
            "firebase_token": "delete-test-token",
            "full_name": "Delete User",
            "email": "delete@example.com",
        }
        reg_response = await client.post("/api/v1/auth/register", json=register_payload)
        assert reg_response.status_code == 201

        headers = {"Authorization": "Bearer delete-test-token"}
        response = await client.delete("/api/v1/auth/me", headers=headers)
        assert response.status_code == 204

        repo = SQLUserRepository(db_session)
        user = await repo.find_by_firebase_uid("delete-test-token")
        assert user is not None
        assert user.is_active is False

    async def test_register_missing_fields(self, client: AsyncClient) -> None:
        payload = {"firebase_token": "test"}
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_empty_name(self, client: AsyncClient) -> None:
        payload = {
            "firebase_token": "test",
            "full_name": "",
            "email": "test@example.com",
        }
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422
