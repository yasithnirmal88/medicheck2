"""Phase 10 — Facility / health-service metadata.

Additive table. A facility is an external (or internal) health-service
destination that a referral may be routed to. Facilities hold ONLY
operational/contact metadata — never clinical content, never patient data.
They are seeded/demo records (no real hospital data is invented). A referral
connects to a facility via the additive ``facility_id`` column on
``ReferralModel`` (added by the Phase 10 migration).

Facilities are NOT a second medical-record system. They describe where care
*may* be delivered, not what care was delivered.
"""

from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class FacilityModel(BaseModel):
    __tablename__ = "facilities"

    code: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    region: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    contact_channel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    availability_status: Mapped[str] = mapped_column(
        String(30), default="unknown", nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    services = relationship(
        "FacilityServiceModel", back_populates="facility", lazy="selectin"
    )
