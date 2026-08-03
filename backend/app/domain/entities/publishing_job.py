from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class PublishingJob:
    id: str
    entity_type: str
    entity_id: str
    version: int
    requested_by: str
    approved_by: str | None
    status: str
    schedule_at: datetime | None
    published_at: datetime | None
    rollback_version: int | None
    notes: str | None
    is_active: bool
    created_by: str | None
    updated_by: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        entity_type: str,
        entity_id: str,
        version: int,
        requested_by: str,
        schedule_at: datetime | None = None,
        notes: str | None = None,
        created_by: str | None = None,
    ) -> PublishingJob:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            entity_type=entity_type,
            entity_id=entity_id,
            version=version,
            requested_by=requested_by,
            approved_by=None,
            status="pending",
            schedule_at=schedule_at,
            published_at=None,
            rollback_version=None,
            notes=notes,
            is_active=True,
            created_by=created_by or requested_by,
            updated_by=created_by or requested_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def approve(self, user_id: str) -> None:
        self.approved_by = user_id
        self.status = "approved"
        self.updated_at = datetime.now(UTC)

    def publish(self) -> None:
        self.status = "published"
        self.published_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def fail(self, reason: str) -> None:
        self.status = "failed"
        self.notes = reason
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "version": self.version,
            "requested_by": self.requested_by,
            "approved_by": self.approved_by,
            "status": self.status,
            "schedule_at": self.schedule_at.isoformat() if self.schedule_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "rollback_version": self.rollback_version,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
