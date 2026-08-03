from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class Notification:
    id: str
    user_id: str
    title: str
    body: str | None
    notification_type: str
    entity_type: str | None
    entity_id: str | None
    is_read: bool
    read_at: datetime | None
    is_active: bool
    version: int
    created_by: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        user_id: str,
        title: str,
        notification_type: str = "info",
        body: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        created_by: str | None = None,
    ) -> Notification:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            user_id=user_id,
            title=title.strip(),
            body=body,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
            is_read=False,
            read_at=None,
            is_active=True,
            version=1,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def mark_read(self) -> None:
        self.is_read = True
        self.read_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "body": self.body,
            "notification_type": self.notification_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "is_active": self.is_active,
            "version": self.version,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
