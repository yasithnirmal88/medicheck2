from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class ExerciseProgram:
    id: str
    body_system_id: str
    code: str
    name: str
    description: str | None
    duration_minutes: int
    frequency_per_week: int
    intensity: str
    contraindications: list[str]
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
        description: str | None = None,
        duration_minutes: int = 30,
        frequency_per_week: int = 3,
        intensity: str = "moderate",
        contraindications: list[str] | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> ExerciseProgram:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            code=code.strip(),
            name=name.strip(),
            description=description,
            duration_minutes=duration_minutes,
            frequency_per_week=frequency_per_week,
            intensity=intensity,
            contraindications=contraindications or [],
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
            "duration_minutes": self.duration_minutes,
            "frequency_per_week": self.frequency_per_week,
            "intensity": self.intensity,
            "contraindications": self.contraindications,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
