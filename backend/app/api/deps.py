from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.logging import get_logger
from app.core.security.firebase import verify_firebase_token
from app.core.security.rbac import Role, has_role
from app.domain.entities.user import User
from app.infrastructure.database import get_db as _get_db
from app.infrastructure.persistence.repositories.sql_user_repository import (
    SQLUserRepository,
)
from app.infrastructure.redis import get_redis as _get_redis

logger = get_logger(__name__)

security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session


async def get_redis() -> AsyncGenerator[Redis, None]:
    async for redis in _get_redis():
        yield redis


async def _populate_user_roles(
    user: User, session: AsyncSession
) -> None:
    from sqlalchemy import select

    from app.infrastructure.persistence.models.role import RoleModel
    from app.infrastructure.persistence.models.user_role import user_role_table

    stmt = (
        select(RoleModel.code)
        .select_from(user_role_table)
        .join(RoleModel, RoleModel.id == user_role_table.c.role_id)
        .where(user_role_table.c.user_id == user.id)
    )
    result = await session.execute(stmt)
    user.roles = {row[0] for row in result.all()}


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security_scheme)
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    token = None
    if credentials is not None:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    if token is None:
        raise AuthenticationError(detail="Missing authentication token")

    try:
        claims = await verify_firebase_token(token)
        firebase_uid = claims.get("uid", "")
    except AuthenticationError:
        raise
    except Exception as exc:
        logger.error("Token verification failed: %s", exc)
        raise AuthenticationError(detail="Invalid authentication token")

    repo = SQLUserRepository(session)
    user = await repo.find_by_firebase_uid(firebase_uid)

    if user is None:
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
        user = await repo.create(user)
        logger.info("Auto-created user from token: %s", user.id)

    if not user.is_active:
        raise AuthenticationError(detail="Account is deactivated")

    # Roles are already eagerly loaded by SQLUserRepository.find_by_firebase_uid
    # (via _base_query's selectinload(UserModel.roles)) and mapped in _to_entity.
    # The previous _populate_user_roles call here issued a redundant second query
    # fetching the same role codes; it is only needed as a fallback if a caller
    # ever produces a User whose roles were not loaded.
    if getattr(user, "roles", None) is None:
        await _populate_user_roles(user, session)
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise AuthenticationError(detail="Account is deactivated")
    return current_user


async def get_current_doctor(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if not has_role(current_user.roles, Role.DOCTOR):
        raise AuthorizationError(detail="Doctor access required")
    return current_user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if not has_role(current_user.roles, Role.MEDICAL_DIRECTOR):
        raise AuthorizationError(detail="Admin access required")
    return current_user


async def get_current_super_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if not has_role(current_user.roles, Role.SUPER_ADMIN):
        raise AuthorizationError(detail="Super admin access required")
    return current_user


async def get_cms_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not current_user.roles:
        raise AuthorizationError(detail="CMS access required")
    if not has_role(current_user.roles, Role.READ_ONLY_REVIEWER):
        raise AuthorizationError(detail="CMS access required")
    return current_user


async def get_analytics_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Population analytics access (Phase 6).

    Requires a role with ANALYTICS_VIEW_POPULATION permission. This is granted
    to RESEARCH_REVIEWER, MEDICAL_DIRECTOR, and SUPER_ADMIN (level >=25).
    Population analytics never grants individual patient data access — only
    de-identified, aggregated metrics.
    """
    if not current_user.roles:
        raise AuthorizationError(detail="Analytics access required")
    if not has_role(current_user.roles, Role.RESEARCH_REVIEWER):
        raise AuthorizationError(detail="Analytics access required")
    return current_user


async def get_ai_governance_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """AI governance access (Phase 7).

    Requires a role with AI_VIEW_GOVERNANCE permission. Granted to
    RESEARCH_REVIEWER, MEDICAL_DIRECTOR, and SUPER_ADMIN (level >=25).
    Returns aggregate AI quality metrics only — never individual patient PHI
    or individual AI audit records.
    """
    if not current_user.roles:
        raise AuthorizationError(detail="AI governance access required")
    if not has_role(current_user.roles, Role.RESEARCH_REVIEWER):
        raise AuthorizationError(detail="AI governance access required")
    return current_user
