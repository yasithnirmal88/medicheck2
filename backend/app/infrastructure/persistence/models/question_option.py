from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class QuestionOptionModel(BaseModel):
    __tablename__ = "question_options"

    question_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    score_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="none", nullable=False)
    color_hex: Mapped[str | None] = mapped_column(String(7), nullable=True)
    recommendation_trigger: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_trigger: Mapped[str | None] = mapped_column(Text, nullable=True)
    medical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    question = relationship("QuestionModel", back_populates="options")
