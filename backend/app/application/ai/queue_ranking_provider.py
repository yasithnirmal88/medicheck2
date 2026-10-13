"""Phase 10 — AI-assisted CHW queue ranking provider.

OPERATIONAL ONLY. Ranks a CHW's referral follow-up tasks by non-clinical
factors: referral age, overdue status, missing follow-up, appointment window,
unresolved administrative status. 

NEVER ranks by: disease severity, probability of disease, medical urgency,
predicted mortality, clinical risk. Clinical urgency remains deterministic
and/or explicitly assigned by the existing clinical workflow (CDSE). The
stub provider is deterministic (no external API) and validates its own output
to reject any clinical-urgency language.

Reuses the Phase 7 AI governance audit pattern (AIAuditService) — records
hashes + reference ids only, NO PHI.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

QUEUE_RANKING_PROMPT_VERSION = "1.0-operational"

#: Forbidden clinical-urgency terms — the provider MUST NOT use these in its
#: rationale (enforced by assert_non_clinical).
_FORBIDDEN_CLINICAL_TERMS = {
    "severe", "severity", "urgent clinically", "critical", "life-threatening",
    "mortality", "morbidity", "diagnos", "probability of disease",
    "clinical risk", "medical urgency", "prognosis",
}


class QueueTaskInput(BaseModel):
    """A single task in the CHW queue (PHI-scrubbed, operational only)."""
    referral_id: str
    task_id: str | None = None
    referral_age_days: float
    overdue: bool
    missing_follow_up: bool
    appointment_window_days: float | None = None
    region: str | None = None
    unresolved_admin_status: bool
    # Clinical fields are intentionally absent. The deterministic clinical
    # priority (if any) is already separately available to the CHW and is
    # NEVER re-ranked by AI.


class QueueRankingInput(BaseModel):
    chw_user_id: str
    tasks: list[QueueTaskInput]


class RankedTask(BaseModel):
    referral_id: str
    task_id: str | None = None
    rank: int
    score: float
    rationale: str
    factors: list[str] = []


class QueueRankingOutput(BaseModel):
    available: bool = True
    ranked_tasks: list[RankedTask] = []
    provider: str = "stub"
    model: str = ""
    prompt_version: str = QUEUE_RANKING_PROMPT_VERSION
    transparency_notice: str = (
        "AI assistance organizes administrative workload only. It does not "
        "determine clinical risk, urgency, or diagnosis."
    )
    quality_status: str = "valid"


class QueueRankingProvider(Protocol):
    name: str
    model: str

    def rank(self, data: QueueRankingInput) -> QueueRankingOutput: ...


def assert_non_clinical(text: str) -> None:
    """Reject any clinical-urgency language in AI output."""
    lower = text.lower()
    for term in _FORBIDDEN_CLINICAL_TERMS:
        if term in lower:
            raise ValueError(
                f"AI queue-ranking output contains forbidden clinical term: '{term}'"
            )


class StubQueueRankingProvider:
    """Deterministic local provider. Operational factors only."""

    name = "stub"
    model = ""

    def rank(self, data: QueueRankingInput) -> QueueRankingOutput:
        scored: list[tuple[float, QueueTaskInput, list[str], str]] = []
        for task in data.tasks:
            score = 0.0
            factors: list[str] = []
            # Operational scoring (deterministic, no clinical factors):
            # overdue + missing follow-up + referral age + appointment window.
            if task.overdue:
                score += 40.0
                factors.append("overdue")
            if task.missing_follow_up:
                score += 25.0
                factors.append("missing_follow_up")
            # Referral age: older referrals rank higher (cap at 20).
            age_score = min(task.referral_age_days, 30.0) / 30.0 * 20.0
            score += age_score
            if task.referral_age_days >= 7:
                factors.append("aged_referral")
            # Appointment window: tasks within a near appointment window +10.
            if task.appointment_window_days is not None and 0 <= task.appointment_window_days <= 3:
                score += 10.0
                factors.append("appointment_window")
            if task.unresolved_admin_status:
                score += 5.0
                factors.append("unresolved_admin")
            rationale = self._rationale(factors)
            assert_non_clinical(rationale)
            scored.append((score, task, factors, rationale))

        # Deterministic ordering: score desc, then referral_id asc (stable).
        scored.sort(key=lambda x: (-x[0], x[1].referral_id))
        ranked: list[RankedTask] = []
        for idx, (score, task, factors, rationale) in enumerate(scored, start=1):
            ranked.append(
                RankedTask(
                    referral_id=task.referral_id,
                    task_id=task.task_id,
                    rank=idx,
                    score=round(score, 1),
                    rationale=rationale,
                    factors=factors,
                )
            )
        return QueueRankingOutput(
            available=True,
            ranked_tasks=ranked,
            provider=self.name,
            model=self.model,
        )

    def _rationale(self, factors: list[str]) -> str:
        if not factors:
            return "No outstanding operational flags."
        labels = {
            "overdue": "referral is overdue",
            "missing_follow_up": "follow-up is missing",
            "aged_referral": "referral is aged",
            "appointment_window": "near appointment window",
            "unresolved_admin": "unresolved administrative status",
        }
        parts = [labels.get(f, f) for f in factors]
        return "Operational priority: " + "; ".join(parts) + "."


def get_queue_ranking_provider() -> QueueRankingProvider:
    from app.core.config import settings
    from app.core.exceptions import AIConfigurationError

    name = (settings.chw_queue_provider or "stub").strip().lower()
    if name == "stub":
        return StubQueueRankingProvider()
    # No real queue-ranking vendor exists yet; fail fast instead of silently
    # serving stub output as if it were a configured provider.
    raise AIConfigurationError(
        detail=(
            f"Unknown CHW_QUEUE_PROVIDER '{name}'. Expected 'stub' "
            "(no real queue-ranking provider is implemented yet)"
        )
    )


def compute_input_hash(data: QueueRankingInput) -> str:
    """SHA-256 of the (PHI-scrubbed) operational input for audit."""
    payload = json.dumps(
        {
            "chw_user_id": data.chw_user_id,
            "tasks": [t.model_dump() for t in data.tasks],
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def compute_output_hash(output: QueueRankingOutput) -> str:
    payload = json.dumps(
        [t.model_dump() for t in output.ranked_tasks],
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()
