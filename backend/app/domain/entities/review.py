from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class Review:
    id: str
    entity_type: str
    entity_id: str
    reviewer_id: str
    review_type: str
    status: str
    decision: str | None
    comments: str | None
    score: int | None
    is_active: bool
    version: int
    created_by: str | None
    updated_by: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    completed_at: datetime | None

    @classmethod
    def create(
        cls,
        entity_type: str,
        entity_id: str,
        reviewer_id: str,
        review_type: str = "medical",
        created_by: str | None = None,
    ) -> Review:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            entity_type=entity_type,
            entity_id=entity_id,
            reviewer_id=reviewer_id,
            review_type=review_type,
            status="pending",
            decision=None,
            comments=None,
            score=None,
            is_active=True,
            version=1,
            created_by=created_by or reviewer_id,
            updated_by=created_by or reviewer_id,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            completed_at=None,
        )

    def complete(
        self,
        decision: str,
        comments: str | None = None,
        score: int | None = None,
    ) -> None:
        self.status = "completed"
        self.decision = decision
        self.comments = comments
        self.score = score
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "reviewer_id": self.reviewer_id,
            "review_type": self.review_type,
            "status": self.status,
            "decision": self.decision,
            "comments": self.comments,
            "score": self.score,
            "is_active": self.is_active,
            "version": self.version,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
