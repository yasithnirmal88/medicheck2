"""Phase 9 — Referral: a care-navigation record derived from an existing
deterministic recommendation.

Additive table. A referral is NEVER an independent clinical judgment. It is
created only from a ``GeneratedRecommendationModel`` (CDSE output) whose
source ``RecommendationModel`` has an eligible CMS-authored ``category``
(referral / testing / monitoring). The referral traces back to:

    assessment_session → assessment_result → generated_recommendation
                                                     → recommendation (CMS)
                                                          → referral

trace_id is carried from the CDSE result summary (parsed once at creation).
No clinical score, severity, or recommendation text is duplicated here —
those remain in the CDSE/report tables. The referral stores only navigation
state (status, due date, assigned CHW) and reference ids.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class ReferralModel(BaseModel):
    __tablename__ = "referrals"

    patient_user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    originating_session_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True,
    )
    originating_report_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True,
    )
    trace_id: Mapped[str | None] = mapped_column(
        String(16), nullable=True, index=True,
    )
    recommendation_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True,
    )
    referral_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
    )
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    assigned_chw_user_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    patient_acknowledged: Mapped[bool] = mapped_column(
        default=False, nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    status_events = relationship(
        "ReferralStatusEventModel", back_populates="referral",
        lazy="selectin", order_by="ReferralStatusEventModel.created_at",
    )
    barriers = relationship(
        "ReferralAccessBarrierModel", back_populates="referral",
        lazy="selectin",
    )
    follow_up_tasks = relationship(
        "FollowUpTaskModel", back_populates="referral",
        lazy="selectin",
    )
