from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class QuestionIndicatorLinkModel(BaseModel):
    __tablename__ = "question_indicator_links"

    question_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    indicator_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class QuestionOptionIndicatorLinkModel(BaseModel):
    __tablename__ = "question_option_indicator_links"

    question_option_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    indicator_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class IndicatorConditionLinkModel(BaseModel):
    __tablename__ = "indicator_condition_links"

    indicator_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    condition_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class IndicatorEvidenceLinkModel(BaseModel):
    __tablename__ = "indicator_evidence_links"

    indicator_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    evidence_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class IndicatorRecommendationLinkModel(BaseModel):
    __tablename__ = "indicator_recommendation_links"

    indicator_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    recommendation_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ConditionRecommendationLinkModel(BaseModel):
    __tablename__ = "condition_recommendation_links"

    condition_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    recommendation_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ConditionLaboratoryTestLinkModel(BaseModel):
    __tablename__ = "condition_laboratory_test_links"

    condition_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    laboratory_test_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class BodySystemConditionLinkModel(BaseModel):
    __tablename__ = "body_system_condition_links"

    body_system_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    condition_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
