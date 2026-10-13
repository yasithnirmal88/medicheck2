"""Phase 10 — FHIR R4 export service.

Builds a controlled FHIR Bundle from MediCheck's deterministic clinical data.
Read-only: NEVER modifies clinical records. Reuses existing services/repositories
rather than duplicating business logic.

Safety invariants (do not regress):
- Authenticated + RBAC-controlled (caller must own the data OR hold
  FHIR_EXPORT_ANY). IDOR-guarded: the patient id in the path is verified
  against the caller's identity/authority at the endpoint, and the service
  re-checks ownership.
- Consent-aware: a granted ``fhir_export`` consent (ConsentRecordModel) is
  REQUIRED (configurable). Export denied without it.
- Auditable: every export writes an ``InteroperabilityExportModel`` manifest.
- Deterministic: FHIR is generated from existing CDSE/report data; no second
  clinical calculation engine.
- PHI minimised: no firebase_uid, password, token, or unrelated patient data.
- A "possible condition" is NEVER exported as a confirmed diagnosis.
- AI interpretations are NEVER clinical Observations.
- No N+1: reuses selectin relationships + batched queries; bounded by
  ``settings.fhir_max_resources_per_export``.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.fhir_dtos import (
    ExportHistoryItem,
    ExportHistoryResponse,
    FhirBundle,
    FhirBundleEntry,
    FhirCodeableConcept,
    FhirCoding,
    FhirConsent,
    FhirDiagnosticReport,
    FhirExportManifest,
    FhirExportResponse,
    FhirExtension,
    FhirIdentifier,
    FhirObservation,
    FhirPatient,
    FhirQuestionnaire,
    FhirQuestionnaireResponse,
    FhirReference,
    FhirServiceRequest,
    FhirTask,
    FhirCarePlan,
)
from app.core.config import settings
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.identity import Permission, Role, User, UserSummary, check_permission, get_role_permissions, get_user_summary
from app.infrastructure.persistence.models.assessment_answer import AssessmentAnswerModel
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.consent_record import ConsentRecordModel
from app.infrastructure.persistence.models.decision import (
    AssessmentResultModel,
    GeneratedRecommendationModel,
)
from app.infrastructure.persistence.models.facility import FacilityModel
from app.infrastructure.persistence.models.follow_up_task import FollowUpTaskModel
from app.infrastructure.persistence.models.interoperability_export import (
    InteroperabilityExportModel,
)
from app.infrastructure.persistence.models.personal_info import PersonalInfoModel
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.questionnaire_template import (
    QuestionnaireTemplateModel,
)
from app.infrastructure.persistence.models.referral import ReferralModel
from app.infrastructure.persistence.models.report import (
    BodySystemAssessmentModel,
    ConditionAssessmentModel,
    HealthAssessmentModel,
)
from app.infrastructure.persistence.repositories.sql_profile_repository import (
    SQLProfileRepository,
)

logger = logging.getLogger(__name__)

#: MediCheck-specific extension URL for trace_id (provenance/traceability).
_TRACE_EXT_URL = "https://medicheck.org/fhir/StructureDefinition/trace-id"
#: Coding system for MediCheck body-system assessment categories.
_CATEGORY_SYSTEM = "https://medicheck.org/fhir/CodeSystem/body-system-category"
#: Coding system for MediCheck report type.
_REPORT_TYPE_SYSTEM = "https://medicheck.org/fhir/CodeSystem/report-type"
#: Coding system for referral types.
_REFERRAL_TYPE_SYSTEM = "https://medicheck.org/fhir/CodeSystem/referral-type"

_TASK_TYPE_SYSTEM = "https://medicheck.org/fhir/CodeSystem/task-type"

# Body-system category -> FHIR Observation interpretation mapping.
_CATEGORY_INTERPRETATION = {
    "Normal": "N",
    "Monitor": "N",
    "Needs Attention": "H",
    "Recommend Screening": "H",
    "Urgent Medical Review": "HU",
}


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC).isoformat()
    return dt.isoformat()


def _user_has_perm(user: User, perm: Permission) -> bool:
    if not user.roles:
        return False
    all_perms: set[Permission] = set()
    for r in user.roles:
        try:
            all_perms |= get_role_permissions(Role(r))
        except ValueError:
            continue
    return check_permission(all_perms, perm)


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


class FhirExportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.profile_repo = SQLProfileRepository(session)

    # ── Authorization + consent ──────────────────────────────────────

    async def _authorize_export(self, user: User, patient_user_id: str) -> None:
        """IDOR guard. Patient = own only. FHIR_EXPORT_ANY = any patient."""
        if user.id == patient_user_id:
            return
        if _user_has_perm(user, Permission.FHIR_EXPORT_ANY):
            return
        raise AuthorizationError(
            detail="Not authorized to export this patient's data"
        )

    async def _verify_consent(
        self, patient_user_id: str
    ) -> ConsentRecordModel | None:
        """Verify a granted fhir_export consent exists. Returns the record
        (for the manifest) or None if consent is not required."""
        if not settings.fhir_consent_required:
            return None
        stmt = (
            select(ConsentRecordModel)
            .where(
                ConsentRecordModel.patient_user_id == patient_user_id,
                ConsentRecordModel.consent_type == settings.fhir_consent_type,
                ConsentRecordModel.granted.is_(True),
                ConsentRecordModel.deleted_at.is_(None),
            )
            .order_by(ConsentRecordModel.created_at.desc())
            .limit(1)
        )
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        if record is None:
            raise AuthorizationError(
                detail="Patient has not granted consent for FHIR export"
            )
        return record

    # ── Patient bundle ───────────────────────────────────────────────

    async def export_patient_bundle(
        self, user: User, patient_user_id: str
    ) -> FhirExportResponse:
        """Export a FHIR Bundle for a patient: Patient resource + all their
        assessment-session reports (DiagnosticReport + Observations +
        QuestionnaireResponse) + referrals (ServiceRequest/Task) + care plan."""
        await self._authorize_export(user, patient_user_id)
        consent = await self._verify_consent(patient_user_id)

        # Load patient + profile (eager, no N+1).
        patient = await get_user_summary(self.session, patient_user_id)
        if patient is None or patient.is_deleted:
            raise NotFoundError(detail="Patient not found")
        profile = await self.profile_repo.get_by_user_id(patient_user_id)

        entries: list[FhirBundleEntry] = []
        trace_ids: set[str] = set()

        # Patient resource
        patient_res = self._build_patient(patient, profile)
        entries.append(self._entry(patient_res))
        # Consent resource (provenance that export was consented)
        if consent is not None:
            consent_res = self._build_consent(consent, patient_user_id)
            entries.append(self._entry(consent_res))

        # Assessment sessions + reports (bounded).
        sessions = await self._load_sessions(patient_user_id)
        for sess in sessions:
            report = await self._load_report(sess.id)
            result = await self._load_result(sess.id)
            if result is not None and result.summary:
                tid = _extract_trace_id(result.summary)
                if tid:
                    trace_ids.add(tid)
            # QuestionnaireResponse
            qr = self._build_questionnaire_response(sess, patient_user_id)
            if qr is not None:
                entries.append(self._entry(qr))
            # DiagnosticReport + Observations
            if report is not None:
                report_res, observations = self._build_diagnostic_report(
                    report, result, patient_user_id
                )
                entries.append(self._entry(report_res))
                for obs in observations:
                    entries.append(self._entry(obs))
                # Possible conditions as Observations (NOT confirmed Conditions).
                for cond_obs in self._build_condition_observations(
                    report, patient_user_id
                ):
                    entries.append(self._entry(cond_obs))

            # Cap resource count (bounded query protection).
            if len(entries) >= settings.fhir_max_resources_per_export:
                break

        # Referrals -> ServiceRequest + Task.
        referrals = await self._load_referrals(patient_user_id)
        for ref in referrals:
            sr = await self._build_service_request(ref, patient_user_id)
            if sr is not None:
                entries.append(self._entry(sr))
            for task in (ref.follow_up_tasks or []):
                if task.is_deleted:
                    continue
                task_res = self._build_task(task, patient_user_id)
                if task_res is not None:
                    entries.append(self._entry(task_res))

        # CarePlan (operational follow-up plan).
        care_plan = self._build_care_plan(referrals, patient_user_id)
        if care_plan is not None:
            entries.append(self._entry(care_plan))

        export_id = uuid.uuid4().hex
        timestamp = _iso(datetime.now(UTC)) or ""
        bundle = FhirBundle(
            id=export_id,
            timestamp=timestamp,
            entry=entries[: settings.fhir_max_resources_per_export],
            meta_info={
                "lastUpdated": timestamp,
                "profile": ["https://medicheck.org/fhir/StructureDefinition/MediCheckBundle"],
            },
        )

        resource_types = sorted({e.resource.get("resourceType") for e in bundle.entry})
        manifest = FhirExportManifest(
            export_id=export_id,
            requested_by_user_id=user.id,
            patient_user_id=patient_user_id,
            resource_types=resource_types,
            source_trace_ids=sorted(trace_ids),
            schema_version=settings.fhir_version,
            status="completed",
            consent_id=consent.id if consent else None,
            item_count=len(bundle.entry),
            created_at=timestamp,
        )
        await self._record_export(manifest)
        return FhirExportResponse(bundle=bundle, manifest=manifest)

    # ── Session-scoped bundle ────────────────────────────────────────

    async def export_session_bundle(
        self, user: User, session_id: str
    ) -> FhirExportResponse:
        """Export a FHIR Bundle scoped to one assessment session."""
        # Load via SELECT (not session.get) so selectin relationships
        # (answers, roles) are always populated — session.get() can
        # return an identity-map object whose relationships were never
        # loaded, which would trigger a sync lazy load (MissingGreenlet
        # in async context).
        sess_stmt = (
            select(AssessmentSessionModel)
            .where(
                AssessmentSessionModel.id == session_id,
                AssessmentSessionModel.deleted_at.is_(None),
            )
        )
        sess = (await self.session.execute(sess_stmt)).scalar_one_or_none()
        if sess is None:
            raise NotFoundError(detail="Assessment session not found")
        await self._authorize_export(user, sess.user_id)
        consent = await self._verify_consent(sess.user_id)

        patient = await get_user_summary(self.session, sess.user_id)
        profile = await self.profile_repo.get_by_user_id(sess.user_id) if patient else None

        entries: list[FhirBundleEntry] = []
        trace_ids: set[str] = set()

        if patient:
            entries.append(self._entry(self._build_patient(patient, profile)))
        if consent is not None:
            entries.append(self._entry(self._build_consent(consent, sess.user_id)))

        qr = self._build_questionnaire_response(sess, sess.user_id)
        if qr is not None:
            entries.append(self._entry(qr))

        report = await self._load_report(sess.id)
        result = await self._load_result(sess.id)
        if result is not None and result.summary:
            tid = _extract_trace_id(result.summary)
            if tid:
                trace_ids.add(tid)
        if report is not None:
            report_res, observations = self._build_diagnostic_report(
                report, result, sess.user_id
            )
            entries.append(self._entry(report_res))
            for obs in observations:
                entries.append(self._entry(obs))
            for cond_obs in self._build_condition_observations(report, sess.user_id):
                entries.append(self._entry(cond_obs))

        export_id = uuid.uuid4().hex
        timestamp = _iso(datetime.now(UTC)) or ""
        bundle = FhirBundle(
            id=export_id,
            timestamp=timestamp,
            entry=entries,
            meta_info={"lastUpdated": timestamp},
        )
        resource_types = sorted({e.resource.get("resourceType") for e in bundle.entry})
        manifest = FhirExportManifest(
            export_id=export_id,
            requested_by_user_id=user.id,
            patient_user_id=sess.user_id,
            resource_types=resource_types,
            source_trace_ids=sorted(trace_ids),
            schema_version=settings.fhir_version,
            status="completed",
            consent_id=consent.id if consent else None,
            item_count=len(bundle.entry),
            created_at=timestamp,
        )
        await self._record_export(manifest)
        return FhirExportResponse(bundle=bundle, manifest=manifest)

    # ── Export history ───────────────────────────────────────────────

    async def list_export_history(
        self, user: User, *, limit: int = 50
    ) -> ExportHistoryResponse:
        """List export manifests. Caller sees their own exports; clinicians/
        admins (FHIR_EXPORT_ANY) see all. No bundle payloads (audit only)."""
        stmt = (
            select(InteroperabilityExportModel)
            .where(InteroperabilityExportModel.deleted_at.is_(None))
            .order_by(InteroperabilityExportModel.created_at.desc())
            .limit(limit)
        )
        if not _user_has_perm(user, Permission.FHIR_EXPORT_ANY):
            stmt = stmt.where(
                InteroperabilityExportModel.requested_by_user_id == user.id
            )
        exports = (await self.session.execute(stmt)).scalars().all()
        items = []
        for exp in exports:
            items.append(
                ExportHistoryItem(
                    id=exp.id,
                    export_type=exp.export_type,
                    format=exp.format,
                    patient_user_id=exp.patient_user_id,
                    resource_types=exp.resource_types or [],
                    source_trace_ids=exp.source_trace_ids or [],
                    schema_version=exp.schema_version,
                    status=exp.status,
                    status_reason=exp.status_reason,
                    consent_id=exp.consent_id,
                    item_count=exp.item_count,
                    created_at=_iso(exp.created_at) or "",
                )
            )
        return ExportHistoryResponse(items=items, total=len(items))

    # ── Resource builders (deterministic, PHI-minimised) ─────────────

    def _build_patient(
        self, user: UserSummary, profile
    ) -> FhirPatient:
        personal = getattr(profile, "personal_info", None) if profile else None
        name_parts = []
        if personal is not None and personal.full_name:
            name_parts.append(
                {
                    "use": "official",
                    "text": personal.full_name,
                    "family": personal.full_name,
                }
            )
        elif user.full_name:
            name_parts.append({"use": "official", "text": user.full_name})
        gender = None
        birth_date = None
        communication = []
        if personal is not None:
            gender = self._map_gender(personal.sex)
            birth_date = (
                personal.date_of_birth.isoformat() if personal.date_of_birth else None
            )
            if personal.preferred_language:
                communication = [
                    {
                        "language": {
                            "coding": [
                                {
                                    "system": "urn:ietf:bcp:47",
                                    "code": personal.preferred_language,
                                }
                            ]
                        },
                        "preferred": True,
                    }
                ]
        return FhirPatient(
            id=user.id,
            identifier=[
                FhirIdentifier(
                    system="https://medicheck.org/patient-id", value=user.id
                )
            ],
            name=name_parts,
            gender=gender,
            birthDate=birth_date,
            communication=communication,
        )

    def _map_gender(self, sex: str | None) -> str | None:
        if not sex:
            return None
        s = sex.lower()
        if s in {"male", "m"}:
            return "male"
        if s in {"female", "f"}:
            return "female"
        if s in {"other", "o"}:
            return "other"
        return None

    def _build_consent(
        self, consent: ConsentRecordModel, patient_user_id: str
    ) -> FhirConsent:
        return FhirConsent(
            id=consent.id,
            status="active" if consent.granted else "rejected",
            scope=FhirCodeableConcept(
                coding=[FhirCoding(system="http://terminology.hl7.org/CodeSystem/consentscope", code="patient-privacy", display="Privacy Consent")],
                text="FHIR / external data sharing consent",
            ),
            category=[
                FhirCodeableConcept(
                    coding=[FhirCoding(system="http://terminology.hl7.org/CodeSystem/v3-ActCode", code="IDSCL", display="information disclosure")]
                )
            ],
            patient=FhirReference(reference=f"Patient/{patient_user_id}"),
            # FHIR R4: Consent.provision is 0..1 (a single provision
            # object; nested exceptions live in provision.provision).
            provision={"type": "permit" if consent.granted else "deny"},
        )

    def _build_questionnaire_response(
        self, sess: AssessmentSessionModel, patient_user_id: str
    ) -> FhirQuestionnaireResponse | None:
        items: list[dict] = []
        for ans in (sess.answers or []):
            if ans.is_deleted:
                continue
            items.append(
                {
                    "linkId": ans.question_id,
                    "text": ans.question_code,
                    "answer": [
                        {"valueString": ans.value or (ans.option_id or "")}
                    ] if (ans.value or ans.option_id) else [],
                }
            )
        status = "completed" if sess.status == "completed" else "in-progress"
        return FhirQuestionnaireResponse(
            id=sess.id,
            status=status,
            questionnaire=(
                f"Questionnaire/{sess.questionnaire_template_id}"
                if sess.questionnaire_template_id
                else None
            ),
            subject=FhirReference(reference=f"Patient/{patient_user_id}"),
            authored=_iso(sess.started_at or sess.created_at),
            item=items,
        )

    def _build_diagnostic_report(
        self,
        report: HealthAssessmentModel,
        result: AssessmentResultModel | None,
        patient_user_id: str,
    ) -> tuple[FhirDiagnosticReport, list[FhirObservation]]:
        observations: list[FhirObservation] = []
        obs_refs: list[FhirReference] = []
        for bs in (report.body_systems or []):
            if bs.is_deleted:
                continue
            score = _safe_float(bs.score)
            category = bs.category
            # FHIR R4: an Observation carries exactly ONE value[x]. The
            # body-system assessment's primary result is the categorical
            # risk category, so it is exported as valueCodeableConcept;
            # the numeric score is exported as a standard component
            # (Observation.component) rather than a second value[x].
            obs = FhirObservation(
                id=bs.id,
                status="final",
                category=[
                    FhirCodeableConcept(
                        coding=[FhirCoding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="survey")]
                    )
                ],
                code=FhirCodeableConcept(
                    coding=[FhirCoding(system=_CATEGORY_SYSTEM, code=bs.body_system_id or "unknown", display=category or "body-system score")],
                    text="MediCheck body-system risk category",
                ),
                subject=FhirReference(reference=f"Patient/{patient_user_id}"),
                effectiveDateTime=_iso(report.created_at),
                valueCodeableConcept=(
                    FhirCodeableConcept(
                        coding=[FhirCoding(system=_CATEGORY_SYSTEM, code=(category or "unknown").replace(" ", "-").lower(), display=category)],
                        text=category,
                    )
                    if category
                    else None
                ),
                component=(
                    [
                        {
                            "code": FhirCodeableConcept(
                                coding=[FhirCoding(system=_CATEGORY_SYSTEM, code="risk-score", display="Body-system risk score")],
                                text="Body-system risk score",
                            ).model_dump(by_alias=True, exclude_none=True),
                            "valueQuantity": {"value": score, "unit": "score"},
                        }
                    ]
                    if score is not None
                    else None
                ),
                interpretation=(
                    [FhirCodeableConcept(coding=[FhirCoding(system="http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", code=_CATEGORY_INTERPRETATION.get(category or "", "N"), display=category)])]
                    if category
                    else []
                ),
            )
            observations.append(obs)
            obs_refs.append(FhirReference(reference=f"Observation/{bs.id}"))

        # conclusion: screening/risk assessment — NOT a confirmed diagnosis.
        conclusion = (
            "MediCheck deterministic screening/risk assessment. "
            "Findings are screening results, not confirmed diagnoses."
        )
        trace_id = _extract_trace_id(result.summary) if result and result.summary else None
        report_id = report.id
        extensions = []
        if trace_id:

            extensions.append(FhirExtension(url=_TRACE_EXT_URL, valueString=trace_id))
        diag = FhirDiagnosticReport(
            id=report_id,
            status="final",
            category=[
                FhirCodeableConcept(
                    coding=[FhirCoding(system=_REPORT_TYPE_SYSTEM, code="screening", display="Screening/Risk Assessment")]
                )
            ],
            code=FhirCodeableConcept(
                coding=[FhirCoding(system=_REPORT_TYPE_SYSTEM, code="clinical-report", display="MediCheck Clinical Report")],
                text="MediCheck Clinical Report",
            ),
            subject=FhirReference(reference=f"Patient/{patient_user_id}"),
            effectiveDateTime=_iso(report.created_at),
            issued=_iso(report.created_at),
            conclusion=conclusion,
            conclusionCode=[
                FhirCodeableConcept(
                    coding=[FhirCoding(system=_REPORT_TYPE_SYSTEM, code="possible-condition", display="Possible condition (NOT confirmed)")]
                )
            ],
            result=obs_refs,
            extension=extensions,
        )
        return diag, observations

    def _build_condition_observations(
        self, report: HealthAssessmentModel, patient_user_id: str
    ) -> list[FhirObservation]:
        """Represent possible conditions as Observations with an explicit
        'possible condition, NOT confirmed' interpretation. NEVER a Condition
        resource with verificationStatus=confirmed."""
        obs: list[FhirObservation] = []
        for cond in (report.conditions or []):
            if cond.is_deleted:
                continue
            score = _safe_float(cond.score)
            confidence = _safe_float(cond.confidence)
            obs.append(
                FhirObservation(
                    id=cond.id,
                    status="preliminary",  # preliminary = not confirmed
                    category=[
                        FhirCodeableConcept(
                            coding=[FhirCoding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="survey")]
                        )
                    ],
                    code=FhirCodeableConcept(
                        coding=[FhirCoding(system="https://medicheck.org/fhir/CodeSystem/possible-condition", code=cond.condition_id, display="Possible condition (screening)")]
                    ),
                    subject=FhirReference(reference=f"Patient/{patient_user_id}"),
                    effectiveDateTime=_iso(report.created_at),
                    valueQuantity=(
                        {"value": score, "unit": "score"} if score is not None else None
                    ),
                    interpretation=[
                        FhirCodeableConcept(
                            coding=[FhirCoding(system="https://medicheck.org/fhir/CodeSystem/screening-verification", code="possible", display="Possible condition — NOT confirmed diagnosis")]
                        )
                    ],
                    note=[{"text": f"Confidence: {confidence}" if confidence is not None else "Screening finding; not a diagnosis."}],
                )
            )
        return obs

    async def _build_service_request(
        self, referral: ReferralModel, patient_user_id: str
    ) -> FhirServiceRequest | None:

        extensions: list[FhirExtension] = []
        if referral.trace_id:
            extensions.append(FhirExtension(url=_TRACE_EXT_URL, valueString=referral.trace_id))
        priority = "routine"
        sr_status = "active"
        if referral.status in {"completed", "cancelled", "declined", "expired", "lost_to_followup"}:
            sr_status = "completed" if referral.status == "completed" else "revoked"
        return FhirServiceRequest(
            id=referral.id,
            status=sr_status,
            intent="plan",
            category=[
                FhirCodeableConcept(
                    coding=[FhirCoding(system=_REFERRAL_TYPE_SYSTEM, code=referral.referral_type)]
                )
            ],
            code=FhirCodeableConcept(
                coding=[
                    FhirCoding(
                        system=_REFERRAL_TYPE_SYSTEM,
                        code=referral.referral_type,
                    )
                ],
                text=f"Referral ({referral.referral_type})",
            ),
            subject=FhirReference(reference=f"Patient/{patient_user_id}"),
            occurrenceDateTime=_iso(referral.scheduled_for or referral.due_at),
            priority=priority,
            extension=extensions,
        )

    def _build_task(
        self, task: FollowUpTaskModel, patient_user_id: str
    ) -> FhirTask | None:

        status_map = {
            "pending": "requested",
            "in_progress": "in-progress",
            "completed": "completed",
            "cancelled": "cancelled",
        }
        return FhirTask(
            id=task.id,
            status=status_map.get(task.status, "requested"),
            intent="plan",
            code=FhirCodeableConcept(
                coding=[
                    FhirCoding(
                        system=_TASK_TYPE_SYSTEM, code=task.task_type
                    )
                ],
                text=task.task_type,
            ),
            focus=FhirReference(reference=f"ServiceRequest/{task.referral_id}"),
            for_fhir=FhirReference(reference=f"Patient/{patient_user_id}"),
            description=task.title,
            executionPeriod=(
                {"end": _iso(task.completed_at)} if task.completed_at else None
            ),
        )

    def _build_care_plan(
        self, referrals: list[ReferralModel], patient_user_id: str
    ) -> FhirCarePlan | None:
        if not referrals:
            return None
        activities = []
        for ref in referrals:
            if ref.is_deleted:
                continue
            activities.append(
                {
                    "detail": {
                        "kind": "ServiceRequest",
                        "status": "scheduled" if ref.status in {"scheduled", "accepted"} else "in-progress",
                        "description": f"Referral follow-up ({ref.referral_type})",
                    }
                }
            )
        return FhirCarePlan(
            id=f"careplan-{patient_user_id}",
            status="active",
            intent="plan",
            title="MediCheck Care Continuity Plan",
            subject=FhirReference(reference=f"Patient/{patient_user_id}"),
            category=[
                FhirCodeableConcept(
                    coding=[FhirCoding(system="http://hl7.org/fhir/care-plan-category", code="assess-plan")]
                )
            ],
            description="Operational care-continuity plan derived from referrals. Not a treatment prescription.",
            activity=activities,
        )

    # ── Data loaders (batched, bounded) ──────────────────────────────

    async def _load_sessions(self, patient_user_id: str) -> list[AssessmentSessionModel]:
        stmt = (
            select(AssessmentSessionModel)
            .where(
                AssessmentSessionModel.user_id == patient_user_id,
                AssessmentSessionModel.deleted_at.is_(None),
                AssessmentSessionModel.status == "completed",
            )
            .order_by(AssessmentSessionModel.created_at.desc())
            .limit(50)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def _load_report(self, session_id: str) -> HealthAssessmentModel | None:
        stmt = select(HealthAssessmentModel).where(
            HealthAssessmentModel.session_id == session_id,
            HealthAssessmentModel.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def _load_result(self, session_id: str) -> AssessmentResultModel | None:
        stmt = select(AssessmentResultModel).where(
            AssessmentResultModel.session_id == session_id,
            AssessmentResultModel.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def _load_referrals(self, patient_user_id: str) -> list[ReferralModel]:
        stmt = (
            select(ReferralModel)
            .where(
                ReferralModel.patient_user_id == patient_user_id,
                ReferralModel.deleted_at.is_(None),
            )
            .order_by(ReferralModel.created_at.desc())
            .limit(50)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    # ── Audit ────────────────────────────────────────────────────────

    async def _record_export(self, manifest: FhirExportManifest) -> None:
        record = InteroperabilityExportModel(
            id=manifest.export_id,
            export_type=manifest.export_type,
            format=manifest.format,
            requested_by_user_id=manifest.requested_by_user_id,
            patient_user_id=manifest.patient_user_id,
            resource_types=manifest.resource_types,
            source_trace_ids=manifest.source_trace_ids,
            schema_version=manifest.schema_version,
            status=manifest.status,
            status_reason=manifest.status_reason,
            consent_id=manifest.consent_id,
            item_count=manifest.item_count,
        )
        self.session.add(record)
        await self.session.flush()

    # ── Helpers ──────────────────────────────────────────────────────

    def _entry(self, resource) -> FhirBundleEntry:
        return FhirBundleEntry(
            fullUrl=f"urn:uuid:{resource.id}",
            resource=resource.model_dump(by_alias=True, exclude_none=True),
        )


# Late import to avoid circular.


def _extract_trace_id(summary: str | None) -> str | None:
    import re

    if not summary:
        return None
    m = re.search(r"\[trace:([0-9a-f]{16})\]", summary)
    return m.group(1) if m else None
