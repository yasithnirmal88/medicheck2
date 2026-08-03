from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class QuestionnaireVersion:
    id: str
    questionnaire_template_id: str
    version: int
    snapshot: dict[str, Any]
    change_notes: str | None
    created_by: str | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        questionnaire_template_id: str,
        version: int,
        snapshot: dict[str, Any],
        change_notes: str | None = None,
        created_by: str | None = None,
    ) -> QuestionnaireVersion:
        return cls(
            id=uuid.uuid4().hex,
            questionnaire_template_id=questionnaire_template_id,
            version=version,
            snapshot=snapshot,
            change_notes=change_notes,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "questionnaire_template_id": self.questionnaire_template_id,
            "version": self.version,
            "snapshot": self.snapshot,
            "change_notes": self.change_notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }
