from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CMSEntityCreate(BaseModel):
    body_system_id: str | None = None
    disease_id: str | None = None
    icd10_code: str | None = None
    code: str | None = None
    key: str | None = None
    name: str | None = None
    title: str | None = None
    text: str | None = None
    description: str | None = None
    summary: str | None = None
    details: str | None = None
    category: str | None = None
    severity: str | None = "moderate"
    evidence_level: str | None = "C"
    evidence_strength: str | None = "C"
    confidence: float | None = 0.5
    positive_weight: float | None = 1.0
    negative_weight: float | None = 0.0
    neutral_weight: float | None = 0.0
    priority: int | None = 5
    urgency: str | None = "routine"
    duration_rule: str | None = None
    loinc_code: str | None = None
    normal_range: str | None = None
    unit: str | None = None
    reference_range_min: float | None = None
    reference_range_max: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    modality: str | None = "X-ray"
    is_contrast_required: bool | None = False
    preparation_notes: str | None = None
    source: str | None = None
    source_type: str | None = "journal"
    doi: str | None = None
    pmid: str | None = None
    url: str | None = None
    authors: list[str] | None = None
    publication_year: int | None = None
    risk_factors: list[str] | None = None
    early_indicators: list[str] | None = None
    related_disease_ids: list[str] | None = None
    related_symptom_ids: list[str] | None = None
    indicator_ids: list[str] | None = None
    disease_ids: list[str] | None = None
    contraindications: list[str] | None = None
    dietary_restrictions: list[str] | None = None
    meal_type: str | None = None
    duration_minutes: int | None = 30
    frequency_per_week: int | None = 3
    intensity: str | None = "moderate"
    tags: list[str] | None = None
    is_active: bool | None = True
    status: str | None = "draft"
    extra: dict[str, Any] | None = None


class CMSEntityUpdate(BaseModel):
    body_system_id: str | None = None
    disease_id: str | None = None
    icd10_code: str | None = None
    code: str | None = None
    key: str | None = None
    name: str | None = None
    title: str | None = None
    text: str | None = None
    description: str | None = None
    summary: str | None = None
    details: str | None = None
    category: str | None = None
    severity: str | None = None
    evidence_level: str | None = None
    evidence_strength: str | None = None
    confidence: float | None = None
    positive_weight: float | None = None
    negative_weight: float | None = None
    neutral_weight: float | None = None
    priority: int | None = None
    urgency: str | None = None
    duration_rule: str | None = None
    loinc_code: str | None = None
    normal_range: str | None = None
    unit: str | None = None
    reference_range_min: float | None = None
    reference_range_max: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    modality: str | None = None
    is_contrast_required: bool | None = None
    preparation_notes: str | None = None
    source: str | None = None
    source_type: str | None = None
    doi: str | None = None
    pmid: str | None = None
    url: str | None = None
    authors: list[str] | None = None
    publication_year: int | None = None
    risk_factors: list[str] | None = None
    early_indicators: list[str] | None = None
    related_disease_ids: list[str] | None = None
    related_symptom_ids: list[str] | None = None
    indicator_ids: list[str] | None = None
    disease_ids: list[str] | None = None
    contraindications: list[str] | None = None
    dietary_restrictions: list[str] | None = None
    meal_type: str | None = None
    duration_minutes: int | None = None
    frequency_per_week: int | None = None
    intensity: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None
    status: str | None = None
    extra: dict[str, Any] | None = None


class CMSStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(draft|medical_review|approved|published|archived)$")


class CMSEntityResponse(BaseModel):
    id: str
    entity_type: str
    data: dict[str, Any]
    version: int
    status: str
    created_by: str | None
    updated_by: str | None
    created_at: datetime
    updated_at: datetime
