from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class HealthAssessmentModel(BaseModel):
    __tablename__ = "health_assessments"

    session_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    body_systems = relationship(
        "BodySystemAssessmentModel", back_populates="assessment", lazy="selectin"
    )
    conditions = relationship(
        "ConditionAssessmentModel", back_populates="assessment", lazy="selectin"
    )
    lifestyle = relationship(
        "LifestyleAssessmentModel", back_populates="assessment", lazy="selectin"
    )
    advices = relationship(
        "GeneratedAdviceModel", back_populates="assessment", lazy="selectin"
    )


class BodySystemAssessmentModel(BaseModel):
    __tablename__ = "body_system_assessments"

    assessment_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("health_assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body_system_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    score: Mapped[float | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assessment = relationship("HealthAssessmentModel", back_populates="body_systems")


class ConditionAssessmentModel(BaseModel):
    __tablename__ = "condition_assessments"

    assessment_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("health_assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    condition_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assessment = relationship("HealthAssessmentModel", back_populates="conditions")


class LifestyleAssessmentModel(BaseModel):
    __tablename__ = "lifestyle_assessments"

    assessment_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("health_assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON stringified snapshot

    assessment = relationship("HealthAssessmentModel", back_populates="lifestyle")


class GeneratedAdviceModel(BaseModel):
    __tablename__ = "generated_advices"

    assessment_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("health_assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    assessment = relationship("HealthAssessmentModel", back_populates="advices")
