from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class AssessmentProgress:
    id: str
    session_id: str
    current_section: str | None
    completed_questions: int
    total_questions: int
    answered_questions: int
    skipped_questions: int
    estimated_time_remaining: int
    completion_percentage: float
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        session_id: str,
        current_section: str | None = None,
        total_questions: int = 0,
        estimated_time_remaining: int = 0,
    ) -> AssessmentProgress:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            session_id=session_id,
            current_section=current_section,
            completed_questions=0,
            total_questions=total_questions,
            answered_questions=0,
            skipped_questions=0,
            estimated_time_remaining=estimated_time_remaining,
            completion_percentage=0.0,
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "current_section": self.current_section,
            "completed_questions": self.completed_questions,
            "total_questions": self.total_questions,
            "answered_questions": self.answered_questions,
            "skipped_questions": self.skipped_questions,
            "estimated_time_remaining": self.estimated_time_remaining,
            "completion_percentage": self.completion_percentage,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
