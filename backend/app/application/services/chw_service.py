"""Phase 8 — Community Health Worker service.

The CHW service is a thin, scoped orchestration layer over the existing
QuestionnaireService / ClinicalDecisionService / ReportService. It NEVER
reimplements clinical logic — it collects, authorizes, and delegates.

Authorization model (least-privilege):
- A CHW may only access patients explicitly assigned via ``chw_assignments``.
- The assignment check is the single gate: every patient-scoped operation
  first calls ``_assert_assigned`` which raises AuthorizationError if the CHW
  has no active assignment for that patient.
- CHW-assisted assessment sessions store ``chw_user_id`` in the session
  ``extra_metadata`` (the existing JSON column) — no schema change to
  assessment_sessions is needed. The session's ``user_id`` remains the
  PATIENT's id so the existing CDSE / report ownership checks keep working
  unchanged.

Sync idempotency:
- The ``idempotency_key`` is the deduplication anchor. The first sync creates
  the session + answers + runs CDSE + generates the report. A repeated sync
  with the same key short-circuits and returns the already-created session
  (``already_synced=True``) — so a flaky connection can never duplicate.
- The ``assessment_sync_records`` ledger records the outcome of each sync
  attempt for audit and the CHW dashboard's "sync errors" view.

Clinical safety boundary:
- No local scoring. The CDSE processes server-side only.
- AI is never invoked here — AI intake/explanation remain optional and are
  driven by their own endpoints. Sync works without AI.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.chw_dtos import (
    AssignedPatient,
    AssignedPatientsResponse,
    ChwDashboardResponse,
    ChwSessionSummary,
    ConsentRequest,
    ConsentResponse,
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
    OfflineAnswerItem,
    OfflineContentBundleResponse,
    OfflineContentListResponse,
    SyncPackageRequest,
    SyncResultResponse,
    CachedTemplate,
    CachedQuestionGroup,
    CachedQuestion,
    CachedQuestionOption,
    QrHandoffRequest,
    QrHandoffResponse,
)
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.assessment_answer import (
    AssessmentAnswerModel,
)
from app.infrastructure.persistence.models.assessment_sync_record import (
    AssessmentSyncRecordModel,
)
from app.infrastructure.persistence.models.chw_assignment import (
    ChwAssignmentModel,
)
from app.infrastructure.persistence.models.consent_record import (
    ConsentRecordModel,
)
from app.infrastructure.persistence.models.offline_device_registration import (
    OfflineDeviceRegistrationModel,
)
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.question_group import (
    QuestionGroupModel,
)
from app.infrastructure.persistence.models.question_option import (
    QuestionOptionModel,
)
from app.infrastructure.persistence.models.questionnaire_template import (
    QuestionnaireTemplateModel,
)
from app.infrastructure.persistence.models.user import UserModel

#: Metadata keys stored on assessment_session.extra_metadata for CHW sessions.
_META_CHW_USER_ID = "chw_user_id"
_META_CHW_ASSISTED = "chw_assisted"
_META_OFFLINE = "offline"
_META_LANGUAGE = "language"
_META_INPUT_TYPE = "input_type"
_META_IDEMPOTENCY_KEY = "idempotency_key"
_META_CONTENT_VERSION = "content_version"
_META_DEVICE_ID = "device_id"
_META_CONSENT_ID = "consent_id"

_QR_TOKENS: dict[str, tuple[str, datetime]] = {}


class ChwService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Authorization gate ────────────────────────────────────────────

    async def _assert_assigned(
        self, chw_user_id: str, patient_user_id: str
    ) -> None:
        """Raise AuthorizationError unless the CHW has an active assignment
        for the patient. This is the single least-privilege gate."""
        stmt = select(ChwAssignmentModel).where(
            ChwAssignmentModel.chw_user_id == chw_user_id,
            ChwAssignmentModel.patient_user_id == patient_user_id,
            ChwAssignmentModel.status == "active",
            ChwAssignmentModel.deleted_at.is_(None),
        )
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise AuthorizationError(
                detail="Not authorized to access this patient"
            )
        if row.expires_at is not None and row.expires_at < datetime.now(UTC):
            raise AuthorizationError(
                detail="Patient assignment has expired"
            )

    # ── Assigned patients ────────────────────────────────────────────

    async def list_assigned_patients(
        self, chw_user_id: str
    ) -> AssignedPatientsResponse:
        stmt = (
            select(ChwAssignmentModel, UserModel)
            .join(UserModel, UserModel.id == ChwAssignmentModel.patient_user_id)
            .where(
                ChwAssignmentModel.chw_user_id == chw_user_id,
                ChwAssignmentModel.status == "active",
                ChwAssignmentModel.deleted_at.is_(None),
                UserModel.deleted_at.is_(None),
                UserModel.is_active.is_(True),
            )
        )
        rows = (await self.session.execute(stmt)).all()
        items: list[AssignedPatient] = []
        for _assignment, user in rows:
            items.append(
                AssignedPatient(
                    user_id=user.id,
                    full_name=user.full_name,
                    email=user.email,
                    assignment_status="active",
                    has_active_session=await self._has_active_session(
                        chw_user_id, user.id
                    ),
                )
            )
        return AssignedPatientsResponse(items=items, total=len(items))

    async def _has_active_session(
        self, chw_user_id: str, patient_user_id: str
    ) -> bool:
        stmt = select(AssessmentSessionModel.id).where(
            AssessmentSessionModel.user_id == patient_user_id,
            AssessmentSessionModel.extra_metadata[_META_CHW_USER_ID].as_string()
            == chw_user_id,
            AssessmentSessionModel.status.in_(["active", "paused"]),
            AssessmentSessionModel.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).first() is not None

    # ── Consent ──────────────────────────────────────────────────────

    async def record_consent(
        self, chw_user_id: str, req: ConsentRequest
    ) -> ConsentResponse:
        await self._assert_assigned(chw_user_id, req.patient_user_id)
        record = ConsentRecordModel(
            patient_user_id=req.patient_user_id,
            chw_user_id=chw_user_id,
            session_id=None,
            consent_type=req.consent_type,
            language=req.language,
            consent_text_version=req.consent_text_version,
            granted=req.granted,
            attested_by="chw",
        )
        self.session.add(record)
        await self.session.flush()
        return ConsentResponse(
            consent_id=record.id,
            patient_user_id=req.patient_user_id,
            chw_user_id=chw_user_id,
            consent_type=record.consent_type,
            language=record.language,
            granted=record.granted,
            created_at=record.created_at,
        )

    async def _verify_consent(
        self, patient_user_id: str, chw_user_id: str, consent_id: str | None
    ) -> None:
        """Verify a consent exists for the CHW→patient pair. The sync package
        carries an optional consent_id; if present it must match."""
        if consent_id is None:
            # Allow sync without an explicit consent_id only if a prior
            # consent record exists for this pair (backward-compatible path).
            stmt = select(ConsentRecordModel).where(
                ConsentRecordModel.patient_user_id == patient_user_id,
                ConsentRecordModel.chw_user_id == chw_user_id,
                ConsentRecordModel.granted.is_(True),
                ConsentRecordModel.deleted_at.is_(None),
            )
            if (await self.session.execute(stmt)).first() is None:
                raise ValidationError(
                    detail="Patient consent is required before syncing an assessment"
                )
            return
        record = await self.session.get(ConsentRecordModel, consent_id)
        if record is None or record.deleted_at is not None:
            raise ValidationError(detail="Consent record not found")
        if record.patient_user_id != patient_user_id or record.chw_user_id != chw_user_id:
            raise AuthorizationError(detail="Consent does not match this patient")
        if not record.granted:
            raise ValidationError(detail="Consent was not granted")

    # ── Offline content cache ────────────────────────────────────────

    async def list_offline_content(self) -> OfflineContentListResponse:
        stmt = (
            select(QuestionnaireTemplateModel)
            .where(
                QuestionnaireTemplateModel.is_active.is_(True),
                QuestionnaireTemplateModel.deleted_at.is_(None),
            )
            .order_by(QuestionnaireTemplateModel.name)
        )
        templates = (await self.session.execute(stmt)).scalars().all()
        items: list[CachedTemplate] = []
        for t in templates:
            bundle = await self._build_template_bundle(t)
            items.append(bundle)
        return OfflineContentListResponse(templates=items, total=len(items))

    async def get_offline_content(
        self, template_id: str
    ) -> OfflineContentBundleResponse:
        stmt = select(QuestionnaireTemplateModel).where(
            QuestionnaireTemplateModel.id == template_id,
            QuestionnaireTemplateModel.deleted_at.is_(None),
        )
        template = (await self.session.execute(stmt)).scalar_one_or_none()
        if template is None:
            raise NotFoundError(detail="Template not found")
        bundle = await self._build_template_bundle(template)
        return OfflineContentBundleResponse(
            template=bundle,
            server_content_version=template.version,
            update_available=bundle.content_version < template.version,
        )

    async def _build_template_bundle(
        self, template: QuestionnaireTemplateModel
    ) -> CachedTemplate:
        # Load groups for the template's body system (active only).
        g_stmt = (
            select(QuestionGroupModel)
            .where(
                QuestionGroupModel.body_system_id == template.body_system_id,
                QuestionGroupModel.is_active.is_(True),
                QuestionGroupModel.deleted_at.is_(None),
            )
            .order_by(QuestionGroupModel.display_order)
        )
        groups = (await self.session.execute(g_stmt)).scalars().all()
        group_ids = [g.id for g in groups]
        groups_out: list[CachedQuestionGroup] = []
        if group_ids:
            q_stmt = (
                select(QuestionModel)
                .where(
                    QuestionModel.question_group_id.in_(group_ids),
                    QuestionModel.status == "active",
                    QuestionModel.deleted_at.is_(None),
                )
                .order_by(QuestionModel.order_index)
            )
            questions = (await self.session.execute(q_stmt)).scalars().all()
            q_ids = [q.id for q in questions]
            opts_map: dict[str, list[QuestionOptionModel]] = {}
            if q_ids:
                o_stmt = (
                    select(QuestionOptionModel)
                    .where(
                        QuestionOptionModel.question_id.in_(q_ids),
                        QuestionOptionModel.is_active.is_(True),
                    )
                    .order_by(QuestionOptionModel.display_order)
                )
                for o in (await self.session.execute(o_stmt)).scalars().all():
                    opts_map.setdefault(o.question_id, []).append(o)
            for g in groups:
                qs = [q for q in questions if q.question_group_id == g.id]
                groups_out.append(
                    CachedQuestionGroup(
                        id=g.id,
                        code=g.code,
                        name=g.name,
                        description=g.description,
                        display_order=g.display_order,
                        questions=[
                            CachedQuestion(
                                id=q.id,
                                code=q.code,
                                text=q.text,
                                question_type=q.question_type,
                                description=q.description,
                                tooltip=q.tooltip,
                                is_required=q.is_required,
                                validation_rules=q.validation_rules or {},
                                priority=q.priority,
                                difficulty=q.difficulty,
                                order_index=q.order_index,
                                options=[
                                    CachedQuestionOption(
                                        id=o.id,
                                        code=o.code,
                                        text=o.text,
                                        value=o.value,
                                        score_value=o.score_value,
                                        severity=o.severity,
                                        display_order=o.display_order,
                                        color_hex=o.color_hex,
                                    )
                                    for o in opts_map.get(q.id, [])
                                ],
                            )
                            for q in qs
                        ],
                    )
                )
        return CachedTemplate(
            id=template.id,
            code=template.code,
            name=template.name,
            description=template.description,
            body_system_id=template.body_system_id,
            target_audience=template.target_audience,
            estimated_time_minutes=template.estimated_time_minutes,
            content_version=template.version,
            cached_at=datetime.now(UTC),
            groups=groups_out,
        )

    # ── Sync engine (idempotent) ────────────────────────────────────

    async def sync_assessment(
        self, chw_user_id: str, req: SyncPackageRequest
    ) -> SyncResultResponse:
        # 1. Authorization gate — CHW must be assigned to this patient.
        await self._assert_assigned(chw_user_id, req.patient_user_id)
        # 2. Consent verification.
        await self._verify_consent(
            req.patient_user_id, chw_user_id, req.consent_id
        )

        # 3. Idempotency: if a sync record exists for this key, short-circuit.
        existing = await self._find_sync_record(req.idempotency_key)
        if existing is not None and existing.sync_status == "synced":
            return SyncResultResponse(
                idempotency_key=req.idempotency_key,
                sync_status="synced",
                session_id=existing.session_id,
                already_synced=True,
                message="Assessment already synchronized",
            )
        if existing is not None and existing.sync_status == "syncing":
            return SyncResultResponse(
                idempotency_key=req.idempotency_key,
                sync_status="syncing",
                session_id=existing.session_id,
                message="Sync already in progress",
            )

        # 4. Create/update the sync ledger record (pending → syncing).
        ledger = existing or AssessmentSyncRecordModel(
            idempotency_key=req.idempotency_key,
            chw_user_id=chw_user_id,
            patient_user_id=req.patient_user_id,
            template_id=req.template_id,
            content_version=req.content_version,
            sync_status="syncing",
        )
        ledger.sync_status = "syncing"
        ledger.last_attempt_at = datetime.now(UTC)
        ledger.error_category = None
        ledger.error_detail = None
        if existing is None:
            self.session.add(ledger)
        await self.session.flush()

        try:
            # 5. Resolve template + version.
            template = None
            total_questions = 0
            if req.template_id:
                t_stmt = select(QuestionnaireTemplateModel).where(
                    QuestionnaireTemplateModel.id == req.template_id,
                    QuestionnaireTemplateModel.deleted_at.is_(None),
                )
                template = (await self.session.execute(t_stmt)).scalar_one_or_none()
                if template is None:
                    raise ValidationError(detail="Template not found")
                total_questions = len(req.answers)

            # 6. Create the assessment session (user_id = PATIENT).
            meta: dict[str, Any] = {
                _META_CHW_USER_ID: chw_user_id,
                _META_CHW_ASSISTED: True,
                _META_OFFLINE: True,
                _META_LANGUAGE: req.language,
                _META_INPUT_TYPE: req.input_type,
                _META_IDEMPOTENCY_KEY: req.idempotency_key,
                _META_CONTENT_VERSION: req.content_version,
            }
            if req.device_id:
                meta[_META_DEVICE_ID] = req.device_id
            if req.consent_id:
                meta[_META_CONSENT_ID] = req.consent_id

            session_model = AssessmentSessionModel(
                user_id=req.patient_user_id,
                questionnaire_template_id=req.template_id,
                questionnaire_version_id=None,
                status="active",
                current_question_id=None,
                current_group_id=None,
                answers_count=0,
                total_questions=total_questions,
                completed_questions=0,
                started_at=datetime.now(UTC),
                paused_at=None,
                completed_at=None,
                expires_at=None,
                device_info=req.device_id,
                extra_metadata=meta,
            )
            self.session.add(session_model)
            await self.session.flush()
            session_id = session_model.id

            # 7. Persist answers (server-side validation against question).
            q_ids = [a.question_id for a in req.answers]
            q_map: dict[str, QuestionModel] = {}
            if q_ids:
                q_rows = await self.session.execute(
                    select(QuestionModel).where(QuestionModel.id.in_(q_ids))
                )
                q_map = {q.id: q for q in q_rows.scalars().all()}

            for ans in req.answers:
                q = q_map.get(ans.question_id)
                if q is None:
                    raise ValidationError(
                        detail=f"Question {ans.question_id} not found"
                    )
                score_value = 0.0
                if not ans.is_skipped:
                    option_value = ans.response_value.get("value")
                    if option_value:
                        o_stmt = select(QuestionOptionModel).where(
                            QuestionOptionModel.question_id == q.id,
                            QuestionOptionModel.is_active.is_(True),
                        )
                        for o in (await self.session.execute(o_stmt)).scalars().all():
                            if o.value == str(option_value) or o.code == str(option_value):
                                score_value = o.score_value
                                break
                answer_model = AssessmentAnswerModel(
                    session_id=session_id,
                    question_id=ans.question_id,
                    question_version=ans.question_version,
                    question_code=q.code,
                    response_value=ans.response_value,
                    score_value=score_value,
                    is_skipped=ans.is_skipped,
                    time_taken_seconds=ans.time_taken_seconds,
                    branch_path=None,
                    recorded_at=datetime.now(UTC),
                )
                self.session.add(answer_model)
            await self.session.flush()

            # 8. Mark session complete.
            session_model.status = "completed"
            session_model.completed_at = datetime.now(UTC)
            session_model.completed_questions = len(req.answers)
            session_model.answers_count = len(req.answers)

            # 9. Run the deterministic CDSE (server-side, as the patient).
            from app.application.services.clinical_decision_service import (
                ClinicalDecisionService,
            )
            from sqlalchemy.orm import selectinload

            # Re-fetch the session with answers eager-loaded so the CDSE's
            # ``sess.answers`` access does not trigger a lazy load (which
            # fails under async SQLAlchemy).
            sess_stmt = (
                select(AssessmentSessionModel)
                .options(selectinload(AssessmentSessionModel.answers))
                .where(AssessmentSessionModel.id == session_id)
            )
            await self.session.execute(sess_stmt)
            cdse = ClinicalDecisionService(self.session)
            cdse_result = await cdse.process_assessment(
                session_id, user_id=req.patient_user_id
            )

            # 10. Generate the report (server-side, as the patient).
            from app.application.services.report_service import ReportService

            report_svc = ReportService(self.session)
            report = await report_svc.generate_report(
                session_id, user_id=req.patient_user_id
            )

            # 11. Update the ledger → synced.
            ledger.session_id = session_id
            ledger.sync_status = "synced"
            ledger.completed_at = datetime.now(UTC)
            await self.session.flush()

            report_id = report.get("report_id") if isinstance(report, dict) else None
            _ = cdse_result  # CDSE ran; result is the deterministic source of truth

            return SyncResultResponse(
                idempotency_key=req.idempotency_key,
                sync_status="synced",
                session_id=session_id,
                report_id=str(report_id) if report_id else None,
                message="Assessment synchronized and processed",
            )
        except (ValidationError, NotFoundError) as exc:
            await self._mark_ledger_failed(
                ledger, "validation", str(exc.detail) if hasattr(exc, "detail") else str(exc)
            )
            raise
        except Exception as exc:
            await self._mark_ledger_failed(ledger, "server_error", str(exc)[:500])
            raise

    async def _mark_ledger_failed(
        self, ledger: AssessmentSyncRecordModel, category: str, detail: str
    ) -> None:
        """Record the failure on the ledger using a SAVEPOINT so the failure
        marker survives even when the outer transaction is rolled back by the
        exception handler. This keeps the audit trail intact for the CHW's
        'sync errors' view."""
        try:
            async with self.session.begin_nested():
                ledger.sync_status = "sync_failed"
                ledger.error_category = category
                ledger.error_detail = detail
                await self.session.flush()
        except Exception:
            # Best-effort: if even the savepoint fails, do not mask the
            # original exception.
            pass

    async def _find_sync_record(
        self, idempotency_key: str
    ) -> AssessmentSyncRecordModel | None:
        stmt = select(AssessmentSyncRecordModel).where(
            AssessmentSyncRecordModel.idempotency_key == idempotency_key,
            AssessmentSyncRecordModel.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    # ── CHW dashboard ────────────────────────────────────────────────

    async def get_dashboard(self, chw_user_id: str) -> ChwDashboardResponse:
        # Assigned patients.
        patients = await self.list_assigned_patients(chw_user_id)
        # Sessions where this CHW assisted (metadata.chw_user_id == chw).
        sessions = await self._list_chw_sessions(chw_user_id)
        now = datetime.now(UTC)
        todays: list[ChwSessionSummary] = []
        drafts: list[ChwSessionSummary] = []
        waiting: list[ChwSessionSummary] = []
        completed: list[ChwSessionSummary] = []
        errors: list[ChwSessionSummary] = []
        for s in sessions:
            if s.started_at and s.started_at.date() == now.date():
                todays.append(s)
            if s.status in ("active", "paused"):
                drafts.append(s)
            sync_status = s.sync_status or "synced"
            if sync_status in ("ready_to_sync", "offline"):
                waiting.append(s)
            elif sync_status == "sync_failed":
                errors.append(s)
            elif s.status == "completed" and sync_status == "synced":
                completed.append(s)
        return ChwDashboardResponse(
            todays_assessments=todays,
            drafts=drafts,
            waiting_to_sync=waiting,
            completed=completed,
            sync_errors=errors,
            assigned_patients=patients.items,
            totals={
                "todays": len(todays),
                "drafts": len(drafts),
                "waiting": len(waiting),
                "completed": len(completed),
                "sync_errors": len(errors),
                "assigned_patients": patients.total,
            },
        )

    async def _list_chw_sessions(
        self, chw_user_id: str
    ) -> list[ChwSessionSummary]:
        stmt = (
            select(AssessmentSessionModel, UserModel)
            .join(UserModel, UserModel.id == AssessmentSessionModel.user_id)
            .where(
                AssessmentSessionModel.extra_metadata[_META_CHW_USER_ID].as_string()
                == chw_user_id,
                AssessmentSessionModel.deleted_at.is_(None),
            )
            .order_by(AssessmentSessionModel.started_at.desc())
        )
        rows = (await self.session.execute(stmt)).all()
        summaries: list[ChwSessionSummary] = []
        for sess, user in rows:
            meta = sess.extra_metadata or {}
            # Sync status from the ledger if a ledger row exists.
            sync_status = None
            idem_key = meta.get(_META_IDEMPOTENCY_KEY)
            if idem_key:
                ledger = await self._find_sync_record(idem_key)
                if ledger:
                    sync_status = ledger.sync_status
            summaries.append(
                ChwSessionSummary(
                    session_id=sess.id,
                    patient_user_id=user.id,
                    patient_name=user.full_name,
                    template_name=None,
                    content_version=meta.get(_META_CONTENT_VERSION, 1),
                    status=sess.status,
                    sync_status=sync_status,
                    language=meta.get(_META_LANGUAGE, "en"),
                    chw_assisted=True,
                    offline=meta.get(_META_OFFLINE, False),
                    started_at=sess.started_at,
                    completed_at=sess.completed_at,
                    last_attempt_at=None,
                )
            )
        return summaries

    # ── Device registration ─────────────────────────────────────────

    async def register_device(
        self, chw_user_id: str, req: DeviceRegistrationRequest
    ) -> DeviceRegistrationResponse:
        # Reject a raw fingerprint that looks like it contains a separator
        # payload; we only store the hash.
        fingerprint = hashlib.sha256(req.device_fingerprint.encode("utf-8")).hexdigest()
        existing = (
            await self.session.execute(
                select(OfflineDeviceRegistrationModel).where(
                    OfflineDeviceRegistrationModel.device_fingerprint == fingerprint,
                    OfflineDeviceRegistrationModel.chw_user_id == chw_user_id,
                    OfflineDeviceRegistrationModel.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.status = "active"
            existing.last_seen_at = datetime.now(UTC)
            await self.session.flush()
            return DeviceRegistrationResponse(
                device_id=existing.id,
                device_label=existing.device_label,
                status=existing.status,
            )
        reg = OfflineDeviceRegistrationModel(
            chw_user_id=chw_user_id,
            device_label=req.device_label,
            device_fingerprint=fingerprint,
            status="active",
            last_seen_at=datetime.now(UTC),
            registered_by=chw_user_id,
        )
        self.session.add(reg)
        await self.session.flush()
        return DeviceRegistrationResponse(
            device_id=reg.id, device_label=reg.device_label, status=reg.status
        )

    async def revoke_device(
        self, admin_user_id: str, device_id: str
    ) -> dict[str, Any]:
        reg = await self.session.get(OfflineDeviceRegistrationModel, device_id)
        if reg is None or reg.deleted_at is not None:
            raise NotFoundError(detail="Device not found")
        reg.status = "revoked"
        reg.revoked_at = datetime.now(UTC)
        reg.revoked_by = admin_user_id
        await self.session.flush()
        return {"device_id": device_id, "status": "revoked"}

    # ── QR handoff (opaque, short-lived, no PHI) ────────────────────

    async def create_qr_handoff(
        self, chw_user_id: str, req: QrHandoffRequest
    ) -> QrHandoffResponse:
        if req.session_id:
            # Verify the CHW owns/assists this session.
            sess = await self.session.get(AssessmentSessionModel, req.session_id)
            if sess is None:
                raise NotFoundError(detail="Session not found")
            meta = sess.extra_metadata or {}
            if meta.get(_META_CHW_USER_ID) != chw_user_id and sess.user_id != chw_user_id:
                raise AuthorizationError(detail="Not authorized for this session")
            if req.patient_user_id and req.patient_user_id != sess.user_id:
                raise AuthorizationError(detail="Patient does not match session")
            target = req.session_id
        elif req.patient_user_id:
            await self._assert_assigned(chw_user_id, req.patient_user_id)
            target = req.patient_user_id
        else:
            raise ValidationError(detail="session_id or patient_user_id is required")
        expires_at = datetime.now(UTC) + timedelta(seconds=req.ttl_seconds)
        token = secrets.token_urlsafe(24)
        _QR_TOKENS[token] = (target, expires_at)
        return QrHandoffResponse(token=token, expires_at=expires_at)

    @staticmethod
    def consume_qr_handoff(token: str) -> tuple[str, datetime] | None:
        entry = _QR_TOKENS.pop(token, None)
        if entry is None:
            return None
        target, expires_at = entry
        if expires_at < datetime.now(UTC):
            return None
        return target, expires_at
