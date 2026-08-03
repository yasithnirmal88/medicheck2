from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class QuestionnaireTemplate:
    id: str
    code: str
    name: str
    description: str | None
    body_system_id: str | None
    target_audience: str
    estimated_time_minutes: int
    is_active: bool
    is_template: bool
    version: int
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        code: str,
        name: str,
        description: str | None = None,
        body_system_id: str | None = None,
        target_audience: str = "all",
        estimated_time_minutes: int = 10,
        is_active: bool = True,
        is_template: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> QuestionnaireTemplate:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            code=code.strip(),
            name=name,
            description=description,
            body_system_id=body_system_id,
            target_audience=target_audience,
            estimated_time_minutes=estimated_time_minutes,
            is_active=is_active,
            is_template=is_template,
            version=1,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "body_system_id": self.body_system_id,
            "target_audience": self.target_audience,
            "estimated_time_minutes": self.estimated_time_minutes,
            "is_active": self.is_active,
            "is_template": self.is_template,
            "version": self.version,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
