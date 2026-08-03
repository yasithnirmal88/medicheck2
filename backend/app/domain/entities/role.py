from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class Role:
    id: str
    code: str
    name: dict[str, str]
    description: str
    is_system: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        code: str,
        name: dict[str, str],
        description: str = "",
        is_system: bool = False,
        priority: int = 0,
    ) -> Role:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            code=code.upper().strip(),
            name=name,
            description=description,
            is_system=is_system,
            priority=priority,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        name: dict[str, str] | None = None,
        description: str | None = None,
        priority: int | None = None,
    ) -> None:
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if priority is not None:
            self.priority = priority
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "is_system": self.is_system,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
