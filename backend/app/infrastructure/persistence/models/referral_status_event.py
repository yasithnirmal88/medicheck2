"""Phase 9 — Append-only referral status transition audit.

Every status change produces one immutable row here. The referral's current
``status`` is denormalized for query speed, but this table is the authoritative
history. The referral service validates transitions against a fixed state
machine before inserting a row + updating the parent status.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class ReferralStatusEventModel(BaseModel):
    __tablename__ = "referral_status_events"

    referral_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("referrals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    actor_user_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True,
    )
    actor_role: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    referral = relationship("ReferralModel", back_populates="status_events")
