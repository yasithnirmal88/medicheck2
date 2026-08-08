from __future__ import annotations

import asyncio
import time
from typing import Any

import firebase_admin
from firebase_admin import auth, credentials

from app.core.config import Environment, settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger(__name__)

_firebase_app: firebase_admin.App | None = None


def _init_firebase() -> None:
    global _firebase_app
    if _firebase_app is not None:
        return

    creds = settings.firebase_credentials
    if creds is None:
        logger.warning(
            "No Firebase credentials configured. Authentication will be disabled."
        )
        return

    try:
        cred = credentials.Certificate(creds)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as exc:
        logger.error("Failed to initialize Firebase Admin SDK: %s", exc)
        _firebase_app = None


def get_firebase_app() -> firebase_admin.App | None:
    if _firebase_app is None:
        _init_firebase()
    return _firebase_app


# Short-TTL in-memory cache of verified Firebase claims, keyed by token hash.
# A Firebase ID token is valid for 1 hour; we cache the *decoded claims* for a
# short window so the 7 requests in a single dashboard load don't each re-run
# the synchronous, network-fetching verify_id_token. Only positive (verified)
# results are cached; failures are never cached. The TTL is kept well below the
# token lifetime so revocation/expiration still take effect promptly.
_CLAIM_CACHE: dict[str, tuple[dict[str, Any], float]] = {}
_CLAIM_CACHE_TTL_SECONDS = 60
_CLAIM_CACHE_MAX_ENTRIES = 512
_cache_lock = asyncio.Lock()


def _token_cache_key(id_token: str) -> str:
    # Hash the raw token so we never store the bearer token itself in memory.
    import hashlib

    return hashlib.sha256(id_token.encode("utf-8")).hexdigest()


async def _get_cached_claims(key: str) -> dict[str, Any] | None:
    entry = _CLAIM_CACHE.get(key)
    if entry is None:
        return None
    claims, expires_at = entry
    if time.monotonic() >= expires_at:
        _CLAIM_CACHE.pop(key, None)
        return None
    return claims


async def _set_cached_claims(key: str, claims: dict[str, Any]) -> None:
    async with _cache_lock:
        # Bounded: drop oldest entries when over capacity.
        if len(_CLAIM_CACHE) >= _CLAIM_CACHE_MAX_ENTRIES:
            for old_key in list(_CLAIM_CACHE)[: _CLAIM_CACHE_MAX_ENTRIES // 4]:
                _CLAIM_CACHE.pop(old_key, None)
        _CLAIM_CACHE[key] = (claims, time.monotonic() + _CLAIM_CACHE_TTL_SECONDS)


def _verify_id_token_sync(id_token: str, app: firebase_admin.App) -> dict[str, Any]:
    # Thin sync wrapper around the Firebase Admin SDK. Preserves the exact
    # exception types (ExpiredIdTokenError, RevokedIdTokenError,
    # InvalidIdTokenError) so the caller can map them to auth errors.
    return auth.verify_id_token(id_token, app=app)


async def verify_firebase_token(id_token: str) -> dict[str, Any]:
    app = get_firebase_app()
    if app is None:
        if not settings.allow_mock_auth:
            if settings.environment in (Environment.STAGING, Environment.PRODUCTION):
                raise AuthenticationError(detail="Firebase is not configured - authentication is required")
            raise AuthenticationError(
                detail="Firebase is not configured. Set allow_mock_auth=True for development only."
            )
        logger.warning("SECURITY: Using mock authentication. DO NOT use in production!")
        return _mock_verify(id_token)

    cache_key = _token_cache_key(id_token)
    cached = await _get_cached_claims(cache_key)
    if cached is not None:
        logger.debug("Firebase token served from claim cache for uid: %s", cached.get("uid"))
        return cached

    try:
        # firebase_admin.auth.verify_id_token is synchronous and performs a
        # network fetch of Google's public keys on cache miss. Running it via
        # asyncio.to_thread keeps the event loop responsive to concurrent
        # requests instead of blocking them.
        decoded_token = await asyncio.to_thread(_verify_id_token_sync, id_token, app)
        logger.debug("Firebase token verified for uid: %s", decoded_token.get("uid"))
        # Cache only verified claims; never cache failures. TTL keeps this
        # well below the 1 h token lifetime so revocation/expiration propagate.
        await _set_cached_claims(cache_key, decoded_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise AuthenticationError(detail="Firebase token has expired") from None
    except auth.RevokedIdTokenError:
        raise AuthenticationError(detail="Firebase token has been revoked") from None
    except auth.InvalidIdTokenError:
        raise AuthenticationError(detail="Invalid Firebase token") from None
    except Exception as exc:
        logger.error("Firebase token verification failed: %s", exc)
        raise AuthenticationError(detail="Failed to verify authentication token") from exc


def _mock_verify(id_token: str) -> dict[str, Any]:
    logger.debug("Using mock Firebase verification")
    return {
        "uid": id_token or "mock-uid",
        "email": "mock@example.com",
        "email_verified": True,
        "name": "Mock User",
        "picture": None,
    }
