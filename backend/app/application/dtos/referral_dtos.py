"""Phase 9 — Referral & care follow-up DTOs.

These contracts are the ONLY data that crosses into/out of the referral
endpoints. They exclude access tokens, unrelated patient records, and any
field not needed for care navigation. The deterministic CDSE/recommendation
remain the source of truth; the referral layer only navigates, tracks, and
audits. AI navigation explanations use ``ReferralNavigationContext`` (no PHI).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ── Enums (mirrored as Literals for strict validation) ─────────────────

ReferralType = Literal[
    "primary_care",
    "specialist",
    "laboratory",
    "imaging",
    "preventive_screening",
    "follow_up_assessment",
    "emergency_care",
]

ReferralStatus = Literal[
    "pending",
    "acknowledged",
    "scheduled",
    "attended",
    "completed",
    "declined",
    "unable_to_access",
    "cancelled",
]

BarrierType = Literal[
    "transportation",
    "cost",
    "distance",
    "language",
    "appointment_unavailable",
    "connectivity",
    "caregiver_constraint",
    "work_schedule",
    "accessibility",
    "other",
]

ActorRole = Literal["patient", "chw", "doctor", "admin", "system"]


# ── Referral ───────────────────────────────────────────────────────────


class ReferralResponse(BaseModel):
    id: str
    patient_user_id: str
    originating_session_id: str
    originating_report_id: str | None = None
    trace_id: str | None = None
    recommendation_id: str
    recommendation_title: str | None = None
    recommendation_category: str | None = None
    recommendation_urgency: str | None = None
    referral_type: ReferralType
    status: ReferralStatus
    due_at: datetime | None = None
    assigned_chw_user_id: str | None = None
    patient_acknowledged: bool = False
    notes: str | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReferralListResponse(BaseModel):
    items: list[ReferralResponse]
    total: int


class ReferralStatusEventResponse(BaseModel):
    id: str
    from_status: str | None
    to_status: ReferralStatus
    actor_user_id: str
    actor_role: ActorRole
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReferralDetailResponse(ReferralResponse):
    status_events: list[ReferralStatusEventResponse] = []
    barriers: list["BarrierResponse"] = []
    follow_up_tasks: list["FollowUpTaskResponse"] = []


# ── Actions ────────────────────────────────────────────────────────────


class AcknowledgeRequest(BaseModel):
    notes: str | None = None


class ScheduleRequest(BaseModel):
    scheduled_for: datetime | None = None
    notes: str | None = None


class StatusUpdateRequest(BaseModel):
    status: ReferralStatus
    reason: str | None = None


class BarrierRequest(BaseModel):
    barrier_type: BarrierType
    detail: str | None = None


class BarrierResponse(BaseModel):
    id: str
    referral_id: str
    barrier_type: BarrierType
    recorded_by_user_id: str
    recorded_by_role: ActorRole
    detail: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Follow-up tasks ────────────────────────────────────────────────────


FollowUpTaskStatus = Literal["pending", "in_progress", "completed", "cancelled"]


class FollowUpTaskResponse(BaseModel):
    id: str
    referral_id: str
    patient_user_id: str
    assigned_chw_user_id: str | None = None
    task_type: str
    title: str
    due_at: datetime | None = None
    status: FollowUpTaskStatus
    completed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowUpTaskListResponse(BaseModel):
    items: list[FollowUpTaskResponse]
    total: int


class CompleteTaskRequest(BaseModel):
    notes: str | None = None


# ── AI navigation explanation ──────────────────────────────────────────


class ReferralExplanationRequest(BaseModel):
    language: str = Field(default="en", description="en, si, or ta")
    literacy_level: Literal["simple", "standard", "detailed"] = "standard"


class ReferralExplanationResponse(BaseModel):
    available: bool
    explanation: str | None = None
    summary: str | None = None
    next_steps: list[str] = []
    referenced_recommendation_id: str | None = None
    referenced_evidence_ids: list[str] = []
    transparency_notice: str | None = None
    quality_status: str = "valid"

    model_config = {"from_attributes": True}


ReferralDetailResponse.model_rebuild()
