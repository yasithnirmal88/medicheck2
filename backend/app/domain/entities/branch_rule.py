from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class BranchRule:
    id: str
    code: str
    name: str
    description: str | None
    body_system_id: str
    condition_operator: str
    conditions: dict[str, Any]
    target_question_id: str
    priority: int
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        code: str,
        name: str,
        body_system_id: str,
        target_question_id: str,
        description: str | None = None,
        condition_operator: str = "AND",
        conditions: dict[str, Any] | None = None,
        priority: int = 0,
        is_active: bool = True,
    ) -> BranchRule:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            code=code.strip(),
            name=name,
            description=description,
            body_system_id=body_system_id,
            condition_operator=condition_operator,
            conditions=conditions or {},
            target_question_id=target_question_id,
            priority=priority,
            is_active=is_active,
            version=1,
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "body_system_id": self.body_system_id,
            "condition_operator": self.condition_operator,
            "conditions": self.conditions,
            "target_question_id": self.target_question_id,
            "priority": self.priority,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
