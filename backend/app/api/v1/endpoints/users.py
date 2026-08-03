from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_admin, get_db
from app.application.dtos.auth_dtos import UserResponse
from app.domain.entities.user import User
from app.infrastructure.persistence.repositories.sql_user_repository import (
    SQLUserRepository,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    return UserResponse.from_entity(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the current user's profile fields such as full_name and avatar_url.",
)
async def update_current_user_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    full_name: str | None = Query(None, min_length=1, max_length=200),
    avatar_url: str | None = Query(None),
) -> UserResponse:
    repo = SQLUserRepository(session)
    current_user.update_profile(
        full_name=full_name,
        avatar_url=avatar_url,
    )
    updated = await repo.update(current_user)
    return UserResponse.from_entity(updated)


@router.get("", response_model=list[UserResponse], summary="List users")
async def list_users(
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[UserResponse]:
    repo = SQLUserRepository(session)
    users = await repo.find_all(skip=skip, limit=limit)
    return [UserResponse.from_entity(u) for u in users]


@router.get("/count", summary="Count users")
async def count_users(
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    repo = SQLUserRepository(session)
    total = await repo.count()
    return {"total": total}
