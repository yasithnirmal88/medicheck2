from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class MedicationRecommendation:
    id: str
    body_system_id: str
    disease_id: str | None
    drug_name: str
    generic_name: str | None
    drug_class: str | None
    dosage: str | None
    frequency: str | None
    route: str | None
    duration: str | None
    contraindications: list[str]
    side_effects: list[str]
    interactions: list[str]
    evidence_level: str
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
        drug_name: str,
        disease_id: str | None = None,
        generic_name: str | None = None,
        drug_class: str | None = None,
        dosage: str | None = None,
        frequency: str | None = None,
        route: str | None = None,
        duration: str | None = None,
        contraindications: list[str] | None = None,
        side_effects: list[str] | None = None,
        interactions: list[str] | None = None,
        evidence_level: str = "C",
        is_active: bool = True,
        created_by: str | None = None,
    ) -> MedicationRecommendation:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            body_system_id=body_system_id,
            disease_id=disease_id,
            drug_name=drug_name.strip(),
            generic_name=generic_name,
            drug_class=drug_class,
            dosage=dosage,
            frequency=frequency,
            route=route,
            duration=duration,
            contraindications=contraindications or [],
            side_effects=side_effects or [],
            interactions=interactions or [],
            evidence_level=evidence_level.upper(),
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
            "drug_name": self.drug_name,
            "generic_name": self.generic_name,
            "drug_class": self.drug_class,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "route": self.route,
            "duration": self.duration,
            "contraindications": self.contraindications,
            "side_effects": self.side_effects,
            "interactions": self.interactions,
            "evidence_level": self.evidence_level,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
