from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class RuleLibrary:
    id: str
    body_system_id: str
    code: str
    name: str
    description: str | None
    rules: list[dict[str, Any]]
    version: int
    status: str
    is_active: bool
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
        rules: list[dict[str, Any]] | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> RuleLibrary:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            code=code.strip(),
            name=name.strip(),
            description=description,
            rules=rules or [],
            version=1,
            status="draft",
            is_active=is_active,
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
            "rules": self.rules,
            "version": self.version,
            "status": self.status,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
