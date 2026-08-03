from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class NutritionModel(BaseModel):
    __tablename__ = "nutritions"

    profile_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("health_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    meals_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fruit_intake_per_day: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vegetable_intake_per_day: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    fast_food_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sugary_drinks_frequency: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    salt_intake: Mapped[str | None] = mapped_column(String(50), nullable=True)
    red_meat_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    processed_meat_frequency: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    fish_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dairy_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    snacks_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    coffee_cups_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tea_cups_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy_drinks_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    special_diet: Mapped[str | None] = mapped_column(String(100), nullable=True)
    food_allergies: Mapped[str | None] = mapped_column(String(255), nullable=True)

    profile = relationship("HealthProfileModel", back_populates="nutrition")
