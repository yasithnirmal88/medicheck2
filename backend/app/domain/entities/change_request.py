from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class ChangeRequest:
    id: str
    entity_type: str
    entity_id: str
    requested_by: str
    title: str
    description: str | None
    changes: dict[str, Any]
    reason: str | None
    status: str
    is_active: bool
    version: int
    created_by: str | None
    updated_by: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    resolved_at: datetime | None
    resolved_by: str | None

    @classmethod
    def create(
        cls,
        entity_type: str,
        entity_id: str,
        requested_by: str,
        title: str,
        changes: dict[str, Any],
        description: str | None = None,
        reason: str | None = None,
        created_by: str | None = None,
    ) -> ChangeRequest:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            entity_type=entity_type,
            entity_id=entity_id,
            requested_by=requested_by,
            title=title.strip(),
            description=description,
            changes=changes,
            reason=reason,
            status="pending",
            is_active=True,
            version=1,
            created_by=created_by or requested_by,
            updated_by=created_by or requested_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            resolved_at=None,
            resolved_by=None,
        )

    def approve(self, user_id: str) -> None:
        self.status = "approved"
        self.resolved_by = user_id
        self.resolved_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def reject(self, user_id: str, reason: str) -> None:
        self.status = "rejected"
        self.resolved_by = user_id
        self.resolved_at = datetime.now(UTC)
        self.reason = reason
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "requested_by": self.requested_by,
            "title": self.title,
            "description": self.description,
            "changes": self.changes,
            "reason": self.reason,
            "status": self.status,
            "is_active": self.is_active,
            "version": self.version,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
        }
