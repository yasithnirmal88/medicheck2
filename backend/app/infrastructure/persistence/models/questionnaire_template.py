from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class QuestionnaireTemplateModel(BaseModel):
    __tablename__ = "questionnaire_templates"

    code: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_system_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    target_audience: Mapped[str] = mapped_column(
        String(30), default="all", nullable=False
    )
    estimated_time_minutes: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True, default=dict)
