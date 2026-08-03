from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class AssessmentAnswerModel(BaseModel):
    __tablename__ = "assessment_answers"

    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    question_code: Mapped[str] = mapped_column(String(100), nullable=False)
    option_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    numeric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    response_value: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    score_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    time_taken_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    branch_path: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    session = relationship("AssessmentSessionModel", back_populates="answers")
