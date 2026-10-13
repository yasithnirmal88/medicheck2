"""Identity-owned permission resolution.

Canonical replacement for the role→permission SQL that used to be duplicated
in CMS endpoint modules. Other bounded contexts must call
:func:`get_user_permissions` (re-exported from ``app.identity``) instead of
querying ``RoleModel`` / ``user_role_table`` directly.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.auth_service import AuthService
from app.core.security.rbac import Permission, Role, get_role_permissions
from app.infrastructure.persistence.repositories.sql_user_repository import (
    SQLUserRepository,
)


async def get_user_permissions(
    session: AsyncSession, user_id: str
) -> set[Permission]:
    """Return the effective permission set for a user id.

    Resolves the user's role codes through the Identity repository, then
    maps them through the RBAC hierarchy. Unknown role codes are skipped
    (same semantics as the CMS helpers this replaces).
    """
    service = AuthService(SQLUserRepository(session))
    user = await service.get_user_by_id(user_id)
    if user is None:
        return set()
    perms: set[Permission] = set()
    for code in user.roles or []:
        try:
            perms |= get_role_permissions(Role(code))
        except ValueError:
            continue
    return perms
