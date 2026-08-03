from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class SeverityThreshold:
    id: str
    body_system_id: str
    scoring_profile_id: str | None
    name: str
    severity: str
    min_score: float
    max_score: float
    color_hex: str | None
    label: str | None
    recommendation: str | None
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
        body_system_id: str,
        name: str,
        severity: str,
        min_score: float = 0.0,
        max_score: float = 100.0,
        scoring_profile_id: str | None = None,
        color_hex: str | None = None,
        label: str | None = None,
        recommendation: str | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> SeverityThreshold:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            scoring_profile_id=scoring_profile_id,
            name=name.strip(),
            severity=severity,
            min_score=min_score,
            max_score=max_score,
            color_hex=color_hex,
            label=label,
            recommendation=recommendation,
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
            "body_system_id": self.body_system_id,
            "scoring_profile_id": self.scoring_profile_id,
            "name": self.name,
            "severity": self.severity,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "color_hex": self.color_hex,
            "label": self.label,
            "recommendation": self.recommendation,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
