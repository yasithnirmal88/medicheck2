"""Phase 8 — Patient consent records.

Additive table. A consent record is created before a CHW begins an assessment
on a patient's behalf. Stores only the fact of consent, the scope, the
language, and reference ids — no clinical answers, no free text beyond a short
consent statement version identifier.

The consent model is deliberately minimal: we record WHAT was consented to
(assessment_assist), WHO consented (patient_user_id), WHO assisted
(chw_user_id), the language, and a content version of the consent text. We do
not store the patient's verbatim signature or biometric data — consent is
attested by the CHW and timestamped.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class ConsentRecordModel(BaseModel):
    __tablename__ = "consent_records"

    patient_user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chw_user_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    consent_type: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en", index=True
    )
    consent_text_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="v1"
    )
    granted: Mapped[bool] = mapped_column(default=True, nullable=False)
    attested_by: Mapped[str] = mapped_column(
        String(20), nullable=False, default="chw"
    )
