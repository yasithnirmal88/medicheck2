from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class LifestyleAdvice:
    id: str
    body_system_id: str
    code: str
    title: str
    summary: str | None
    details: str | None
    category: str
    tags: list[str]
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
        title: str,
        summary: str | None = None,
        details: str | None = None,
        category: str = "general",
        tags: list[str] | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> LifestyleAdvice:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            code=code.strip(),
            title=title.strip(),
            summary=summary,
            details=details,
            category=category,
            tags=tags or [],
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
            "title": self.title,
            "summary": self.summary,
            "details": self.details,
            "category": self.category,
            "tags": self.tags,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
