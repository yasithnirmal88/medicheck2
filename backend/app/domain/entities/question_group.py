from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class QuestionGroup:
    id: str
    body_system_id: str
    code: str
    name: str
    description: str | None
    display_order: int
    is_active: bool
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        body_system_id: str,
        code: str,
        name: str,
        description: str | None = None,
        display_order: int = 0,
        is_active: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> QuestionGroup:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            code=code.strip(),
            name=name,
            description=description,
            display_order=display_order,
            is_active=is_active,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "body_system_id": self.body_system_id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
