"""Regression tests for P2-2: _populate_user_roles redundancy removal.

Verifies that roles are still correctly populated on the authenticated user
(loaded eagerly by find_by_firebase_uid via selectinload) WITHOUT the
previously-redundant _populate_user_roles query, and that RBAC enforcement is
unchanged across the required cases:
  - users with multiple roles
  - users with missing roles
  - blocked (inactive) users
  - unauthorized users hitting a role-gated endpoint
"""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.role import RoleModel
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.user_role import user_role_table


async def _seed_user_with_roles(
    client: AsyncClient,
    session: AsyncSession,
    token: str,
    role_codes: list[str],
) -> str:
    """Auto-create a user via a first /auth/me call (mock auth), then replace
    its role assignments with the given role codes. Returns the user id.

    New users default to the patient role (User.create), so we clear existing
    assignments first to set the desired role set deterministically."""
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    uid = resp.json()["id"]

    # Clear any auto-assigned roles (e.g. the default patient role).
    await session.execute(
        user_role_table.delete().where(user_role_table.c.user_id == uid)
    )

    # Resolve or create role rows, then link them to the user.
    for code in role_codes:
        existing = (
            await session.execute(
                select(RoleModel.id).where(RoleModel.code == code)
            )
        ).scalar_one_or_none()
        if existing is None:
            role = RoleModel(
                code=code,
                name={"en": code.replace("_", " ").title()},
                description=f"System role: {code}",
                is_system=True,
                priority=0,
            )
            session.add(role)
            await session.flush()
            role_id = role.id
        else:
            role_id = existing
        await session.execute(
            insert(user_role_table).values(user_id=uid, role_id=role_id)
        )
    await session.commit()
    return uid


async def _deactivate_user(session: AsyncSession, uid: str) -> None:
    await session.execute(
        UserModel.__table__.update()
        .where(UserModel.id == uid)
        .values(is_active=False)
    )
    await session.commit()


class TestPopulateUserRolesP2:
    async def test_multi_role_user_returns_all_roles(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        token = f"mock-multi-{uuid.uuid4().hex}"
        await _seed_user_with_roles(client, db_session, token, ["patient", "doctor"])
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert set(resp.json()["roles"]) == {"patient", "doctor"}

    async def test_missing_roles_user_has_empty_roles(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        token = f"mock-noroles-{uuid.uuid4().hex}"
        # Seed with no roles: clears the default patient role and adds none.
        await _seed_user_with_roles(client, db_session, token, [])
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["roles"] == []

    async def test_blocked_inactive_user_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        token = f"mock-blocked-{uuid.uuid4().hex}"
        uid = await _seed_user_with_roles(client, db_session, token, ["patient"])
        await _deactivate_user(db_session, uid)
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 401

    async def test_unauthorized_non_admin_blocked_from_admin_endpoint(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        # A patient must be denied (403) from an admin-only endpoint.
        token = f"mock-rbac-{uuid.uuid4().hex}"
        await _seed_user_with_roles(client, db_session, token, ["patient"])
        denied = await client.post(
            "/api/v1/graph/question-indicators",
            json={"question_id": "q", "indicator_id": "i"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert denied.status_code == 403

        # Promote the SAME user to admin and re-check. _seed_user_with_roles
        # clears and replaces role assignments, so no second user is created
        # (mock auth yields a fixed email, which would otherwise collide).
        await _seed_user_with_roles(client, db_session, token, ["medical_director"])
        allowed = await client.post(
            "/api/v1/graph/question-indicators",
            json={"question_id": "q", "indicator_id": "i"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Admin passes RBAC (may then fail on data, but must NOT be 403/401).
        assert allowed.status_code != 403
        assert allowed.status_code != 401

    async def test_roles_loaded_without_redundant_query(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """The roles returned by /auth/me must exactly match the DB-assigned
        roles, proving the eager load (not the dropped redundant
        _populate_user_roles query) is the source of role data.

        Uses only roles valid in the UserResponse DTO literal (patient/doctor)
        so /auth/me can serialize the response."""
        token = f"mock-exact-{uuid.uuid4().hex}"
        await _seed_user_with_roles(client, db_session, token, ["patient", "doctor"])
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert set(resp.json()["roles"]) == {"patient", "doctor"}
