"""Regression tests for the CMS recovery endpoints added in Task 3:

- GET /api/v1/cms/rules            -> bare array of rule sets
- GET /api/v1/cms/rules/{id}       -> single rule set (or 404)
- POST /api/v1/cms/rules           -> create rule set
- PUT /api/v1/cms/rules/{id}       -> update rule set
- GET /api/v1/admin/users          -> paginated {items,total,skip,limit}
- GET /api/v1/admin/users/{id}     -> single user (or 404)
- PUT /api/v1/admin/users/{id}/roles
- POST /api/v1/admin/users/{id}/toggle-active
- GET /api/v1/admin/roles          -> bare array of roles
"""
import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_cms_user, get_db
from app.domain.entities.user import User
from app.core.security.rbac import Role
from app.infrastructure.persistence.models.questionnaire_rule_set import (
    QuestionnaireRuleSetModel,
)
from app.infrastructure.persistence.models.role import RoleModel
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.user_role import user_role_table


def _cms_admin() -> User:
    return User(
        id=uuid.uuid4().hex,
        firebase_uid="cms-admin-uid",
        email="cms-admin@example.com",
        full_name="CMS Admin",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles={Role.MEDICAL_DIRECTOR},
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )


@pytest_asyncio.fixture
async def cms_overrides(client, db_session: AsyncSession):
    """Authenticate the request as a CMS MEDICAL_DIRECTOR.

    The write endpoints now resolve the caller's effective permissions from the
    database (``app.identity.get_user_permissions``), so the injected user must
    exist in the DB with its MEDICAL_DIRECTOR role linked — exactly as in
    production. The override only short-circuits token authentication.
    """
    admin = _cms_admin()
    app = client._transport.app  # type: ignore[attr-defined]
    role = RoleModel(
        code=Role.MEDICAL_DIRECTOR.value,
        name={"en": "Medical Director"},
        description="test role",
        is_system=True,
        priority=30,
    )
    user_row = UserModel(
        id=admin.id,
        firebase_uid=admin.firebase_uid,
        email=admin.email,
        full_name=admin.full_name,
        email_verified=True,
        is_active=True,
    )
    db_session.add_all([role, user_row])
    await db_session.flush()
    await db_session.execute(
        user_role_table.insert().values(user_id=admin.id, role_id=role.id)
    )
    await db_session.commit()

    app.dependency_overrides[get_cms_user] = lambda: admin
    app.dependency_overrides[get_current_admin] = lambda: admin
    yield app
    app.dependency_overrides.pop(get_cms_user, None)
    app.dependency_overrides.pop(get_current_admin, None)


@pytest.mark.asyncio
async def test_list_rule_sets_bare_array(client, db_session: AsyncSession, cms_overrides):
    db_session.add(
        QuestionnaireRuleSetModel(
            questionnaire_id="q-1",
            name="RS1",
            rules={"x": 1},
            logic="ALL",
            is_active=True,
            version=1,
            status="draft",
        )
    )
    await db_session.commit()

    r = await client.get("/api/v1/cms/rules")
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert any(item["name"] == "RS1" for item in data)


@pytest.mark.asyncio
async def test_get_rule_set_not_found(client, cms_overrides):
    r = await client.get("/api/v1/cms/rules/does-not-exist")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_and_update_rule_set(client, db_session: AsyncSession, cms_overrides):
    payload = {
        "questionnaire_id": "q-2",
        "name": "New RS",
        "rules": {"x": 1},
        "logic": "ALL",
    }
    r = await client.post("/api/v1/cms/rules", json=payload)
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["name"] == "New RS"
    rid = created["id"]

    r2 = await client.put(f"/api/v1/cms/rules/{rid}", json={"name": "Renamed RS"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["name"] == "Renamed RS"


@pytest.mark.asyncio
async def test_admin_list_roles_bare_array(client, db_session: AsyncSession, cms_overrides):
    db_session.add(
        RoleModel(
            code="TEST_ROLE",
            name={"en": "Test"},
            description="d",
            is_system=False,
            priority=1,
        )
    )
    await db_session.commit()

    r = await client.get("/api/v1/admin/roles")
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert any(item["code"] == "TEST_ROLE" for item in data)


@pytest.mark.asyncio
async def test_admin_list_users_paginated(client, db_session: AsyncSession, cms_overrides):
    r = await client.get("/api/v1/admin/users", params={"limit": 5})
    assert r.status_code == 200, r.text
    body = r.json()
    assert {"items", "total", "skip", "limit"} <= set(body.keys())
    assert body["limit"] == 5


@pytest.mark.asyncio
async def test_admin_toggle_user_active_and_roles(
    client, db_session: AsyncSession, cms_overrides
):
    user = UserModel(
        firebase_uid="tu-" + uuid.uuid4().hex,
        email="tu@example.com",
        full_name="Target User",
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    uid = user.id

    r = await client.post(f"/api/v1/admin/users/{uid}/toggle-active")
    assert r.status_code == 200, r.text
    assert r.json()["is_active"] is False

    role = RoleModel(
        code="CONTENT_EDITOR",
        name={"en": "Content Editor"},
        description="d",
        is_system=False,
        priority=1,
    )
    db_session.add(role)
    await db_session.commit()

    r2 = await client.put(
        f"/api/v1/admin/users/{uid}/roles", json={"roles": ["CONTENT_EDITOR"]}
    )
    assert r2.status_code == 200, r2.text
    roles = r2.json()["roles"]
    assert "CONTENT_EDITOR" in roles
