"""Phase 4 — Longitudinal AI explanation provider abstraction.

Mirrors the Phase 1 ``AIExplanationProvider`` pattern: the service depends on a
Protocol, not a vendor SDK. The deterministic stub provider builds a valid
explanation strictly from the supplied deterministic longitudinal context — it
never invents entities, ids, or evidence, and never calls a network service.
A real vendor provider can implement the Protocol later with no service-layer
change.
"""

from __future__ import annotations

import json
from typing import Any, Protocol, runtime_checkable

from app.application.ai.longitudinal_prompts import LONGITUDINAL_PROMPT_VERSION
from app.application.dtos.longitudinal_dtos import (
    LongitudinalExplanationContext,
    assert_non_diagnostic,
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@runtime_checkable
class LongitudinalExplanationProvider(Protocol):
    """Produces a raw JSON string explanation of a deterministic trajectory."""

    async def explain_trajectory(
        self, context: LongitudinalExplanationContext
    ) -> str: ...


class AIProviderError(RuntimeError):
    """Raised when the longitudinal AI provider cannot produce a usable response."""


class StubLongitudinalProvider:
    """Deterministic local provider — the default.

    Builds a valid explanation JSON strictly from the supplied deterministic
    trajectory context. Never invents entities/ids/evidence.
    """

    name = "stub-longitudinal"

    async def explain_trajectory(
        self, context: LongitudinalExplanationContext
    ) -> str:
        try:
            bs_changes = context.body_system_changes
            ind = context.indicator_changes
            cond = context.condition_changes
            rec = context.recommendation_changes
            overall = context.overall_change

            key_changes: list[dict[str, Any]] = []
            if overall:
                key_changes.append({
                    "label": overall.get("label", "Overall severity"),
                    "ref_type": "body_system",
                    "ref_id": None,
                    "explanation": assert_non_diagnostic(
                        _overall_phrase(overall)
                    ),
                    "evidence_ids": [],
                })
            for c in bs_changes:
                key_changes.append({
                    "label": c.get("label", "Body system"),
                    "ref_type": "body_system",
                    "ref_id": c.get("ref_id"),
                    "explanation": assert_non_diagnostic(_bs_phrase(c)),
                    "evidence_ids": [],
                })

            def _findings(group: list[str], ref_type: str, kind: str) -> list[dict[str, Any]]:
                return [
                    {
                        "label": f"{ref_type} {rid}",
                        "ref_type": ref_type,
                        "ref_id": rid,
                        "explanation": assert_non_diagnostic(
                            f"The {ref_type} {rid} was {kind} in the latest assessment."
                        ),
                        "evidence_ids": [],
                    }
                    for rid in group
                ]

            new_findings = (
                _findings(ind.get("new", []), "indicator", "newly activated")
                + _findings(cond.get("new", []), "condition", "newly appearing as a possible condition")
            )
            persistent_findings = (
                _findings(ind.get("persistent", []), "indicator", "persistent")
                + _findings(cond.get("persistent", []), "condition", "a persistent possible condition")
            )
            improved_findings = _findings(ind.get("resolved", []), "indicator", "no longer activated")
            stable_findings: list[dict[str, Any]] = [
                {
                    "label": f"body system {c.get('ref_id')}",
                    "ref_type": "body_system",
                    "ref_id": c.get("ref_id"),
                    "explanation": assert_non_diagnostic(_stable_phrase(c)),
                    "evidence_ids": [],
                }
                for c in bs_changes
                if c.get("trend") == "stable"
            ]

            important_context: list[str] = []
            if not context.evidence_available:
                important_context.append(
                    "No supporting evidence was available from the MediCheck "
                    "evidence repository for this explanation."
                )
            important_context.append(
                "These are changes in assessment findings over time, not confirmed "
                "diagnoses or disease progression."
            )

            summary = assert_non_diagnostic(_summary(overall, ind, cond, rec))

            payload: dict[str, Any] = {
                "available": True,
                "summary": summary,
                "key_changes": key_changes,
                "persistent_findings": persistent_findings,
                "new_findings": new_findings,
                "improved_findings": improved_findings,
                "stable_findings": stable_findings,
                "important_context": important_context,
                "evidence_ids": [],
                "prompt_version": LONGITUDINAL_PROMPT_VERSION,
                "trace_ids": context.trace_ids,
                "disclaimer": (
                    "This AI-generated explanation summarizes changes in your "
                    "assessment history and does not diagnose conditions or replace "
                    "professional medical advice."
                ),
            }
            return json.dumps(payload)
        except ValueError:
            # Non-diagnostic guard tripped — surface as a provider error so the
            # service falls back safely.
            raise AIProviderError("stub produced diagnostic language")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("stub longitudinal provider failed: %s", exc)
            raise AIProviderError("stub longitudinal provider failure") from exc


def _overall_phrase(overall: dict[str, Any]) -> str:
    trend = overall.get("trend", "stable")
    prev = overall.get("previous_value")
    curr = overall.get("current_value")
    if trend == "worsening":
        return f"Your overall assessment severity increased from {prev} to {curr} across your recent assessments."
    if trend == "improving":
        return f"Your overall assessment severity decreased from {prev} to {curr} across your recent assessments."
    return f"Your overall assessment severity remained {curr} across your recent assessments."


def _bs_phrase(c: dict[str, Any]) -> str:
    label = c.get("label", "this body system")
    trend = c.get("trend", "stable")
    prev = c.get("previous_value")
    curr = c.get("current_value")
    if trend == "new":
        return f"{label} was newly flagged in the latest assessment."
    if trend == "removed":
        return f"{label} was no longer flagged in the latest assessment."
    if trend == "worsening":
        return f"{label} assessment findings were higher in severity ({prev} → {curr})."
    if trend == "improving":
        return f"{label} assessment findings were lower in severity ({prev} → {curr})."
    return f"{label} assessment findings remained stable at {curr}."


def _stable_phrase(c: dict[str, Any]) -> str:
    label = c.get("label", "this body system")
    curr = c.get("current_value")
    return f"{label} assessment findings remained stable at {curr}."


def _summary(overall, ind, cond, rec) -> str:
    parts: list[str] = []
    if overall:
        t = overall.get("trend", "stable")
        if t == "worsening":
            parts.append("Your latest assessment showed higher-severity findings overall.")
        elif t == "improving":
            parts.append("Your latest assessment showed lower-severity findings overall.")
        else:
            parts.append("Your overall assessment findings were stable.")
    if ind:
        n_new = len(ind.get("new", []))
        n_res = len(ind.get("resolved", []))
        if n_new:
            parts.append(f"{n_new} finding(s) were newly activated.")
        if n_res:
            parts.append(f"{n_res} finding(s) were no longer activated.")
    if cond:
        n_new = len(cond.get("new", []))
        n_rem = len(cond.get("removed", []))
        if n_new:
            parts.append(f"{n_new} possible condition(s) appeared.")
        if n_rem:
            parts.append(f"{n_rem} possible condition(s) were no longer present.")
    if not parts:
        parts.append("Your assessment findings were largely stable across recent assessments.")
    parts.append("These are assessment findings, not confirmed diagnoses.")
    return " ".join(parts)


def get_longitudinal_provider() -> LongitudinalExplanationProvider:
    """Return the configured longitudinal AI provider (default: stub)."""
    name = (settings.ai_provider or "stub").strip().lower()
    if name == "stub":
        return StubLongitudinalProvider()
    logger.info(
        "AI provider '%s' not implemented for longitudinal; using stub", name
    )
    return StubLongitudinalProvider()
