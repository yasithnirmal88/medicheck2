from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class ImagingTest:
    id: str
    code: str
    name: str
    description: str | None
    body_system_id: str
    modality: str
    is_contrast_required: bool
    preparation_notes: str | None
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
        modality: str = "X-ray",
        description: str | None = None,
        is_contrast_required: bool = False,
        preparation_notes: str | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> ImagingTest:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            code=code.strip(),
            name=name.strip(),
            description=description,
            body_system_id=body_system_id,
            modality=modality,
            is_contrast_required=is_contrast_required,
            preparation_notes=preparation_notes,
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
            "modality": self.modality,
            "is_contrast_required": self.is_contrast_required,
            "preparation_notes": self.preparation_notes,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
