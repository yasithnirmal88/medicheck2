"""Phase 11 — AI operational suggestion service (CHW care coordination).

Loads a CHW's assigned referral follow-up tasks, builds PHI-scrubbed
OPERATIONAL contexts (referral age, overdue, contact attempts, facility/
appointment/communication status, language, offline status — NO clinical
fields), invokes the operational-suggestion provider, validates every
``task_id`` against the allow-list of actually-assigned task ids (hallucinated
ids REJECTED), persists each suggestion with a PENDING_REVIEW lifecycle, and
audits via the Phase 7 ``AIAuditService`` (hashes + ids only, NO PHI).

INVARIANT: AI ranks/suggests by operational factors ONLY. It NEVER ranks by
disease severity, probability, urgency, or clinical risk. Clinical priority is
already separately available to the CHW via the deterministic CDSE and is
never re-ranked or overridden here. AI never modifies referral records — the
output is a read-only suggestion + labelled rationale. AI never publishes its
own output (review_status starts at pending_review; only a human reviewer may
approve/reject/edit/publish).
"""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.operational_suggestion_provider import (
    OPERATIONAL_SUGGESTION_PROMPT_VERSION,
    StubOperationalSuggestionProvider,
    compute_operational_input_hash,
    compute_operational_output_hash,
    get_operational_suggestion_provider,
)
from app.application.dtos.ai_governance_dtos import (
    OperationalQueueContext,
    OperationalQueueSuggestion,
    OperationalSuggestionBatchResponse,
    OperationalSuggestionRecord,
)
from app.application.services.ai_audit_service import AIAuditService
from app.core.config import settings
from app.core.exceptions import AuthorizationError
from app.domain.entities.user import User
from app.infrastructure.persistence.models.ai_operational_suggestion import (
    AiOperationalSuggestionModel,
)
from app.infrastructure.persistence.models.referral import ReferralModel

logger = logging.getLogger(__name__)
_UTC = ZoneInfo("UTC")

_TERMINAL = {
    "completed", "cancelled", "declined", "expired", "lost_to_followup",
}


class AiOperationalSuggestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.provider = get_operational_suggestion_provider()
        self.audit = AIAuditService(session)

    async def generate_for_chw(
        self, chw_user: User
    ) -> OperationalSuggestionBatchResponse:
        """Generate + persist operational suggestions for a CHW's queue."""
        self._assert_chw_access(chw_user)

        referrals = await self._load_chw_referrals(chw_user)
        if not referrals:
            return self._empty_response(reason="No assigned follow-up tasks.")

        # Build PHI-scrubbed operational contexts (NO clinical fields).
        contexts = [self._to_context(r) for r in referrals]
        # Allow-list = the actual assigned task ids. Hallucinated ids are
        # rejected by the service-level validation below.
        allow_list = {c.task_id for c in contexts}

        try:
            suggestions = self.provider.suggest(contexts)
        except Exception as exc:  # provider failure -> safe fallback
            logger.warning("Operational suggestion provider failed: %s", exc)
            await self._audit_call(
                chw_user, contexts, None, "provider_unavailable", str(exc)
            )
            return self._empty_response(
                reason="AI operational provider unavailable.",
                quality_status="provider_unavailable",
            )

        # Validate task_id allow-list: reject any hallucinated id.
        validated: list[OperationalQueueSuggestion] = []
        for s in suggestions:
            if s.task_id not in allow_list:
                await self._audit_call(
                    chw_user, contexts, suggestions,
                    "validation_failed",
                    f"hallucinated task_id: {s.task_id}",
                )
                return self._empty_response(
                    reason="AI output referenced an unknown task.",
                    quality_status="validation_failed",
                )
            validated.append(s)

        # Validate output hash + persist with pending_review lifecycle.
        out_hash = compute_operational_output_hash(validated)
        in_hash = compute_operational_input_hash(contexts)
        records: list[OperationalSuggestionRecord] = []
        for s in validated:
            rec = AiOperationalSuggestionModel(
                chw_user_id=chw_user.id,
                task_id=s.task_id,
                operational_reason_codes=list(s.operational_reason_codes),
                explanation=s.explanation,
                operational_priority_score=s.operational_priority_score,
                requires_human_review=s.requires_human_review,
                provider=self.provider.name,
                model=getattr(self.provider, "model", "") or "",
                prompt_version=OPERATIONAL_SUGGESTION_PROMPT_VERSION,
                input_context_hash=in_hash,
                output_hash=out_hash,
                quality_status="valid",
                review_status="pending_review",
            )
            self.session.add(rec)
        await self.session.commit()

        # Reload to get ids/timestamps.
        for s in validated:
            stmt = (
                select(AiOperationalSuggestionModel)
                .where(
                    AiOperationalSuggestionModel.chw_user_id == chw_user.id,
                    AiOperationalSuggestionModel.task_id == s.task_id,
                    AiOperationalSuggestionModel.deleted_at.is_(None),
                )
                .order_by(AiOperationalSuggestionModel.created_at.desc())
                .limit(1)
            )
            rec = (await self.session.execute(stmt)).scalar_one_or_none()
            if rec:
                records.append(self._to_record_dto(rec))

        await self._audit_call(
            chw_user, contexts, validated, "success", None
        )
        return OperationalSuggestionBatchResponse(
            available=True,
            suggestions=validated,
            provider=self.provider.name,
            model=getattr(self.provider, "model", "") or "",
            prompt_version=OPERATIONAL_SUGGESTION_PROMPT_VERSION,
            quality_status="valid",
            records=records,
        )

    async def list_for_chw(
        self, chw_user: User, *, limit: int | None = None
    ) -> list[OperationalSuggestionRecord]:
        """List a CHW's persisted suggestions (own only — IDOR enforced)."""
        self._assert_chw_access(chw_user)
        cap = min(
            limit or settings.ai_insight_max_results,
            settings.ai_insight_max_results,
        )
        stmt = (
            select(AiOperationalSuggestionModel)
            .where(
                AiOperationalSuggestionModel.chw_user_id == chw_user.id,
                AiOperationalSuggestionModel.deleted_at.is_(None),
            )
            .order_by(AiOperationalSuggestionModel.created_at.desc())
            .limit(cap)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return [self._to_record_dto(r) for r in rows]

    # ── internal helpers ─────────────────────────────────────────────

    def _assert_chw_access(self, user: User) -> None:
        from app.core.security.rbac import Permission, Role, check_permission, get_role_permissions

        if not user.roles:
            raise AuthorizationError(detail="Operational AI access required")
        perms: set[Permission] = set()
        for r in user.roles:
            try:
                perms |= get_role_permissions(Role(r))
            except ValueError:
                continue
        if not check_permission(
            perms, Permission.AI_VIEW_OPERATIONAL_SUGGESTIONS
        ):
            raise AuthorizationError(detail="Operational AI access required")

    async def _load_chw_referrals(
        self, chw_user: User
    ) -> list[ReferralModel]:
        stmt = (
            select(ReferralModel)
            .where(
                ReferralModel.assigned_chw_user_id == chw_user.id,
                ReferralModel.deleted_at.is_(None),
            )
            .order_by(ReferralModel.created_at.asc())
            .limit(settings.ai_operational_max_tasks)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    def _to_context(self, ref: ReferralModel) -> OperationalQueueContext:
        now = datetime.now(_UTC)
        created = ref.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=_UTC)
        age_days = max((now - created).total_seconds() / 86400.0, 0.0)
        overdue_days: float | None = None
        if ref.due_at:
            due = ref.due_at
            if due.tzinfo is None:
                due = due.replace(tzinfo=_UTC)
            if due < now:
                overdue_days = max((now - due).total_seconds() / 86400.0, 0.0)
        # appointment_status: scheduled if scheduled_for set & unresolved.
        appointment_status = (
            "scheduled"
            if ref.scheduled_for and ref.status not in _TERMINAL
            else ("unscheduled" if ref.status not in _TERMINAL else None)
        )
        facility_status = ref.receiving_status if ref.receiving_status else (
            "sent" if ref.status == "sent" else None
        )
        return OperationalQueueContext(
            task_id=ref.id,
            referral_age_days=round(age_days, 1),
            overdue_days=round(overdue_days, 1) if overdue_days else None,
            contact_attempts=0,  # contact-attempt tracking not modeled; default
            facility_status=facility_status,
            appointment_status=appointment_status,
            communication_status=(
                "acknowledged" if ref.patient_acknowledged else "pending"
            ),
            language=None,  # language preference lives on the patient profile,
            # intentionally NOT loaded here to keep AI context minimal/PHI-free.
            offline_status=None,
        )

    def _to_record_dto(
        self, rec: AiOperationalSuggestionModel
    ) -> OperationalSuggestionRecord:
        return OperationalSuggestionRecord(
            id=rec.id,
            chw_user_id=rec.chw_user_id,
            task_id=rec.task_id,
            operational_reason_codes=list(rec.operational_reason_codes or []),
            explanation=rec.explanation,
            operational_priority_score=rec.operational_priority_score,
            requires_human_review=rec.requires_human_review,
            provider=rec.provider,
            model=rec.model,
            prompt_version=rec.prompt_version,
            quality_status=rec.quality_status,
            quality_reason=rec.quality_reason,
            review_status=rec.review_status,  # type: ignore[arg-type]
            reviewer_id=rec.reviewer_id,
            reviewer_comment=rec.reviewer_comment,
            edited_output=rec.edited_output,
            approved_at=rec.approved_at,
            created_at=(
                rec.created_at.isoformat() if rec.created_at else None
            ),
        )

    def _empty_response(
        self,
        *,
        reason: str,
        quality_status: str = "valid",
    ) -> OperationalSuggestionBatchResponse:
        return OperationalSuggestionBatchResponse(
            available=False,
            suggestions=[],
            provider=self.provider.name
            if not isinstance(self.provider, StubOperationalSuggestionProvider)
            or quality_status == "valid"
            else "stub",
            model=getattr(self.provider, "model", "") or "",
            prompt_version=OPERATIONAL_SUGGESTION_PROMPT_VERSION,
            quality_status=quality_status,  # type: ignore[arg-type]
            quality_reason=reason,
            records=[],
        )

    async def _audit_call(
        self,
        user: User,
        contexts: list[OperationalQueueContext],
        suggestions: list[OperationalQueueSuggestion] | None,
        status: str,
        reason: str | None,
    ) -> None:
        try:
            input_ctx = {
                "chw_user_id": user.id,
                "task_count": len(contexts),
                "task_ids": [c.task_id for c in contexts],
            }
            output_str = (
                ",".join(
                    f"{s.task_id}:{s.operational_priority_score}"
                    for s in suggestions
                )
                if suggestions
                else ""
            )
            await self.audit.record(
                trace_id=None,
                session_id=None,
                request_type="chw_operational_suggestion",
                provider=self.provider.name,
                model=getattr(self.provider, "model", "") or "",
                prompt_version=OPERATIONAL_SUGGESTION_PROMPT_VERSION,
                language="en",
                literacy_level="standard",
                input_context=input_ctx,
                output_str=output_str,
                status=status,
                status_reason=reason,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Operational suggestion audit failed: %s", exc)
