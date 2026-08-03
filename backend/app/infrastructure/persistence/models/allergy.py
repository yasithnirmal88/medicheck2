from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class AllergyModel(BaseModel):
    __tablename__ = "allergies"

    profile_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("health_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # medication/food/environmental/other
    substance: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reaction: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile = relationship("HealthProfileModel", back_populates="allergies")
