from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class FamilyHistoryModel(BaseModel):
    __tablename__ = "family_histories"

    profile_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("health_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relative: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # mother/father/sibling/grandparent/child
    disease: Mapped[str] = mapped_column(String(255), nullable=False)
    age_at_diagnosis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile = relationship("HealthProfileModel", back_populates="family_histories")
