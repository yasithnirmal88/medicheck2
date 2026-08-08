from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class User:
    id: str
    firebase_uid: str
    email: str
    full_name: str
    avatar_url: str | None
    email_verified: bool
    is_active: bool
    roles: set[str]
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        firebase_uid: str,
        email: str,
        full_name: str,
        avatar_url: str | None = None,
        role: str = "patient",
    ) -> User:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            firebase_uid=firebase_uid,
            email=email.lower().strip(),
            full_name=full_name.strip(),
            avatar_url=avatar_url,
            email_verified=False,
            is_active=True,
            roles={role} if role else set(),
            last_login_at=None,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(UTC)

    def mark_login(self) -> None:
        self.last_login_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def update_profile(
        self,
        full_name: str | None = None,
        avatar_url: str | None = None,
    ) -> None:
        if full_name is not None:
            self.full_name = full_name.strip()
        if avatar_url is not None:
            self.avatar_url = avatar_url
        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        self.deactivate()
        self.deleted_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "firebase_uid": self.firebase_uid,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "email_verified": self.email_verified,
            "is_active": self.is_active,
            "roles": list(self.roles),
            "last_login_at": (
                self.last_login_at.isoformat() if self.last_login_at else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
