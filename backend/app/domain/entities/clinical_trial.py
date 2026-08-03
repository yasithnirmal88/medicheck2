from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class ClinicalTrial:
    id: str
    title: str
    nct_id: str | None
    phase: str | None
    status: str
    conditions: list[str]
    interventions: list[str]
    sponsor: str | None
    enrollment: int | None
    start_date: datetime | None
    completion_date: datetime | None
    results: str | None
    url: str | None
    is_active: bool
    version: int
    created_by: str | None
    updated_by: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        title: str,
        nct_id: str | None = None,
        phase: str | None = None,
        conditions: list[str] | None = None,
        interventions: list[str] | None = None,
        sponsor: str | None = None,
        enrollment: int | None = None,
        start_date: datetime | None = None,
        completion_date: datetime | None = None,
        results: str | None = None,
        url: str | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> ClinicalTrial:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            title=title.strip(),
            nct_id=nct_id,
            phase=phase,
            status="registered",
            conditions=conditions or [],
            interventions=interventions or [],
            sponsor=sponsor,
            enrollment=enrollment,
            start_date=start_date,
            completion_date=completion_date,
            results=results,
            url=url,
            is_active=is_active,
            version=1,
            created_by=created_by,
            updated_by=created_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "nct_id": self.nct_id,
            "phase": self.phase,
            "status": self.status,
            "conditions": self.conditions,
            "interventions": self.interventions,
            "sponsor": self.sponsor,
            "enrollment": self.enrollment,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "results": self.results,
            "url": self.url,
            "is_active": self.is_active,
            "version": self.version,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
