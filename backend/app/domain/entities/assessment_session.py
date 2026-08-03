from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class SessionStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class AssessmentSession:
    id: str
    user_id: str
    questionnaire_template_id: str | None
    questionnaire_version_id: str | None
    status: SessionStatus
    current_question_id: str | None
    current_group_id: str | None
    answers_count: int
    total_questions: int
    completed_questions: int
    started_at: datetime | None
    paused_at: datetime | None
    completed_at: datetime | None
    expires_at: datetime | None
    device_info: str | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        user_id: str,
        questionnaire_template_id: str | None = None,
        questionnaire_version_id: str | None = None,
        total_questions: int = 0,
        expires_at: datetime | None = None,
        device_info: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AssessmentSession:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            user_id=user_id,
            questionnaire_template_id=questionnaire_template_id,
            questionnaire_version_id=questionnaire_version_id,
            status=SessionStatus.ACTIVE,
            current_question_id=None,
            current_group_id=None,
            answers_count=0,
            total_questions=total_questions,
            completed_questions=0,
            started_at=now,
            paused_at=None,
            completed_at=None,
            expires_at=expires_at,
            device_info=device_info,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )

    def pause(self) -> None:
        self.status = SessionStatus.PAUSED
        self.paused_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def resume(self) -> None:
        self.status = SessionStatus.ACTIVE
        self.paused_at = None
        self.updated_at = datetime.now(UTC)

    def complete(self) -> None:
        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def cancel(self) -> None:
        self.status = SessionStatus.CANCELLED
        self.updated_at = datetime.now(UTC)

    def expire(self) -> None:
        self.status = SessionStatus.EXPIRED
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "questionnaire_template_id": self.questionnaire_template_id,
            "questionnaire_version_id": self.questionnaire_version_id,
            "status": self.status.value,
            "current_question_id": self.current_question_id,
            "current_group_id": self.current_group_id,
            "answers_count": self.answers_count,
            "total_questions": self.total_questions,
            "completed_questions": self.completed_questions,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "device_info": self.device_info,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
