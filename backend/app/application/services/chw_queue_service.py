"""Phase 10 — CHW operational queue service.

Loads a CHW's referral follow-up tasks, builds a PHI-scrubbed operational
input (referral age, overdue, missing follow-up, appointment window, region,
unresolved admin status — NO clinical fields), invokes the (deterministic
stub) queue-ranking provider, and audits the call via Phase 7
``AIAuditService`` (hashes + ids only, NO PHI).

INVARIANT: AI ranks by operational factors ONLY. It NEVER ranks by disease
severity, probability, urgency, or clinical risk. Clinical priority is
already separately available to the CHW via the deterministic CDSE and is
never re-ranked or overridden here. AI never modifies referral records — the
output is a read-only ranking + labelled rationale.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.queue_ranking_provider import (
    QueueRankingInput,
    QueueRankingOutput,
    QueueTaskInput,
    get_queue_ranking_provider,
)
from app.application.services.ai_audit_service import AIAuditService
from app.core.config import settings
from app.core.exceptions import AuthorizationError
from app.identity import User
from app.infrastructure.persistence.models.chw_assignment import ChwAssignmentModel
from app.infrastructure.persistence.models.referral import ReferralModel

logger = logging.getLogger(__name__)
_UTC = ZoneInfo("UTC")


class ChwQueueService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.provider = get_queue_ranking_provider()
        self.audit = AIAuditService(session)

    async def get_queue(self, chw_user: User) -> QueueRankingOutput:
        """Build + rank the CHW's operational follow-up queue."""
        if "community_health_worker" not in (chw_user.roles or set()):
            if not self._is_supervisor(chw_user):
                raise AuthorizationError(
                    detail="Community Health Worker access required"
                )

        now = datetime.now(_UTC)
        # Load referrals assigned to this CHW (bounded).
        stmt = (
            select(ReferralModel)
            .where(
                ReferralModel.assigned_chw_user_id == chw_user.id,
                ReferralModel.deleted_at.is_(None),
            )
            .order_by(ReferralModel.created_at.asc())
            .limit(settings.chw_queue_max_size)
        )
        referrals = (await self.session.execute(stmt)).scalars().all()

        tasks: list[QueueTaskInput] = []
        for ref in referrals:
            # Operational factors only — NO clinical fields.
            age_days = (now - (ref.created_at.replace(tzinfo=_UTC) if ref.created_at.tzinfo is None else ref.created_at)).total_seconds() / 86400.0
            overdue = bool(ref.due_at) and (
                (ref.due_at.replace(tzinfo=_UTC) if ref.due_at.tzinfo is None else ref.due_at) < now
            )
            appointment_window_days = None
            if ref.scheduled_for:
                sched = ref.scheduled_for.replace(tzinfo=_UTC) if ref.scheduled_for.tzinfo is None else ref.scheduled_for
                appointment_window_days = (sched - now).total_seconds() / 86400.0
            unresolved_admin = ref.status not in {
                "completed", "cancelled", "declined", "expired", "lost_to_followup"
            }
            missing_follow_up = unresolved_admin and not bool(ref.patient_acknowledged)
            tasks.append(
                QueueTaskInput(
                    referral_id=ref.id,
                    referral_age_days=round(max(age_days, 0.0), 1),
                    overdue=overdue,
                    missing_follow_up=missing_follow_up,
                    appointment_window_days=(
                        round(appointment_window_days, 1)
                        if appointment_window_days is not None
                        else None
                    ),
                    region=None,  # region not on referral; facility region could be joined in future.
                    unresolved_admin_status=unresolved_admin,
                )
            )

        data = QueueRankingInput(chw_user_id=chw_user.id, tasks=tasks)
        output = self.provider.rank(data)

        # Audit (hashes + ids only, NO PHI).
        await self._audit_ranking(chw_user, data, output)
        return output

    def _is_supervisor(self, user: User) -> bool:
        from app.identity import Role

        return Role.MEDICAL_DIRECTOR in (user.roles or set()) or Role.SUPER_ADMIN in (
            user.roles or set()
        )

    async def _audit_ranking(
        self, user: User, data: QueueRankingInput, output: QueueRankingOutput
    ) -> None:
        try:
            input_context = {
                "chw_user_id": data.chw_user_id,
                "task_count": len(data.tasks),
                "referral_ids": [t.referral_id for t in data.tasks],
            }
            output_str = ",".join(
                f"{t.referral_id}:{t.rank}" for t in output.ranked_tasks
            )
            await self.audit.record(
                trace_id=None,
                session_id=None,
                request_type="chw_queue_ranking",
                provider=output.provider,
                model=output.model or "",
                prompt_version=output.prompt_version,
                language="en",
                literacy_level="standard",
                input_context=input_context,
                output_str=output_str,
                status="success" if output.available else "fallback",
                status_reason=None if output.available else "provider_unavailable",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("CHW queue ranking audit failed: %s", exc)
