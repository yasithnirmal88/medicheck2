from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class VersionSnapshot:
    id: str
    entity_type: str
    entity_id: str
    version: int
    snapshot: dict[str, Any]
    snapshot_type: str
    reason: str | None
    created_by: str | None
    created_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        entity_type: str,
        entity_id: str,
        version: int,
        snapshot: dict[str, Any],
        snapshot_type: str = "auto",
        reason: str | None = None,
        created_by: str | None = None,
    ) -> VersionSnapshot:
        return cls(
            id=uuid.uuid4().hex,
            entity_type=entity_type,
            entity_id=entity_id,
            version=version,
            snapshot=snapshot,
            snapshot_type=snapshot_type,
            reason=reason,
            created_by=created_by,
            created_at=datetime.now(UTC),
            deleted_at=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "version": self.version,
            "snapshot": self.snapshot,
            "snapshot_type": self.snapshot_type,
            "reason": self.reason,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
