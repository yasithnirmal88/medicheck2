from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class QuestionnaireRuleSet:
    id: str
    questionnaire_id: str
    name: str
    rules: list[dict[str, Any]]
    logic: str
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
        questionnaire_id: str,
        name: str,
        rules: list[dict[str, Any]] | None = None,
        logic: str = "ALL",
        is_active: bool = True,
        created_by: str | None = None,
    ) -> QuestionnaireRuleSet:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            questionnaire_id=questionnaire_id,
            name=name.strip(),
            rules=rules or [],
            logic=logic.upper(),
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
            "questionnaire_id": self.questionnaire_id,
            "name": self.name,
            "rules": self.rules,
            "logic": self.logic,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
