"""Phase 10 — FHIR R4 export DTOs.

These DTOs model a minimal, controlled subset of FHIR R4 resources that map
naturally to MediCheck's deterministic clinical data. They are NOT a complete
FHIR implementation — only the resources MediCheck can populate faithfully
from deterministic sources.

Safety rules enforced by the DTOs + service:
- A "possible condition" is NEVER exported as a confirmed diagnosis. The
  DiagnosticReport ``conclusionCode`` uses screening/risk-assessment coding,
  and possible conditions are represented as findings, not Condition resources
  with a verificationStatus of "confirmed".
- AI-generated interpretations are NEVER represented as clinical Observations.
- Internal DB ids are reused as FHIR logical ids (stable, opaque UUIDs) but
  NO firebase_uid, password, token, or unrelated patient data is emitted.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

FhirFormat = Literal["json", "xml"]

#: FHIR R4 resource types exported by MediCheck.
FhirResourceType = Literal[
    "Patient",
    "Questionnaire",
    "QuestionnaireResponse",
    "Observation",
    "DiagnosticReport",
    "ServiceRequest",
    "Task",
    "CarePlan",
    "Consent",
    "Composition",
]


class FhirExtension(BaseModel):
    url: str
    valueString: str | None = None
    valueDateTime: str | None = None


class FhirCoding(BaseModel):
    system: str
    code: str
    display: str | None = None


class FhirCodeableConcept(BaseModel):
    coding: list[FhirCoding] = []
    text: str | None = None


class FhirReference(BaseModel):
    reference: str
    display: str | None = None


class FhirIdentifier(BaseModel):
    system: str
    value: str


class FhirResource(BaseModel):
    """Base FHIR resource. ``id`` is the FHIR logical id (opaque UUID)."""
    resourceType: str
    id: str
    meta: dict | None = None


class FhirPatient(FhirResource):
    resourceType: str = "Patient"
    identifier: list[FhirIdentifier] = []
    name: list[dict] = []
    gender: str | None = None
    birthDate: str | None = None
    communication: list[dict] = []
    # No email/phone unless explicitly consented + required. Minimal PHI.


class FhirQuestionnaire(FhirResource):
    resourceType: str = "Questionnaire"
    status: str = "active"
    title: str | None = None
    url: str | None = None
    item: list[dict] = []


class FhirQuestionnaireResponse(FhirResource):
    resourceType: str = "QuestionnaireResponse"
    status: str = "completed"
    questionnaire: str | None = None
    subject: FhirReference | None = None
    authored: str | None = None
    item: list[dict] = []


class FhirObservation(FhirResource):
    resourceType: str = "Observation"
    status: str = "final"
    category: list[FhirCodeableConcept] = []
    code: FhirCodeableConcept
    subject: FhirReference | None = None
    effectiveDateTime: str | None = None
    valueQuantity: dict | None = None
    valueCodeableConcept: FhirCodeableConcept | None = None
    valueString: str | None = None
    # Observation.component — standard way to carry supplementary
    # measured values alongside the single value[x] result.
    component: list[dict] | None = None
    interpretation: list[FhirCodeableConcept] = []
    note: list[dict] = []


class FhirDiagnosticReport(FhirResource):
    resourceType: str = "DiagnosticReport"
    status: str = "final"
    category: list[FhirCodeableConcept] = []
    code: FhirCodeableConcept
    subject: FhirReference | None = None
    effectiveDateTime: str | None = None
    issued: str | None = None
    conclusion: str | None = None
    conclusionCode: list[FhirCodeableConcept] = []
    result: list[FhirReference] = []
    presentedForm: list[dict] = []
    extension: list[FhirExtension] = []


class FhirServiceRequest(FhirResource):
    resourceType: str = "ServiceRequest"
    status: str = "active"
    intent: str = "plan"
    category: list[FhirCodeableConcept] = []
    code: FhirCodeableConcept
    subject: FhirReference | None = None
    occurrenceDateTime: str | None = None
    priority: str | None = None
    reasonCode: list[FhirCodeableConcept] = []
    note: list[dict] = []
    extension: list[FhirExtension] = []


class FhirTask(FhirResource):
    resourceType: str = "Task"
    status: str = "requested"
    intent: str = "plan"
    code: FhirCodeableConcept | None = None
    focus: FhirReference | None = None
    for_fhir: FhirReference | None = Field(default=None, alias="for")
    description: str | None = None
    executionPeriod: dict | None = None

    model_config = {"populate_by_name": True}


class FhirCarePlan(FhirResource):
    resourceType: str = "CarePlan"
    status: str = "active"
    intent: str = "plan"
    title: str | None = None
    subject: FhirReference | None = None
    category: list[FhirCodeableConcept] = []
    description: str | None = None
    activity: list[dict] = []
    note: list[dict] = []


class FhirConsent(FhirResource):
    resourceType: str = "Consent"
    status: str = "active"
    scope: FhirCodeableConcept
    category: list[FhirCodeableConcept] = []
    patient: FhirReference | None = None
    # FHIR R4: Consent.provision is 0..1 (single provision object).
    provision: dict | None = None


class FhirBundleEntry(BaseModel):
    fullUrl: str
    resource: dict
    request: dict | None = None


class FhirBundle(BaseModel):
    resourceType: str = "Bundle"
    type: str = "collection"
    id: str
    timestamp: str
    entry: list[FhirBundleEntry] = []
    # MediCheck export metadata (traceability).
    meta_info: dict = Field(default_factory=dict, alias="meta")

    model_config = {"populate_by_name": True}


class FhirExportManifest(BaseModel):
    """Manifest returned alongside/after a FHIR export (audit trail)."""
    export_id: str
    export_type: str = "fhir"
    format: str = "json"
    requested_by_user_id: str
    patient_user_id: str | None = None
    resource_types: list[str]
    source_trace_ids: list[str] = []
    schema_version: str = "4.0.1"
    status: str = "completed"
    status_reason: str | None = None
    consent_id: str | None = None
    item_count: int = 0
    created_at: str


class FhirExportResponse(BaseModel):
    bundle: FhirBundle
    manifest: FhirExportManifest
    transparency_notice: str = (
        "This export contains structured health information intended for "
        "authorized healthcare interoperability. AI assistance does not "
        "determine clinical risk or diagnosis."
    )


class ExportHistoryItem(BaseModel):
    id: str
    export_type: str
    format: str
    patient_user_id: str | None = None
    resource_types: list[str] = []
    source_trace_ids: list[str] = []
    schema_version: str
    status: str
    status_reason: str | None = None
    consent_id: str | None = None
    item_count: int = 0
    created_at: str

    model_config = {"from_attributes": True}


class ExportHistoryResponse(BaseModel):
    items: list[ExportHistoryItem]
    total: int
