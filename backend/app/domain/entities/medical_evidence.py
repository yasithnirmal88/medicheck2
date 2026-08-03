from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class MedicalEvidence:
    id: str
    title: str
    source: str
    source_type: str
    doi: str | None
    pmid: str | None
    url: str | None
    authors: list[str]
    publication_year: int | None
    evidence_level: str
    summary: str | None
    body_system_id: str | None
    disease_ids: list[str]
    indicator_ids: list[str]
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
        title: str,
        source: str,
        source_type: str = "journal",
        doi: str | None = None,
        pmid: str | None = None,
        url: str | None = None,
        authors: list[str] | None = None,
        publication_year: int | None = None,
        evidence_level: str = "C",
        summary: str | None = None,
        body_system_id: str | None = None,
        disease_ids: list[str] | None = None,
        indicator_ids: list[str] | None = None,
        created_by: str | None = None,
    ) -> MedicalEvidence:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            title=title.strip(),
            source=source.strip(),
            source_type=source_type,
            doi=doi,
            pmid=pmid,
            url=url,
            authors=authors or [],
            publication_year=publication_year,
            evidence_level=evidence_level.upper(),
            summary=summary,
            body_system_id=body_system_id,
            disease_ids=disease_ids or [],
            indicator_ids=indicator_ids or [],
            is_active=True,
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
            "title": self.title,
            "source": self.source,
            "source_type": self.source_type,
            "doi": self.doi,
            "pmid": self.pmid,
            "url": self.url,
            "authors": self.authors,
            "publication_year": self.publication_year,
            "evidence_level": self.evidence_level,
            "summary": self.summary,
            "body_system_id": self.body_system_id,
            "disease_ids": self.disease_ids,
            "indicator_ids": self.indicator_ids,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
