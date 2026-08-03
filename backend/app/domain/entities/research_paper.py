from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class ResearchPaper:
    id: str
    title: str
    abstract: str | None
    authors: list[str]
    journal: str | None
    doi: str | None
    pmid: str | None
    publication_year: int | None
    keywords: list[str]
    mesh_terms: list[str]
    evidence_level: str | None
    sample_size: int | None
    methodology: str | None
    findings: str | None
    limitations: str | None
    conflict_of_interest: str | None
    url: str | None
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
        authors: list[str] | None = None,
        abstract: str | None = None,
        journal: str | None = None,
        doi: str | None = None,
        pmid: str | None = None,
        publication_year: int | None = None,
        keywords: list[str] | None = None,
        mesh_terms: list[str] | None = None,
        evidence_level: str | None = None,
        sample_size: int | None = None,
        methodology: str | None = None,
        findings: str | None = None,
        limitations: str | None = None,
        conflict_of_interest: str | None = None,
        url: str | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> ResearchPaper:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            title=title.strip(),
            abstract=abstract,
            authors=authors or [],
            journal=journal,
            doi=doi,
            pmid=pmid,
            publication_year=publication_year,
            keywords=keywords or [],
            mesh_terms=mesh_terms or [],
            evidence_level=evidence_level,
            sample_size=sample_size,
            methodology=methodology,
            findings=findings,
            limitations=limitations,
            conflict_of_interest=conflict_of_interest,
            url=url,
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
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "journal": self.journal,
            "doi": self.doi,
            "pmid": self.pmid,
            "publication_year": self.publication_year,
            "keywords": self.keywords,
            "mesh_terms": self.mesh_terms,
            "evidence_level": self.evidence_level,
            "sample_size": self.sample_size,
            "methodology": self.methodology,
            "findings": self.findings,
            "limitations": self.limitations,
            "conflict_of_interest": self.conflict_of_interest,
            "url": self.url,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
