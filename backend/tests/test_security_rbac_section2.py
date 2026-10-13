"""Regression tests for the Security & RBAC hardening (section 2).

Covers:
- 2.1 empty/missing email (phone-only Firebase tokens) no longer crashes the
  entity or the auth DTOs; stored as NULL.
- 2.2 profile section payloads cannot mass-assign ORM-managed columns
  (id/profile_id/timestamps).
- 2.3 ``list_users`` search is applied in SQL, before pagination, so ``total``
  reflects the filtered set.

Run: ALLOW_MOCK_AUTH=true python -m pytest tests/test_security_rbac_section2.py -q
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth_dtos import UserResponse
from app.domain.entities.user import User
from app.infrastructure.persistence.models.lifestyle import LifestyleModel
from app.infrastructure.persistence.repositories.sql_profile_repository import (
    SQLProfileRepository,
)
from app.infrastructure.persistence.repositories.sql_user_repository import (
    SQLUserRepository,
)


class TestEmailNullability:
    def test_entity_create_with_none_email(self) -> None:
        user = User.create(
            firebase_uid="phone-only-1", email=None, full_name="Phone User"
        )
        assert user.email is None

    def test_entity_create_with_empty_email(self) -> None:
        user = User.create(
            firebase_uid="phone-only-2", email="", full_name="Phone User"
        )
        assert user.email is None

    def test_entity_create_normalizes_email(self) -> None:
        user = User.create(
            firebase_uid="norm-1", email="  Mixed@Case.COM ", full_name="Norm User"
        )
        assert user.email == "mixed@case.com"

    def test_user_response_serializes_null_email(self) -> None:
        # A None email must not raise Pydantic EmailStr validation (was a 500
        # on /auth/me for Firebase phone-auth users).
        user = User(
            id="u1",
            firebase_uid="phone-only-3",
            email=None,
            full_name="Phone User",
            avatar_url=None,
            email_verified=False,
            is_active=True,
            roles={"patient"},
            last_login_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            deleted_at=None,
        )
        dto = UserResponse.from_entity(user)
        assert dto.email is None


class TestProfileMassAssignment:
    @pytest.mark.asyncio
    async def test_section_payload_cannot_override_protected_columns(
        self, db_session: AsyncSession
    ) -> None:
        repo = SQLProfileRepository(db_session)
        victim = User.create(
            firebase_uid="mass-victim", email="victim@example.test", full_name="V"
        )
        attacker = User.create(
            firebase_uid="mass-attacker", email="attacker@example.test", full_name="A"
        )
        attacker_profile = await repo.create_for_user(attacker.id)
        await db_session.flush()

        # Attempt to hijack the row's identity + soft-delete flag.
        await repo.upsert_lifestyle(
            attacker_profile.id,
            {
                "id": "attacker-chosen-id",
                "profile_id": victim.id,
                "deleted_at": datetime.now(UTC),
                "created_at": datetime(1999, 1, 1, tzinfo=UTC),
                "smoking": "never",
            },
        )
        await db_session.flush()

        row = (
            await db_session.execute(
                select(LifestyleModel).where(
                    LifestyleModel.profile_id == attacker_profile.id
                )
            )
        ).scalars().first()
        assert row is not None
        assert row.profile_id == attacker_profile.id
        assert row.id != "attacker-chosen-id"
        assert row.deleted_at is None
        assert row.smoking == "never"

    @pytest.mark.asyncio
    async def test_unknown_keys_are_dropped(self, db_session: AsyncSession) -> None:
        repo = SQLProfileRepository(db_session)
        user = User.create(
            firebase_uid="mass-unknown", email="u@example.test", full_name="U"
        )
        profile = await repo.create_for_user(user.id)
        await db_session.flush()

        # Should not raise "unexpected keyword" / invalid column.
        await repo.upsert_lifestyle(
            profile.id, {"smoking": "former", "not_a_real_column": "x"}
        )
        await db_session.flush()

        row = (
            await db_session.execute(
                select(LifestyleModel).where(LifestyleModel.profile_id == profile.id)
            )
        ).scalars().first()
        assert row.smoking == "former"


class TestListUsersSearch:
    @pytest.mark.asyncio
    async def test_find_all_and_count_apply_search_in_sql(
        self, db_session: AsyncSession
    ) -> None:
        repo = SQLUserRepository(db_session)
        for i in range(3):
            await repo.create(
                User.create(
                    firebase_uid=f"search-alpha-{i}",
                    email=f"alpha{i}@example.test",
                    full_name=f"Alpha {i}",
                )
            )
        await repo.create(
            User.create(
                firebase_uid="search-beta-0",
                email="beta0@example.test",
                full_name="Beta Zero",
            )
        )
        await db_session.flush()

        page = await repo.find_all(skip=0, limit=2, search="alpha")
        total = await repo.count(search="alpha")
        assert len(page) == 2
        assert total == 3
        assert all("alpha" in (u.email or "") for u in page)

        by_name = await repo.find_all(skip=0, limit=10, search="Beta Zero")
        assert [u.full_name for u in by_name] == ["Beta Zero"]

        no_match = await repo.count(search="does-not-exist")
        assert no_match == 0


class TestAuditIdentityNotSpoofable:
    @pytest.mark.asyncio
    async def test_audit_user_id_ignores_client_header(
        self, client, caplog
    ) -> None:
        caplog.set_level(logging.INFO, logger="audit")
        headers = {
            "Authorization": "Bearer mock-firebase-id-token",
            "x-user-id": "spoofed-attacker",
        }

        me = await client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200
        real_id = me.json()["id"]

        resp = await client.post(
            "/api/v1/profiles/me/lifestyle",
            json={"smoking": "never"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

        records = [r for r in caplog.records if getattr(r, "event", None) == "api_access"]
        assert records, "expected an api_access audit record"
        logged = records[-1].user_id  # type: ignore[attr-defined]
        assert logged == real_id
        assert logged != "spoofed-attacker"
