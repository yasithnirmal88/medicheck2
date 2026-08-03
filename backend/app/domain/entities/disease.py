from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class Disease:
    id: str
    icd10_code: str
    name: str
    description: str | None
    body_system_id: str
    risk_factors: list[str]
    early_indicators: list[str]
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
        icd10_code: str,
        name: str,
        body_system_id: str,
        description: str | None = None,
        risk_factors: list[str] | None = None,
        early_indicators: list[str] | None = None,
        is_active: bool = True,
        created_by: str | None = None,
        updated_by: str | None = None,
    ) -> Disease:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            icd10_code=icd10_code.upper().strip(),
            name=name.strip(),
            description=description,
            body_system_id=body_system_id,
            risk_factors=risk_factors or [],
            early_indicators=early_indicators or [],
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
            "icd10_code": self.icd10_code,
            "name": self.name,
            "description": self.description,
            "body_system_id": self.body_system_id,
            "risk_factors": self.risk_factors,
            "early_indicators": self.early_indicators,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
