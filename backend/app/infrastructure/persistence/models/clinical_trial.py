from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class ClinicalTrialModel(BaseModel):
    __tablename__ = "clinical_trials"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    nct_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="registered", nullable=False)
    conditions: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    interventions: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    sponsor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enrollment: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    results: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
