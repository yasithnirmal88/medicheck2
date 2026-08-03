from __future__ import annotations

from sqlalchemy import JSON, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class HealthProfileModel(BaseModel):
    __tablename__ = "health_profiles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    # Whether this profile is a draft (autosave) or published
    draft: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # JSON metadata
    profile_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    # relationships to sections (one-to-one / one-to-many)
    personal_info = relationship(
        "PersonalInfoModel", back_populates="profile", uselist=False
    )
    lifestyle = relationship("LifestyleModel", back_populates="profile", uselist=False)
    nutrition = relationship("NutritionModel", back_populates="profile", uselist=False)

    # one-to-many collections
    medical_histories = relationship(
        "MedicalHistoryModel", back_populates="profile", lazy="selectin"
    )
    medication_histories = relationship(
        "MedicationHistoryModel", back_populates="profile", lazy="selectin"
    )
    surgical_histories = relationship(
        "SurgicalHistoryModel", back_populates="profile", lazy="selectin"
    )
    family_histories = relationship(
        "FamilyHistoryModel", back_populates="profile", lazy="selectin"
    )
    allergies = relationship("AllergyModel", back_populates="profile", lazy="selectin")
    immunizations = relationship(
        "ImmunizationModel", back_populates="profile", lazy="selectin"
    )
    measurements = relationship("MeasurementModel", back_populates="profile", lazy="selectin")
    lab_reports = relationship("LabReportModel", back_populates="profile", lazy="selectin")

    __table_args__ = (Index("ix_health_profiles_user_id", "user_id"),)
