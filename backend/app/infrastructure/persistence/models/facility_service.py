"""Phase 10 — Services offered by a facility.

Additive table. Describes the discrete services a facility can accept
referrals for (e.g. ``specialist_consult``, ``laboratory``, ``imaging``).
Operational metadata only — no clinical content.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class FacilityServiceModel(BaseModel):
    __tablename__ = "facility_services"

    facility_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("facilities.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    service_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    facility = relationship("FacilityModel", back_populates="services")
