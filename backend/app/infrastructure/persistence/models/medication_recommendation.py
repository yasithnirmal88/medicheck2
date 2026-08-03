from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class MedicationRecommendationModel(BaseModel):
    __tablename__ = "medication_recommendations"

    body_system_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    disease_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    drug_name: Mapped[str] = mapped_column(String(255), nullable=False)
    generic_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    drug_class: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    route: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contraindications: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    side_effects: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    interactions: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    evidence_level: Mapped[str] = mapped_column(String(5), default="C", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
