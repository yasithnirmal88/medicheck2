from __future__ import annotations

from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class ClinicalIndicatorModel(BaseModel):
    __tablename__ = "clinical_indicators"

    body_system_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="moderate", nullable=False)
    evidence_strength: Mapped[str] = mapped_column(String(5), default="C", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    positive_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    negative_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    neutral_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    related_disease_ids: Mapped[list | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    related_symptom_ids: Mapped[list | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False, index=True
    )
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
