"""Mock auth must generate a unique email per identity.

``users.email`` is UNIQUE, and ``get_current_user`` auto-creates a user for every
unseen Firebase uid. The old mock claims hardcoded ``mock@example.com``, so the
second distinct mock token collided on that unique constraint. These tests pin
the new behaviour:

- every distinct mock uid gets its own email (no collision);
- the same uid is still stable with respect to user lookup (repeated calls
  resolve the same user by firebase_uid, never re-insert);
- an explicit email can still be pinned for tests that need a known address;
- the generated addresses are valid and fit the column.

Run: ALLOW_MOCK_AUTH=true python -m pytest tests/test_mock_auth_unique_email.py -q
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.firebase import _mock_verify, mock_email_for_uid
from app.infrastructure.persistence.models.user import UserModel

# users.email is String(255)
_EMAIL_COLUMN_MAX_LEN = 255


def test_distinct_uids_get_distinct_emails():
    emails = [mock_email_for_uid(f"mock-multi-{i}") for i in range(50)]
    assert len(set(emails)) == 50, "each mock identity must get a unique email"


def test_generated_email_is_valid_and_fits_column():
    email = mock_email_for_uid("mock-firebase-id-token")
    local, _, domain = email.partition("@")
    assert domain == "example.com"
    assert local.startswith("mock-")
    assert len(email) <= _EMAIL_COLUMN_MAX_LEN
    # uid slug stays readable for debugging
    assert "mock-firebase-id-token" in local


def test_generated_email_survives_awkward_uids():
    for uid in ("", "weird!!!chars@@@", "A" * 500, "üñïçø∂é"):
        email = mock_email_for_uid(uid)
        assert email.endswith("@example.com")
        assert len(email) <= _EMAIL_COLUMN_MAX_LEN
        assert " " not in email


def test_mock_verify_defaults_to_unique_email_per_uid():
    a = _mock_verify("mock-token-a")
    b = _mock_verify("mock-token-b")
    assert a["uid"] == "mock-token-a"
    assert b["uid"] == "mock-token-b"
    assert a["email"] != b["email"]
    assert a["email"] != "mock@example.com"


def test_mock_verify_honours_explicit_email_override():
    claims = _mock_verify("mock-token-explicit", email="pinned@example.com")
    assert claims["email"] == "pinned@example.com"
    assert claims["uid"] == "mock-token-explicit"


def test_mock_verify_keeps_other_claims_unchanged():
    claims = _mock_verify("mock-token-a")
    assert claims["email_verified"] is True
    assert claims["name"] == "Mock User"
    assert claims["picture"] is None


@pytest.mark.asyncio
async def test_multiple_mock_users_can_coexist(
    db_session: AsyncSession, client: AsyncClient
):
    """The regression itself: several distinct mock tokens used to collide on
    users.email UNIQUE. All must authenticate and persist independently."""
    tokens = [f"mock-unique-{i}" for i in range(5)]

    ids: list[str] = []
    for token in tokens:
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text
        ids.append(resp.json()["id"])

    assert len(set(ids)) == len(tokens), "each mock token must yield a distinct user"

    rows = (
        await db_session.execute(
            select(func.count()).select_from(UserModel).where(
                UserModel.firebase_uid.in_(tokens)
            )
        )
    ).scalar_one()
    assert rows == len(tokens)

    emails = list(
        (
            await db_session.execute(
                select(UserModel.email).where(UserModel.firebase_uid.in_(tokens))
            )
        ).scalars()
    )
    assert len(set(emails)) == len(tokens), f"emails collided: {emails}"


@pytest.mark.asyncio
async def test_repeated_auth_with_same_token_reuses_one_user(
    db_session: AsyncSession, client: AsyncClient
):
    """A stable token must resolve to the SAME user every time (lookup is by
    firebase_uid), and must not attempt a second insert."""
    token = "mock-unique-repeat"
    first = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    second = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]

    count = (
        await db_session.execute(
            select(func.count()).select_from(UserModel).where(UserModel.firebase_uid == token)
        )
    ).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_auto_created_mock_users_get_unique_emails(
    db_session: AsyncSession, client: AsyncClient
):
    """Auto-created mock users must each receive their own generated address,
    never the old fixed mock@example.com."""
    tokens = [f"mock-email-{i}" for i in range(4)]

    emails: list[str] = []
    for token in tokens:
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200, resp.text
        email = resp.json()["email"]
        assert email is not None
        emails.append(email)

    assert "mock@example.com" not in emails, "fixed mock email must not be reused"
    assert len(set(emails)) == len(tokens), f"emails collided: {emails}"

    persisted = list(
        (
            await db_session.execute(
                select(UserModel.email).where(UserModel.firebase_uid.in_(tokens))
            )
        ).scalars()
    )
    assert sorted(persisted) == sorted(emails)
