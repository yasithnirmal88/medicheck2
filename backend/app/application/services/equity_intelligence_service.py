"""Phase 11 — AI equity intelligence service ("left-behind" intelligence).

Composes DE-IDENTIFIED, already-aggregated, k-anonymity-suppressed analytics
from the Phase 6 ``PopulationAnalyticsService`` into an ``EquityInsightContext``,
invokes the equity-intelligence provider, validates the output (entity
allow-list, no clinical/causal/identification language), persists the insight
with a PENDING_REVIEW lifecycle, and audits via ``AIAuditService``.

The AI receives ONLY already-suppressed aggregates — never patient ids, names,
phone numbers, addresses, emergency contacts, or raw answers. If the AI fails
or produces invalid output, the underlying deterministic analytics remain
available (the caller can still fetch them directly). AI never self-publishes.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.equity_intelligence_provider import (
    EQUITY_INTELLIGENCE_PROMPT_VERSION,
    compute_equity_input_hash,
    compute_equity_output_hash,
    get_equity_intelligence_provider,
)
from app.application.dtos.ai_governance_dtos import (
    EquityInsightContext,
    EquityInsightOutput,
    EquityInsightResponse,
    EquityMetricContext,
    PopulationInsightRecord,
)
from app.application.dtos.analytics_dtos import AnalyticsFilters
from app.application.services.ai_audit_service import AIAuditService
from app.application.services.population_analytics_service import (
    PopulationAnalyticsService,
)
from app.core.config import settings
from app.core.exceptions import AuthorizationError
from app.domain.entities.user import User
from app.infrastructure.persistence.models.ai_population_insight import (
    AiPopulationInsightModel,
)

logger = logging.getLogger(__name__)


class EquityIntelligenceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.provider = get_equity_intelligence_provider()
        self.audit = AIAuditService(session)
        self.pop = PopulationAnalyticsService(session)

    async def generate_equity_insight(
        self, user: User, filters: AnalyticsFilters
    ) -> EquityInsightResponse:
        self._assert_access(user)
        context = await self._build_context(filters)
        in_hash = compute_equity_input_hash(context)

        try:
            output = self.provider.explain(context)
            self._validate_output(output, context)
        except Exception as exc:
            logger.warning("Equity intelligence provider failed: %s", exc)
            await self._audit(user, context, None, "validation_failed", str(exc))
            return self._fallback(
                reason=f"AI equity output rejected: {exc}",
                quality_status="validation_failed",
            )

        out_hash = compute_equity_output_hash(output)
        record = await self._persist(
            user, context, output, in_hash, out_hash, "valid", None
        )
        await self._audit(user, context, output, "success", None)
        return EquityInsightResponse(
            available=True,
            insight=output,
            record=record,
            provider=self.provider.name,
            prompt_version=EQUITY_INTELLIGENCE_PROMPT_VERSION,
            quality_status="valid",
        )

    async def list_insights(
        self, user: User, *, limit: int | None = None
    ) -> list[PopulationInsightRecord]:
        self._assert_access(user)
        cap = min(
            limit or settings.ai_insight_max_results,
            settings.ai_insight_max_results,
        )
        from sqlalchemy import select

        stmt = (
            select(AiPopulationInsightModel)
            .where(
                AiPopulationInsightModel.insight_type == "equity",
                AiPopulationInsightModel.deleted_at.is_(None),
            )
            .order_by(AiPopulationInsightModel.created_at.desc())
            .limit(cap)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return [self._to_record_dto(r) for r in rows]

    # ── internal ──────────────────────────────────────────────────────

    def _assert_access(self, user: User) -> None:
        from app.core.security.rbac import (
            Permission,
            Role,
            check_permission,
            get_role_permissions,
        )

        if not user.roles:
            raise AuthorizationError(detail="Population insight access required")
        perms: set[Permission] = set()
        for r in user.roles:
            try:
                perms |= get_role_permissions(Role(r))
            except ValueError:
                continue
        if not check_permission(
            perms, Permission.AI_VIEW_POPULATION_INSIGHTS
        ):
            raise AuthorizationError(detail="Population insight access required")

    def _validate_output(
        self, output: EquityInsightOutput, context: EquityInsightContext
    ) -> None:
        """Defense-in-depth: validate provider output before persisting.

        Re-runs the provider's own safety checks at the service layer so a
        misbehaving/real LLM provider can never persist clinical, causal,
        identification, or hallucinated-metric output.
        """
        from app.application.ai.equity_intelligence_provider import (
            _validate_findings,
            _validate_interpretations,
        )

        allowed = {m.label for m in context.metrics}
        _validate_findings(output.observed_findings, allowed)
        _validate_interpretations(output.possible_interpretations)

    async def _build_context(
        self, filters: AnalyticsFilters
    ) -> EquityInsightContext:
        """Compose de-identified, k-suppressed accessibility aggregates.

        Only released (non-suppressed) metrics are described; suppressed
        cohorts are passed through with ``suppressed=True`` so the AI sees the
        suppression state but never the small counts.
        """
        accessibility = await self.pop.get_accessibility(filters)
        acc = accessibility.accessibility
        metrics: list[EquityMetricContext] = []
        for lm in acc.by_language:
            metrics.append(
                EquityMetricContext(
                    label=f"{lm.language} language completion",
                    metric_type="language",
                    value=lm.completion_rate,
                    numerator=(
                        int(lm.assessment_count * (lm.completion_rate or 0))
                        if not lm.suppressed and lm.completion_rate is not None
                        else None
                    ),
                    denominator=lm.assessment_count if not lm.suppressed else None,
                    suppressed=lm.suppressed,
                    comparison="completion_rate",
                )
            )
        if not acc.voice_suppressed:
            metrics.append(
                EquityMetricContext(
                    label="voice intake completion",
                    metric_type="modality",
                    value=acc.voice_completion_rate,
                    suppressed=False,
                    comparison="completion_rate",
                )
            )
        else:
            metrics.append(
                EquityMetricContext(
                    label="voice intake completion",
                    metric_type="modality",
                    value=None,
                    suppressed=True,
                    comparison="completion_rate",
                )
            )
        start = filters.start_date or date(2026, 1, 1)
        end = filters.end_date or datetime.now(UTC).date()
        return EquityInsightContext(
            dimension="language",
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            metrics=metrics,
        )

    async def _persist(
        self,
        _user: User,
        context: EquityInsightContext,
        output: EquityInsightOutput,
        in_hash: str,
        out_hash: str,
        quality_status: str,
        quality_reason: str | None,
    ) -> PopulationInsightRecord:
        rec = AiPopulationInsightModel(
            insight_type="equity",
            period_start=context.period_start,
            period_end=context.period_end,
            target=context.dimension,
            metric_context=context.model_dump(),
            narrative=self._narrative(output),
            observed_findings=[
                f.model_dump() for f in output.observed_findings
            ],
            possible_interpretations=[
                i.model_dump() for i in output.possible_interpretations
            ],
            limitations=output.limitations,
            requires_human_review=output.requires_human_review,
            provider=self.provider.name,
            model=getattr(self.provider, "model", "") or "",
            prompt_version=EQUITY_INTELLIGENCE_PROMPT_VERSION,
            input_context_hash=in_hash,
            output_hash=out_hash,
            quality_status=quality_status,
            quality_reason=quality_reason,
            review_status="pending_review",
        )
        self.session.add(rec)
        await self.session.commit()
        await self.session.refresh(rec)
        return self._to_record_dto(rec)

    def _narrative(self, output: EquityInsightOutput) -> str:
        parts = ["Observed:"]
        for f in output.observed_findings:
            parts.append(f"- {f.statement}")
        if output.possible_interpretations:
            parts.append("Possible operational interpretation (non-causal):")
            for i in output.possible_interpretations:
                parts.append(f"- {i.interpretation}")
        parts.append(f"Limitations: {output.limitations}")
        return "\n".join(parts)

    def _to_record_dto(
        self, rec: AiPopulationInsightModel
    ) -> PopulationInsightRecord:
        return PopulationInsightRecord(
            id=rec.id,
            insight_type="equity",  # type: ignore[arg-type]
            target=rec.target,
            period_start=rec.period_start,
            period_end=rec.period_end,
            narrative=rec.narrative,
            observed_findings=rec.observed_findings,
            possible_interpretations=rec.possible_interpretations,
            limitations=rec.limitations,
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

    def _fallback(
        self, *, reason: str, quality_status: str
    ) -> EquityInsightResponse:
        return EquityInsightResponse(
            available=False,
            insight=None,
            record=None,
            provider=self.provider.name,
            prompt_version=EQUITY_INTELLIGENCE_PROMPT_VERSION,
            quality_status=quality_status,  # type: ignore[arg-type]
            quality_reason=reason,
        )

    async def _audit(
        self,
        _user: User,
        context: EquityInsightContext,
        output: EquityInsightOutput | None,
        status: str,
        reason: str | None,
    ) -> None:
        try:
            await self.audit.record(
                trace_id=None,
                session_id=None,
                request_type="equity_intelligence",
                provider=self.provider.name,
                model=getattr(self.provider, "model", "") or "",
                prompt_version=EQUITY_INTELLIGENCE_PROMPT_VERSION,
                language="en",
                literacy_level="standard",
                input_context={"dimension": context.dimension, "metric_count": len(context.metrics)},
                output_str=self._narrative(output) if output else "",
                status=status,
                status_reason=reason,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Equity intelligence audit failed: %s", exc)
