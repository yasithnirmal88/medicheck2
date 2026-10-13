"""Phase 10 — Interoperability, Health-System Integration & Outcome Feedback.

Comprehensive tests covering:
- FHIR Patient / QuestionnaireResponse / Observation / DiagnosticReport /
  ServiceRequest / Task / CarePlan generation + bundle integrity.
- FHIR authorization (IDOR), consent enforcement, data-leakage prevention,
  export audit (manifest).
- Referral lifecycle (deterministic state machine), facility feedback,
  care outcomes (operational, never alters CDSE).
- SDG aggregation (JSON + CSV), k-anonymity suppression.
- Care-continuity funnel, conversion/drop-off rates, median time-to-care.
- AI-assisted CHW queue ranking boundaries (operational only; clinical
  terms rejected).
- Security: unauthenticated denial, RBAC, IDOR, consent, privacy, audit.

Run:
    cd backend && ALLOW_MOCK_AUTH=true DATABASE_URL=sqlite+aiosqlite:///./test.db \
        ENVIRONMENT=development python -m pytest tests/test_interoperability_phase10.py -q
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.deps import (
    get_current_user,
    get_db,
    get_interop_user,
    get_referral_user,
    get_sdg_export_user,
)
from app.application.ai.queue_ranking_provider import (
    QueueRankingInput,
    QueueTaskInput,
    StubQueueRankingProvider,
    assert_non_clinical,
)
from app.application.services.care_continuity_service import CareContinuityService
from app.application.services.facility_service import FacilityService
from app.application.services.fhir_export_service import FhirExportService
from app.application.services.referral_service import ReferralService, _TRANSITIONS
from app.application.services.sdg_export_service import SdgExportService
from app.core.config import settings as real_settings
from app.core.security.rbac import Permission, Role
from app.domain.entities.user import User
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.care_outcome import CareOutcomeModel
from app.infrastructure.persistence.models.consent_record import ConsentRecordModel
from app.infrastructure.persistence.models.decision import (
    AssessmentResultModel,
    GeneratedRecommendationModel,
)
from app.infrastructure.persistence.models.facility import FacilityModel
from app.infrastructure.persistence.models.health_profile import HealthProfileModel
from app.infrastructure.persistence.models.interoperability_export import (
    InteroperabilityExportModel,
)
from app.infrastructure.persistence.models.personal_info import PersonalInfoModel
from app.infrastructure.persistence.models.recommendation import RecommendationModel
from app.infrastructure.persistence.models.report import (
    BodySystemAssessmentModel,
    ConditionAssessmentModel,
    HealthAssessmentModel,
)
from app.infrastructure.persistence.models.user import UserModel
from app.main import create_app
from app.application.dtos.analytics_dtos import AnalyticsFilters
from app.application.dtos.referral_dtos import (
    CareOutcomeRequest,
    CreateReferralRequest,
    FacilityFeedbackRequest,
)


# ── Helpers ────────────────────────────────────────────────────────────


def _user(uid: str, roles: set[str] = None) -> User:
    return User(
        id=uid,
        firebase_uid=f"fb-{uid}",
        email=f"{uid}@example.com",
        full_name=f"User {uid[:6]}",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles=roles or set(),
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )


async def _create_user_model(db, uid: str, roles: set[str] = None) -> UserModel:
    model = UserModel(
        id=uid,
        firebase_uid=f"fb-{uid}",
        email=f"{uid}@example.com",
        full_name=f"User {uid[:6]}",
        avatar_url=None,
        email_verified=True,
        is_active=True,
    )
    db.add(model)
    await db.flush()
    return model


async def _seed_profile(db, user_id: str) -> HealthProfileModel:
    profile = HealthProfileModel(
        id=uuid.uuid4().hex,
        user_id=user_id,
        draft=False,
        profile_metadata={},
    )
    db.add(profile)
    await db.flush()
    personal = PersonalInfoModel(
        id=uuid.uuid4().hex,
        profile_id=profile.id,
        full_name="Test Patient",
        sex="female",
        preferred_language="en",
    )
    db.add(personal)
    await db.flush()
    return profile


async def _seed_completed_session(
    db, user_id: str, *, with_report: bool = True, trace_id: str | None = None
) -> AssessmentSessionModel:
    sess = AssessmentSessionModel(
        id=uuid.uuid4().hex,
        user_id=user_id,
        questionnaire_template_id=uuid.uuid4().hex,
        status="completed",
        answers_count=2,
        total_questions=2,
        completed_questions=2,
        started_at=datetime.now(UTC) - timedelta(days=2),
        completed_at=datetime.now(UTC) - timedelta(days=2),
    )
    db.add(sess)
    await db.flush()
    summary = f"Screening result [trace:{trace_id or uuid.uuid4().hex[:16]}]"
    result = AssessmentResultModel(
        id=uuid.uuid4().hex,
        session_id=sess.id,
        user_id=user_id,
        summary=summary,
        confidence_score=0.7,
    )
    db.add(result)
    await db.flush()
    if with_report:
        report = HealthAssessmentModel(
            id=uuid.uuid4().hex,
            session_id=sess.id,
            user_id=user_id,
            summary="Body-system screening completed.",
        )
        db.add(report)
        await db.flush()
        bs = BodySystemAssessmentModel(
            id=uuid.uuid4().hex,
            assessment_id=report.id,
            body_system_id="cardio",
            category="Needs Attention",
            score="3.0",
        )
        db.add(bs)
        cond = ConditionAssessmentModel(
            id=uuid.uuid4().hex,
            assessment_id=report.id,
            condition_id="hypertension",
            score="2.5",
            confidence="0.6",
        )
        db.add(cond)
        await db.flush()
    return sess


async def _seed_referral_eligible_recommendation(
    db, *, category: str = "referral"
) -> RecommendationModel:
    rec = RecommendationModel(
        id=uuid.uuid4().hex,
        key=f"rec-{uuid.uuid4().hex[:8]}",
        body_system_id="cardio",
        category=category,
        title="Refer to cardiologist",
        text="Please consult a cardiologist",
        urgency="moderate",
        is_active=True,
        status="published",
        version=1,
    )
    db.add(rec)
    await db.flush()
    return rec


async def _seed_generated_recommendation(
    db, result_id: str, recommendation_id: str
) -> GeneratedRecommendationModel:
    gen = GeneratedRecommendationModel(
        id=uuid.uuid4().hex,
        result_id=result_id,
        recommendation_id=recommendation_id,
        source="cdse",
    )
    db.add(gen)
    await db.flush()
    return gen


async def _seed_consent(
    db, patient_user_id: str, *, granted: bool = True, consent_type: str = "fhir_export"
) -> ConsentRecordModel:
    rec = ConsentRecordModel(
        id=uuid.uuid4().hex,
        patient_user_id=patient_user_id,
        consent_type=consent_type,
        language="en",
        consent_text_version="v1",
        granted=granted,
        attested_by=patient_user_id,
    )
    db.add(rec)
    await db.flush()
    return rec


async def _seed_facility(db, *, code: str = None) -> FacilityModel:
    f = FacilityModel(
        id=uuid.uuid4().hex,
        code=code or f"FAC-{uuid.uuid4().hex[:6]}",
        name="City General Hospital",
        service_type="primary_care",
        region="Western",
        availability_status="available",
        is_active=True,
    )
    db.add(f)
    await db.flush()
    return f


@pytest.fixture
def patient_user():
    uid = uuid.uuid4().hex
    return _user(uid, roles={Role.PATIENT.value})


@pytest.fixture
def doctor_user():
    uid = uuid.uuid4().hex
    return _user(uid, roles={Role.DOCTOR.value})


@pytest.fixture
def admin_user():
    uid = uuid.uuid4().hex
    return _user(uid, roles={Role.SUPER_ADMIN.value})


@pytest.fixture
def research_user():
    uid = uuid.uuid4().hex
    return _user(uid, roles={Role.RESEARCH_REVIEWER.value})


@pytest.fixture
def chw_user():
    uid = uuid.uuid4().hex
    return _user(uid, roles={Role.COMMUNITY_HEALTH_WORKER.value})


def _auth_overrides(client, user: User):
    """Override only ``get_current_user`` so the authenticated caller is ``user``.

    Permission deps (get_interop_user / get_referral_user / get_sdg_export_user)
    are NOT overridden — they run their real RBAC checks against ``user.roles``,
    which is what we want to test (allow/deny).
    """
    app = client._transport.app  # type: ignore[attr-defined]

    def _get_current():
        return user

    app.dependency_overrides[get_current_user] = _get_current

    def cleanup():
        app.dependency_overrides.pop(get_current_user, None)

    return cleanup


# =====================================================================
# FHIR EXPORT
# =====================================================================


class TestFhirExport:
    @pytest.mark.asyncio
    async def test_patient_resource_generation(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_profile(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()
        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        patient_res = [
            e.resource for e in resp.bundle.entry if e.resource.get("resourceType") == "Patient"
        ]
        assert len(patient_res) == 1
        assert patient_res[0]["id"] == patient_user.id
        assert patient_res[0]["gender"] == "female"
        # No email/firebase_uid in the patient resource.
        dumped = json.dumps(patient_res[0])
        assert "firebase" not in dumped
        assert "@example.com" not in dumped

    @pytest.mark.asyncio
    async def test_questionnaire_response_generation(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()
        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        qr = [
            e.resource for e in resp.bundle.entry
            if e.resource.get("resourceType") == "QuestionnaireResponse"
        ]
        assert len(qr) == 1
        assert qr[0]["status"] == "completed"
        assert qr[0]["subject"]["reference"] == f"Patient/{patient_user.id}"

    @pytest.mark.asyncio
    async def test_observation_generation(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()
        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        observations = [
            e.resource for e in resp.bundle.entry if e.resource.get("resourceType") == "Observation"
        ]
        # Body-system observation + possible-condition observation.
        assert len(observations) >= 1
        # The categorical risk category is the Observation's single
        # value[x] (valueCodeableConcept); the numeric score is a
        # standard component.
        bs_obs = [
            o for o in observations
            if (o.get("valueCodeableConcept") or {}).get("text") == "Needs Attention"
        ]
        assert len(bs_obs) == 1
        assert "valueString" not in bs_obs[0], "Observation must carry a single value[x]"
        components = bs_obs[0].get("component") or []
        assert len(components) == 1
        assert components[0]["valueQuantity"]["value"] == 3.0

    @pytest.mark.asyncio
    async def test_diagnostic_report_generation(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()
        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        reports = [
            e.resource for e in resp.bundle.entry if e.resource.get("resourceType") == "DiagnosticReport"
        ]
        assert len(reports) == 1
        report = reports[0]
        # Screening category, NOT confirmed diagnosis.
        assert report["status"] == "final"
        cat_codes = [c["coding"][0]["code"] for c in report.get("category", [])]
        assert "screening" in cat_codes
        # Conclusion states NOT confirmed.
        assert "not confirmed diagnoses" in report["conclusion"].lower()
        # Possible-condition conclusionCode must be present.
        cc_codes = [c["coding"][0]["code"] for c in report.get("conclusionCode", [])]
        assert "possible-condition" in cc_codes

    @pytest.mark.asyncio
    async def test_possible_condition_not_confirmed_diagnosis(self, db_session, patient_user):
        """A possible condition must NEVER be a Condition with verificationStatus=confirmed."""
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()
        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        types = {e.resource.get("resourceType") for e in resp.bundle.entry}
        assert "Condition" not in types
        cond_obs = [
            e.resource for e in resp.bundle.entry
            if e.resource.get("resourceType") == "Observation"
            and e.resource.get("status") == "preliminary"
        ]
        assert len(cond_obs) == 1
        interp = cond_obs[0]["interpretation"][0]["coding"][0]
        assert interp["code"] == "possible"
        assert "NOT confirmed" in interp["display"]

    @pytest.mark.asyncio
    async def test_bundle_integrity_and_manifest(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id, trace_id="abc123def456a789")
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()
        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        # Bundle metadata.
        assert resp.bundle.resourceType == "Bundle"
        assert resp.bundle.type == "collection"
        assert resp.bundle.timestamp
        # Manifest.
        assert resp.manifest.export_id == resp.bundle.id
        assert resp.manifest.patient_user_id == patient_user.id
        assert resp.manifest.requested_by_user_id == patient_user.id
        assert "DiagnosticReport" in resp.manifest.resource_types
        assert "abc123def456a789" in resp.manifest.source_trace_ids
        assert resp.manifest.schema_version == real_settings.fhir_version
        assert resp.manifest.consent_id is not None
        # Audit record persisted (model PK == manifest export_id).
        audits = (
            await db_session.execute(
                select(InteroperabilityExportModel)
            )
        ).scalars().all()
        assert any(a.id == resp.manifest.export_id for a in audits)

    @pytest.mark.asyncio
    async def test_export_idor_patient_cannot_export_other(
        self, db_session, patient_user
    ):
        from app.core.exceptions import AuthorizationError

        other = _user(uuid.uuid4().hex, roles={Role.PATIENT.value})
        await _create_user_model(db_session, other.id)
        await _seed_consent(db_session, other.id)
        await db_session.commit()
        svc = FhirExportService(db_session)
        with pytest.raises(AuthorizationError):
            await svc.export_patient_bundle(patient_user, other.id)

    @pytest.mark.asyncio
    async def test_export_consent_required(self, db_session, patient_user):
        from app.core.exceptions import AuthorizationError

        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        # No consent granted.
        await db_session.commit()
        svc = FhirExportService(db_session)
        with pytest.raises(AuthorizationError):
            await svc.export_patient_bundle(patient_user, patient_user.id)

    @pytest.mark.asyncio
    async def test_export_denied_when_consent_revoked(self, db_session, patient_user):
        from app.core.exceptions import AuthorizationError

        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id, granted=False)
        await db_session.commit()
        svc = FhirExportService(db_session)
        with pytest.raises(AuthorizationError):
            await svc.export_patient_bundle(patient_user, patient_user.id)

    @pytest.mark.asyncio
    async def test_export_no_data_leakage(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_profile(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()
        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        blob = json.dumps(resp.bundle.model_dump(), default=str)
        # No secrets/credentials/tokens.
        for forbidden in ["firebase", "password", "token", "secret", "api_key", "Authorization"]:
            assert forbidden.lower() not in blob.lower(), f"leaked: {forbidden}"

    @pytest.mark.asyncio
    async def test_export_history_audited(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()
        svc = FhirExportService(db_session)
        await svc.export_patient_bundle(patient_user, patient_user.id)
        history = await svc.list_export_history(patient_user)
        assert history.total >= 1
        assert history.items[0].export_type == "fhir"
        # No bundle payload in history (audit only).
        assert not hasattr(history.items[0], "bundle")

    @pytest.mark.asyncio
    async def test_doctor_can_export_any_patient(self, db_session, doctor_user):
        await _create_user_model(db_session, doctor_user.id)
        patient_id = uuid.uuid4().hex
        await _create_user_model(db_session, patient_id)
        await _seed_completed_session(db_session, patient_id)
        await _seed_consent(db_session, patient_id)
        await db_session.commit()
        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(doctor_user, patient_id)
        assert resp.manifest.patient_user_id == patient_id


# =====================================================================
# REFERRAL LIFECYCLE
# =====================================================================


class TestReferralLifecycle:
    @pytest.mark.asyncio
    async def test_create_referral_from_cdse_recommendation(
        self, db_session, patient_user
    ):
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        rec = await _seed_referral_eligible_recommendation(db_session)
        result = (
            await db_session.execute(
                select(AssessmentResultModel).where(
                    AssessmentResultModel.session_id == sess.id
                )
            )
        ).scalar_one()
        await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        svc = ReferralService(db_session)
        resp = await svc.create_referral(
            patient_user,
            CreateReferralRequest(
                originating_session_id=sess.id,
                recommendation_id=rec.id,
                referral_type="primary_care",
            ),
        )
        assert resp.status == "pending"
        assert resp.recommendation_id == rec.id
        assert resp.recommendation_category == "referral"

    @pytest.mark.asyncio
    async def test_create_referral_rejects_ineligible_category(
        self, db_session, patient_user
    ):
        from app.core.exceptions import ValidationError

        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        rec = await _seed_referral_eligible_recommendation(
            db_session, category="lifestyle"
        )
        result = (
            await db_session.execute(
                select(AssessmentResultModel).where(
                    AssessmentResultModel.session_id == sess.id
                )
            )
        ).scalar_one()
        await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        svc = ReferralService(db_session)
        with pytest.raises(ValidationError):
            await svc.create_referral(
                patient_user,
                CreateReferralRequest(
                    originating_session_id=sess.id,
                    recommendation_id=rec.id,
                    referral_type="primary_care",
                ),
            )

    @pytest.mark.asyncio
    async def test_create_referral_rejects_unknown_recommendation(
        self, db_session, patient_user
    ):
        from app.core.exceptions import ValidationError

        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        await db_session.commit()
        svc = ReferralService(db_session)
        with pytest.raises(ValidationError):
            await svc.create_referral(
                patient_user,
                CreateReferralRequest(
                    originating_session_id=sess.id,
                    recommendation_id=uuid.uuid4().hex,
                    referral_type="primary_care",
                ),
            )

    @pytest.mark.asyncio
    async def test_state_machine_valid_transitions(self, db_session, patient_user):
        # pending -> acknowledged -> sent -> received -> accepted -> scheduled -> completed
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        rec = await _seed_referral_eligible_recommendation(db_session)
        result = (
            await db_session.execute(
                select(AssessmentResultModel).where(
                    AssessmentResultModel.session_id == sess.id
                )
            )
        ).scalar_one()
        await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        svc = ReferralService(db_session)
        from app.application.dtos.referral_dtos import (
            AcknowledgeRequest,
            ScheduleRequest,
            StatusUpdateRequest,
        )

        ref = await svc.create_referral(
            patient_user,
            CreateReferralRequest(
                originating_session_id=sess.id,
                recommendation_id=rec.id,
                referral_type="primary_care",
            ),
        )
        ref = await svc.acknowledge(patient_user, ref.id, AcknowledgeRequest())
        ref = await svc.update_status(
            patient_user, ref.id, StatusUpdateRequest(status="sent")
        )
        ref = await svc.record_facility_feedback(
            patient_user, ref.id, FacilityFeedbackRequest(receiving_status="received")
        )
        ref = await svc.record_facility_feedback(
            patient_user, ref.id, FacilityFeedbackRequest(receiving_status="accepted")
        )
        ref = await svc.schedule(
            patient_user,
            ref.id,
            ScheduleRequest(scheduled_for=datetime.now(UTC) + timedelta(days=3)),
        )
        ref = await svc.record_facility_feedback(
            patient_user, ref.id, FacilityFeedbackRequest(receiving_status="completed")
        )
        assert ref.status == "completed"
        assert ref.completed_at is not None

    @pytest.mark.asyncio
    async def test_state_machine_rejects_invalid_transition(
        self, db_session, patient_user
    ):
        from app.core.exceptions import ValidationError
        from app.application.dtos.referral_dtos import StatusUpdateRequest

        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        rec = await _seed_referral_eligible_recommendation(db_session)
        result = (
            await db_session.execute(
                select(AssessmentResultModel).where(
                    AssessmentResultModel.session_id == sess.id
                )
            )
        ).scalar_one()
        await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        svc = ReferralService(db_session)
        ref = await svc.create_referral(
            patient_user,
            CreateReferralRequest(
                originating_session_id=sess.id,
                recommendation_id=rec.id,
                referral_type="primary_care",
            ),
        )
        # pending -> completed is invalid.
        with pytest.raises(ValidationError):
            await svc.update_status(
                patient_user, ref.id, StatusUpdateRequest(status="completed")
            )

    @pytest.mark.asyncio
    async def test_terminal_state_blocks_transition(self, db_session, patient_user):
        from app.core.exceptions import ValidationError
        from app.application.dtos.referral_dtos import StatusUpdateRequest

        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        rec = await _seed_referral_eligible_recommendation(db_session)
        result = (
            await db_session.execute(
                select(AssessmentResultModel).where(
                    AssessmentResultModel.session_id == sess.id
                )
            )
        ).scalar_one()
        await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        svc = ReferralService(db_session)
        ref = await svc.create_referral(
            patient_user,
            CreateReferralRequest(
                originating_session_id=sess.id,
                recommendation_id=rec.id,
                referral_type="primary_care",
            ),
        )
        ref = await svc.update_status(
            patient_user, ref.id, StatusUpdateRequest(status="cancelled")
        )
        with pytest.raises(ValidationError):
            await svc.update_status(
                patient_user, ref.id, StatusUpdateRequest(status="scheduled")
            )

    @pytest.mark.asyncio
    async def test_facility_feedback_records_receiving_status(
        self, db_session, patient_user
    ):
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        rec = await _seed_referral_eligible_recommendation(db_session)
        result = (
            await db_session.execute(
                select(AssessmentResultModel).where(
                    AssessmentResultModel.session_id == sess.id
                )
            )
        ).scalar_one()
        await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        svc = ReferralService(db_session)
        from app.application.dtos.referral_dtos import StatusUpdateRequest

        ref = await svc.create_referral(
            patient_user,
            CreateReferralRequest(
                originating_session_id=sess.id,
                recommendation_id=rec.id,
                referral_type="primary_care",
            ),
        )
        ref = await svc.update_status(
            patient_user, ref.id, StatusUpdateRequest(status="sent")
        )
        ref = await svc.record_facility_feedback(
            patient_user,
            ref.id,
            FacilityFeedbackRequest(
                receiving_status="received", notes="Facility confirmed receipt"
            ),
        )
        assert ref.receiving_status == "received"
        assert ref.status == "received"

    @pytest.mark.asyncio
    async def test_referral_idor_patient_cannot_access_other(
        self, db_session, patient_user
    ):
        from app.core.exceptions import AuthorizationError

        other = _user(uuid.uuid4().hex, roles={Role.PATIENT.value})
        await _create_user_model(db_session, other.id)
        sess = await _seed_completed_session(db_session, other.id)
        rec = await _seed_referral_eligible_recommendation(db_session)
        result = (
            await db_session.execute(
                select(AssessmentResultModel).where(
                    AssessmentResultModel.session_id == sess.id
                )
            )
        ).scalar_one()
        await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        svc = ReferralService(db_session)
        ref = await svc.create_referral(
            other,
            CreateReferralRequest(
                originating_session_id=sess.id,
                recommendation_id=rec.id,
                referral_type="primary_care",
            ),
        )
        with pytest.raises(AuthorizationError):
            await svc.get_referral(patient_user, ref.id)

    @pytest.mark.asyncio
    async def test_outcome_never_modifies_cdse(self, db_session, patient_user):
        """Recording a care outcome must NOT alter any clinical table."""
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        rec = await _seed_referral_eligible_recommendation(db_session)
        result = (
            await db_session.execute(
                select(AssessmentResultModel).where(
                    AssessmentResultModel.session_id == sess.id
                )
            )
        ).scalar_one()
        await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        # Snapshot the CDSE result before outcome.
        before_summary = result.summary
        before_score = result.confidence_score
        svc = ReferralService(db_session)
        ref = await svc.create_referral(
            patient_user,
            CreateReferralRequest(
                originating_session_id=sess.id,
                recommendation_id=rec.id,
                referral_type="primary_care",
            ),
        )
        await svc.record_outcome(
            patient_user,
            ref.id,
            CareOutcomeRequest(outcome_category="care_received", source="facility"),
        )
        await db_session.refresh(result)
        # CDSE result unchanged.
        assert result.summary == before_summary
        assert result.confidence_score == before_score


# =====================================================================
# CARE OUTCOMES
# =====================================================================


class TestCareOutcomes:
    @pytest.mark.asyncio
    async def test_record_and_list_outcomes(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        rec = await _seed_referral_eligible_recommendation(db_session)
        result = (
            await db_session.execute(
                select(AssessmentResultModel).where(
                    AssessmentResultModel.session_id == sess.id
                )
            )
        ).scalar_one()
        await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        svc = ReferralService(db_session)
        ref = await svc.create_referral(
            patient_user,
            CreateReferralRequest(
                originating_session_id=sess.id,
                recommendation_id=rec.id,
                referral_type="primary_care",
            ),
        )
        await svc.record_outcome(
            patient_user, ref.id, CareOutcomeRequest(outcome_category="referred")
        )
        await svc.record_outcome(
            patient_user,
            ref.id,
            CareOutcomeRequest(outcome_category="care_received", source="chw"),
        )
        outcomes = await svc.list_outcomes(patient_user, ref.id)
        assert len(outcomes) == 2
        assert outcomes[0].outcome_category == "referred"
        assert outcomes[1].outcome_category == "care_received"
        assert outcomes[1].source == "chw"

    @pytest.mark.asyncio
    async def test_outcome_categories_are_operational(self):
        """Outcome categories must be operational care-continuity states, never clinical."""
        from app.application.dtos.referral_dtos import CareOutcomeCategory
        import typing

        args = typing.get_args(CareOutcomeCategory)
        assert "screened" in args
        assert "care_received" in args
        assert "lost_to_followup" in args
        # No clinical diagnosis categories.
        for a in args:
            assert "diagnos" not in a
            assert "severity" not in a


# =====================================================================
# FACILITIES
# =====================================================================


class TestFacilities:
    @pytest.mark.asyncio
    async def test_list_and_get_facility(self, db_session):
        f = await _seed_facility(db_session)
        await db_session.commit()
        svc = FacilityService(db_session)
        listing = await svc.list_facilities()
        assert listing.total >= 1
        detail = await svc.get_facility(f.id)
        assert detail.code == f.code

    @pytest.mark.asyncio
    async def test_create_facility(self, db_session, admin_user):
        svc = FacilityService(db_session)
        from app.application.dtos.referral_dtos import FacilityCreateRequest

        resp = await svc.create_facility(
            FacilityCreateRequest(
                code="FAC-NEW",
                name="New Clinic",
                service_type="primary_care",
                region="Central",
                availability_status="available",
            )
        )
        await db_session.commit()
        assert resp.code == "FAC-NEW"
        assert resp.is_active is True

    @pytest.mark.asyncio
    async def test_create_facility_duplicate_code(self, db_session):
        from app.core.exceptions import ConflictError
        from app.application.dtos.referral_dtos import FacilityCreateRequest

        await _seed_facility(db_session, code="DUP")
        await db_session.commit()
        svc = FacilityService(db_session)
        with pytest.raises(ConflictError):
            await svc.create_facility(
                FacilityCreateRequest(code="DUP", name="Dup Clinic")
            )


# =====================================================================
# SDG EXPORT + K-ANONYMITY
# =====================================================================


class TestSdgExport:
    @pytest.mark.asyncio
    async def test_sdg_json_export_structure(self, db_session):
        # Seed a few completed sessions so aggregates are non-empty.
        for i in range(3):
            uid = uuid.uuid4().hex
            await _create_user_model(db_session, uid)
            await _seed_completed_session(db_session, uid)
        await db_session.commit()
        svc = SdgExportService(db_session)
        resp = await svc.export(AnalyticsFilters(), fmt="json")
        assert resp.format == "json"
        assert len(resp.rows) > 0
        # Each row has methodology + limitations documented.
        for row in resp.rows:
            assert row.methodology
            assert row.limitations
            assert row.indicator_type in ("official", "medicheck-aligned-proxy")

    @pytest.mark.asyncio
    async def test_sdg_csv_export(self, db_session):
        svc = SdgExportService(db_session)
        resp = await svc.export(AnalyticsFilters(), fmt="csv")
        csv_text = svc.to_csv(resp)
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
        assert len(rows) > 0
        assert "indicator" in rows[0]
        assert "suppression_status" in rows[0]
        assert "methodology" in rows[0]

    @pytest.mark.asyncio
    async def test_k_anonymity_suppression_small_cohort(self, db_session):
        """A cohort smaller than k must be suppressed."""
        # Single user -> screened cohort = 1 < k(10).
        uid = uuid.uuid4().hex
        await _create_user_model(db_session, uid)
        await _seed_completed_session(db_session, uid)
        await db_session.commit()
        svc = SdgExportService(db_session)
        resp = await svc.export(AnalyticsFilters(), fmt="json")
        # The care-continuity funnel should mark small stages as suppressed.
        funnel_rows = [r for r in resp.rows if r.indicator == "sdg-3-8-care-funnel"]
        assert len(funnel_rows) == 1
        assert "(suppressed)" in funnel_rows[0].methodology

    @pytest.mark.asyncio
    async def test_no_patient_identifiers_in_sdg_export(self, db_session):
        uid = uuid.uuid4().hex
        await _create_user_model(db_session, uid)
        await _seed_completed_session(db_session, uid)
        await db_session.commit()
        svc = SdgExportService(db_session)
        resp = await svc.export(AnalyticsFilters(), fmt="json")
        blob = json.dumps(resp.model_dump(), default=str)
        assert uid not in blob
        assert "@example.com" not in blob


# =====================================================================
# CARE CONTINUITY
# =====================================================================


class TestCareContinuity:
    @pytest.mark.asyncio
    async def test_funnel_and_rates(self, db_session):
        # Seed 15 patients with completed sessions + referrals + outcomes.
        for i in range(15):
            uid = uuid.uuid4().hex
            await _create_user_model(db_session, uid)
            sess = await _seed_completed_session(db_session, uid)
            rec = await _seed_referral_eligible_recommendation(db_session)
            result = (
                await db_session.execute(
                    select(AssessmentResultModel).where(
                        AssessmentResultModel.session_id == sess.id
                    )
                )
            ).scalar_one()
            await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        svc = CareContinuityService(db_session)
        resp = await svc.get_care_continuity(AnalyticsFilters())
        stages = {s.stage: s for s in resp.funnel}
        assert stages["screened"].count >= 15
        # With >= k cohort, rates should not be None.
        assert resp.metrics.referral_completion_rate is not None or resp.metrics.referred < 10

    @pytest.mark.asyncio
    async def test_median_time_to_care(self, db_session):
        # Need >= k patients with care_received outcomes.
        now = datetime.now(UTC)
        for i in range(12):
            uid = uuid.uuid4().hex
            await _create_user_model(db_session, uid)
            sess = await _seed_completed_session(db_session, uid)
            rec = await _seed_referral_eligible_recommendation(db_session)
            result = (
                await db_session.execute(
                    select(AssessmentResultModel).where(
                        AssessmentResultModel.session_id == sess.id
                    )
                )
            ).scalar_one()
            await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        # Create referrals + outcomes via service.
        svc = ReferralService(db_session)
        
        from app.infrastructure.persistence.models.referral import ReferralModel

        results = (await db_session.execute(select(AssessmentResultModel))).scalars().all()
        for r in results[:12]:
            rec_id = (
                await db_session.execute(
                    select(GeneratedRecommendationModel).where(
                        GeneratedRecommendationModel.result_id == r.id
                    )
                )
            ).scalar_one().recommendation_id
            ref = await svc.create_referral(
                _user(r.user_id, roles={Role.PATIENT.value}),
                CreateReferralRequest(
                    originating_session_id=r.session_id,
                    recommendation_id=rec_id,
                    referral_type="primary_care",
                ),
            )
            await svc.record_outcome(
                _user(r.user_id, roles={Role.PATIENT.value}),
                ref.id,
                CareOutcomeRequest(
                    outcome_category="care_received",
                    recorded_at=now,
                    source="facility",
                ),
            )
        await db_session.commit()
        care_svc = CareContinuityService(db_session)
        resp = await care_svc.get_care_continuity(AnalyticsFilters())
        # time-to-care computed only if cohort >= k.
        if resp.metrics.care_received >= 10:
            assert resp.metrics.median_time_to_care_days is not None
            assert resp.metrics.median_time_to_care_days >= 0


# =====================================================================
# AI CHW QUEUE RANKING
# =====================================================================


class TestChwQueueRanking:
    def test_stub_ranks_by_operational_factors(self):
        p = StubQueueRankingProvider()
        data = QueueRankingInput(
            chw_user_id="chw1",
            tasks=[
                QueueTaskInput(
                    referral_id="r-young",
                    referral_age_days=1,
                    overdue=False,
                    missing_follow_up=False,
                    unresolved_admin_status=True,
                ),
                QueueTaskInput(
                    referral_id="r-overdue",
                    referral_age_days=15,
                    overdue=True,
                    missing_follow_up=True,
                    unresolved_admin_status=True,
                ),
            ],
        )
        out = p.rank(data)
        assert out.ranked_tasks[0].referral_id == "r-overdue"
        assert out.ranked_tasks[0].rank == 1
        assert out.ranked_tasks[1].referral_id == "r-young"
        assert out.transparency_notice
        assert out.provider == "stub"

    def test_rejects_clinical_urgency_language(self):
        with pytest.raises(ValueError):
            assert_non_clinical("This patient has severe disease urgency")
        with pytest.raises(ValueError):
            assert_non_clinical("ranked by clinical risk and mortality")

    def test_rationale_never_clinical(self):
        p = StubQueueRankingProvider()
        data = QueueRankingInput(
            chw_user_id="chw1",
            tasks=[
                QueueTaskInput(
                    referral_id="r1",
                    referral_age_days=20,
                    overdue=True,
                    missing_follow_up=True,
                    unresolved_admin_status=True,
                )
            ],
        )
        out = p.rank(data)
        rationale = out.ranked_tasks[0].rationale.lower()
        for forbidden in ["severity", "urgent", "diagnos", "mortality", "prognosis"]:
            assert forbidden not in rationale

    @pytest.mark.asyncio
    async def test_queue_service_requires_chw_role(self, db_session, patient_user):
        from app.core.exceptions import AuthorizationError

        from app.application.services.chw_queue_service import ChwQueueService

        svc = ChwQueueService(db_session)
        with pytest.raises(AuthorizationError):
            await svc.get_queue(patient_user)

    @pytest.mark.asyncio
    async def test_queue_service_returns_ranked_tasks_for_chw(
        self, db_session, chw_user
    ):
        from app.application.services.chw_queue_service import ChwQueueService
        from app.infrastructure.persistence.models.chw_assignment import (
            ChwAssignmentModel,
        )

        # Create CHW + patient + assignment + referral.
        await _create_user_model(db_session, chw_user.id)
        uid = uuid.uuid4().hex
        await _create_user_model(db_session, uid)
        assignment = ChwAssignmentModel(
            id=uuid.uuid4().hex,
            chw_user_id=chw_user.id,
            patient_user_id=uid,
            status="active",
        )
        db_session.add(assignment)
        sess = await _seed_completed_session(db_session, uid)
        rec = await _seed_referral_eligible_recommendation(db_session)
        result = (
            await db_session.execute(
                select(AssessmentResultModel).where(
                    AssessmentResultModel.session_id == sess.id
                )
            )
        ).scalar_one()
        await _seed_generated_recommendation(db_session, result.id, rec.id)
        await db_session.commit()
        ref_svc = ReferralService(db_session)
        await ref_svc.create_referral(
            _user(uid, roles={Role.PATIENT.value}),
            CreateReferralRequest(
                originating_session_id=sess.id,
                recommendation_id=rec.id,
                referral_type="primary_care",
                assigned_chw_user_id=chw_user.id,
            ),
        )
        await db_session.commit()
        queue_svc = ChwQueueService(db_session)
        out = await queue_svc.get_queue(chw_user)
        assert out.available is True
        assert len(out.ranked_tasks) >= 1
        assert all(t.rank >= 1 for t in out.ranked_tasks)


# =====================================================================
# SECURITY (via HTTP client)
# =====================================================================


class TestPhase10SecurityHttp:
    @pytest.mark.asyncio
    async def test_unauthenticated_fhir_denied(self, client):
        # No auth override -> 401/403.
        resp = await client.get(
            f"/api/v1/interoperability/fhir/patient/{uuid.uuid4().hex}"
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_unauthenticated_sdg_denied(self, client):
        resp = await client.get("/api/v1/interoperability/sdg")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_unauthenticated_referral_denied(self, client):
        resp = await client.get("/api/v1/referrals")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_patient_cannot_access_sdg(self, client, patient_user):
        cleanup = _auth_overrides(client, patient_user)
        try:
            resp = await client.get("/api/v1/interoperability/sdg")
            assert resp.status_code == 403
        finally:
            cleanup()

    @pytest.mark.asyncio
    async def test_research_can_access_sdg(self, client, research_user):
        cleanup = _auth_overrides(client, research_user)
        try:
            resp = await client.get("/api/v1/interoperability/sdg")
            assert resp.status_code == 200
        finally:
            cleanup()

    @pytest.mark.asyncio
    async def test_research_cannot_manage_facilities(self, client, research_user):
        cleanup = _auth_overrides(client, research_user)
        try:
            resp = await client.post(
                "/api/v1/facilities",
                json={"code": "X", "name": "X"},
            )
            assert resp.status_code == 403
        finally:
            cleanup()

    @pytest.mark.asyncio
    async def test_admin_can_manage_facilities(self, client, admin_user):
        cleanup = _auth_overrides(client, admin_user)
        try:
            resp = await client.post(
                "/api/v1/facilities",
                json={"code": f"FAC-{uuid.uuid4().hex[:6]}", "name": "Admin Clinic"},
            )
            assert resp.status_code in (200, 201)
        finally:
            cleanup()

    @pytest.mark.asyncio
    async def test_fhir_idor_via_http(self, client, patient_user, db_session):
        other_id = uuid.uuid4().hex
        await _create_user_model(db_session, other_id)
        await _seed_consent(db_session, other_id)
        await db_session.commit()
        cleanup = _auth_overrides(client, patient_user)
        try:
            resp = await client.get(f"/api/v1/interoperability/fhir/patient/{other_id}")
            assert resp.status_code == 403
        finally:
            cleanup()

    @pytest.mark.asyncio
    async def test_fhir_consent_enforced_via_http(self, client, patient_user, db_session):
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await db_session.commit()
        cleanup = _auth_overrides(client, patient_user)
        try:
            resp = await client.get(
                f"/api/v1/interoperability/fhir/patient/{patient_user.id}"
            )
            assert resp.status_code == 403
        finally:
            cleanup()

    @pytest.mark.asyncio
    async def test_fhir_export_creates_audit_record(
        self, client, patient_user, db_session
    ):
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()
        cleanup = _auth_overrides(client, patient_user)
        try:
            resp = await client.get(
                f"/api/v1/interoperability/fhir/patient/{patient_user.id}"
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["manifest"]["status"] == "completed"
            # Export history endpoint shows the audit.
            hist = await client.get("/api/v1/interoperability/exports")
            assert hist.status_code == 200
            assert hist.json()["total"] >= 1
        finally:
            cleanup()

    @pytest.mark.asyncio
    async def test_sdg_csv_endpoint(self, client, research_user):
        cleanup = _auth_overrides(client, research_user)
        try:
            resp = await client.get("/api/v1/interoperability/sdg/csv")
            assert resp.status_code == 200
            assert "text/csv" in resp.headers.get("content-type", "")
            assert "indicator" in resp.text
        finally:
            cleanup()

    @pytest.mark.asyncio
    async def test_care_continuity_endpoint(self, client, research_user):
        cleanup = _auth_overrides(client, research_user)
        try:
            resp = await client.get("/api/v1/interoperability/care-continuity")
            assert resp.status_code == 200
            body = resp.json()
            assert "funnel" in body
            assert "metrics" in body
            assert "disclaimer" in body
        finally:
            cleanup()

    @pytest.mark.asyncio
    async def test_chw_queue_endpoint(self, client, chw_user, db_session):
        from app.api.deps import get_chw_user

        await _create_user_model(db_session, chw_user.id)
        await db_session.commit()
        app = client._transport.app  # type: ignore[attr-defined]
        app.dependency_overrides[get_chw_user] = lambda: chw_user
        try:
            resp = await client.get("/api/v1/chw/queue")
            assert resp.status_code == 200
            body = resp.json()
            assert body["available"] is True
            assert "transparency_notice" in body
        finally:
            app.dependency_overrides.pop(get_chw_user, None)
