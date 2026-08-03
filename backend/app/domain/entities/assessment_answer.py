from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class AssessmentAnswer:
    id: str
    session_id: str
    question_id: str
    question_version: int
    question_code: str
    response_value: dict[str, Any]
    score_value: float
    is_skipped: bool
    time_taken_seconds: int
    branch_path: list[str]
    created_at: datetime

    @classmethod
    def create(
        cls,
        session_id: str,
        question_id: str,
        question_code: str,
        response_value: dict[str, Any] | None = None,
        question_version: int = 1,
        score_value: float = 0.0,
        is_skipped: bool = False,
        time_taken_seconds: int = 0,
        branch_path: list[str] | None = None,
    ) -> AssessmentAnswer:
        return cls(
            id=uuid.uuid4().hex,
            session_id=session_id,
            question_id=question_id,
            question_version=question_version,
            question_code=question_code,
            response_value=response_value or {},
            score_value=score_value,
            is_skipped=is_skipped,
            time_taken_seconds=time_taken_seconds,
            branch_path=branch_path or [],
            created_at=datetime.now(UTC),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "question_id": self.question_id,
            "question_version": self.question_version,
            "question_code": self.question_code,
            "response_value": self.response_value,
            "score_value": self.score_value,
            "is_skipped": self.is_skipped,
            "time_taken_seconds": self.time_taken_seconds,
            "branch_path": self.branch_path,
            "created_at": self.created_at.isoformat(),
        }
