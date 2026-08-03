from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class ReviewComment:
    id: str
    review_id: str
    user_id: str
    comment: str
    parent_id: str | None
    is_active: bool
    version: int
    created_by: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        review_id: str,
        user_id: str,
        comment: str,
        parent_id: str | None = None,
        created_by: str | None = None,
    ) -> ReviewComment:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            review_id=review_id,
            user_id=user_id,
            comment=comment.strip(),
            parent_id=parent_id,
            is_active=True,
            version=1,
            created_by=created_by or user_id,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "review_id": self.review_id,
            "user_id": self.user_id,
            "comment": self.comment,
            "parent_id": self.parent_id,
            "is_active": self.is_active,
            "version": self.version,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
