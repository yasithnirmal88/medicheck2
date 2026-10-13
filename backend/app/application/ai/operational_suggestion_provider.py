"""Phase 11 — AI-assisted CHW operational suggestion provider.

OPERATIONAL ONLY. Produces a suggestion (reason codes + explanation +
operational priority + confidence) for a CHW's follow-up task using
NON-CLINICAL factors: referral age, overdue duration, contact attempts,
facility/appointment/communication status, language, offline sync status.

NEVER uses: disease severity, probability of disease, medical urgency,
predicted mortality, clinical risk, possible condition, clinical score,
diagnosis. ``assert_non_clinical`` rejects any clinical-urgency language in
the explanation. ``_ALLOWED_REASON_CODES`` is a closed set — anything else is
rejected. The service layer validates ``task_id`` against an allow-list of the
CHW's actual assigned task ids (hallucinated ids are REJECTED).

Deterministic stub (no external API). Reuses the Phase 10
``assert_non_clinical`` pattern.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Protocol

from app.application.dtos.ai_governance_dtos import (
    OperationalQueueContext,
    OperationalQueueSuggestion,
)

logger = logging.getLogger(__name__)

OPERATIONAL_SUGGESTION_PROMPT_VERSION = "1.0-operational-phase11"

#: Closed set of allowed operational reason codes. The provider may ONLY emit
#: codes from this set — anything else is a validation failure.
_ALLOWED_REASON_CODES = {
    "overdue",
    "missing_follow_up",
    "aged_referral",
    "appointment_window",
    "unresolved_admin",
    "unsuccessful_contact",
    "facility_unresponsive",
    "offline_pending_sync",
    "no_outstanding_flags",
}

#: Forbidden clinical-urgency terms — the explanation MUST NOT contain these.
_FORBIDDEN_CLINICAL_TERMS = {
    "severe", "severity", "urgent clinically", "critical", "life-threatening",
    "mortality", "morbidity", "diagnos", "probability of disease",
    "clinical risk", "medical urgency", "prognosis", "high-risk patient",
    "medically", "disease risk",
}


class OperationalSuggestionProvider(Protocol):
    name: str
    model: str

    def suggest(
        self, contexts: list[OperationalQueueContext]
    ) -> list[OperationalQueueSuggestion]: ...


def assert_non_clinical(text: str) -> None:
    """Reject any clinical-urgency language in AI operational output."""
    lower = text.lower()
    for term in _FORBIDDEN_CLINICAL_TERMS:
        if term in lower:
            raise ValueError(
                f"AI operational suggestion contains forbidden clinical term: "
                f"'{term}'"
            )


def _validate_reason_codes(codes: list[str]) -> list[str]:
    for c in codes:
        if c not in _ALLOWED_REASON_CODES:
            raise ValueError(
                f"AI emitted disallowed operational reason code: '{c}'"
            )
    return codes


class StubOperationalSuggestionProvider:
    """Deterministic local provider. Operational factors only."""

    name = "stub"
    model = ""

    def suggest(
        self, contexts: list[OperationalQueueContext]
    ) -> list[OperationalQueueSuggestion]:
        out: list[OperationalQueueSuggestion] = []
        for ctx in contexts:
            codes: list[str] = []
            score = 0.0
            if ctx.overdue_days is not None and ctx.overdue_days > 0:
                codes.append("overdue")
                score += 0.35
            if ctx.contact_attempts >= 2:
                codes.append("unsuccessful_contact")
                score += 0.20
            if ctx.facility_status in {"sent", "received"}:
                codes.append("facility_unresponsive")
                score += 0.10
            if ctx.referral_age_days >= 7:
                codes.append("aged_referral")
                score += 0.15
            if ctx.offline_status == "pending_sync":
                codes.append("offline_pending_sync")
                score += 0.05
            if ctx.appointment_status == "unscheduled":
                codes.append("unresolved_admin")
                score += 0.10
            if not codes:
                codes.append("no_outstanding_flags")
            score = min(score, 1.0)
            explanation = self._explanation(ctx, codes)
            assert_non_clinical(explanation)
            _validate_reason_codes(codes)
            out.append(
                OperationalQueueSuggestion(
                    task_id=ctx.task_id,
                    operational_reason_codes=codes,  # type: ignore[arg-type]
                    explanation=explanation,
                    operational_priority_score=round(score, 3),
                    confidence=0.8,
                    requires_human_review=True,
                )
            )
        return out

    def _explanation(
        self, ctx: OperationalQueueContext, codes: list[str]
    ) -> str:
        if "no_outstanding_flags" in codes:
            return (
                "No outstanding operational flags for this follow-up task."
            )
        parts: list[str] = []
        if "overdue" in codes:
            days = ctx.overdue_days or 0
            parts.append(f"follow-up is overdue by {int(days)} day(s)")
        if "unsuccessful_contact" in codes:
            parts.append(
                f"{ctx.contact_attempts} contact attempt(s) have not been "
                f"completed"
            )
        if "aged_referral" in codes:
            parts.append(f"referral has been open for {int(ctx.referral_age_days)} day(s)")
        if "facility_unresponsive" in codes:
            parts.append("the receiving facility has not yet responded")
        if "offline_pending_sync" in codes:
            parts.append("an offline session is pending synchronization")
        if "unresolved_admin" in codes:
            parts.append("an appointment has not been scheduled")
        return "Operational priority: " + "; ".join(parts) + "."


def get_operational_suggestion_provider() -> OperationalSuggestionProvider:
    from app.core.config import settings

    if (settings.ai_operational_provider or "stub").lower() == "stub":
        return StubOperationalSuggestionProvider()
    # Unknown/unconfigured vendor -> fall back to stub (never breaks the queue).
    logger.info(
        "Operational suggestion provider '%s' not implemented; using stub",
        settings.ai_operational_provider,
    )
    return StubOperationalSuggestionProvider()


def compute_operational_input_hash(
    contexts: list[OperationalQueueContext],
) -> str:
    payload = json.dumps(
        [c.model_dump() for c in contexts], sort_keys=True, default=str
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def compute_operational_output_hash(
    suggestions: list[OperationalQueueSuggestion],
) -> str:
    payload = json.dumps(
        [s.model_dump() for s in suggestions], sort_keys=True, default=str
    )
    return hashlib.sha256(payload.encode()).hexdigest()
