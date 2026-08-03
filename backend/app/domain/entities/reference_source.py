from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class ReferenceSource:
    id: str
    title: str
    authors: list[str]
    source_type: str
    journal: str | None
    volume: str | None
    issue: str | None
    pages: str | None
    doi: str | None
    pmid: str | None
    isbn: str | None
    url: str | None
    publication_year: int | None
    publisher: str | None
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
        source_type: str = "journal",
        journal: str | None = None,
        volume: str | None = None,
        issue: str | None = None,
        pages: str | None = None,
        doi: str | None = None,
        pmid: str | None = None,
        isbn: str | None = None,
        url: str | None = None,
        publication_year: int | None = None,
        publisher: str | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> ReferenceSource:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            title=title.strip(),
            authors=authors or [],
            source_type=source_type,
            journal=journal,
            volume=volume,
            issue=issue,
            pages=pages,
            doi=doi,
            pmid=pmid,
            isbn=isbn,
            url=url,
            publication_year=publication_year,
            publisher=publisher,
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
            "authors": self.authors,
            "source_type": self.source_type,
            "journal": self.journal,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "doi": self.doi,
            "pmid": self.pmid,
            "isbn": self.isbn,
            "url": self.url,
            "publication_year": self.publication_year,
            "publisher": self.publisher,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
