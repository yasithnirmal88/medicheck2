from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class QuestionModel(BaseModel):
    __tablename__ = "questions"

    body_system_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("body_systems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_group_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("question_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tooltip: Mapped[str | None] = mapped_column(String(500), nullable=True)
    medical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="basic", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_rules: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    scoring_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    activation_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expiration_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    options = relationship(
        "QuestionOptionModel", back_populates="question", lazy="selectin"
    )
    group = relationship("QuestionGroupModel", back_populates="questions")
    dependencies = relationship(
        "QuestionDependencyModel",
        back_populates="question",
        lazy="selectin",
        foreign_keys="QuestionDependencyModel.question_id",
    )
