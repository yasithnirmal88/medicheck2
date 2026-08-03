from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.role import RoleModel


class UserModel(BaseModel):
    __tablename__ = "users"

    firebase_uid: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    roles: Mapped[list[RoleModel]] = relationship(
        "RoleModel",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_users_firebase_uid", "firebase_uid"),
        Index("ix_users_email", "email"),
        Index("ix_users_is_active", "is_active"),
    )

    def to_entity_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "firebase_uid": self.firebase_uid,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "email_verified": self.email_verified,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }
