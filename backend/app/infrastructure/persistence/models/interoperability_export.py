"""Phase 10 — Interoperability export manifest / audit.

Additive, append-only table. Every FHIR or SDG export produces one row here
recording the export's identity, requester, scope, resource types, source
trace IDs, schema version, consent reference, and status. This is the
auditability backbone required by the Phase 10 safety requirements.

NO patient PHI is stored here — only reference ids, hashes, and metadata.
The bundle payload itself is generated on demand (read-only) and is NOT
persisted (to avoid creating a stale second copy of clinical data). The
manifest records THAT an export happened and WHAT it contained, not the
content.
"""

from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class InteroperabilityExportModel(BaseModel):
    __tablename__ = "interoperability_exports"

    export_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="json")
    requested_by_user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    patient_user_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    resource_types: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_trace_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    schema_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="4.0.1"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completed", index=True
    )
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    item_count: Mapped[int] = mapped_column(default=0, nullable=False)
