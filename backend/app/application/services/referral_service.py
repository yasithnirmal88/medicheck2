"""Phase 10 — Referral service: state machine, facility feedback, care outcomes.

Built on the Phase 9 referral models (data contract) + Phase 10 additive
facility/outcome tables. The Phase 9 baseline left the service layer absent;
this is the first implementation.

INVARIANTS (do not regress):
- A referral is created ONLY from an existing deterministic
  ``GeneratedRecommendationModel`` (CDSE output) whose source
  ``RecommendationModel`` has an eligible CMS-authored ``category``
  (referral / testing / monitoring). AI never participates in eligibility.
- Every status transition is validated against a fixed state machine and
  recorded in the append-only ``ReferralStatusEventModel`` + ``AuditLogModel``.
- Receiving-side/facility status is NEVER inferred from a timestamp; it must
  be explicitly provided by an authorized actor (facility/CHW/clinician/admin).
- Care outcomes are OPERATIONAL states. They NEVER modify CDSE scoring,
  condition probability, severity, or recommendation generation. There is no
  code path from outcomes back into clinical tables.
- IDOR: patient sees only own referrals; CHW only assigned patients'
  referrals (assignment verified); clinicians/admins with REFERRAL_MANAGE may
  access any (still auditable).
- No clinical notes are accepted in facility feedback (no second
  medical-record system).
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.referral_dtos import (
    AcknowledgeRequest,
    BarrierRequest,
    BarrierResponse,
    CareOutcomeRequest,
    CareOutcomeResponse,
    CompleteTaskRequest,
    CreateReferralRequest,
    FacilityFeedbackRequest,
    FollowUpTaskListResponse,
    FollowUpTaskResponse,
    ReferralDetailResponse,
    ReferralListResponse,
    ReferralResponse,
    ReferralStatusEventResponse,
    ScheduleRequest,
    StatusUpdateRequest,
)
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.identity import Permission, Role, User, check_permission, get_role_permissions
from app.infrastructure.persistence.models.audit_log import AuditLogModel
from app.infrastructure.persistence.models.care_outcome import CareOutcomeModel
from app.infrastructure.persistence.models.decision import (
    AssessmentResultModel,
    GeneratedRecommendationModel,
)
from app.infrastructure.persistence.models.facility import FacilityModel
from app.infrastructure.persistence.models.referral import ReferralModel
from app.infrastructure.persistence.models.referral_access_barrier import (
    ReferralAccessBarrierModel,
)
from app.infrastructure.persistence.models.referral_status_event import (
    ReferralStatusEventModel,
)
from app.infrastructure.persistence.models.recommendation import RecommendationModel
from app.infrastructure.persistence.models.follow_up_task import FollowUpTaskModel

logger = logging.getLogger(__name__)

# ── Eligibility: CMS-authored recommendation categories that may produce a
# referral. AI never participates. ``referral`` is the primary signal;
# ``testing``/``monitoring`` are follow-up-eligible (lab/imaging/monitoring).
REFERRAL_ELIGIBLE_CATEGORIES = {"referral", "testing", "monitoring"}

# Referral type derived from recommendation category when caller does not
# specify. Deterministic mapping — no AI.
_CATEGORY_TO_REFERRAL_TYPE = {
    "referral": "primary_care",
    "testing": "laboratory",
    "monitoring": "follow_up_assessment",
}

# ── State machine ──────────────────────────────────────────────────────
# Phase 9 statuses + Phase 10 facility/outcome states. Every allowed
# transition is explicit; anything else is rejected (ValidationError).
_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"acknowledged", "sent", "cancelled", "unable_to_access", "expired"},
    "acknowledged": {"sent", "scheduled", "cancelled", "unable_to_access"},
    "sent": {"received", "declined", "cancelled", "expired", "lost_to_followup"},
    "received": {"accepted", "declined", "cancelled", "expired", "lost_to_followup"},
    "accepted": {"scheduled", "declined", "cancelled", "lost_to_followup"},
    "scheduled": {"attended", "completed", "cancelled", "lost_to_followup", "unable_to_access"},
    "attended": {"completed", "follow_up_assessment", "lost_to_followup"},
    "completed": {"lost_to_followup"},
    "declined": set(),  # terminal
    "unable_to_access": {"scheduled", "cancelled", "lost_to_followup"},
    "cancelled": set(),  # terminal
    "expired": set(),  # terminal
    "lost_to_followup": set(),  # terminal
    # follow_up_assessment is a referral_type, not a status; guard below.
}

# Terminal states (no outgoing transitions).
TERMINAL_STATES = {
    s for s, nxt in _TRANSITIONS.items() if not nxt
}

# Facility feedback receiving_status -> referral status side-effect.
# Recording receiving-side feedback also advances the referral status through
# the deterministic machine. The receiving_status itself is stored on the
# referral for operational display; the authoritative lifecycle is the status.
_FEEDBACK_TO_STATUS = {
    "received": "received",
    "accepted": "accepted",
    "declined": "declined",
    "scheduled": "scheduled",
    "completed": "completed",
    "lost_to_followup": "lost_to_followup",
}

# Care outcome categories (operational funnel). NEVER clinical.
_OUTCOME_ORDER = [
    "screened",
    "referred",
    "referral_received",
    "appointment_scheduled",
    "care_received",
    "followup_completed",
]
_OUTCOME_TERMINAL = {"lost_to_followup"}

_TRACE_RE = re.compile(r"\[trace:([0-9a-f]{16})\]")


def _extract_trace_id(summary: str | None) -> str | None:
    if not summary:
        return None
    m = _TRACE_RE.search(summary)
    return m.group(1) if m else None


def _actor_role(user: User) -> str:
    """Map a user's roles to a single actor_role label."""
    roles = user.roles or set()
    if Role.SUPER_ADMIN in roles or Role.MEDICAL_DIRECTOR in roles:
        return "admin"
    if Role.DOCTOR in roles or Role.SPECIALIST_DOCTOR in roles or Role.GENERAL_PHYSICIAN in roles:
        return "doctor"
    if Role.COMMUNITY_HEALTH_WORKER in roles:
        return "chw"
    return "patient"


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


