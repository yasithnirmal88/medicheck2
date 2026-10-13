from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.api.v1.cms.evidence as evidence_endpoint
from app.api.deps import get_cms_user, get_current_admin
from app.core.security.rbac import Permission, Role
from app.domain.entities.user import User
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.evidence_reference import (
    EvidenceReferenceModel,
)
from app.infrastructure.persistence.models.links import (
    QuestionIndicatorLinkModel,
    QuestionOptionIndicatorLinkModel,
)
from app.infrastructure.persistence.models.role import RoleModel
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.user_role import user_role_table
from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
    SQLKnowledgeGraphRepository,
)


def _cms_admin() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid.uuid4().hex,
        firebase_uid=f"critical-admin-{uuid.uuid4().hex}",
        email="critical-admin@example.test",
        full_name="Critical Fix Admin",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles={Role.MEDICAL_DIRECTOR},
        last_login_at=None,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


@pytest.fixture
def admin_overrides(client):
    app = client._transport.app
    admin = _cms_admin()
    app.dependency_overrides[get_cms_user] = lambda: admin
    app.dependency_overrides[get_current_admin] = lambda: admin
    yield app
    app.dependency_overrides.pop(get_cms_user, None)
    app.dependency_overrides.pop(get_current_admin, None)


def _role(code: str, priority: int) -> RoleModel:
    return RoleModel(
        code=code,
        name={"en": code},
        description="test role",
        is_system=True,
        priority=priority,
    )


def _user() -> UserModel:
    unique = uuid.uuid4().hex
    return UserModel(
        firebase_uid=f"critical-fix-{unique}",
        email=f"{unique}@example.test",
        full_name="Critical Fix Test",
        email_verified=True,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_role_updates_reject_self_escalation_and_unknown_roles(
    client, db_session: AsyncSession, admin_overrides
):
    target = _user()
    super_admin_role = _role("SUPER_ADMIN", 40)
    editor_role = _role("CONTENT_EDITOR", 15)
    db_session.add_all([target, super_admin_role, editor_role])
    await db_session.flush()
    await db_session.execute(
        user_role_table.insert().values(user_id=target.id, role_id=editor_role.id)
    )
    await db_session.commit()

    escalation = await client.put(
        f"/api/v1/admin/users/{target.id}/roles",
        json={"roles": ["SUPER_ADMIN"]},
    )
    assert escalation.status_code == 403

    invalid = await client.put(
        f"/api/v1/admin/users/{target.id}/roles",
        json={"roles": ["NOT_A_ROLE"]},
    )
    assert invalid.status_code == 422

    unchanged_roles = await db_session.execute(
        select(RoleModel.code)
        .join(user_role_table, user_role_table.c.role_id == RoleModel.id)
        .where(user_role_table.c.user_id == target.id)
    )
    assert unchanged_roles.scalars().all() == ["CONTENT_EDITOR"]

@pytest.mark.asyncio
async def test_role_updates_block_current_user_target(client, admin_overrides):
    admin = admin_overrides.dependency_overrides[get_current_admin]()
    response = await client.put(
        f"/api/v1/admin/users/{admin.id}/roles",
        json={"roles": ["SUPER_ADMIN"]},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_knowledge_graph_indicator_queries_filter_inactive_links_and_indicators(
    db_session: AsyncSession,
):
    now = datetime.now(UTC)
    suffix = uuid.uuid4().hex
    active = ClinicalIndicatorModel(
        body_system_id=f"bs-{suffix}",
        key=f"active-{suffix}",
        name="Active",
        is_active=True,
    )
    inactive = ClinicalIndicatorModel(
        body_system_id=f"bs-{suffix}",
        key=f"inactive-{suffix}",
        name="Inactive",
        is_active=False,
    )
    deleted = ClinicalIndicatorModel(
        body_system_id=f"bs-{suffix}",
        key=f"deleted-{suffix}",
        name="Deleted",
        is_active=True,
        deleted_at=now,
    )
    db_session.add_all([active, inactive, deleted])
    await db_session.flush()
    question_id = f"q-{suffix}"
    option_id = f"opt-{suffix}"
    db_session.add_all(
        [
            QuestionIndicatorLinkModel(
                question_id=question_id, indicator_id=active.id, active=True
            ),
            QuestionIndicatorLinkModel(
                question_id=question_id, indicator_id=inactive.id, active=True
            ),
            QuestionIndicatorLinkModel(
                question_id=question_id, indicator_id=deleted.id, active=True
            ),
            QuestionIndicatorLinkModel(
                question_id=question_id, indicator_id=active.id, active=False
            ),
            QuestionOptionIndicatorLinkModel(
                question_option_id=option_id, indicator_id=active.id, active=True
            ),
            QuestionOptionIndicatorLinkModel(
                question_option_id=option_id, indicator_id=inactive.id, active=True
            ),
            QuestionOptionIndicatorLinkModel(
                question_option_id=option_id, indicator_id=deleted.id, active=True
            ),
        ]
    )
    await db_session.flush()

    repo = SQLKnowledgeGraphRepository(db_session)
    question_indicators = await repo.get_indicators_by_question(question_id)
    question_batch = await repo.get_indicators_by_question_batch([question_id])
    option_indicators = await repo.get_indicators_by_question_option(option_id)
    option_batch = await repo.get_indicators_by_option_batch([option_id])

    assert [item.id for item in question_indicators] == [active.id]
    assert [item.id for item in question_batch[question_id]] == [active.id]
    assert [item.id for item in option_indicators] == [active.id]
    assert [item.id for item in option_batch[option_id]] == [active.id]


@pytest.mark.asyncio
async def test_graph_read_routes_require_authenticated_user(client):
    for path in (
        "/api/v1/graph/question/question-id",
        "/api/v1/graph/indicator/indicator-id",
        "/api/v1/graph/condition/condition-id",
    ):
        response = await client.get(path)
        assert response.status_code == 401, (path, response.text)


@pytest.mark.asyncio
async def test_evidence_create_uses_real_model_and_requires_write_permission(
    client, db_session: AsyncSession, admin_overrides, monkeypatch
):
    async def read_only_permissions(_session, _user_id):
        return {Permission.CMS_READ_EVIDENCE}

    monkeypatch.setattr(
        evidence_endpoint, "get_user_permissions", read_only_permissions
    )
    denied = await client.post(
        "/api/v1/cms/evidence",
        json={"title": "Read-only write attempt", "evidence_level": "A"},
    )
    assert denied.status_code == 403

    async def write_permissions(_session, _user_id):
        return {Permission.CMS_WRITE_EVIDENCE}

    monkeypatch.setattr(evidence_endpoint, "get_user_permissions", write_permissions)
    created = await client.post(
        "/api/v1/cms/evidence",
        json={
            "title": "Evidence title",
            "source": "Guideline",
            "url": "https://example.test/evidence",
            "evidence_level": "B",
            "summary": "Evidence summary",
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["evidence_level"] == "B"
    assert created.json()["source"] == "Guideline"

    invalid_grade = await client.post(
        "/api/v1/cms/evidence",
        json={"title": "Too-long grade", "evidence_level": "Level I"},
    )
    assert invalid_grade.status_code == 422

    stored = await db_session.execute(
        select(EvidenceReferenceModel).where(
            EvidenceReferenceModel.title == "Evidence title"
        )
    )
    record = stored.scalar_one()
    assert record.url == "https://example.test/evidence"
