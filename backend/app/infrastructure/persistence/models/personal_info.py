from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class PersonalInfoModel(BaseModel):
    __tablename__ = "personal_infos"

    profile_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("health_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(16), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    blood_group: Mapped[str | None] = mapped_column(String(10), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    emergency_contact: Mapped[dict | None] = mapped_column(Text, nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(150), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    children_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    profile = relationship("HealthProfileModel", back_populates="personal_info")
