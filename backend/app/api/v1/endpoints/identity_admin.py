"""Identity administration API (user + role management).

Split out of ``admin.py`` so user/role administration lives in an
identity-owned module: the routes, DTO mapping, and persistence access here
are part of the Identity bounded context. Clinical administration stays in
``admin.py``.

HTTP contract is unchanged: same ``/admin`` prefix, same tags, same paths,
same function (operation) names, same response shapes.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.identity import User, get_current_admin
from app.infrastructure.persistence.models.role import RoleModel
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.user_role import user_role_table
from app.infrastructure.persistence.repositories.sql_user_repository import (
    SQLUserRepository,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# --- Users & Roles (CMS user management) ---
# Used by the CMS UsersRolesPage. Kept admin-only (get_current_admin) so only
# medical directors / super admins can manage users and roles.

def _role_to_dict(role: RoleModel) -> dict[str, Any]:
    # RoleModel.name is a JSON dict of locale->display name; surface a flat
    # string for the frontend UserRole.name field.
    name = role.name
    if isinstance(name, dict):
        name = name.get("en") or next(iter(name.values()), role.code)
    return {
        "id": role.id,
        "name": name,
        "code": role.code,
        "description": role.description or None,
        "hierarchy_level": role.priority,
        "is_active": role.deleted_at is None,
    }


@router.get("/users")
async def list_users(
    current_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None),
):
    repo = SQLUserRepository(session)
    users = await repo.find_all(skip=skip, limit=limit)
    total = await repo.count()
    items = [u.to_dict() for u in users]
    if search:
        s = search.lower()
        items = [
            i for i in items
            if s in (i.get("email") or "").lower()
            or s in (i.get("full_name") or "").lower()
        ]
        total = len(items)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    repo = SQLUserRepository(session)
    user = await repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(404, f"User {user_id} not found")
    return user.to_dict()


@router.put("/users/{user_id}/roles")
async def update_user_roles(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    roles: list[str] = payload.get("roles", [])
    # Replace the user's role assignments in user_roles.
    await session.execute(
        user_role_table.delete().where(user_role_table.c.user_id == user_id)
    )
    for role_code in roles:
        role_row = await session.execute(
            select(RoleModel.id).where(RoleModel.code == role_code)
        )
        role_id = role_row.scalar_one_or_none()
        if role_id is not None:
            await session.execute(
                user_role_table.insert().values(
                    user_id=user_id, role_id=role_id
                )
            )
    await session.commit()
    repo = SQLUserRepository(session)
    user = await repo.find_by_id(user_id)
    return user.to_dict() if user else {"id": user_id, "roles": roles}


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(UserModel).where(UserModel.id == user_id)
    model = (await session.execute(stmt)).scalar_one_or_none()
    if model is None:
        raise HTTPException(404, f"User {user_id} not found")
    model.is_active = not model.is_active
    await session.commit()
    return {"id": user_id, "is_active": model.is_active}


@router.get("/roles")
async def list_roles(
    current_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(RoleModel).where(RoleModel.deleted_at.is_(None)).order_by(
        RoleModel.priority.desc()
    )
    result = await session.execute(stmt)
    return [_role_to_dict(r) for r in result.scalars().all()]


@router.get("/roles/{role_id}/permissions")
async def get_role_permissions(
    role_id: str,
    current_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    # Local import: the route function shadows the rbac helper name.
    from app.identity import Role as RBACRole, get_role_permissions

    stmt = select(RoleModel).where(RoleModel.id == role_id)
    role = (await session.execute(stmt)).scalar_one_or_none()
    if role is None:
        raise HTTPException(404, f"Role {role_id} not found")
    try:
        perms = get_role_permissions(RBACRole(role.code))
    except ValueError:
        perms = set()
    return sorted(p.value for p in perms)
