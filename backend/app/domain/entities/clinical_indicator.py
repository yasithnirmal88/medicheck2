from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class ClinicalIndicator:
    id: str
    body_system_id: str
    key: str
    name: str
    description: str | None
    severity: str
    evidence_strength: str
    confidence: float
    positive_weight: float
    negative_weight: float
    neutral_weight: float
    related_disease_ids: list[str]
    related_symptom_ids: list[str]
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
        key: str,
        name: str,
        description: str | None = None,
        severity: str = "moderate",
        evidence_strength: str = "C",
        confidence: float = 0.5,
        positive_weight: float = 1.0,
        negative_weight: float = 0.0,
        neutral_weight: float = 0.0,
        related_disease_ids: list[str] | None = None,
        related_symptom_ids: list[str] | None = None,
        is_active: bool = True,
        created_by: str | None = None,
        updated_by: str | None = None,
    ) -> ClinicalIndicator:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            key=key.upper().strip(),
            name=name.strip(),
            description=description,
            severity=severity,
            evidence_strength=evidence_strength.upper(),
            confidence=max(0.0, min(1.0, confidence)),
            positive_weight=positive_weight,
            negative_weight=negative_weight,
            neutral_weight=neutral_weight,
            related_disease_ids=related_disease_ids or [],
            related_symptom_ids=related_symptom_ids or [],
            is_active=is_active,
            version=1,
            status="draft",
            created_by=created_by,
            updated_by=updated_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "body_system_id": self.body_system_id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "evidence_strength": self.evidence_strength,
            "confidence": self.confidence,
            "positive_weight": self.positive_weight,
            "negative_weight": self.negative_weight,
            "neutral_weight": self.neutral_weight,
            "related_disease_ids": self.related_disease_ids,
            "related_symptom_ids": self.related_symptom_ids,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
