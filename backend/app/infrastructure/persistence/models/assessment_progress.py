from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class AssessmentProgressModel(BaseModel):
    __tablename__ = "assessment_progress"

    session_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    current_section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    completed_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    answered_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_time_remaining: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    completion_percentage: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
