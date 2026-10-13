"""Unit tests for P1-1: Firebase verification off the event loop + claim cache.

Verifies:
- The same token is verified once; subsequent calls within the TTL are served
  from the claim cache (no repeated synchronous verify_id_token calls).
- Failures (expired/revoked/invalid) are NOT cached and propagate as
  AuthenticationError with the correct detail.
- The cache is bounded and TTL-expired entries are evicted.

These tests exercise the REAL Firebase path (not mock auth) by stubbing
get_firebase_app and firebase_admin.auth.verify_id_token.
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from app.core import security
from app.core.exceptions import AuthenticationError

firebase_module = security.firebase


@pytest.fixture(autouse=True)
def _clear_claim_cache():
    firebase_module._CLAIM_CACHE.clear()
    yield
    firebase_module._CLAIM_CACHE.clear()


def _stub_app():
    """A non-None sentinel so verify_firebase_token takes the real-Firebase path."""
    return object()


async def test_repeated_token_served_from_cache_verifies_once():
    calls = {"n": 0}

    def fake_verify(id_token, app=None):
        calls["n"] += 1
        return {"uid": "uid-123", "email": "x@example.com"}

    with patch.object(firebase_module, "get_firebase_app", return_value=_stub_app()), \
         patch("firebase_admin.auth.verify_id_token", side_effect=fake_verify):
        first = await firebase_module.verify_firebase_token("token-A")
        second = await firebase_module.verify_firebase_token("token-A")
        third = await firebase_module.verify_firebase_token("token-A")

    assert calls["n"] == 1, "verify_id_token should run once; rest served from cache"
    assert first["uid"] == "uid-123"
    assert second == first
    assert third == first


async def test_different_tokens_each_verified():
    def fake_verify(id_token, app=None):
        return {"uid": id_token}

    with patch.object(firebase_module, "get_firebase_app", return_value=_stub_app()), \
         patch("firebase_admin.auth.verify_id_token", side_effect=fake_verify):
        a = await firebase_module.verify_firebase_token("token-A")
        b = await firebase_module.verify_firebase_token("token-B")

    assert a["uid"] == "token-A"
    assert b["uid"] == "token-B"


async def test_expired_token_not_cached_and_raises():
    calls = {"n": 0}

    def fake_verify(id_token, app=None):
        calls["n"] += 1
        raise firebase_module.auth.ExpiredIdTokenError("expired", Exception("token-expired"))

    with patch.object(firebase_module, "get_firebase_app", return_value=_stub_app()), \
         patch("firebase_admin.auth.verify_id_token", side_effect=fake_verify):
        with pytest.raises(AuthenticationError, match="expired"):
            await firebase_module.verify_firebase_token("token-exp")
        # second call must also verify (failure not cached)
        with pytest.raises(AuthenticationError, match="expired"):
            await firebase_module.verify_firebase_token("token-exp")

    assert calls["n"] == 2, "failures must never be cached"


async def test_revoked_and_invalid_tokens_raise_correct_errors():
    import firebase_admin

    def fake_verify(id_token, app=None):
        if id_token == "rev":
            raise firebase_admin.auth.RevokedIdTokenError("revoked")
        raise firebase_admin.auth.InvalidIdTokenError("invalid")

    with patch.object(firebase_module, "get_firebase_app", return_value=_stub_app()), \
         patch("firebase_admin.auth.verify_id_token", side_effect=fake_verify):
        with pytest.raises(AuthenticationError, match="revoked"):
            await firebase_module.verify_firebase_token("rev")
        with pytest.raises(AuthenticationError, match="Invalid Firebase token"):
            await firebase_module.verify_firebase_token("inv")


async def test_cached_entry_expires_after_ttl():
    calls = {"n": 0}

    def fake_verify(id_token, app=None):
        calls["n"] += 1
        return {"uid": "uid-x"}

    with patch.object(firebase_module, "get_firebase_app", return_value=_stub_app()), \
         patch("firebase_admin.auth.verify_id_token", side_effect=fake_verify), \
         patch.object(firebase_module, "_CLAIM_CACHE_TTL_SECONDS", 0.1):
        await firebase_module.verify_firebase_token("token-ttl")
        # within TTL
        await firebase_module.verify_firebase_token("token-ttl")
        assert calls["n"] == 1
        # wait past TTL
        time.sleep(0.15)
        await firebase_module.verify_firebase_token("token-ttl")
        assert calls["n"] == 2, "expired cache entry should force a re-verify"


async def test_cache_is_bounded():
    def fake_verify(id_token, app=None):
        return {"uid": id_token}

    # Lower the cap to make the bound testable.
    with patch.object(firebase_module, "get_firebase_app", return_value=_stub_app()), \
         patch("firebase_admin.auth.verify_id_token", side_effect=fake_verify), \
         patch.object(firebase_module, "_CLAIM_CACHE_MAX_ENTRIES", 4):
        for i in range(10):
            await firebase_module.verify_firebase_token(f"token-{i}")
        assert len(firebase_module._CLAIM_CACHE) <= 4
