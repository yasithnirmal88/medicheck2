"""Phase 11 — AI equity intelligence provider ("left-behind" intelligence).

Operates ONLY on DE-IDENTIFIED, already-aggregated, k-anonymity-suppressed
metrics. The AI explains operational/equity patterns (completion gaps, loss-to-
follow-up, time-to-care, modality/access differences) — it NEVER infers disease
prevalence, causation, or identifies an individual.

Safety enforced structurally:
- ``assert_no_clinical_or_causal``: rejects disease-prevalence / causal /
  individual-identification language.
- entity allow-list: every ``EquityFinding.metric_labels`` entry MUST be a
  subset of the supplied context metric labels — hallucinated labels are
  rejected.
- OBSERVED vs POSSIBLE: findings are observed facts; interpretations are
  explicitly flagged as possible (non-causal) explanations.

Deterministic stub (no external API). Aggregate labels are treated as
UNTRUSTED data (prompt-injection defense) — never as instructions.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Protocol

from app.application.dtos.ai_governance_dtos import (
    EquityFinding,
    EquityInsightContext,
    EquityInsightOutput,
    EquityInterpretation,
)

logger = logging.getLogger(__name__)

EQUITY_INTELLIGENCE_PROMPT_VERSION = "1.0-equity-phase11"

#: Forbidden language: disease prevalence / causation / individual identification.
_FORBIDDEN_EQUITY_TERMS = {
    "diagnos", "disease prevalence", "prevalence of", "causes", "caused by",
    "because of", "due to", "is at risk of disease", "sicker", "unhealthier",
    "poorer health", "has diabetes", "has hypertension", "patient name",
    "phone number", "address", "email", "emergency contact",
}


class EquityIntelligenceProvider(Protocol):
    name: str
    model: str

    def explain(self, context: EquityInsightContext) -> EquityInsightOutput: ...


def assert_no_clinical_or_causal(text: str) -> None:
    """Reject disease-prevalence, causal, or individual-identification language."""
    lower = text.lower()
    for term in _FORBIDDEN_EQUITY_TERMS:
        if term in lower:
            raise ValueError(
                f"AI equity output contains forbidden term: '{term}'"
            )


def _validate_findings(
    findings: list[EquityFinding], allowed_labels: set[str]
) -> list[EquityFinding]:
    for f in findings:
        for label in f.metric_labels:
            if label not in allowed_labels:
                raise ValueError(
                    f"AI equity finding references metric not in context: "
                    f"'{label}'"
                )
        assert_no_clinical_or_causal(f.statement)
    return findings


def _validate_interpretations(
    interps: list[EquityInterpretation],
) -> list[EquityInterpretation]:
    for i in interps:
        assert_no_clinical_or_causal(i.interpretation)
    return interps


class StubEquityIntelligenceProvider:
    """Deterministic local provider over de-identified aggregates."""

    name = "stub"
    model = ""

    def explain(self, context: EquityInsightContext) -> EquityInsightOutput:
        allowed = {m.label for m in context.metrics}
        # Only describe metrics that were NOT suppressed (k-anonymity).
        released = [m for m in context.metrics if not m.suppressed]
        if not released:
            return EquityInsightOutput(
                observed_findings=[],
                possible_interpretations=[],
                limitations=(
                    "Insufficient released data: all cohorts were below the "
                    "k-anonymity threshold for this period. No equity pattern "
                    "could be described."
                ),
                requires_human_review=True,
            )

        findings: list[EquityFinding] = []
        interps: list[EquityInterpretation] = []
        # Detect completion-rate gaps across the dimension.
        rates = [
            (m.label, m.value)
            for m in released
            if m.value is not None and m.comparison == "completion_rate"
        ]
        if len(rates) >= 2:
            rates.sort(key=lambda x: x[1])
            lowest_label, lowest_val = rates[0]
            highest_label, highest_val = rates[-1]
            findings.append(
                EquityFinding(
                    statement=(
                        f"{lowest_label} completion ({lowest_val:.0%}) is "
                        f"lower than {highest_label} ({highest_val:.0%}) in "
                        f"the observed period."
                    ),
                    metric_labels=[lowest_label, highest_label],
                )
            )
            interps.append(
                EquityInterpretation(
                    interpretation=(
                        f"Lower {lowest_label} completion may indicate an "
                        f"accessibility or workflow gap. Further investigation "
                        f"is recommended."
                    ),
                    is_observed=False,
                )
            )

        if not findings:
            findings.append(
                EquityFinding(
                    statement=(
                        f"No notable completion gap observed across "
                        f"{context.dimension} in the released data."
                    ),
                    metric_labels=[m.label for m in released],
                )
            )

        _validate_findings(findings, allowed)
        _validate_interpretations(interps)
        return EquityInsightOutput(
            observed_findings=findings,
            possible_interpretations=interps,
            limitations=(
                "These observations describe aggregate access/completion "
                "patterns only. They do not infer disease prevalence or "
                "causation, and small cohorts are suppressed per the "
                "k-anonymity threshold."
            ),
            requires_human_review=True,
        )


def get_equity_intelligence_provider() -> EquityIntelligenceProvider:
    from app.core.config import settings

    if (settings.ai_equity_provider or "stub").lower() == "stub":
        return StubEquityIntelligenceProvider()
    logger.info(
        "Equity intelligence provider '%s' not implemented; using stub",
        settings.ai_equity_provider,
    )
    return StubEquityIntelligenceProvider()


def compute_equity_input_hash(context: EquityInsightContext) -> str:
    payload = json.dumps(
        context.model_dump(), sort_keys=True, default=str
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def compute_equity_output_hash(output: EquityInsightOutput) -> str:
    payload = json.dumps(
        output.model_dump(), sort_keys=True, default=str
    )
    return hashlib.sha256(payload.encode()).hexdigest()
