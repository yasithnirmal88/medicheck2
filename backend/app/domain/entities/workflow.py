from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class Workflow:
    id: str
    name: str
    description: str | None
    entity_type: str
    steps: list[dict[str, Any]]
    current_step: int
    status: str
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
        name: str,
        entity_type: str,
        steps: list[dict[str, Any]] | None = None,
        description: str | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> Workflow:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            name=name.strip(),
            description=description,
            entity_type=entity_type,
            steps=steps or [],
            current_step=0,
            status="active",
            is_active=is_active,
            version=1,
            created_by=created_by,
            updated_by=created_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "entity_type": self.entity_type,
            "steps": self.steps,
            "current_step": self.current_step,
            "status": self.status,
            "is_active": self.is_active,
            "version": self.version,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
