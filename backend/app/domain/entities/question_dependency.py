from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class QuestionDependency:
    id: str
    question_id: str
    depends_on_question_id: str
    condition_type: str
    condition_value: dict[str, Any]
    logic_operator: str
    group_id: int
    created_at: datetime

    @classmethod
    def create(
        cls,
        question_id: str,
        depends_on_question_id: str,
        condition_type: str = "equals",
        condition_value: dict[str, Any] | None = None,
        logic_operator: str = "AND",
        group_id: int = 0,
    ) -> QuestionDependency:
        return cls(
            id=uuid.uuid4().hex,
            question_id=question_id,
            depends_on_question_id=depends_on_question_id,
            condition_type=condition_type,
            condition_value=condition_value or {},
            logic_operator=logic_operator,
            group_id=group_id,
            created_at=datetime.now(UTC),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question_id": self.question_id,
            "depends_on_question_id": self.depends_on_question_id,
            "condition_type": self.condition_type,
            "condition_value": self.condition_value,
            "logic_operator": self.logic_operator,
            "group_id": self.group_id,
            "created_at": self.created_at.isoformat(),
        }
