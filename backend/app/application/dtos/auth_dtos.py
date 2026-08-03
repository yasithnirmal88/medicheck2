from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    constr,
    field_validator,
)


class LoginRequest(BaseModel):
    firebase_token: constr(min_length=10) = Field(..., description="Firebase ID token")

    model_config = ConfigDict(extra="forbid")


class RegisterRequest(BaseModel):
    firebase_token: constr(min_length=10) = Field(..., description="Firebase ID token")
    full_name: constr(min_length=1, max_length=200) = Field(..., description="Full name")
    email: EmailStr | None = Field(None, description="Email address")

    model_config = ConfigDict(extra="forbid")


class RefreshTokenRequest(BaseModel):
    refresh_token: constr(min_length=20) = Field(..., description="Refresh token")

    model_config = ConfigDict(extra="forbid")


class VerifyTokenResponse(BaseModel):
    uid: str
    email: EmailStr | None = None
    email_verified: bool = False
    issued_at: datetime | None = None
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email to send reset link to")

    model_config = ConfigDict(extra="forbid")


class ResetPasswordRequest(BaseModel):
    token: constr(min_length=20)
    new_password: SecretStr

    model_config = ConfigDict(extra="forbid")


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Logged out"

    model_config = ConfigDict(from_attributes=True)


class AuthenticatedUserResponse(BaseModel):
    id: str
    firebase_uid: str
    email: EmailStr | None
    full_name: str
    avatar_url: str | None = None
    email_verified: bool = False
    is_active: bool = True
    roles: list[Literal["patient", "doctor", "researcher", "administrator"]] = []
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, user: Any) -> AuthenticatedUserResponse:
        if hasattr(user, "to_dict"):
            data = user.to_dict()
        else:
            data = user
        return cls(**data)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: Literal["bearer"] = "bearer"
    expires_in: int | None = None
    user: AuthenticatedUserResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: str
    firebase_uid: str
    email: EmailStr | None
    full_name: str
    avatar_url: str | None = None
    email_verified: bool = False
    is_active: bool = True
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, user: Any) -> UserResponse:
        if hasattr(user, "to_dict"):
            data = user.to_dict()
        else:
            data = user
        return cls(**data)


# simple validation example for password strength if needed elsewhere
class PasswordPolicy(BaseModel):
    min_length: int = Field(8, ge=6, le=128)
    require_numbers: bool = True
    require_special: bool = False

    model_config = ConfigDict()

    @field_validator("min_length")
    @classmethod
    def validate_min_length(cls, v: int) -> int:
        if v < 6:
            raise ValueError("min_length must be >= 6")
        return v
