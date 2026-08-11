"""Phase 8 — Assessment sync records (offline synchronization ledger).

Additive table. One row per offline assessment that has been submitted for
synchronization. The ``idempotency_key`` is the deduplication anchor: a
repeated sync with the same key is a no-op (returns the already-created
session), so a flaky connection can never duplicate patients, assessments,
answers, or reports.

Stores only reference ids + status + version metadata — no raw clinical
answers (answers live in assessment_answers as before) and no PHI beyond the
patient/chw user ids.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class AssessmentSyncRecordModel(BaseModel):
    __tablename__ = "assessment_sync_records"

    idempotency_key: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    chw_user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    template_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    content_version: Mapped[int] = mapped_column(
        nullable=False, default=1
    )
    sync_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    error_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
