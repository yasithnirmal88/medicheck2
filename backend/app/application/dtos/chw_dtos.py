"""Phase 8 — Community Health Worker + offline sync DTOs.

These contracts are the ONLY data that crosses into/out of the CHW and
offline-sync endpoints. They deliberately exclude access tokens, CMS
content, and any field a CHW does not need. The deterministic CDSE remains
the source of truth; the CHW/sync layer only collects, validates, and
synchronizes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Patient lookup / assignment ─────────────────────────────────────────


class AssignedPatient(BaseModel):
    """A patient the CHW is authorized to assist."""

    user_id: str
    full_name: str
    email: str | None = None
    assignment_status: str = "active"
    has_active_session: bool = False
    last_assisted_at: datetime | None = None

    model_config = {"from_attributes": True}


class AssignedPatientsResponse(BaseModel):
    items: list[AssignedPatient]
    total: int


# ── Consent ────────────────────────────────────────────────────────────


class ConsentRequest(BaseModel):
    """Record patient consent before a CHW assessment.

    Consent is attested by the CHW (``attested_by="chw"``) on the patient's
    behalf. We do NOT store a verbatim signature or biometric — only the fact
    of consent, scope, language, and consent-text version.
    """

    patient_user_id: str
    consent_type: str = Field(
        default="assessment_assist",
        description="The scope of consent being granted.",
    )
    language: str = Field(default="en", description="en, si, or ta")
    consent_text_version: str = Field(
        default="v1",
        description="Version of the consent text that was presented.",
    )
    granted: bool = True


class ConsentResponse(BaseModel):
    consent_id: str
    patient_user_id: str
    chw_user_id: str | None
    consent_type: str
    language: str
    granted: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Offline content cache ──────────────────────────────────────────────


class CachedQuestionOption(BaseModel):
    id: str
    code: str
    text: str
    value: str
    score_value: float
    severity: str = "none"
    display_order: int = 0
    color_hex: str | None = None

    model_config = {"from_attributes": True}


class CachedQuestion(BaseModel):
    id: str
    code: str
    text: str
    question_type: str
    description: str | None = None
    tooltip: str | None = None
    is_required: bool = False
    validation_rules: dict[str, Any] = {}
    priority: int = 3
    difficulty: str = "basic"
    order_index: int = 0
    options: list[CachedQuestionOption] = []

    model_config = {"from_attributes": True}


class CachedQuestionGroup(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None
    display_order: int = 0
    questions: list[CachedQuestion] = []

    model_config = {"from_attributes": True}


class CachedTemplate(BaseModel):
    """A versioned, offline-cacheable questionnaire bundle.

    Only published (active) templates with their groups/questions/options are
    included. The ``content_version`` anchors reproducibility: an offline
    assessment completed against v12 stays v12 even after the server updates
    to v13 — the sync uses the original version.
    """

    id: str
    code: str
    name: str
    description: str | None = None
    body_system_id: str | None = None
    target_audience: str = "all"
    estimated_time_minutes: int = 10
    content_version: int
    cached_at: datetime
    groups: list[CachedQuestionGroup] = []

    model_config = {"from_attributes": True}


class OfflineContentBundleResponse(BaseModel):
    """Response for GET /chw/offline-content/{template_id}."""

    template: CachedTemplate
    server_content_version: int
    update_available: bool = False

    model_config = {"from_attributes": True}


class OfflineContentListResponse(BaseModel):
    """Response for GET /chw/offline-content — list of cacheable templates."""

    templates: list[CachedTemplate]
    total: int


# ── Sync engine ────────────────────────────────────────────────────────


SyncStatus = Literal[
    "draft",
    "offline",
    "ready_to_sync",
    "syncing",
    "synced",
    "sync_failed",
    "completed",
]


class OfflineAnswerItem(BaseModel):
    """A single answer collected offline, to be synced."""

    question_id: str
    question_code: str = ""
    question_version: int = 1
    response_value: dict[str, Any]
    is_skipped: bool = False
    time_taken_seconds: int = 0


class SyncPackageRequest(BaseModel):
    """The offline sync package.

    The ``idempotency_key`` is the deduplication anchor: a repeated sync with
    the same key is a no-op. The CHW never needs to remember whether a sync
    succeeded — the server remembers for them.
    """

    idempotency_key: str = Field(..., min_length=8, max_length=64)
    patient_user_id: str
    template_id: str | None = None
    content_version: int = 1
    language: str = "en"
    input_type: str = "text"
    answers: list[OfflineAnswerItem] = Field(default_factory=list)
    device_id: str | None = None
    consent_id: str | None = None


class SyncResultResponse(BaseModel):
    """Result of a sync operation."""

    idempotency_key: str
    sync_status: SyncStatus
    session_id: str | None = None
    report_id: str | None = None
    already_synced: bool = False
    error_category: str | None = None
    message: str = ""

    model_config = {"from_attributes": True}


# ── CHW dashboard ──────────────────────────────────────────────────────


class ChwSessionSummary(BaseModel):
    """A session summary visible on the CHW dashboard."""

    session_id: str
    patient_user_id: str
    patient_name: str
    template_name: str | None = None
    content_version: int = 1
    status: str
    sync_status: str | None = None
    language: str = "en"
    chw_assisted: bool = True
    offline: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_attempt_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChwDashboardResponse(BaseModel):
    todays_assessments: list[ChwSessionSummary]
    drafts: list[ChwSessionSummary]
    waiting_to_sync: list[ChwSessionSummary]
    completed: list[ChwSessionSummary]
    sync_errors: list[ChwSessionSummary]
    assigned_patients: list[AssignedPatient]
    totals: dict[str, int]


# ── Device registration ────────────────────────────────────────────────


class DeviceRegistrationRequest(BaseModel):
    device_label: str = Field(..., min_length=1, max_length=100)
    device_fingerprint: str = Field(..., min_length=8, max_length=64)


class DeviceRegistrationResponse(BaseModel):
    device_id: str
    device_label: str
    status: str = "active"

    model_config = {"from_attributes": True}


# ── QR handoff ─────────────────────────────────────────────────────────


class QrHandoffRequest(BaseModel):
    """Generate a short-lived opaque QR handoff token.

    The token contains NO PHI — it is an opaque reference the patient scans to
    review/consent. The actual session stays server-side behind auth.
    """

    session_id: str | None = None
    patient_user_id: str | None = None
    ttl_seconds: int = Field(default=300, ge=30, le=900)


class QrHandoffResponse(BaseModel):
    token: str
    expires_at: datetime
