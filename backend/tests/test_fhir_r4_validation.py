"""FHIR R4 export — structural validation + clinical mapping tests.

Generates real FHIR payloads from FhirExportService (seeded with
deterministic test data) and validates every resource against the
FHIR R4 structural rules (app.application.services.fhir_validation):
required elements, Observation.value[x] exactly-one, enum value
sets, Reference/CodeableConcept/Identifier formats, extension
namespacing, and the safety invariant that possible conditions are
NEVER exported as confirmed Condition resources.

Run:
    cd backend && ALLOW_MOCK_AUTH=true DATABASE_URL=sqlite+aiosqlite:///./test.db \
        ENVIRONMENT=development python -m pytest tests/test_fhir_r4_validation.py -q
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.application.services.fhir_export_service import FhirExportService
from app.application.services.fhir_validation import (
    validate_fhir_bundle,
    validate_fhir_resource,
)
from app.core.security.rbac import Role
from app.domain.entities.user import User
from app.infrastructure.persistence.models.assessment_answer import (
    AssessmentAnswerModel,
)
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.consent_record import ConsentRecordModel
from app.infrastructure.persistence.models.decision import AssessmentResultModel
from app.infrastructure.persistence.models.facility import FacilityModel
from app.infrastructure.persistence.models.follow_up_task import FollowUpTaskModel
from app.infrastructure.persistence.models.health_profile import HealthProfileModel
from app.infrastructure.persistence.models.personal_info import PersonalInfoModel
from app.infrastructure.persistence.models.referral import ReferralModel
from app.infrastructure.persistence.models.report import (
    BodySystemAssessmentModel,
    ConditionAssessmentModel,
    HealthAssessmentModel,
)
from app.infrastructure.persistence.models.user import UserModel

# Reuse the deterministic seeders from the Phase 10 suite.
from tests.test_interoperability_phase10 import (
    _create_user_model,
    _seed_completed_session,
    _seed_consent,
    _seed_profile,
    _user,
)


@pytest.fixture
def patient_user():
    uid = uuid.uuid4().hex
    return _user(uid, roles={Role.PATIENT.value})


async def _seed_referral(db, patient_id: str, session_id: str) -> ReferralModel:
    facility = FacilityModel(
        id=uuid.uuid4().hex,
        code=f"FAC-{uuid.uuid4().hex[:6]}",
        name="City General Hospital",
        service_type="primary_care",
        region="Western",
        availability_status="available",
        is_active=True,
    )
    db.add(facility)
    await db.flush()
    referral = ReferralModel(
        id=uuid.uuid4().hex,
        patient_user_id=patient_id,
        facility_id=facility.id,
        referral_type="specialist",
        status="scheduled",
        notes="Cardiology follow-up",
        due_at=datetime.now(UTC) + timedelta(days=7),
        scheduled_for=datetime.now(UTC) + timedelta(days=7),
        trace_id=uuid.uuid4().hex[:16],
        originating_session_id=session_id,
        recommendation_id=uuid.uuid4().hex,
    )
    db.add(referral)
    await db.flush()
    db.add(FollowUpTaskModel(
        id=uuid.uuid4().hex,
        referral_id=referral.id,
        patient_user_id=patient_id,
        task_type="appointment_scheduling",
        title="Schedule cardiology appointment",
        status="pending",
        due_at=datetime.now(UTC) + timedelta(days=3),
    ))
    await db.flush()
    return referral


def _entries(resp) -> list[dict]:
    return [e.resource for e in resp.bundle.entry]


def _by_type(entries: list[dict], rtype: str) -> list[dict]:
    return [e for e in entries if e.get("resourceType") == rtype]


# =====================================================================
# STRUCTURAL VALIDATION (every resource, both bundle shapes)
# =====================================================================


class TestFhirR4StructuralValidation:
    @pytest.mark.asyncio
    async def test_patient_bundle_is_valid_r4(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_profile(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id, trace_id="abc123def456a789")
        await _seed_consent(db_session, patient_user.id)
        await _seed_referral(db_session, patient_user.id, sess.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)

        errors = validate_fhir_bundle(resp.bundle.model_dump(by_alias=True, exclude_none=True))
        assert errors == [], f"FHIR R4 validation errors: {errors}"

    @pytest.mark.asyncio
    async def test_session_bundle_is_valid_r4(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_session_bundle(patient_user, sess.id)

        errors = validate_fhir_bundle(resp.bundle.model_dump(by_alias=True, exclude_none=True))
        assert errors == [], f"FHIR R4 validation errors: {errors}"

    @pytest.mark.asyncio
    async def test_every_resource_validates_individually(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_profile(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await _seed_referral(db_session, patient_user.id, sess.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        for entry in _entries(resp):
            errors = validate_fhir_resource(entry)
            assert errors == [], f"{entry.get('resourceType')}/{entry.get('id')}: {errors}"

    @pytest.mark.asyncio
    async def test_observation_single_value_x(self, db_session, patient_user):
        """An Observation carries exactly ONE value[x] (R4 choice constraint)."""
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        value_fields = [
            f for f in (
                "valueQuantity", "valueCodeableConcept", "valueString", "valueBoolean",
                "valueInteger", "valueDateTime", "valuePeriod", "valueRatio",
                "valueReference", "valueSampledData", "valueTime", "valueAttachment",
                "valueRange",
            )
        ]
        for obs in _by_type(_entries(resp), "Observation"):
            present = [f for f in value_fields if obs.get(f) is not None]
            assert len(present) == 1, f"Observation {obs['id']} has multiple value[x]: {present}"

    @pytest.mark.asyncio
    async def test_validator_rejects_dual_value_x(self):
        """Guard test: the validator itself must catch the classic bug of
        emitting both valueQuantity and valueString on one Observation."""
        bad = {
            "resourceType": "Observation",
            "id": "bad-obs",
            "status": "final",
            "code": {"coding": [{"system": "https://medicheck.org/fhir/CodeSystem/body-system-category", "code": "cardio"}]},
            "valueQuantity": {"value": 3.0, "unit": "score"},
            "valueString": "Needs Attention",
        }
        errors = validate_fhir_resource(bad)
        assert any("value[x]" in e for e in errors), errors

    @pytest.mark.asyncio
    async def test_validator_rejects_condition_resources(self):
        """Safety invariant: MediCheck never exports Condition resources."""
        cond = {
            "resourceType": "Condition",
            "id": "bad-condition",
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
            "code": {"coding": [{"system": "http://snomed.info/sct", "code": "38341003"}]},
            "subject": {"reference": "Patient/abc"},
        }
        errors = validate_fhir_resource(cond)
        assert any("forbidden" in e for e in errors), errors


# =====================================================================
# CLINICAL FIELD MAPPING
# =====================================================================


class TestFhirClinicalMapping:
    @pytest.mark.asyncio
    async def test_patient_demographics_mapping(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_profile(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        (patient,) = _by_type(_entries(resp), "Patient")

        assert patient["id"] == patient_user.id
        assert patient["gender"] == "female"
        # HumanName is a well-formed official name object.
        name = patient["name"][0]
        assert name["use"] == "official"
        assert name["text"] == "Test Patient"
        # Identifier uses a namespaced system.
        ident = patient["identifier"][0]
        assert ident["system"] == "https://medicheck.org/patient-id"
        assert ident["value"] == patient_user.id
        # Language communication uses BCP-47.
        comm = patient["communication"][0]
        assert comm["language"]["coding"][0]["system"] == "urn:ietf:bcp:47"
        assert comm["language"]["coding"][0]["code"] == "en"
        # PHI minimisation: no email/firebase uid.
        blob = json.dumps(patient)
        assert "@example.com" not in blob
        assert "firebase" not in blob

    @pytest.mark.asyncio
    async def test_body_system_observation_mapping(self, db_session, patient_user):
        """The categorical risk category is the Observation's single
        value[x]; the numeric score is a component."""
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        obs = [
            o for o in _by_type(_entries(resp), "Observation")
            if (o.get("valueCodeableConcept") or {}).get("text") == "Needs Attention"
        ]
        assert len(obs) == 1
        body_obs = obs[0]
        # Categorical result as the single value[x].
        vcc = body_obs["valueCodeableConcept"]
        assert vcc["coding"][0]["code"] == "needs-attention"
        assert vcc["coding"][0]["display"] == "Needs Attention"
        # Numeric score in a standard component.
        components = body_obs["component"]
        assert len(components) == 1
        assert components[0]["valueQuantity"]["value"] == 3.0
        assert components[0]["valueQuantity"]["unit"] == "score"
        # Interpretation maps the category to the standard v3 code.
        interp = body_obs["interpretation"][0]["coding"][0]
        assert interp["system"] == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
        assert interp["code"] == "H"  # High

    @pytest.mark.asyncio
    async def test_possible_condition_mapping(self, db_session, patient_user):
        """Possible conditions export as preliminary Observations with an
        explicit NOT-confirmed interpretation — never as Conditions."""
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        entries = _entries(resp)
        assert "Condition" not in {e["resourceType"] for e in entries}

        cond_obs = [
            o for o in _by_type(entries, "Observation")
            if o["status"] == "preliminary"
        ]
        assert len(cond_obs) == 1
        interp = cond_obs[0]["interpretation"][0]["coding"][0]
        assert interp["code"] == "possible"
        assert "NOT confirmed" in interp["display"]
        # Confidence is exported as a note (screening context, not a diagnosis).
        assert "Confidence: 0.6" in cond_obs[0]["note"][0]["text"]

    @pytest.mark.asyncio
    async def test_diagnostic_report_mapping(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id, trace_id="abc123def456a789")
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        (report,) = _by_type(_entries(resp), "DiagnosticReport")

        assert report["status"] == "final"
        # Screening category — NOT a confirmed diagnosis.
        assert report["category"][0]["coding"][0]["code"] == "screening"
        # Conclusion explicitly states findings are not diagnoses.
        assert "not confirmed diagnoses" in report["conclusion"].lower()
        assert report["conclusionCode"][0]["coding"][0]["code"] == "possible-condition"
        # Result references point at the exported Observations.
        obs_ids = {o["id"] for o in _by_type(_entries(resp), "Observation")}
        for ref in report["result"]:
            obs_id = ref["reference"].split("/", 1)[1]
            assert obs_id in obs_ids
        # Trace id is carried in a namespaced extension.
        trace_exts = [
            e for e in report.get("extension", [])
            if e["url"] == "https://medicheck.org/fhir/StructureDefinition/trace-id"
        ]
        assert trace_exts and trace_exts[0]["valueString"] == "abc123def456a789"

    @pytest.mark.asyncio
    async def test_questionnaire_response_mapping(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        # Seed a real answer row so the item mapping is exercised.
        answer = AssessmentAnswerModel(
            id=uuid.uuid4().hex,
            session_id=sess.id,
            question_id=uuid.uuid4().hex,
            question_version=1,
            question_code="Q-CARDIO-01",
            option_id="opt-yes",
            value="Yes",
            response_value={"option_id": "opt-yes"},
            score_value=1.0,
            is_skipped=False,
            time_taken_seconds=12,
        )
        db_session.add(answer)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        (qr,) = _by_type(_entries(resp), "QuestionnaireResponse")

        assert qr["status"] == "completed"
        assert qr["questionnaire"] == f"Questionnaire/{sess.questionnaire_template_id}"
        assert qr["subject"]["reference"] == f"Patient/{patient_user.id}"
        assert qr["item"][0]["linkId"] == answer.question_id
        assert qr["item"][0]["text"] == "Q-CARDIO-01"
        assert qr["item"][0]["answer"][0]["valueString"] == "Yes"

    @pytest.mark.asyncio
    async def test_consent_resource_mapping(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        consent = await _seed_consent(db_session, patient_user.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        (consent_res,) = _by_type(_entries(resp), "Consent")

        assert consent_res["id"] == consent.id
        assert consent_res["status"] == "active"
        # Standard R4 consent scope code system.
        assert consent_res["scope"]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/consentscope"
        assert consent_res["scope"]["coding"][0]["code"] == "patient-privacy"
        assert consent_res["patient"]["reference"] == f"Patient/{patient_user.id}"
        # R4: provision is a single object with permit/deny type.
        assert consent_res["provision"]["type"] == "permit"

    @pytest.mark.asyncio
    async def test_service_request_and_task_mapping(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await _seed_referral(db_session, patient_user.id, sess.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        entries = _entries(resp)

        (sr,) = _by_type(entries, "ServiceRequest")
        assert sr["status"] == "active"
        assert sr["intent"] == "plan"
        assert sr["subject"]["reference"] == f"Patient/{patient_user.id}"
        assert sr["priority"] == "routine"
        # Referral trace id carried in the namespaced extension.
        assert any(
            e["url"] == "https://medicheck.org/fhir/StructureDefinition/trace-id"
            for e in sr.get("extension", [])
        )

        (task,) = _by_type(entries, "Task")
        assert task["status"] == "requested"
        assert task["intent"] == "plan"
        assert task["focus"]["reference"] == f"ServiceRequest/{sr['id']}"
        assert task["for"]["reference"] == f"Patient/{patient_user.id}"

    @pytest.mark.asyncio
    async def test_care_plan_mapping(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await _seed_referral(db_session, patient_user.id, sess.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        (care_plan,) = _by_type(_entries(resp), "CarePlan")

        assert care_plan["status"] == "active"
        assert care_plan["intent"] == "plan"
        assert care_plan["subject"]["reference"] == f"Patient/{patient_user.id}"
        assert care_plan["activity"][0]["detail"]["kind"] == "ServiceRequest"

    @pytest.mark.asyncio
    async def test_bundle_structure(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        bundle = resp.bundle.model_dump(by_alias=True, exclude_none=True)

        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "collection"
        assert bundle["timestamp"]
        for entry in bundle["entry"]:
            assert entry["fullUrl"].startswith("urn:uuid:")
            assert entry["resource"]["resourceType"]


# =====================================================================
# SAFETY / PRIVACY INVARIANTS
# =====================================================================


class TestFhirSafetyInvariants:
    @pytest.mark.asyncio
    async def test_no_phi_leakage(self, db_session, patient_user):
        await _create_user_model(db_session, patient_user.id)
        await _seed_profile(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        blob = json.dumps(resp.bundle.model_dump(), default=str)
        for forbidden in ("firebase", "password", "token", "secret", "api_key", "Authorization"):
            assert forbidden.lower() not in blob.lower(), f"leaked: {forbidden}"

    @pytest.mark.asyncio
    async def test_no_confirmed_diagnosis_claim(self, db_session, patient_user):
        """The conclusion and all condition-related codings must never
        assert a confirmed diagnosis."""
        await _create_user_model(db_session, patient_user.id)
        await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        blob = json.dumps(_entries(resp)).lower()
        assert "confirmed diagnosis" not in blob.replace("not confirmed diagnosis", "")

    @pytest.mark.asyncio
    async def test_extension_namespacing(self, db_session, patient_user):
        """Every extension URL is absolute and namespaced under
        https://medicheck.org/fhir/StructureDefinition/."""
        await _create_user_model(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await _seed_referral(db_session, patient_user.id, sess.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        for entry in _entries(resp):
            for ext in entry.get("extension", []):
                assert ext["url"].startswith("https://medicheck.org/fhir/StructureDefinition/")

    @pytest.mark.asyncio
    async def test_references_resolve_within_bundle(self, db_session, patient_user):
        """Every internal reference (Patient/..., Observation/...)
        points at a resource actually present in the bundle."""
        await _create_user_model(db_session, patient_user.id)
        await _seed_profile(db_session, patient_user.id)
        sess = await _seed_completed_session(db_session, patient_user.id)
        await _seed_consent(db_session, patient_user.id)
        await _seed_referral(db_session, patient_user.id, sess.id)
        await db_session.commit()

        svc = FhirExportService(db_session)
        resp = await svc.export_patient_bundle(patient_user, patient_user.id)
        entries = _entries(resp)
        present = {f"{e['resourceType']}/{e['id']}" for e in entries}

        def _check_ref(ref: str) -> None:
            target = ref.split("/", 1)
            assert len(target) == 2
            assert ref in present, f"dangling reference: {ref}"

        for entry in entries:
            for key in ("subject", "patient", "focus", "for"):
                if isinstance(entry.get(key), dict):
                    _check_ref(entry[key]["reference"])
            for ref in entry.get("result", []):
                _check_ref(ref["reference"])
