"""Phase 8 — Offline device registrations.

Additive table. Tracks a CHW-authorized device so an admin can audit and
revoke offline access. Stores a device label, a derived device fingerprint
hash (NOT raw device identifiers), status, and last-seen. No secrets, tokens,
or credentials are stored here — only a non-secret fingerprint so a lost
device can be revoked.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class OfflineDeviceRegistrationModel(BaseModel):
    __tablename__ = "offline_device_registrations"

    chw_user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_label: Mapped[str] = mapped_column(String(100), nullable=False)
    device_fingerprint: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registered_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
