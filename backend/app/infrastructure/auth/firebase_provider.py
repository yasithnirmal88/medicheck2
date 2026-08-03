from __future__ import annotations

from typing import Any

from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger
from app.core.security.firebase import verify_firebase_token

logger = get_logger(__name__)


class FirebaseAuthProvider:
    async def authenticate(self, id_token: str) -> dict[str, Any]:
        try:
            claims = await verify_firebase_token(id_token)
            return {
                "sub": claims.get("uid", ""),
                "email": claims.get("email", ""),
                "email_verified": claims.get("email_verified", False),
                "name": claims.get("name", ""),
                "picture": claims.get("picture"),
                "firebase": claims,
            }
        except AuthenticationError:
            raise
        except Exception as exc:
            logger.error("Authentication failed: %s", exc)
            raise AuthenticationError(detail="Authentication failed") from exc

    async def create_user(self, email: str, password: str) -> dict[str, Any]:
        try:
            import firebase_admin.auth as firebase_auth

            user_record = firebase_auth.create_user(
                email=email,
                password=password,
            )
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "email_verified": user_record.email_verified,
            }
        except Exception as exc:
            logger.error("Failed to create Firebase user: %s", exc)
            raise

    async def delete_user(self, uid: str) -> None:
        try:
            import firebase_admin.auth as firebase_auth

            firebase_auth.delete_user(uid)
            logger.info("Firebase user deleted: %s", uid)
        except Exception as exc:
            logger.error("Failed to delete Firebase user: %s", exc)
            raise

    async def update_user(self, uid: str, **kwargs: Any) -> dict[str, Any]:
        try:
            import firebase_admin.auth as firebase_auth

            user_record = firebase_auth.update_user(uid, **kwargs)
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "email_verified": user_record.email_verified,
            }
        except Exception as exc:
            logger.error("Failed to update Firebase user: %s", exc)
            raise
