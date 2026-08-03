from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class Approval:
    id: str
    entity_type: str
    entity_id: str
    requested_by: str
    assigned_to: str | None
    role_required: str | None
    status: str
    comments: list[dict[str, Any]]
    decided_at: datetime | None
    is_active: bool
    version: int
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
        requested_by: str,
        assigned_to: str | None = None,
        role_required: str | None = None,
        created_by: str | None = None,
    ) -> Approval:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            entity_type=entity_type,
            entity_id=entity_id,
            requested_by=requested_by,
            assigned_to=assigned_to,
            role_required=role_required,
            status="pending",
            comments=[],
            decided_at=None,
            is_active=True,
            version=1,
            created_by=created_by or requested_by,
            updated_by=created_by or requested_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def add_comment(
        self, user_id: str, comment: str
    ) -> None:
        self.comments.append(
            {
                "user_id": user_id,
                "comment": comment,
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
        self.updated_at = datetime.now(UTC)

    def approve(self, user_id: str, comment: str | None = None) -> None:
        self.status = "approved"
        self.decided_at = datetime.now(UTC)
        self.assigned_to = user_id
        if comment:
            self.add_comment(user_id, comment)
        self.updated_at = datetime.now(UTC)

    def reject(self, user_id: str, reason: str) -> None:
        self.status = "rejected"
        self.decided_at = datetime.now(UTC)
        self.assigned_to = user_id
        self.add_comment(user_id, reason)
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "requested_by": self.requested_by,
            "assigned_to": self.assigned_to,
            "role_required": self.role_required,
            "status": self.status,
            "comments": self.comments,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "is_active": self.is_active,
            "version": self.version,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
