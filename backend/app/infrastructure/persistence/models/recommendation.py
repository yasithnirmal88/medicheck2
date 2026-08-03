from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class RecommendationModel(BaseModel):
    __tablename__ = "recommendations"

    key: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    body_system_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    disease_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False, index=True)
    urgency: Mapped[str] = mapped_column(
        String(20), default="routine", nullable=False
    )
    evidence_level: Mapped[str] = mapped_column(String(5), default="C", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False, index=True
    )
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
