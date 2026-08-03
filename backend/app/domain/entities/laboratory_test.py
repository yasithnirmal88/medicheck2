from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class LaboratoryTest:
    id: str
    code: str
    name: str
    description: str | None
    body_system_id: str
    loinc_code: str | None
    normal_range: str | None
    unit: str | None
    reference_range_min: float | None
    reference_range_max: float | None
    critical_low: float | None
    critical_high: float | None
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
        code: str,
        name: str,
        body_system_id: str,
        description: str | None = None,
        loinc_code: str | None = None,
        normal_range: str | None = None,
        unit: str | None = None,
        reference_range_min: float | None = None,
        reference_range_max: float | None = None,
        critical_low: float | None = None,
        critical_high: float | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> LaboratoryTest:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            code=code.strip(),
            name=name.strip(),
            description=description,
            body_system_id=body_system_id,
            loinc_code=loinc_code,
            normal_range=normal_range,
            unit=unit,
            reference_range_min=reference_range_min,
            reference_range_max=reference_range_max,
            critical_low=critical_low,
            critical_high=critical_high,
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
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "body_system_id": self.body_system_id,
            "loinc_code": self.loinc_code,
            "normal_range": self.normal_range,
            "unit": self.unit,
            "reference_range_min": self.reference_range_min,
            "reference_range_max": self.reference_range_max,
            "critical_low": self.critical_low,
            "critical_high": self.critical_high,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
