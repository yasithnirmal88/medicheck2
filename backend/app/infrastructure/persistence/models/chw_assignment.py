"""Phase 8 — Community Health Worker ↔ patient assignment.

Additive table. Models the explicit least-privilege authorization: a CHW may
only access patients explicitly assigned to them (by an admin/medical
director). A CHW never receives unrestricted patient search.

Columns store only reference ids + status — no PHI beyond the patient/worker
user ids (which are already FKs to users).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class ChwAssignmentModel(BaseModel):
    __tablename__ = "chw_assignments"

    chw_user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False, index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )