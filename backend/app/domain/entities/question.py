from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class QuestionType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    YES_NO = "yes_no"
    NUMERIC = "numeric"
    DECIMAL = "decimal"
    SLIDER = "slider"
    DATE = "date"
    TIME = "time"
    DROPDOWN = "dropdown"
    MULTI_SELECT = "multi_select"
    FREE_TEXT = "free_text"
    SEARCH = "search"
    FILE_UPLOAD = "file_upload"


class QuestionDifficulty(StrEnum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuestionStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


@dataclass
class Question:
    id: str
    body_system_id: str
    question_group_id: str
    code: str
    question_type: QuestionType
    text: str | dict[str, Any]
    description: str | None
    tooltip: str | None
    medical_notes: str | None
    evidence_ref: str | None
    order_index: int
    priority: int
    difficulty: QuestionDifficulty
    status: QuestionStatus
    is_required: bool
    validation_rules: dict[str, Any]
    scoring_weight: float
    version: int
    created_by: str | None
    updated_by: str | None
    activation_date: datetime | None
    expiration_date: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        body_system_id: str,
        question_group_id: str,
        code: str,
        question_type: QuestionType,
        text: str | dict[str, Any],
        description: str | None = None,
        tooltip: str | None = None,
        medical_notes: str | None = None,
        evidence_ref: str | None = None,
        order_index: int = 0,
        priority: int = 3,
        difficulty: QuestionDifficulty = QuestionDifficulty.BASIC,
        status: QuestionStatus = QuestionStatus.ACTIVE,
        is_required: bool = False,
        validation_rules: dict[str, Any] | None = None,
        scoring_weight: float = 1.0,
        created_by: str | None = None,
        updated_by: str | None = None,
        activation_date: datetime | None = None,
        expiration_date: datetime | None = None,
    ) -> Question:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            question_group_id=question_group_id,
            code=code.strip(),
            question_type=question_type,
            text=text,
            description=description,
            tooltip=tooltip,
            medical_notes=medical_notes,
            evidence_ref=evidence_ref,
            order_index=order_index,
            priority=priority,
            difficulty=difficulty,
            status=status,
            is_required=is_required,
            validation_rules=validation_rules or {},
            scoring_weight=scoring_weight,
            version=1,
            created_by=created_by,
            updated_by=updated_by,
            activation_date=activation_date,
            expiration_date=expiration_date,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "body_system_id": self.body_system_id,
            "question_group_id": self.question_group_id,
            "code": self.code,
            "question_type": self.question_type.value,
            "text": self.text,
            "description": self.description,
            "tooltip": self.tooltip,
            "medical_notes": self.medical_notes,
            "evidence_ref": self.evidence_ref,
            "order_index": self.order_index,
            "priority": self.priority,
            "difficulty": self.difficulty.value,
            "status": self.status.value,
            "is_required": self.is_required,
            "validation_rules": self.validation_rules,
            "scoring_weight": self.scoring_weight,
            "version": self.version,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "activation_date": (
                self.activation_date.isoformat() if self.activation_date else None
            ),
            "expiration_date": (
                self.expiration_date.isoformat() if self.expiration_date else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
