"""Regression: public self-registration can never mint a privileged role.

Previously ``POST /auth/register`` accepted a client-chosen ``role``
("patient" or "doctor"). ``Role.DOCTOR`` grants CMS access plus
READ_ASSESSMENTS_ALL, FHIR_EXPORT_ANY and REFERRAL_MANAGE, so any
unauthenticated caller could self-assign a clinical role. These tests pin the
fixed behavior: self-registration always creates a PATIENT and the ``role``
field is not accepted at all.

Run: ALLOW_MOCK_AUTH=true python -m pytest tests/test_register_role_escalation.py -q
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

from app.core.config import Environment, settings
from app.core.exceptions import AuthenticationError
from app.infrastructure.persistence.repositories.sql_user_repository import (
    SQLUserRepository,
)


class TestRegisterCannotEscalateRole:
    async def test_register_defaults_to_patient(
        self, client: AsyncClient, db_session: Any
    ) -> None:
        payload = {
            "firebase_token": "escalation-token-1",
            "full_name": "Sneaky User",
            "email": "sneaky1@example.com",
        }
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        assert response.json()["roles"] == ["patient"]

        repo = SQLUserRepository(db_session)
        user = await repo.find_by_firebase_uid("escalation-token-1")
        assert user is not None
        assert user.roles == {"patient"}

    async def test_register_rejects_role_field(
        self, client: AsyncClient, db_session: Any
    ) -> None:
        payload = {
            "firebase_token": "escalation-token-2",
            "full_name": "Sneaky User",
            "email": "sneaky2@example.com",
            "role": "doctor",
        }
        response = await client.post("/api/v1/auth/register", json=payload)
        # extra="forbid": a client-supplied role is refused outright (422).
        assert response.status_code == 422

        repo = SQLUserRepository(db_session)
        assert await repo.find_by_firebase_uid("escalation-token-2") is None


class TestMockAuthEnvironmentGuard:
    """Mock auth must work in development and be impossible when deployed."""

    @pytest.mark.asyncio
    async def test_mock_auth_refused_in_staging_even_when_enabled(
        self, monkeypatch
    ) -> None:
        import app.core.security.firebase as fb

        monkeypatch.setattr(fb, "get_firebase_app", lambda: None)
        monkeypatch.setattr(settings, "environment", Environment.STAGING)
        monkeypatch.setattr(settings, "allow_mock_auth", True)
        with pytest.raises(AuthenticationError):
            await fb.verify_firebase_token("mock-firebase-id-token")

    @pytest.mark.asyncio
    async def test_mock_auth_allowed_in_development(self, monkeypatch) -> None:
        import app.core.security.firebase as fb

        monkeypatch.setattr(fb, "get_firebase_app", lambda: None)
        monkeypatch.setattr(settings, "environment", Environment.DEVELOPMENT)
        monkeypatch.setattr(settings, "allow_mock_auth", True)
        claims = await fb.verify_firebase_token("mock-firebase-id-token")
        assert claims["uid"] == "mock-firebase-id-token"
