from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class ClinicalGuideline:
    id: str
    body_system_id: str
    disease_id: str | None
    code: str
    title: str
    summary: str | None
    recommendations: list[dict[str, Any]]
    evidence_level: str
    source_organization: str | None
    guideline_url: str | None
    publication_year: int | None
    is_active: bool
    version: int
    status: str
    created_by: str | None
    updated_by: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    reviewed_at: datetime | None
    published_at: datetime | None
    archived_at: datetime | None

    @classmethod
    def create(
        cls,
        body_system_id: str,
        code: str,
        title: str,
        disease_id: str | None = None,
        summary: str | None = None,
        recommendations: list[dict[str, Any]] | None = None,
        evidence_level: str = "C",
        source_organization: str | None = None,
        guideline_url: str | None = None,
        publication_year: int | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> ClinicalGuideline:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            disease_id=disease_id,
            code=code.strip(),
            title=title.strip(),
            summary=summary,
            recommendations=recommendations or [],
            evidence_level=evidence_level.upper(),
            source_organization=source_organization,
            guideline_url=guideline_url,
            publication_year=publication_year,
            is_active=is_active,
            version=1,
            status="draft",
            created_by=created_by,
            updated_by=created_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            reviewed_at=None,
            published_at=None,
            archived_at=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "body_system_id": self.body_system_id,
            "disease_id": self.disease_id,
            "code": self.code,
            "title": self.title,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "evidence_level": self.evidence_level,
            "source_organization": self.source_organization,
            "guideline_url": self.guideline_url,
            "publication_year": self.publication_year,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }
