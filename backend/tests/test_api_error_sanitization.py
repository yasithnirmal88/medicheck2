"""API error-sanitization tests (S-11 hardening).

Internal exception details must never leak to clients, while intentional 4xx
validation/ownership messages are preserved:

* ``app/api/v1/endpoints/profile.py`` update/restore handlers log unexpected
  exceptions and return a generic 500 body.
* ``app/api/errors.py`` ``http_exception_handler`` sanitizes 5xx
  ``HTTPException`` responses but keeps 4xx detail.
* ``app/api/v1/cms/rules.py`` ``/validate`` does not echo raw evaluation errors.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.application.services.cms.rule_engine_service import RuleEngineService
from app.application.services.profile_service import ProfileService
from app.domain.entities.user import User
from app.identity import get_cms_user, get_current_active_user

GENERIC_MESSAGE = "An unexpected error occurred"
SECRET = "internal-db-secret-xyz"


def _active_user(roles: set[str] | None = None) -> User:
    now = datetime.now(UTC)
    unique = uuid.uuid4().hex
    return User(
        id=unique,
        firebase_uid=f"user-{unique}",
        email=f"user-{unique}@example.test",
        full_name="Test User",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles=set(roles or ()),
        last_login_at=None,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


def _app(client: AsyncClient):
    return client._transport.app  # type: ignore[attr-defined]


@pytest.fixture
def auth(client: AsyncClient):
    app = _app(client)
    app.dependency_overrides[get_current_active_user] = lambda: _active_user()
    yield
    app.dependency_overrides.pop(get_current_active_user, None)


# --- profile.py: unexpected exceptions -> generic 500 ------------------------


@pytest.mark.asyncio
async def test_profile_update_unexpected_error_is_sanitized(client, auth, monkeypatch):
    async def _boom(self, user, payload):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(ProfileService, "update_personal_info", _boom)

    resp = await client.post("/api/v1/profiles/me/personal", json={"full_name": "Jane"})
    assert resp.status_code == 500, resp.text
    assert SECRET not in resp.text
    assert resp.json()["error"]["message"] == GENERIC_MESSAGE


@pytest.mark.asyncio
async def test_profile_restore_unexpected_error_is_sanitized(client, auth, monkeypatch):
    async def _boom(self, user, version):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(ProfileService, "restore_version", _boom)

    resp = await client.post("/api/v1/profiles/me/versions/3/restore")
    assert resp.status_code == 500, resp.text
    assert SECRET not in resp.text
    assert resp.json()["error"]["message"] == GENERIC_MESSAGE


@pytest.mark.asyncio
async def test_profile_restore_value_error_keeps_404_message(client, auth, monkeypatch):
    async def _missing(self, user, version):
        raise ValueError("version not found for this user")

    monkeypatch.setattr(ProfileService, "restore_version", _missing)

    resp = await client.post("/api/v1/profiles/me/versions/3/restore")
    assert resp.status_code == 404, resp.text
    assert resp.json()["error"]["message"] == "version not found for this user"


# --- errors.py: 5xx sanitized, 4xx preserved ---------------------------------


@pytest.mark.asyncio
async def test_5xx_http_exception_detail_is_sanitized(client):
    async def _boom():
        raise HTTPException(status_code=500, detail=SECRET)

    _app(client).add_api_route("/__test/boom500", _boom, methods=["GET"])
    resp = await client.get("/__test/boom500")
    assert resp.status_code == 500, resp.text
    assert SECRET not in resp.text
    body = resp.json()
    assert body["error"]["message"] == GENERIC_MESSAGE
    assert body["error"]["code"] == "internal_error"


@pytest.mark.asyncio
async def test_4xx_http_exception_detail_is_preserved(client):
    async def _bad():
        raise HTTPException(status_code=400, detail="Field X is required")

    _app(client).add_api_route("/__test/bad400", _bad, methods=["GET"])
    resp = await client.get("/__test/bad400")
    assert resp.status_code == 400, resp.text
    assert resp.json()["error"]["message"] == "Field X is required"


# --- cms/rules.py: no raw evaluation error echo ------------------------------


@pytest.mark.asyncio
async def test_rule_validate_does_not_echo_internal_error(client, monkeypatch):
    app = _app(client)
    app.dependency_overrides[get_cms_user] = lambda: _active_user({"medical_director"})

    def _boom(self, expression, context):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(RuleEngineService, "evaluate_expression", _boom)

    resp = await client.post(
        "/api/v1/cms/rules/validate",
        json={"expression": {"type": "condition"}, "context": {}},
    )
    app.dependency_overrides.pop(get_cms_user, None)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["valid"] is False
    assert SECRET not in resp.text
    assert body["error"] == "Invalid or unsupported expression"
