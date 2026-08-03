from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.user import UserModel


class RoleModel(BaseModel):
    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    users: Mapped[list[UserModel]] = relationship(
        "UserModel",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )

    def to_entity_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "is_system": self.is_system,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
