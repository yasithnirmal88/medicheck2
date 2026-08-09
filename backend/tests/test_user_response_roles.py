"""Regression test: /auth/me must serialize real CMS roles without 500ing.

The UserResponse.roles Literal previously only allowed patient|doctor|
researcher|administrator, so any user holding a real CMS role
(medical_director, specialist_doctor, ...) caused UserResponse.from_entity
to raise a Pydantic ValidationError and /auth/me returned 500, which
prevented the frontend from ever resolving a CMS role.
"""
import uuid
from datetime import UTC, datetime

import pytest

from app.application.dtos.auth_dtos import UserResponse
from app.core.security.rbac import Role
from app.domain.entities.user import User


@pytest.mark.asyncio
async def test_user_response_serializes_all_cms_roles():
    for role in (
        Role.MEDICAL_DIRECTOR,
        Role.SPECIALIST_DOCTOR,
        Role.GENERAL_PHYSICIAN,
        Role.RESEARCH_REVIEWER,
        Role.CONTENT_EDITOR,
        Role.READ_ONLY_REVIEWER,
        Role.SUPER_ADMIN,
        Role.PATIENT,
        Role.DOCTOR,
    ):
        user = User(
            id=uuid.uuid4().hex,
            firebase_uid="uid-" + role.value,
            email=f"{role.value}@example.com",
            full_name="Test",
            avatar_url=None,
            email_verified=True,
            is_active=True,
            roles={role},
            last_login_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            deleted_at=None,
        )
        resp = UserResponse.from_entity(user)
        assert resp.roles == [role.value], f"role {role.value} not serialized"


@pytest.mark.asyncio
async def test_auth_me_endpoint_returns_cms_role(
    db_session, test_settings
):
    """End-to-end: a user with a CMS role gets a 200 /auth/me carrying the role,
    not a 500 from response-model validation."""
    import app.core.config as config_module
    import app.main as app_main
    import app.infrastructure.database as database_module
    from app.api.deps import get_current_active_user, get_db
    from app.domain.entities.user import User as DomainUser
    from app.main import create_app
    from httpx import ASGITransport, AsyncClient

    originals = (
        config_module.settings, app_main.settings, database_module.settings,
        database_module._engine, database_module._async_session_factory,
    )
    config_module.settings = test_settings
    app_main.settings = test_settings
    database_module.settings = test_settings
    database_module._engine = None
    database_module._async_session_factory = None

    cms_user = DomainUser(
        id=uuid.uuid4().hex,
        firebase_uid="cms-me-uid",
        email="cms@example.com",
        full_name="CMS User",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles={Role.MEDICAL_DIRECTOR},
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )

    app = create_app()
    app.dependency_overrides[get_db] = lambda: (lambda: (yield db_session))()
    app.dependency_overrides[get_current_active_user] = lambda: cms_user
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            r = await c.get("/api/v1/auth/me")
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["roles"] == ["medical_director"]
    finally:
        app.dependency_overrides.clear()
        (
            config_module.settings, app_main.settings, database_module.settings,
            database_module._engine, database_module._async_session_factory,
        ) = originals


