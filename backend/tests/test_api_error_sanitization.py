from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

import app.core.config as config_module
import app.main as app_main
import app.infrastructure.database as database_module
from app.api.deps import get_current_active_user, get_db
from app.application.services.profile_service import ProfileService
from app.application.services.cms.rule_engine_service import RuleEngineService
from app.domain.entities.user import User
from app.main import create_app


@pytest.mark.asyncio
async def test_profile_unexpected_errors_are_sanitized(db_session, test_settings, monkeypatch):
    originals = (
        config_module.settings, app_main.settings, database_module.settings,
        database_module._engine, database_module._async_session_factory,
    )
    config_module.settings = test_settings
    app_main.settings = test_settings
    database_module.settings = test_settings
    database_module._engine = None
    database_module._async_session_factory = None

    user = User(
        id="profile-user",
        firebase_uid="profile-uid",
        email="profile@example.com",
        full_name="Profile User",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles=set(),
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )

    async def boom(self, current_user, payload):
        raise RuntimeError("database error: sqlite3.OperationalError: no such table 'profiles'")

    monkeypatch.setattr(ProfileService, "update_personal_info", boom)

    app = create_app()
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: user

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/profiles/me/personal",
                json={"full_name": "Updated User"},
            )
            assert response.status_code == 500, response.text
            body = response.json()
            assert body["error"]["code"] == "internal_error"
            assert body["error"]["message"] == "An unexpected error occurred"
            text = response.text.lower()
            assert "no such table" not in text
            assert "sqlite3" not in text
            assert "operationalerror" not in text
    finally:
        app.dependency_overrides.clear()
        (
            config_module.settings, app_main.settings, database_module.settings,
            database_module._engine, database_module._async_session_factory,
        ) = originals


@pytest.mark.asyncio
async def test_restore_version_unexpected_errors_are_sanitized(db_session, test_settings, monkeypatch):
    originals = (
        config_module.settings, app_main.settings, database_module.settings,
        database_module._engine, database_module._async_session_factory,
    )
    config_module.settings = test_settings
    app_main.settings = test_settings
    database_module.settings = test_settings
    database_module._engine = None
    database_module._async_session_factory = None

    user = User(
        id="restore-user",
        firebase_uid="restore-uid",
        email="restore@example.com",
        full_name="Restore User",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles=set(),
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )

    async def boom(self, current_user, version):
        raise RuntimeError("transaction failed: IntegrityError: duplicate key on profiles_versions")

    monkeypatch.setattr(ProfileService, "restore_version", boom)

    app = create_app()
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: user

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/profiles/me/versions/1/restore")
            assert response.status_code == 500, response.text
            body = response.json()
            assert body["error"]["message"] == "An unexpected error occurred"
            assert "duplicate key" not in response.text.lower()
            assert "integrityerror" not in response.text.lower()
    finally:
        app.dependency_overrides.clear()
        (
            config_module.settings, app_main.settings, database_module.settings,
            database_module._engine, database_module._async_session_factory,
        ) = originals


@pytest.mark.asyncio
async def test_rule_validation_keeps_validation_errors_and_sanitizes_internal_errors(db_session, test_settings, monkeypatch):
    originals = (
        config_module.settings, app_main.settings, database_module.settings,
        database_module._engine, database_module._async_session_factory,
    )
    config_module.settings = test_settings
    app_main.settings = test_settings
    database_module.settings = test_settings
    database_module._engine = None
    database_module._async_session_factory = None

    user = User(
        id="rules-user",
        firebase_uid="rules-uid",
        email="rules@example.com",
        full_name="Rules User",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles=set(),
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )

    from app.identity import get_cms_user

    app = create_app()
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cms_user] = lambda: user

    def validation_error(self, expression, context):
        raise ValueError("Unsupported operator: @")

    def internal_error(self, expression, context):
        raise RuntimeError("database error: sqlite3.OperationalError: no such table 'rules'")

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            monkeypatch.setattr(RuleEngineService, "evaluate_expression", validation_error)
            response = await client.post(
                "/api/v1/cms/rules/validate",
                json={"expression": {"op": "@"}, "context": {}},
            )
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["valid"] is False
            assert body["error"] == "Unsupported operator: @"

            monkeypatch.setattr(RuleEngineService, "evaluate_expression", internal_error)
            response = await client.post(
                "/api/v1/cms/rules/validate",
                json={"expression": {"op": "?"}, "context": {}},
            )
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["valid"] is False
            assert body["error"] == "Expression validation failed"
            assert "no such table" not in response.text.lower()
            assert "sqlite3" not in response.text.lower()
    finally:
        app.dependency_overrides.clear()
        (
            config_module.settings, app_main.settings, database_module.settings,
            database_module._engine, database_module._async_session_factory,
        ) = originals
