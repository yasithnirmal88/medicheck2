from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class EvidenceReference:
    id: str
    question_id: str
    title: str
    url: str | None
    source: str | None
    evidence_level: str
    summary: str | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        question_id: str,
        title: str,
        url: str | None = None,
        source: str | None = None,
        evidence_level: str = "C",
        summary: str | None = None,
    ) -> EvidenceReference:
        return cls(
            id=uuid.uuid4().hex,
            question_id=question_id,
            title=title,
            url=url,
            source=source,
            evidence_level=evidence_level.upper(),
            summary=summary,
            created_at=datetime.now(UTC),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question_id": self.question_id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "evidence_level": self.evidence_level,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
        }
