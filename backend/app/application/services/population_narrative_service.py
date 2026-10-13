"""Phase 11 — AI SDG / population narrative service.

Composes DE-IDENTIFIED, already-aggregated, k-anonymity-suppressed SDG metric
rows from the Phase 10 ``SdgExportService`` into ``SdgNarrativeContext``
objects (one per SDG target), invokes the population-narrative provider,
validates the output (entity allow-list, no unsupported/causal/identification
claims), persists each narrative with a PENDING_REVIEW lifecycle, and audits
via ``AIAuditService``.

The AI may ONLY describe metrics supplied in the context. SDG row labels are
treated as UNTRUSTED data (prompt-injection defense). If the AI fails, the
underlying deterministic SDG rows remain available. AI never self-publishes.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.population_narrative_provider import (
    SDG_NARRATIVE_PROMPT_VERSION,
    compute_narrative_input_hash,
    compute_narrative_output_hash,
    get_population_narrative_provider,
)
from app.application.dtos.ai_governance_dtos import (
    EquityMetricContext,
    PopulationInsightRecord,
    SdgNarrativeContext,
    SdgNarrativeOutput,
    SdgNarrativeResponse,
)
from app.application.dtos.analytics_dtos import AnalyticsFilters
from app.application.dtos.interoperability_dtos import SdgExportRow
from app.application.services.ai_audit_service import AIAuditService
from app.application.services.sdg_export_service import SdgExportService
from app.core.config import settings
from app.core.exceptions import AuthorizationError
from app.domain.entities.user import User
from app.infrastructure.persistence.models.ai_population_insight import (
    AiPopulationInsightModel,
)

logger = logging.getLogger(__name__)

#: Map SDG row indicators to their SDG target for grouping.
_INDICATOR_TO_TARGET = {
    "sdg-3-4": "3.4",
    "sdg-3-8": "3.8",
    "sdg-10": "10",
}


def _target_for(indicator: str) -> str:
    for prefix, target in _INDICATOR_TO_TARGET.items():
        if indicator.startswith(prefix):
            return target
    return "unknown"


class PopulationNarrativeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.provider = get_population_narrative_provider()
        self.audit = AIAuditService(session)
        self.sdg = SdgExportService(session)

    async def generate_narratives(
        self, user: User, filters: AnalyticsFilters
    ) -> SdgNarrativeResponse:
        self._assert_access(user)
        export = await self.sdg.export(filters)
        contexts = self._build_contexts(export.rows, filters)
        if not contexts:
            return self._fallback("No SDG metrics available for the period.")

        in_hash = compute_narrative_input_hash(contexts)
        try:
            outputs = self.provider.narrate(contexts)
        except Exception as exc:
            logger.warning("Population narrative provider failed: %s", exc)
            await self._audit(user, contexts, None, "validation_failed", str(exc))
            return self._fallback(
                f"AI narrative output rejected: {exc}",
                quality_status="validation_failed",
            )

        out_hash = compute_narrative_output_hash(outputs)
        records: list[PopulationInsightRecord] = []
        try:
            self._validate_outputs(outputs, contexts)
        except Exception as exc:
            logger.warning("Population narrative output rejected: %s", exc)
            await self._audit(user, contexts, outputs, "validation_failed", str(exc))
            return self._fallback(
                f"AI narrative output rejected: {exc}",
                quality_status="validation_failed",
            )
        for out in outputs:
            rec = await self._persist(
                out, in_hash, out_hash, "valid", None
            )
            records.append(rec)
        await self._audit(user, contexts, outputs, "success", None)
        return SdgNarrativeResponse(
            available=True,
            narratives=outputs,
            records=records,
            provider=self.provider.name,
            prompt_version=SDG_NARRATIVE_PROMPT_VERSION,
            quality_status="valid",
        )

    async def list_narratives(
        self, user: User, *, limit: int | None = None
    ) -> list[PopulationInsightRecord]:
        self._assert_access(user)
        cap = min(
            limit or settings.ai_insight_max_results,
            settings.ai_insight_max_results,
        )
        stmt = (
            select(AiPopulationInsightModel)
            .where(
                AiPopulationInsightModel.insight_type == "sdg_narrative",
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

    def _validate_outputs(
        self,
        outputs: list[SdgNarrativeOutput],
        contexts: list[SdgNarrativeContext],
    ) -> None:
        """Defense-in-depth: validate narrative output before persisting.

        Re-runs the provider's safety checks (entity allow-list + narrative
        safety) so a misbehaving/real LLM provider can never persist
        hallucinated metrics, unsupported claims, or 'SDG achieved' language.
        """
        from app.application.ai.population_narrative_provider import (
            _validate_metrics_used,
            assert_narrative_safe,
        )

        allowed_by_target = {
            c.target: {r.label for r in c.rows} for c in contexts
        }
        for out in outputs:
            _validate_metrics_used(
                out.metrics_used, allowed_by_target.get(out.target, set())
            )
            for t in out.observed_trends:
                assert_narrative_safe(t)
            assert_narrative_safe(out.possible_operational_interpretation)

    def _build_contexts(
        self, rows: list[SdgExportRow], filters: AnalyticsFilters
    ) -> list[SdgNarrativeContext]:
        by_target: dict[str, list[SdgExportRow]] = defaultdict(list)
        for r in rows:
            by_target[_target_for(r.indicator)].append(r)
        start = (filters.start_date or date(2026, 1, 1)).isoformat()
        end = (filters.end_date or datetime.now(UTC).date()).isoformat()
        contexts: list[SdgNarrativeContext] = []
        for target, trows in by_target.items():
            if target == "unknown":
                continue
            metrics: list[EquityMetricContext] = []
            for r in trows:
                metrics.append(
                    EquityMetricContext(
                        label=r.indicator,
                        metric_type=r.indicator_type,
                        value=r.value,
                        numerator=r.numerator,
                        denominator=r.denominator,
                        suppressed=r.suppression_status == "suppressed",
                        comparison=r.unit,
                    )
                )
            contexts.append(
                SdgNarrativeContext(
                    target=target,
                    period_start=start,
                    period_end=end,
                    rows=metrics,
                )
            )
        return contexts

    async def _persist(
        self,
        out: SdgNarrativeOutput,
        in_hash: str,
        out_hash: str,
        quality_status: str,
        quality_reason: str | None,
    ) -> PopulationInsightRecord:
        rec = AiPopulationInsightModel(
            insight_type="sdg_narrative",
            period_start=out.reporting_period,
            period_end=None,
            target=out.target,
            metric_context={"metrics_used": out.metrics_used},
            narrative=self._narrative(out),
            observed_findings=[{"trend": t} for t in out.observed_trends],
            possible_interpretations=[
                {"interpretation": out.possible_operational_interpretation}
            ],
            limitations=out.limitations,
            requires_human_review=out.requires_human_review,
            provider=self.provider.name,
            model=getattr(self.provider, "model", "") or "",
            prompt_version=SDG_NARRATIVE_PROMPT_VERSION,
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

    def _narrative(self, out: SdgNarrativeOutput) -> str:
        parts = [f"SDG {out.target} narrative ({out.reporting_period or 'n/a'})."]
        parts.append(f"Population scope: {out.population_scope}.")
        if out.observed_trends:
            parts.append("Observed trends:")
            for t in out.observed_trends:
                parts.append(f"- {t}")
        parts.append(f"Possible operational interpretation: {out.possible_operational_interpretation}")
        parts.append(f"Limitations: {out.limitations}")
        return "\n".join(parts)

    def _to_record_dto(
        self, rec: AiPopulationInsightModel
    ) -> PopulationInsightRecord:
        return PopulationInsightRecord(
            id=rec.id,
            insight_type="sdg_narrative",  # type: ignore[arg-type]
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
        self, reason: str, *, quality_status: str = "valid"
    ) -> SdgNarrativeResponse:
        return SdgNarrativeResponse(
            available=False,
            narratives=[],
            records=[],
            provider=self.provider.name,
            prompt_version=SDG_NARRATIVE_PROMPT_VERSION,
            quality_status=quality_status,  # type: ignore[arg-type]
            quality_reason=reason,
        )

    async def _audit(
        self,
        _user: User,
        contexts: list[SdgNarrativeContext],
        outputs: list[SdgNarrativeOutput] | None,
        status: str,
        reason: str | None,
    ) -> None:
        try:
            await self.audit.record(
                trace_id=None,
                session_id=None,
                request_type="sdg_narrative",
                provider=self.provider.name,
                model=getattr(self.provider, "model", "") or "",
                prompt_version=SDG_NARRATIVE_PROMPT_VERSION,
                language="en",
                literacy_level="standard",
                input_context={
                    "targets": [c.target for c in contexts],
                    "row_count": sum(len(c.rows) for c in contexts),
                },
                output_str=(
                    " | ".join(self._narrative(o) for o in outputs)
                    if outputs
                    else ""
                ),
                status=status,
                status_reason=reason,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("SDG narrative audit failed: %s", exc)
