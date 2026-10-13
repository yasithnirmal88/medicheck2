"""Phase 11 — AI SDG / population narrative provider.

Generates human-reviewable narratives for SDG 3.4 / 3.8 / 10 from DE-IDENTIFIED,
already-aggregated, k-anonymity-suppressed SDG metric rows. The AI may ONLY
describe metrics supplied in the context — any indicator/metric it references
that is not in the allow-list is REJECTED.

Safety enforced structurally:
- ``assert_narrative_safe``: rejects disease-prevalence, causal, individual-
  identification, and "SDG achieved" claims not supported by data.
- entity allow-list: ``metrics_used`` MUST be a subset of supplied row labels.
- The AI describes OBSERVED trends + a POSSIBLE operational interpretation;
  it never claims causation or official SDG achievement.

Deterministic stub (no external API). SDG row labels are treated as UNTRUSTED
data (prompt-injection defense) — never as instructions.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Protocol

from app.application.dtos.ai_governance_dtos import (
    SdgNarrativeContext,
    SdgNarrativeOutput,
)

logger = logging.getLogger(__name__)

SDG_NARRATIVE_PROMPT_VERSION = "1.0-sdg-narrative-phase11"

_FORBIDDEN_NARRATIVE_TERMS = {
    "diagnos", "disease prevalence", "prevalence of", "causes", "caused by",
    "because of", "due to", "sdg achieved", "target achieved",
    "has been achieved", "target has been achieved",
    "patient name", "phone number", "address", "email",
    "sicker", "unhealthier", "poorer health",
}


class PopulationNarrativeProvider(Protocol):
    name: str
    model: str

    def narrate(
        self, contexts: list[SdgNarrativeContext]
    ) -> list[SdgNarrativeOutput]: ...


def assert_narrative_safe(text: str) -> None:
    lower = text.lower()
    for term in _FORBIDDEN_NARRATIVE_TERMS:
        if term in lower:
            raise ValueError(
                f"AI SDG narrative contains forbidden term: '{term}'"
            )


def _validate_metrics_used(
    used: list[str], allowed: set[str]
) -> list[str]:
    for m in used:
        if m not in allowed:
            raise ValueError(
                f"AI SDG narrative references metric not in context: '{m}'"
            )
    return used


class StubPopulationNarrativeProvider:
    """Deterministic local provider over de-identified SDG aggregates."""

    name = "stub"
    model = ""

    def narrate(
        self, contexts: list[SdgNarrativeContext]
    ) -> list[SdgNarrativeOutput]:
        outputs: list[SdgNarrativeOutput] = []
        for ctx in contexts:
            allowed = {r.label for r in ctx.rows}
            released = [r for r in ctx.rows if not r.suppressed]
            if not released:
                out = SdgNarrativeOutput(
                    target=ctx.target,
                    reporting_period=(
                        f"{ctx.period_start} to {ctx.period_end}"
                        if ctx.period_start
                        else None
                    ),
                    metrics_used=[],
                    observed_trends=[],
                    limitations=(
                        "Insufficient released data: all metrics were below "
                        "the k-anonymity threshold. No narrative could be "
                        "generated."
                    ),
                    possible_operational_interpretation=(
                        "No operational interpretation possible from "
                        "suppressed data."
                    ),
                    requires_human_review=True,
                )
                outputs.append(out)
                continue

            metrics_used = [r.label for r in released]
            _validate_metrics_used(metrics_used, allowed)
            trends: list[str] = []
            for r in released:
                if r.value is not None:
                    trends.append(
                        f"{r.label}: {r.value}"
                        + (f" ({r.comparison})" if r.comparison else "")
                    )
            interpretation = (
                f"The observed SDG {ctx.target} metrics reflect platform "
                f"screening/care-continuity activity. Any decrease in "
                f"completion or referral rates may indicate a care-continuity "
                f"bottleneck and warrants investigation."
            )
            assert_narrative_safe(interpretation)
            for t in trends:
                assert_narrative_safe(t)
            out = SdgNarrativeOutput(
                target=ctx.target,
                reporting_period=(
                    f"{ctx.period_start} to {ctx.period_end}"
                    if ctx.period_start
                    else None
                ),
                metrics_used=metrics_used,
                observed_trends=trends,
                limitations=(
                    "These are platform-derived monitoring indicators aligned "
                    "with SDG targets. They do not prove an SDG target has "
                    "been achieved and are not official UN SDG indicators. "
                    "Small cohorts are suppressed per the k-anonymity threshold."
                ),
                possible_operational_interpretation=interpretation,
                requires_human_review=True,
            )
            outputs.append(out)
        return outputs


def get_population_narrative_provider() -> PopulationNarrativeProvider:
    from app.core.config import settings

    if (settings.ai_population_narrative_provider or "stub").lower() == "stub":
        return StubPopulationNarrativeProvider()
    logger.info(
        "Population narrative provider '%s' not implemented; using stub",
        settings.ai_population_narrative_provider,
    )
    return StubPopulationNarrativeProvider()


def compute_narrative_input_hash(
    contexts: list[SdgNarrativeContext],
) -> str:
    payload = json.dumps(
        [c.model_dump() for c in contexts], sort_keys=True, default=str
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def compute_narrative_output_hash(
    outputs: list[SdgNarrativeOutput],
) -> str:
    payload = json.dumps(
        [o.model_dump() for o in outputs], sort_keys=True, default=str
    )
    return hashlib.sha256(payload.encode()).hexdigest()
