from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class AssessmentResultModel(BaseModel):
    __tablename__ = "assessment_results"

    session_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    activated_indicators = relationship(
        "ActivatedIndicatorModel", back_populates="result", lazy="selectin"
    )
    activated_conditions = relationship(
        "ActivatedConditionModel", back_populates="result", lazy="selectin"
    )
    generated_recommendations = relationship(
        "GeneratedRecommendationModel", back_populates="result", lazy="selectin"
    )
    generated_laboratory_tests = relationship(
        "GeneratedLaboratoryTestModel", back_populates="result", lazy="selectin"
    )
    generated_screenings = relationship(
        "GeneratedScreeningModel", back_populates="result", lazy="selectin"
    )
    explanations = relationship(
        "ExplanationRecordModel", back_populates="result", lazy="selectin"
    )


class ActivatedIndicatorModel(BaseModel):
    __tablename__ = "activated_indicators"

    result_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("assessment_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    indicator_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    result = relationship(
        "AssessmentResultModel", back_populates="activated_indicators"
    )


class ActivatedConditionModel(BaseModel):
    __tablename__ = "activated_conditions"

    result_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("assessment_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    condition_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    result = relationship(
        "AssessmentResultModel", back_populates="activated_conditions"
    )


class GeneratedRecommendationModel(BaseModel):
    __tablename__ = "generated_recommendations"

    result_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("assessment_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    result = relationship(
        "AssessmentResultModel", back_populates="generated_recommendations"
    )


class GeneratedLaboratoryTestModel(BaseModel):
    __tablename__ = "generated_laboratory_tests"

    result_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("assessment_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    laboratory_test_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    result = relationship(
        "AssessmentResultModel", back_populates="generated_laboratory_tests"
    )


class GeneratedScreeningModel(BaseModel):
    __tablename__ = "generated_screenings"

    result_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("assessment_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    result = relationship(
        "AssessmentResultModel", back_populates="generated_screenings"
    )


class ExplanationRecordModel(BaseModel):
    __tablename__ = "explanation_records"

    result_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("assessment_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # answer, indicator, condition
    source_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    result = relationship("AssessmentResultModel", back_populates="explanations")
