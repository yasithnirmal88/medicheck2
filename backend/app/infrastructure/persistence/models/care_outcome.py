"""Phase 10 — Care-continuity outcome records.

Additive table. An outcome is an OPERATIONAL care-continuity state recording
whether a screened/flagged/referred patient actually reached care. It is
append-only per referral (a new outcome supersedes the previous one
operationally, but the history is retained for the funnel analytics).

CRITICAL INVARIANT: outcome data NEVER feeds back into the CDSE. There is no
foreign-key or code path from this table into scoring/indicator/condition/
recommendation tables. Outcomes may become a future clinician-reviewed
calibration dataset, but this phase does not alter clinical rules
automatically. Outcome categories are operational states, NOT clinical
verdicts — ``CARE_RECEIVED`` does not confirm a diagnosis was treated, only
that a service was delivered.

Categories (operational funnel):
    SCREENED -> REFERRED -> REFERRAL_RECEIVED -> APPOINTMENT_SCHEDULED
        -> CARE_RECEIVED -> FOLLOWUP_COMPLETED
    terminal: LOST_TO_FOLLOWUP
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class CareOutcomeModel(BaseModel):
    __tablename__ = "care_outcomes"

    referral_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("referrals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    patient_user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    outcome_category: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True
    )
    recorded_by_user_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    recorded_by_role: Mapped[str] = mapped_column(String(40), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(
        String(30), default="manual", nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
