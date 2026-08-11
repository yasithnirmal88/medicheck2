"""AI provider abstraction for the Phase 1 explanation layer.

The application service depends on the ``AIExplanationProvider`` Protocol, not
on any concrete vendor SDK. This keeps the clinical/explanation code decoupled
from a specific LLM vendor and lets a deterministic stub provider be used in
development/tests (and as the default) without any external API key or network
dependency.

A real vendor provider can be added later by implementing the Protocol and
selecting it via ``settings.ai_provider`` — no change to the service layer is
required. Phase 1 ships only the stub provider; no third-party AI packages are
installed.
"""

from __future__ import annotations

import json
from typing import Any, Protocol, runtime_checkable

from app.application.dtos.ai_dtos import (
    NO_EVIDENCE_AVAILABLE_MESSAGE,
    ReportExplanationContext,
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@runtime_checkable
class AIExplanationProvider(Protocol):
    """Produces a raw JSON string explanation for a report context.

    Implementations MUST:
    - return only data derived from the supplied ``context`` (no external
      clinical facts, no invented ids),
    - raise ``AIProviderError`` on any failure (timeout, network, malformed,
      auth) so the service can fall back gracefully.

    The returned string is parsed + validated by the service layer; raw output
    is never trusted.
    """

    async def explain(self, context: ReportExplanationContext) -> str: ...


class AIProviderError(RuntimeError):
    """Raised when an AI provider cannot produce a response at all.

    This is a *provider-down* condition: timeout, network, auth, rate limit.
    Maps to ``AIQualityStatus.PROVIDER_UNAVAILABLE`` in the audit trail.
    """


class AIValidationFailure(RuntimeError):
    """Raised when the AI returns a syntactically or semantically invalid
    response (non-JSON, unknown indicator id, hallucinated citation).

    The provider *was* reachable, but its output is unusable. Maps to
    ``AIQualityStatus.VALIDATION_FAILED`` in the audit trail.
    """


class StubExplanationProvider:
    """Deterministic local provider — the default.

    It builds a valid explanation JSON strictly from the supplied context using
    the indicator/condition/recommendation names already present. It never
    calls a network service and never invents entities, so it is safe to use
    in development, tests, and production environments that have not yet
    configured a real LLM provider.
    """

    name = "stub"

    async def explain(self, context: ReportExplanationContext) -> str:
        try:
            # Evidence by linked indicator, for citation grounding.
            ev_by_indicator: dict[str, list[Any]] = {}
            for ev in context.evidence:
                if ev.linked_entity_type == "indicator":
                    ev_by_indicator.setdefault(ev.linked_entity_id, []).append(ev)

            findings = []
            for ind in context.activated_indicators:
                linked = ev_by_indicator.get(ind.id, [])
                findings.append(
                    {
                        "title": ind.name or "Assessment finding",
                        "explanation": _indicator_explanation(ind, has_evidence=bool(linked)),
                        "source_indicator_ids": [ind.id],
                        "evidence_ids": [ev.id for ev in linked],
                    }
                )

            # Recommendation evidence (tier 3) for citation grounding.
            ev_by_rec: dict[str, list[Any]] = {}
            for ev in context.evidence:
                if ev.linked_entity_type == "recommendation":
                    ev_by_rec.setdefault(ev.linked_entity_id, []).append(ev)
            rec_exps = []
            for r in context.recommendations:
                linked = ev_by_rec.get(r.id, [])
                rec_exps.append(
                    {
                        "recommendation_id": r.id,
                        "explanation": (r.text or r.title or "Recommended follow-up.")
                        + (
                            " This recommendation is supported by supplied "
                            "MediCheck evidence." if linked else ""
                        ),
                        "evidence_ids": [ev.id for ev in linked],
                    }
                )

            body_summary = ", ".join(
                filter(None, [b.name or b.body_system_id for b in context.body_systems])
            ) or "no specific body systems flagged"

            cond_names = ", ".join(c.name for c in context.possible_conditions) or "none"

            summary = (
                f"Your assessment flagged {len(context.activated_indicators)} "
                f"finding(s) across: {body_summary}. "
                f"Possible condition(s) considered by the engine: {cond_names}. "
                "These are assessment signals, not confirmed diagnoses."
            )

            severity_explanation = _severity_explanation(context.severity)

            evidence_notes = []
            if context.evidence_available and context.evidence:
                for ev in context.evidence[:5]:
                    note = ev.title
                    if ev.evidence_level:
                        note += f" (evidence level {ev.evidence_level})"
                    if ev.source:
                        note += f" — {ev.source}"
                    evidence_notes.append(note)
            else:
                # Phase 2 safety: never pretend evidence exists.
                evidence_notes.append(NO_EVIDENCE_AVAILABLE_MESSAGE)

            payload: dict[str, Any] = {
                "summary": summary,
                "key_findings": findings,
                "severity_explanation": severity_explanation,
                "recommendation_explanations": rec_exps,
                "evidence_notes": evidence_notes,
                "limitations": (
                    "This explanation describes what the deterministic "
                    "assessment found. It is not a diagnosis and does not "
                    "replace evaluation by a qualified clinician."
                ),
                "disclaimer": (
                    "This AI-generated explanation is based on your MediCheck "
                    "assessment and does not constitute a diagnosis. The "
                    "underlying assessment is generated by the deterministic "
                    "clinical engine."
                ),
            }
            return json.dumps(payload)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("stub explanation provider failed: %s", exc)
            raise AIProviderError("stub provider failure") from exc


def _indicator_explanation(ind: Any, has_evidence: bool = False) -> str:
    parts = [ind.name or "This finding"]
    if ind.severity:
        parts.append(f"is rated {ind.severity} severity")
    else:
        parts.append("was flagged by the assessment")
    if ind.evidence_strength:
        parts.append(f"(evidence strength {ind.evidence_strength})")
    base = (
        " ".join(parts)
        + ". It is a signal from your answers, not a confirmed condition."
    )
    if has_evidence:
        base += " Supporting evidence from the MediCheck evidence repository is cited below."
    return base


def _severity_explanation(severity: str | None) -> str:
    if not severity:
        return (
            "No overall severity category was assigned to this report. "
            "Individual findings carry their own severity where applicable."
        )
    table = {
        "none": "No notable severity was detected by the assessment.",
        "mild": "Mild severity: findings are present but low in intensity.",
        "moderate": "Moderate severity: findings warrant attention and follow-up.",
        "severe": "Severe severity: findings are significant and should be discussed with a clinician.",
        "high": "High severity: findings are significant and should be discussed with a clinician.",
        "critical": "Critical severity: findings are urgent — seek timely clinical review.",
        "Normal": "Findings are within normal range.",
        "Monitor": "Findings are worth monitoring over time.",
        "Needs Attention": "Findings need attention and possible follow-up.",
        "Recommend Screening": "The assessment suggests screening may be appropriate.",
        "Urgent Medical Review": "The assessment suggests urgent medical review.",
    }
    return table.get(
        severity,
        f"The reported severity category is '{severity}'. It is an assessment label, not a diagnosis.",
    )


def get_explanation_provider() -> AIExplanationProvider:
    """Return the configured AI explanation provider.

    Defaults to the deterministic stub provider. Phase 7 adds a
    ``personalized-stub`` provider that supports multilingual + health-literacy
    levels; select it by setting ``AI_PROVIDER=personalized-stub``.
    """
    name = (settings.ai_provider or "stub").strip().lower()
    if name == "personalized-stub":
        from app.application.ai.personalized_provider import (
            PersonalizedExplanationProvider,
        )

        return PersonalizedExplanationProvider()
    if name == "stub":
        return StubExplanationProvider()
    # Unknown / unconfigured vendor → fall back to the stub so the report is
    # never broken. A future phase wires a real provider here.
    logger.info(
        "AI provider '%s' not implemented in Phase 1; using stub provider", name
    )
    return StubExplanationProvider()
