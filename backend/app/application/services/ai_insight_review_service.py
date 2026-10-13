"""Phase 11 — AI insight human-review workflow.

Implements the review lifecycle for AI-generated operational suggestions and
population/equity/SDG insights:

    GENERATED -> PENDING_REVIEW -> APPROVED | REJECTED | EDITED -> PUBLISHED

AI NEVER sets PUBLISHED — only a human reviewer (AI_REVIEW_INSIGHTS) may
approve/reject/edit/publish. Every review action is recorded on the insight
row (reviewer_id, reviewer_comment, edited_output, approved_at) and audited
via ``AIAuditService``.

This service is the single chokepoint for review state transitions, enforcing
the deterministic state machine so AI output can never self-publish.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.ai_governance_dtos import (
    InsightReviewResponse,
    ReviewAction,
    ReviewRequest,
)
from app.application.services.ai_audit_service import AIAuditService
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.domain.entities.user import User
from app.infrastructure.persistence.models.ai_operational_suggestion import (
    AiOperationalSuggestionModel,
)
from app.infrastructure.persistence.models.ai_population_insight import (
    AiPopulationInsightModel,
)

logger = logging.getLogger(__name__)

#: Allowed review_status transitions. AI may only create PENDING_REVIEW rows;
#: a human reviewer drives the rest. PUBLISHED is reachable only from
#: APPROVED or EDITED.
_REVIEW_TRANSITIONS: dict[str, set[str]] = {
    "generated": {"pending_review"},
    "pending_review": {"approved", "rejected", "edited"},
    "approved": {"published"},
    "edited": {"published", "rejected"},
    "rejected": set(),
    "published": set(),
}


def _resolve_target_status(action: ReviewAction) -> str:
    return {
        "approve": "approved",
        "reject": "rejected",
        "edit": "edited",
    }[action]


class AiInsightReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = AIAuditService(session)

    async def review_operational(
        self, reviewer: User, suggestion_id: str, req: ReviewRequest
    ) -> InsightReviewResponse:
        self._assert_reviewer(reviewer)
        rec = await self._get_operational(suggestion_id)
        target = _resolve_target_status(req.action)
        self._check_transition(rec.review_status, target)
        if req.action == "edit" and not req.edited_output:
            raise ValidationError(detail="edited_output is required for edit")
        rec.review_status = target
        rec.reviewer_id = reviewer.id
        rec.reviewer_comment = req.reviewer_comment
        if req.action == "edit":
            rec.edited_output = req.edited_output
        if target == "approved":
            rec.approved_at = datetime.now(UTC).isoformat()
        await self.session.commit()
        await self.session.refresh(rec)
        await self._audit_review(
            reviewer, suggestion_id, "operational", target, req
        )
        return InsightReviewResponse(
            id=rec.id,
            insight_type="operational",
            review_status=rec.review_status,  # type: ignore[arg-type]
            reviewer_id=reviewer.id,
            reviewer_comment=rec.reviewer_comment,
            edited_output=rec.edited_output,
            approved_at=rec.approved_at,
        )

    async def publish_operational(
        self, reviewer: User, suggestion_id: str
    ) -> InsightReviewResponse:
        """Publish an approved/edited operational suggestion."""
        self._assert_reviewer(reviewer)
        rec = await self._get_operational(suggestion_id)
        self._check_transition(rec.review_status, "published")
        rec.review_status = "published"
        rec.reviewer_id = reviewer.id
        await self.session.commit()
        await self.session.refresh(rec)
        await self._audit_review(
            reviewer, suggestion_id, "operational", "published", None
        )
        return InsightReviewResponse(
            id=rec.id,
            insight_type="operational",
            review_status="published",  # type: ignore[arg-type]
            reviewer_id=reviewer.id,
            reviewer_comment=rec.reviewer_comment,
            edited_output=rec.edited_output,
            approved_at=rec.approved_at,
        )

    async def review_population(
        self, reviewer: User, insight_id: str, req: ReviewRequest
    ) -> InsightReviewResponse:
        self._assert_reviewer(reviewer)
        rec = await self._get_population(insight_id)
        target = _resolve_target_status(req.action)
        self._check_transition(rec.review_status, target)
        if req.action == "edit" and not req.edited_output:
            raise ValidationError(detail="edited_output is required for edit")
        rec.review_status = target
        rec.reviewer_id = reviewer.id
        rec.reviewer_comment = req.reviewer_comment
        if req.action == "edit":
            rec.edited_output = req.edited_output
        if target == "approved":
            rec.approved_at = datetime.now(UTC).isoformat()
        await self.session.commit()
        await self.session.refresh(rec)
        await self._audit_review(
            reviewer, insight_id, "population", target, req
        )
        return InsightReviewResponse(
            id=rec.id,
            insight_type=rec.insight_type,  # type: ignore[arg-type]
            review_status=rec.review_status,  # type: ignore[arg-type]
            reviewer_id=reviewer.id,
            reviewer_comment=rec.reviewer_comment,
            edited_output=rec.edited_output,
            approved_at=rec.approved_at,
        )

    async def publish_population(
        self, reviewer: User, insight_id: str
    ) -> InsightReviewResponse:
        self._assert_reviewer(reviewer)
        rec = await self._get_population(insight_id)
        self._check_transition(rec.review_status, "published")
        rec.review_status = "published"
        rec.reviewer_id = reviewer.id
        await self.session.commit()
        await self.session.refresh(rec)
        await self._audit_review(
            reviewer, insight_id, "population", "published", None
        )
        return InsightReviewResponse(
            id=rec.id,
            insight_type=rec.insight_type,  # type: ignore[arg-type]
            review_status="published",  # type: ignore[arg-type]
            reviewer_id=reviewer.id,
            reviewer_comment=rec.reviewer_comment,
            edited_output=rec.edited_output,
            approved_at=rec.approved_at,
        )

    # ── internal ──────────────────────────────────────────────────────

    def _assert_reviewer(self, user: User) -> None:
        from app.core.security.rbac import (
            Permission,
            Role,
            check_permission,
            get_role_permissions,
        )

        if not user.roles:
            raise AuthorizationError(detail="AI review access required")
        perms: set[Permission] = set()
        for r in user.roles:
            try:
                perms |= get_role_permissions(Role(r))
            except ValueError:
                continue
        if not check_permission(perms, Permission.AI_REVIEW_INSIGHTS):
            raise AuthorizationError(detail="AI review access required")

    def _check_transition(self, from_status: str, to_status: str) -> None:
        allowed = _REVIEW_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise ValidationError(
                detail=(
                    f"Invalid review transition: {from_status} -> {to_status}"
                )
            )

    async def _get_operational(
        self, suggestion_id: str
    ) -> AiOperationalSuggestionModel:
        rec = await self.session.get(AiOperationalSuggestionModel, suggestion_id)
        if not rec or rec.deleted_at is not None:
            raise NotFoundError(detail="Operational suggestion not found")
        return rec

    async def _get_population(
        self, insight_id: str
    ) -> AiPopulationInsightModel:
        rec = await self.session.get(AiPopulationInsightModel, insight_id)
        if not rec or rec.deleted_at is not None:
            raise NotFoundError(detail="Population insight not found")
        return rec

    async def _audit_review(
        self,
        _reviewer: User,
        insight_id: str,
        insight_kind: str,
        target_status: str,
        req: ReviewRequest | None,
    ) -> None:
        try:
            await self.audit.record(
                trace_id=None,
                session_id=None,
                request_type=f"ai_insight_review:{insight_kind}",
                provider="human-reviewer",
                model="",
                prompt_version="",
                language="en",
                literacy_level="standard",
                input_context={
                    "insight_id": insight_id,
                    "insight_kind": insight_kind,
                    "target_status": target_status,
                },
                output_str=(
                    f"{target_status}:{req.reviewer_comment or ''}"
                    if req
                    else f"{target_status}:publish"
                ),
                status="success",
                status_reason=None,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI insight review audit failed: %s", exc)
