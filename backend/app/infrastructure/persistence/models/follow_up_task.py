"""Phase 9 — Follow-up tasks linked to a referral.

A deterministic task (e.g. "schedule appointment", "attend follow-up
assessment") created from referral metadata or CMS-authored rules. Due dates
are derived ONLY from deterministic recommendation urgency/referral type —
never invented by AI. AI may explain a task but never create or re-date one.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class FollowUpTaskModel(BaseModel):
    __tablename__ = "follow_up_tasks"

    referral_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("referrals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    patient_user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    assigned_chw_user_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    task_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    referral = relationship("ReferralModel", back_populates="follow_up_tasks")
