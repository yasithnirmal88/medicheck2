from __future__ import annotations

from datetime import date, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PersonalInfoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str
    date_of_birth: date | None = None
    sex: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    blood_group: str | None = None
    nationality: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    preferred_language: str | None = None
    emergency_contact: dict | None = None
    occupation: str | None = None
    industry: str | None = None
    education_level: str | None = None
    marital_status: str | None = None
    children_count: int | None = None


class HealthProfileDTO(BaseModel):
    id: str
    user_id: str
    draft: bool
    # The ORM column is named `profile_metadata` (the model attribute `metadata`
    # resolves to SQLAlchemy's MetaData object). Read the right attribute while
    # keeping the public API field name `metadata`.
    metadata: dict | None = Field(
        default=None, validation_alias=AliasChoices("profile_metadata", "metadata")
    )
    personal_info: PersonalInfoDTO | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
