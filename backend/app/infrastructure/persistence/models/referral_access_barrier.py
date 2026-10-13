"""Phase 9 — Referral access barriers (SDG 3.8 / SDG 10).

Structured, non-clinical records describing why a patient could not reach
care. These are access barriers, NOT medical diagnoses. They feed
population-level equity analytics in de-identified, k-anonymity-suppressed
form. Individual barrier detail is visible only to the patient, their
assigned CHW, and authorized clinicians — never to other patients or in
aggregate below the k threshold.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class ReferralAccessBarrierModel(BaseModel):
    __tablename__ = "referral_access_barriers"

    referral_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("referrals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    barrier_type: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True,
    )
    recorded_by_user_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True,
    )
    recorded_by_role: Mapped[str] = mapped_column(String(40), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    referral = relationship("ReferralModel", back_populates="barriers")