class ReferralService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Authorization ────────────────────────────────────────────────

    async def _assert_can_access(
        self, user: User, patient_user_id: str, *, manage: bool = False
    ) -> None:
        """IDOR guard. Patient = own only. CHW = assigned only. Clinician/admin
        with REFERRAL_MANAGE = any (still auditable)."""
        if _user_has_perm(user, Permission.REFERRAL_MANAGE) and (
            Role.DOCTOR in user.roles
            or Role.SPECIALIST_DOCTOR in user.roles
            or Role.GENERAL_PHYSICIAN in user.roles
            or Role.SUPER_ADMIN in user.roles
            or Role.MEDICAL_DIRECTOR in user.roles
        ):
            return
        if Role.COMMUNITY_HEALTH_WORKER in user.roles:
            await self._assert_assigned(user.id, patient_user_id)
            return
        # Patient: own only.
        if user.id != patient_user_id:
            raise AuthorizationError(detail="Not authorized to access this referral")

    async def _assert_assigned(self, chw_id: str, patient_id: str) -> None:
        """Verify the CHW is actively assigned to the patient (Phase 8 guard)."""
        from app.infrastructure.persistence.models.chw_assignment import (
            ChwAssignmentModel,
        )

        stmt = select(ChwAssignmentModel).where(
            ChwAssignmentModel.chw_user_id == chw_id,
            ChwAssignmentModel.patient_user_id == patient_id,
            ChwAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        assignment = result.scalar_one_or_none()
        if assignment is None:
            raise AuthorizationError(
                detail="Not authorized: patient is not assigned to this CHW"
            )
        if assignment.status not in {"active", "assigned"}:
            raise AuthorizationError(
                detail="Not authorized: CHW assignment is not active"
            )

    def _assert_transition(self, from_status: str, to_status: str) -> None:
        if to_status not in _TRANSITIONS:
            raise ValidationError(detail=f"Unknown referral status: {to_status}")
        allowed = _TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            if from_status in TERMINAL_STATES:
                raise ValidationError(
                    detail=f"Referral is in terminal state '{from_status}'"
                )
            raise ValidationError(
                detail=f"Invalid status transition: {from_status} -> {to_status}"
            )

    # ── Create ───────────────────────────────────────────────────────

    async def create_referral(
        self, user: User, req: CreateReferralRequest
    ) -> ReferralResponse:
        """Create a referral from an existing deterministic recommendation.

        Verifies the originating session's CDSE result belongs to the patient
        (IDOR) and that the recommendation is referral-eligible (CMS category).
        Eligibility is deterministic; AI never participates.
        """
        # Load the CDSE result for the originating session.
        result_stmt = select(AssessmentResultModel).where(
            AssessmentResultModel.session_id == req.originating_session_id,
            AssessmentResultModel.deleted_at.is_(None),
        )
        result = (
            await self.session.execute(result_stmt)
        ).scalar_one_or_none()
        if result is None:
            raise NotFoundError(detail="Assessment result not found for session")

        # IDOR: patient must own the session; CHW must be assigned; clinician/admin ok.
        await self._assert_can_access(user, result.user_id, manage=True)
        patient_user_id = result.user_id

        # If a CHW is creating on behalf of the patient, the assigned_chw_user_id
        # defaults to the CHW. The patient_user_id comes from the CDSE result.
        assigned_chw = req.assigned_chw_user_id
        if assigned_chw is None and Role.COMMUNITY_HEALTH_WORKER in (user.roles or set()):
            assigned_chw = user.id

        # Find the generated recommendation (CDSE output) for this result.
        gen_stmt = select(GeneratedRecommendationModel).where(
            GeneratedRecommendationModel.result_id == result.id,
            GeneratedRecommendationModel.recommendation_id == req.recommendation_id,
            GeneratedRecommendationModel.deleted_at.is_(None),
        )
        gen_rec = (await self.session.execute(gen_stmt)).scalar_one_or_none()
        if gen_rec is None:
            raise ValidationError(
                detail="Recommendation is not part of this assessment result"
            )

        # Load the CMS recommendation to check eligibility category.
        cms_rec = await self.session.get(RecommendationModel, req.recommendation_id)
        if cms_rec is None or cms_rec.deleted_at is not None:
            raise NotFoundError(detail="Recommendation not found")
        if (cms_rec.category or "").lower() not in REFERRAL_ELIGIBLE_CATEGORIES:
            raise ValidationError(
                detail=(
                    "Recommendation category is not referral-eligible "
                    f"(category='{cms_rec.category}')"
                )
            )

        # Optional facility validation.
        if req.facility_id is not None:
            facility = await self.session.get(FacilityModel, req.facility_id)
            if facility is None or facility.deleted_at is not None or not facility.is_active:
                raise NotFoundError(detail="Facility not found or inactive")

        # Extract trace_id from the CDSE result summary (deterministic).
        trace_id = _extract_trace_id(result.summary)

        referral = ReferralModel(
            patient_user_id=patient_user_id,
            originating_session_id=req.originating_session_id,
            originating_report_id=None,
            trace_id=trace_id,
            recommendation_id=req.recommendation_id,
            referral_type=req.referral_type,
            status="pending",
            due_at=req.due_at,
            assigned_chw_user_id=assigned_chw,
            patient_acknowledged=False,
            notes=req.notes,
            facility_id=req.facility_id,
            receiving_status=None,
            scheduled_for=None,
        )
        self.session.add(referral)
        await self.session.flush()

        # Initial status event + audit.
        await self._record_event(
            referral, None, "pending", user, reason="referral created"
        )
        await self._audit(
            user, referral.id, "create",
            new_value={"status": "pending", "recommendation_id": req.recommendation_id},
        )
        await self.session.flush()
        return await self._to_response(referral, cms_rec=cms_rec)

    # ── Read ─────────────────────────────────────────────────────────

    async def list_referrals(
        self, user: User, *, patient_user_id: str | None = None
    ) -> ReferralListResponse:
        """List referrals. Patient: own only. CHW: assigned patients'.
        Clinician/admin (REFERRAL_MANAGE): optionally filtered by patient."""
        stmt = select(ReferralModel).where(
            ReferralModel.deleted_at.is_(None)
        )
        if _user_has_perm(user, Permission.REFERRAL_MANAGE) and (
            Role.DOCTOR in user.roles
            or Role.SPECIALIST_DOCTOR in user.roles
            or Role.GENERAL_PHYSICIAN in user.roles
            or Role.SUPER_ADMIN in user.roles
            or Role.MEDICAL_DIRECTOR in user.roles
        ):
            if patient_user_id:
                stmt = stmt.where(ReferralModel.patient_user_id == patient_user_id)
        elif Role.COMMUNITY_HEALTH_WORKER in (user.roles or set()):
            stmt = stmt.where(ReferralModel.assigned_chw_user_id == user.id)
        else:
            # Patient: own only.
            stmt = stmt.where(ReferralModel.patient_user_id == user.id)
        stmt = stmt.order_by(ReferralModel.created_at.desc())
        referrals = (await self.session.execute(stmt)).scalars().all()
        items = [await self._to_response(r) for r in referrals]
        return ReferralListResponse(items=items, total=len(items))

    async def get_referral(self, user: User, referral_id: str) -> ReferralDetailResponse:
        referral = await self._get_owned_referral(user, referral_id)
        return await self._to_detail_response(referral)

    # ── Status transitions ───────────────────────────────────────────

    async def acknowledge(
        self, user: User, referral_id: str, req: AcknowledgeRequest
    ) -> ReferralResponse:
        referral = await self._get_owned_referral(user, referral_id)
        self._assert_transition(referral.status, "acknowledged")
        referral.status = "acknowledged"
        referral.patient_acknowledged = True
        if req.notes:
            referral.notes = (referral.notes or "") + "\n" + req.notes if referral.notes else req.notes
        await self._record_event(referral, referral.status, "acknowledged", user, req.notes)
        await self._audit(user, referral.id, "acknowledge", new_value={"status": "acknowledged"})
        await self.session.flush()
        return await self._to_response(referral)

    async def schedule(
        self, user: User, referral_id: str, req: ScheduleRequest
    ) -> ReferralResponse:
        referral = await self._get_owned_referral(user, referral_id)
        self._assert_transition(referral.status, "scheduled")
        referral.status = "scheduled"
        if req.scheduled_for:
            referral.scheduled_for = req.scheduled_for
        if req.notes:
            referral.notes = (referral.notes or "") + "\n" + req.notes if referral.notes else req.notes
        await self._record_event(referral, referral.status, "scheduled", user, req.notes)
        await self._audit(user, referral.id, "schedule", new_value={"status": "scheduled", "scheduled_for": str(req.scheduled_for)})
        await self.session.flush()
        return await self._to_response(referral)

    async def update_status(
        self, user: User, referral_id: str, req: StatusUpdateRequest
    ) -> ReferralResponse:
        referral = await self._get_owned_referral(user, referral_id)
        self._assert_transition(referral.status, req.status)
        old = referral.status
        referral.status = req.status
        if req.status in TERMINAL_STATES or req.status == "completed":
            referral.completed_at = datetime.now(UTC)
        await self._record_event(referral, old, req.status, user, req.reason)
        await self._audit(user, referral.id, "status_update", new_value={"status": req.status})
        await self.session.flush()
        return await self._to_response(referral)

    # ── Facility feedback (receiving-side) ───────────────────────────

    async def record_facility_feedback(
        self, user: User, referral_id: str, req: FacilityFeedbackRequest
    ) -> ReferralResponse:
        """Record receiving-side facility feedback.

        The receiving_status is stored on the referral, and the referral's
        lifecycle status is advanced through the deterministic state machine.
        Clinical notes are NOT accepted (no second medical-record system).
        """
        referral = await self._get_owned_referral(user, referral_id, manage=True)
        target_status = _FEEDBACK_TO_STATUS[req.receiving_status]
        self._assert_transition(referral.status, target_status)
        old = referral.status
        referral.receiving_status = req.receiving_status
        referral.status = target_status
        if req.scheduled_for:
            referral.scheduled_for = req.scheduled_for
        if target_status in TERMINAL_STATES or target_status == "completed":
            referral.completed_at = datetime.now(UTC)
        await self._record_event(
            referral, old, target_status, user,
            reason=f"facility feedback: {req.receiving_status}" + (f"; {req.notes}" if req.notes else ""),
        )
        await self._audit(
            user, referral.id, "facility_feedback",
            new_value={"receiving_status": req.receiving_status, "status": target_status},
        )
        await self.session.flush()
        return await self._to_response(referral)

    # ── Barriers ─────────────────────────────────────────────────────

    async def record_barrier(
        self, user: User, referral_id: str, req: BarrierRequest
    ) -> BarrierResponse:
        referral = await self._get_owned_referral(user, referral_id)
        barrier = ReferralAccessBarrierModel(
            referral_id=referral.id,
            barrier_type=req.barrier_type,
            recorded_by_user_id=user.id,
            recorded_by_role=_actor_role(user),
            detail=req.detail,
        )
        self.session.add(barrier)
        await self.session.flush()
        await self._audit(user, referral.id, "barrier_recorded", new_value={"barrier_type": req.barrier_type})
        await self.session.flush()
        await self.session.refresh(barrier)
        return BarrierResponse.model_validate(barrier)

    # ── Care outcomes (operational; never feeds CDSE) ────────────────

    async def record_outcome(
        self, user: User, referral_id: str, req: CareOutcomeRequest
    ) -> CareOutcomeResponse:
        referral = await self._get_owned_referral(user, referral_id, manage=True)
        recorded_at = req.recorded_at or datetime.now(UTC)
        outcome = CareOutcomeModel(
            referral_id=referral.id,
            patient_user_id=referral.patient_user_id,
            outcome_category=req.outcome_category,
            recorded_by_user_id=user.id,
            recorded_by_role=_actor_role(user),
            recorded_at=recorded_at,
            source=req.source,
            notes=req.notes,
        )
        self.session.add(outcome)
        await self.session.flush()
        await self._audit(
            user, referral.id, "outcome_recorded",
            new_value={"outcome_category": req.outcome_category},
        )
        await self.session.flush()
        await self.session.refresh(outcome)
        return CareOutcomeResponse.model_validate(outcome)

    async def list_outcomes(
        self, user: User, referral_id: str
    ) -> list[CareOutcomeResponse]:
        referral = await self._get_owned_referral(user, referral_id)
        stmt = (
            select(CareOutcomeModel)
            .where(
                CareOutcomeModel.referral_id == referral.id,
                CareOutcomeModel.deleted_at.is_(None),
            )
            .order_by(CareOutcomeModel.recorded_at.asc())
        )
        outcomes = (await self.session.execute(stmt)).scalars().all()
        return [CareOutcomeResponse.model_validate(o) for o in outcomes]

    # ── Follow-up tasks ──────────────────────────────────────────────

    async def list_follow_up_tasks(
        self, user: User, referral_id: str
    ) -> FollowUpTaskListResponse:
        referral = await self._get_owned_referral(user, referral_id)
        tasks = referral.follow_up_tasks or []
        items = [FollowUpTaskResponse.model_validate(t) for t in tasks if not t.is_deleted]
        return FollowUpTaskListResponse(items=items, total=len(items))

    async def complete_task(
        self, user: User, referral_id: str, task_id: str, req: CompleteTaskRequest
    ) -> FollowUpTaskResponse:
        referral = await self._get_owned_referral(user, referral_id)
        task = await self.session.get(FollowUpTaskModel, task_id)
        if task is None or task.referral_id != referral.id or task.is_deleted:
            raise NotFoundError(detail="Follow-up task not found")
        task.status = "completed"
        task.completed_at = datetime.now(UTC)
        if req.notes:
            task.notes = (task.notes or "") + "\n" + req.notes if task.notes else req.notes
        await self.session.flush()
        await self.session.refresh(task)
        return FollowUpTaskResponse.model_validate(task)

    # ── Internal helpers ─────────────────────────────────────────────

    async def _get_owned_referral(
        self, user: User, referral_id: str, *, manage: bool = False
    ) -> ReferralModel:
        referral = await self.session.get(ReferralModel, referral_id)
        if referral is None or referral.is_deleted:
            raise NotFoundError(detail="Referral not found")
        await self._assert_can_access(user, referral.patient_user_id, manage=manage)
        return referral

    async def _record_event(
        self,
        referral: ReferralModel,
        from_status: str | None,
        to_status: str,
        user: User,
        reason: str | None = None,
    ) -> None:
        event = ReferralStatusEventModel(
            referral_id=referral.id,
            from_status=from_status,
            to_status=to_status,
            actor_user_id=user.id,
            actor_role=_actor_role(user),
            reason=reason,
        )
        self.session.add(event)

    async def _audit(
        self,
        user: User,
        referral_id: str,
        action: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        import json

        log = AuditLogModel(
            actor_id=user.id,
            actor_role=_actor_role(user),
            entity_type="referral",
            entity_id=referral_id,
            action=action,
            changed_at=datetime.now(UTC),
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
        )
        self.session.add(log)

    async def _load_cms_recommendation(
        self, referral: ReferralModel
    ) -> RecommendationModel | None:
        if not referral.recommendation_id:
            return None
        rec = await self.session.get(RecommendationModel, referral.recommendation_id)
        if rec is None or rec.is_deleted:
            return None
        return rec

    async def _load_facility_name(self, referral: ReferralModel) -> str | None:
        if not referral.facility_id:
            return None
        facility = await self.session.get(FacilityModel, referral.facility_id)
        if facility is None or facility.is_deleted:
            return None
        return facility.name

    async def _to_response(
        self, referral: ReferralModel, *, cms_rec: RecommendationModel | None = None
    ) -> ReferralResponse:
        # Ensure server-default columns (created_at/updated_at) are loaded —
        # after a flush they are expired and accessing them would trigger a
        # synchronous refresh (MissingGreenlet in async). Check expiry via
        # inspection rather than attribute access (which itself triggers IO).
        from sqlalchemy import inspect as sa_inspect

        state = sa_inspect(referral)
        if "created_at" in state.unloaded or "updated_at" in state.unloaded:
            await self.session.refresh(referral)
        if cms_rec is None:
            cms_rec = await self._load_cms_recommendation(referral)
        facility_name = await self._load_facility_name(referral)
        return ReferralResponse(
            id=referral.id,
            patient_user_id=referral.patient_user_id,
            originating_session_id=referral.originating_session_id,
            originating_report_id=referral.originating_report_id,
            trace_id=referral.trace_id,
            recommendation_id=referral.recommendation_id,
            recommendation_title=cms_rec.title if cms_rec else None,
            recommendation_category=cms_rec.category if cms_rec else None,
            recommendation_urgency=cms_rec.urgency if cms_rec else None,
            referral_type=referral.referral_type,  # type: ignore[arg-type]
            status=referral.status,  # type: ignore[arg-type]
            due_at=referral.due_at,
            assigned_chw_user_id=referral.assigned_chw_user_id,
            patient_acknowledged=referral.patient_acknowledged,
            notes=referral.notes,
            completed_at=referral.completed_at,
            facility_id=referral.facility_id,
            facility_name=facility_name,
            receiving_status=referral.receiving_status,
            scheduled_for=referral.scheduled_for,
            created_at=referral.created_at,
            updated_at=referral.updated_at,
        )

    async def _to_detail_response(
        self, referral: ReferralModel
    ) -> ReferralDetailResponse:
        base = await self._to_response(referral)
        events = [
            ReferralStatusEventResponse(
                id=e.id,
                from_status=e.from_status,
                to_status=e.to_status,  # type: ignore[arg-type]
                actor_user_id=e.actor_user_id,
                actor_role=e.actor_role,  # type: ignore[arg-type]
                reason=e.reason,
                created_at=e.created_at,
            )
            for e in (referral.status_events or []) if not e.is_deleted
        ]
        barriers = [
            BarrierResponse(
                id=b.id,
                referral_id=b.referral_id,
                barrier_type=b.barrier_type,  # type: ignore[arg-type]
                recorded_by_user_id=b.recorded_by_user_id,
                recorded_by_role=b.recorded_by_role,  # type: ignore[arg-type]
                detail=b.detail,
                created_at=b.created_at,
            )
            for b in (referral.barriers or []) if not b.is_deleted
        ]
        tasks = [
            FollowUpTaskResponse(
                id=t.id,
                referral_id=t.referral_id,
                patient_user_id=t.patient_user_id,
                assigned_chw_user_id=t.assigned_chw_user_id,
                task_type=t.task_type,
                title=t.title,
                due_at=t.due_at,
                status=t.status,  # type: ignore[arg-type]
                completed_at=t.completed_at,
                notes=t.notes,
                created_at=t.created_at,
            )
            for t in (referral.follow_up_tasks or []) if not t.is_deleted
        ]
        return ReferralDetailResponse(
            **base.model_dump(),
            status_events=events,
            barriers=barriers,
            follow_up_tasks=tasks,
        )
