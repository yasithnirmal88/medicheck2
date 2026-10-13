from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.application.dtos.auth_dtos import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.application.services.auth_service import AuthService
from app.domain.entities.user import User
from app.infrastructure.persistence.repositories.sql_user_repository import (
    SQLUserRepository,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_auth_service(session: AsyncSession) -> AuthService:
    repo = SQLUserRepository(session)
    return AuthService(repo)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user",
    description="Register a user using a Firebase ID token. Returns the created user profile.",
)
async def register(
    request: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    service = _get_auth_service(session)
    user = await service.register_user(
        firebase_token=request.firebase_token,
        full_name=request.full_name,
        email=str(request.email) if request.email else None,
        role=request.role,
    )
    return UserResponse.from_entity(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login or create user",
    description="Exchange a Firebase ID token for an application access token and user profile.",
)
async def login(
    request: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    service = _get_auth_service(session)
    user = await service.get_or_create_user(
        firebase_token=request.firebase_token,
    )
    return TokenResponse(
        access_token=request.firebase_token,
        user=UserResponse.from_entity(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Retrieve the currently authenticated user's profile.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    return UserResponse.from_entity(current_user)


@router.delete(
    "/me",
    status_code=204,
    summary="Delete current user",
    description="Deactivate the currently authenticated user's account.",
)
async def delete_account(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = _get_auth_service(session)
    await service.deactivate_user(current_user.id)
