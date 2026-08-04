from __future__ import annotations

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

    try:
        decoded_token = auth.verify_id_token(id_token, app=app)
        logger.debug("Firebase token verified for uid: %s", decoded_token.get("uid"))
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
