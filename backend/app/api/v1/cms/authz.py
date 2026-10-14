"""CMS write-authorization dependency factory.

``get_cms_user`` only asserts that the caller holds *any* CMS role
(READ_ONLY_REVIEWER and above). Read-only reviewers and other lower-privilege
CMS roles must not be able to mutate content, so every mutating CMS endpoint
guards itself with a concrete ``CMS_WRITE_*`` / ``CMS_APPROVE_CONTENT``
permission.

``require_cms_permission`` builds a FastAPI dependency that authenticates the
CMS user (via ``get_cms_user``) and then resolves their effective permissions
through ``app.identity.get_user_permissions`` before allowing the request. It
is a thin, declarative wrapper over the same
``get_user_permissions``/``check_permission`` pattern already used inline in
``content.py``/``evidence.py`` and via ``_check_write_perm`` in ``builder.py``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.identity import (
    Permission,
    User,
    check_permission,
    get_cms_user,
    get_user_permissions,
)


def require_cms_permission(
    required: Permission,
) -> Callable[..., Awaitable[User]]:
    """Return a dependency that requires the CMS user to hold ``required``.

    Replaces ``Depends(get_cms_user)`` on mutating endpoints so that
    read-only CMS roles are denied (HTTP 403) even though they pass the
    generic CMS access gate.
    """

    async def _dependency(
        user: Annotated[User, Depends(get_cms_user)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        permissions = await get_user_permissions(session, user.id)
        if not check_permission(permissions, required):
            raise HTTPException(403, "Insufficient permissions")
        return user

    return _dependency
