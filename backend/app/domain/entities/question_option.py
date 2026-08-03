from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class QuestionOption:
    id: str
    question_id: str
    code: str
    text: str
    value: str
    score_value: float
    severity: str
    color_hex: str | None
    recommendation_trigger: str | None
    follow_up_trigger: str | None
    medical_notes: str | None
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        question_id: str,
        code: str,
        text: str,
        value: str,
        score_value: float = 0.0,
        severity: str = "none",
        color_hex: str | None = None,
        recommendation_trigger: str | None = None,
        follow_up_trigger: str | None = None,
        medical_notes: str | None = None,
        display_order: int = 0,
        is_active: bool = True,
    ) -> QuestionOption:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            question_id=question_id,
            code=code.strip(),
            text=text,
            value=value,
            score_value=score_value,
            severity=severity,
            color_hex=color_hex,
            recommendation_trigger=recommendation_trigger,
            follow_up_trigger=follow_up_trigger,
            medical_notes=medical_notes,
            display_order=display_order,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question_id": self.question_id,
            "code": self.code,
            "text": self.text,
            "value": self.value,
            "score_value": self.score_value,
            "severity": self.severity,
            "color_hex": self.color_hex,
            "recommendation_trigger": self.recommendation_trigger,
            "follow_up_trigger": self.follow_up_trigger,
            "medical_notes": self.medical_notes,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
