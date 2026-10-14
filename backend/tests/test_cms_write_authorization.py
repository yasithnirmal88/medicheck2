"""Regression tests for CMS write-authorization (least-privilege enforcement).

``get_cms_user`` only requires *any* CMS role (READ_ONLY_REVIEWER and above).
Before this fix, the rules / publishing / knowledge-graph routers declared only
``Depends(get_cms_user)`` on mutating endpoints, so a read-only reviewer could
create/update/delete content. Every mutation now requires the operation-specific
``CMS_WRITE_*`` / ``CMS_APPROVE_CONTENT`` permission.

These tests exercise the real permission-resolution path
(``app.identity.get_user_permissions``), seeding a DB user + role and overriding
only token authentication (``get_cms_user``), so the authorization decision is
made exactly as in production.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cms_user
from app.core.security.rbac import Role
from app.domain.entities.user import User
from app.infrastructure.persistence.models.role import RoleModel
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.user_role import user_role_table

KG_GRAPH = "/api/v1/cms/knowledge-graph/graphs"
PUBLISHING = "/api/v1/cms/publishing"


def _cms_user(role: Role) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid.uuid4().hex,
        firebase_uid=f"cms-authz-{uuid.uuid4().hex}",
        email=None,
        full_name="CMS Authz User",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles={role},
        last_login_at=None,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


@pytest_asyncio.fixture
async def cms_as(client, db_session: AsyncSession):
    """Yield a coroutine that authenticates subsequent requests as ``role``.

    Seeds a real user + role link (so ``get_user_permissions`` resolves) and
    overrides ``get_cms_user`` only (token authentication), never the
    permission resolution under test.
    """
    app = client._transport.app  # type: ignore[attr-defined]
    seeded_roles: dict[str, RoleModel] = {}

    async def _as(role: Role) -> User:
        user = _cms_user(role)
        role_model = seeded_roles.get(role.value)
        if role_model is None:
            role_model = RoleModel(
                code=role.value,
                name={"en": role.display_name},
                description="test role",
                is_system=True,
                priority=1,
            )
            db_session.add(role_model)
            await db_session.flush()
            seeded_roles[role.value] = role_model
        db_session.add(
            UserModel(
                id=user.id,
                firebase_uid=user.firebase_uid,
                email=user.email,
                full_name=user.full_name,
                email_verified=True,
                is_active=True,
            )
        )
        await db_session.flush()
        await db_session.execute(
            user_role_table.insert().values(
                user_id=user.id, role_id=role_model.id
            )
        )
        await db_session.commit()
        app.dependency_overrides[get_cms_user] = lambda: user
        return user

    yield _as
    app.dependency_overrides.pop(get_cms_user, None)


# --- rules.py -------------------------------------------------------------

@pytest.mark.asyncio
async def test_rule_set_writes_require_cms_write_rule(client, cms_as):
    await cms_as(Role.READ_ONLY_REVIEWER)
    body = {"questionnaire_id": "q-1", "name": "RS", "rules": {"a": 1}}
    assert (await client.post("/api/v1/cms/rules", json=body)).status_code == 403
    assert (
        await client.put("/api/v1/cms/rules/does-not-exist", json={"name": "x"})
    ).status_code == 403

    await cms_as(Role.CONTENT_EDITOR)
    created = await client.post("/api/v1/cms/rules", json=body)
    assert created.status_code == 200, created.text


# --- knowledge_graph.py ---------------------------------------------------

@pytest.mark.asyncio
async def test_knowledge_graph_writes_require_cms_write_kg(client, cms_as):
    await cms_as(Role.READ_ONLY_REVIEWER)
    graph_body = {"name": "G", "body_system_id": "bs-1"}
    assert (await client.post(KG_GRAPH, json=graph_body)).status_code == 403
    assert (
        await client.post(
            f"{KG_GRAPH}/g-1/nodes",
            json={"entity_type": "question", "entity_id": "q-1"},
        )
    ).status_code == 403
    assert (
        await client.post(
            f"{KG_GRAPH}/g-1/edges",
            json={
                "source_node_id": "n1",
                "target_node_id": "n2",
                "relationship_type": "related_to",
            },
        )
    ).status_code == 403
    assert (await client.delete(f"{KG_GRAPH}/g-1")).status_code == 403
    assert (
        await client.post(
            "/api/v1/cms/knowledge-graph/bulk-link",
            json={
                "entity_type": "question",
                "source_ids": ["q1"],
                "target_type": "indicator",
                "target_ids": ["i1"],
            },
        )
    ).status_code == 403

    await cms_as(Role.SPECIALIST_DOCTOR)
    created = await client.post(KG_GRAPH, json=graph_body)
    assert created.status_code == 200, created.text


# --- publishing.py --------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_writes_require_cms_write_workflow(client, cms_as):
    await cms_as(Role.READ_ONLY_REVIEWER)
    body = {"name": "WF", "entity_type": "question"}
    assert (await client.post(f"{PUBLISHING}/workflows", json=body)).status_code == 403

    # SPECIALIST_DOCTOR has CMS_WRITE_PUBLISH but NOT CMS_WRITE_WORKFLOW.
    await cms_as(Role.SPECIALIST_DOCTOR)
    assert (await client.post(f"{PUBLISHING}/workflows", json=body)).status_code == 403

    await cms_as(Role.MEDICAL_DIRECTOR)
    created = await client.post(f"{PUBLISHING}/workflows", json=body)
    assert created.status_code == 200, created.text


@pytest.mark.asyncio
async def test_job_writes_require_cms_write_publish(client, cms_as):
    await cms_as(Role.READ_ONLY_REVIEWER)
    body = {"entity_type": "question", "entity_id": "q-1", "version": 1}
    assert (await client.post(f"{PUBLISHING}/jobs", json=body)).status_code == 403

    # GENERAL_PHYSICIAN has CMS access + CMS_WRITE_RULE but no CMS_WRITE_PUBLISH.
    await cms_as(Role.GENERAL_PHYSICIAN)
    assert (await client.post(f"{PUBLISHING}/jobs", json=body)).status_code == 403

    await cms_as(Role.SPECIALIST_DOCTOR)
    created = await client.post(f"{PUBLISHING}/jobs", json=body)
    assert created.status_code == 200, created.text


@pytest.mark.asyncio
async def test_approval_decisions_require_cms_approve_content(client, cms_as):
    # CONTENT_EDITOR has CMS access but no CMS_APPROVE_CONTENT.
    await cms_as(Role.CONTENT_EDITOR)
    denied = await client.post(f"{PUBLISHING}/jobs/some-job/approve")
    assert denied.status_code == 403

    # RESEARCH_REVIEWER holds CMS_APPROVE_CONTENT: authorization passes, and the
    # missing job surfaces as a 404 (not 403).
    await cms_as(Role.RESEARCH_REVIEWER)
    allowed = await client.post(f"{PUBLISHING}/jobs/some-job/approve")
    assert allowed.status_code == 404, allowed.text


@pytest.mark.asyncio
async def test_approval_and_change_request_writes_require_permissions(client, cms_as):
    await cms_as(Role.READ_ONLY_REVIEWER)
    assert (
        await client.post(
            f"{PUBLISHING}/approvals",
            json={"entity_type": "question", "entity_id": "q-1"},
        )
    ).status_code == 403
    assert (
        await client.post(
            f"{PUBLISHING}/change-requests",
            json={
                "entity_type": "question",
                "entity_id": "q-1",
                "title": "CR",
            },
        )
    ).status_code == 403

    await cms_as(Role.MEDICAL_DIRECTOR)
    created = await client.post(
        f"{PUBLISHING}/approvals",
        json={"entity_type": "question", "entity_id": "q-1"},
    )
    assert created.status_code == 200, created.text


# --- reads remain open to read-only CMS roles -----------------------------

@pytest.mark.asyncio
async def test_reads_allowed_for_read_only_reviewer(client, cms_as):
    await cms_as(Role.READ_ONLY_REVIEWER)
    assert (await client.get("/api/v1/cms/rules")).status_code == 200
    assert (await client.get(KG_GRAPH)).status_code == 200
    assert (await client.get(f"{PUBLISHING}/workflows")).status_code == 200
    assert (await client.get(f"{PUBLISHING}/jobs")).status_code == 200


# --- unauthenticated ------------------------------------------------------

@pytest.mark.asyncio
async def test_unauthenticated_mutation_is_denied(client):
    body = {"questionnaire_id": "q-1", "name": "RS", "rules": {"a": 1}}
    response = await client.post("/api/v1/cms/rules", json=body)
    assert response.status_code == 401, response.text
