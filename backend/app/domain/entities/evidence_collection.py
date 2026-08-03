from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class EvidenceCollection:
    id: str
    body_system_id: str
    disease_id: str | None
    title: str
    methodology: str | None
    evidence_ids: list[str]
    conclusion: str | None
    overall_grade: str | None
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
        title: str,
        disease_id: str | None = None,
        methodology: str | None = None,
        evidence_ids: list[str] | None = None,
        conclusion: str | None = None,
        overall_grade: str | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> EvidenceCollection:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            disease_id=disease_id,
            title=title.strip(),
            methodology=methodology,
            evidence_ids=evidence_ids or [],
            conclusion=conclusion,
            overall_grade=overall_grade,
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
            "disease_id": self.disease_id,
            "title": self.title,
            "methodology": self.methodology,
            "evidence_ids": self.evidence_ids,
            "conclusion": self.conclusion,
            "overall_grade": self.overall_grade,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
