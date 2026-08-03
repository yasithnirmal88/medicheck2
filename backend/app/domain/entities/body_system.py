from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class BodySystem:
    id: str
    code: str
    name: str
    description: str
    icon: str | None
    color_hex: str | None
    display_order: int
    module_version: str
    is_active: bool
    is_core: bool
    scoring_weight: float
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        code: str,
        name: str,
        description: str = "",
        icon: str | None = None,
        color_hex: str | None = None,
        display_order: int = 0,
        module_version: str = "1.0.0",
        is_active: bool = True,
        is_core: bool = False,
        scoring_weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> BodySystem:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            code=code.upper().strip(),
            name=name,
            description=description,
            icon=icon,
            color_hex=color_hex,
            display_order=display_order,
            module_version=module_version,
            is_active=is_active,
            is_core=is_core,
            scoring_weight=scoring_weight,
            metadata=metadata or {},
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
            "icon": self.icon,
            "color_hex": self.color_hex,
            "display_order": self.display_order,
            "module_version": self.module_version,
            "is_active": self.is_active,
            "is_core": self.is_core,
            "scoring_weight": self.scoring_weight,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
