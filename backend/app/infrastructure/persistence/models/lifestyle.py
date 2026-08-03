from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class LifestyleModel(BaseModel):
    __tablename__ = "lifestyles"

    profile_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("health_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    smoking: Mapped[str | None] = mapped_column(String(50), nullable=True)
    alcohol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    water_intake_l_per_day: Mapped[float | None] = mapped_column(Integer, nullable=True)
    daily_walking_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_daily_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exercise_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exercise_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sleep_duration_hours: Mapped[float | None] = mapped_column(Integer, nullable=True)
    sleep_quality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stress_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    working_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    working_style: Mapped[str | None] = mapped_column(String(50), nullable=True)
    remote_office: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sitting_hours: Mapped[float | None] = mapped_column(Integer, nullable=True)
    transportation_method: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    physical_activity_level: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    profile = relationship("HealthProfileModel", back_populates="lifestyle")
