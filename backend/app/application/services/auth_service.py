from __future__ import annotations

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.logging import get_logger
from app.core.security.firebase import verify_firebase_token
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repo = user_repository

    async def register_user(
        self,
        firebase_token: str,
        full_name: str,
        email: str | None = None,
        role: str = "patient",
    ) -> User:
        claims = await verify_firebase_token(firebase_token)
        firebase_uid = claims["uid"]
        user_email = email or claims.get("email", "")
        user_name = full_name or claims.get("name", "User")
        avatar_url = claims.get("picture")

        existing = await self._user_repo.find_by_firebase_uid(firebase_uid)
        if existing is not None:
            raise ConflictError(
                detail="User already registered",
                code="user_already_exists",
            )

        if user_email:
            existing_email = await self._user_repo.find_by_email(user_email)
            if existing_email is not None:
                raise ConflictError(
                    detail="Email already in use",
                    code="email_already_exists",
                )

        user = User.create(
            firebase_uid=firebase_uid,
            email=user_email,
            full_name=user_name,
            avatar_url=avatar_url,
            role=role,
        )
        user.email_verified = claims.get("email_verified", False)

        created = await self._user_repo.create(user)
        logger.info("User registered: %s (%s) with role: %s", created.id, created.email, role)
        return created

    async def get_or_create_user(self, firebase_token: str) -> User:
        claims = await verify_firebase_token(firebase_token)
        firebase_uid = claims["uid"]

        existing = await self._user_repo.find_by_firebase_uid(firebase_uid)
        if existing is not None:
            if not existing.is_active:
                raise AuthenticationError(detail="Account is deactivated")
            existing.mark_login()
            await self._user_repo.update(existing)
            return existing

        user_email = claims.get("email", "")
        user_name = claims.get("name", "User")
        avatar_url = claims.get("picture")

        user = User.create(
            firebase_uid=firebase_uid,
            email=user_email,
            full_name=user_name,
            avatar_url=avatar_url,
        )
        user.email_verified = claims.get("email_verified", False)
        user.mark_login()

        created = await self._user_repo.create(user)
        logger.info(
            "New user created from Firebase: %s (%s)", created.id, created.email
        )
        return created

    async def deactivate_user(self, user_id: str) -> None:
        user = await self._user_repo.find_by_id(user_id)
        if user is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError(detail="User not found")

        user.deactivate()
        await self._user_repo.update(user)
        logger.info("User deactivated: %s", user_id)

    async def get_user_by_id(self, user_id: str) -> User | None:
        return await self._user_repo.find_by_id(user_id)

    async def get_user_by_firebase_uid(self, uid: str) -> User | None:
        return await self._user_repo.find_by_firebase_uid(uid)
