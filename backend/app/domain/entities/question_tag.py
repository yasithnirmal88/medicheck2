from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class QuestionTag:
    id: str
    code: str
    name: str
    category: str
    color_hex: str | None
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
        code: str,
        name: str,
        category: str = "general",
        color_hex: str | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> QuestionTag:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            code=code.strip(),
            name=name.strip(),
            category=category,
            color_hex=color_hex,
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
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "color_hex": self.color_hex,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
