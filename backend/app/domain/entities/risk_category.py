from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class RiskCategory:
    id: str
    body_system_id: str
    code: str
    name: str
    description: str | None
    min_probability: float
    max_probability: float
    color_hex: str | None
    action_required: str | None
    is_active: bool
    version: int
    status: str
    created_by: str | None
    updated_by: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        body_system_id: str,
        code: str,
        name: str,
        min_probability: float = 0.0,
        max_probability: float = 1.0,
        description: str | None = None,
        color_hex: str | None = None,
        action_required: str | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> RiskCategory:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            code=code.strip(),
            name=name.strip(),
            description=description,
            min_probability=min_probability,
            max_probability=max_probability,
            color_hex=color_hex,
            action_required=action_required,
            is_active=is_active,
            version=1,
            status="draft",
            created_by=created_by,
            updated_by=created_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "body_system_id": self.body_system_id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "min_probability": self.min_probability,
            "max_probability": self.max_probability,
            "color_hex": self.color_hex,
            "action_required": self.action_required,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
