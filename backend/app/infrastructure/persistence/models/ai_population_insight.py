"""Phase 11 — AI population / equity / SDG insight (governed AI intelligence).

Additive model storing an AI-generated insight over DE-IDENTIFIED, aggregated
analytics (population equity patterns and SDG narratives), together with its
human-review lifecycle. The AI operates ONLY on already-aggregated, k-anonymity-
suppressed metrics — never on individual patient data.

``insight_type`` discriminates:
    - "equity"      : left-behind equity intelligence (Feature B)
    - "sdg_narrative": AI-generated SDG/population narrative (Feature C)

Review lifecycle (set ONLY by a human reviewer; AI never self-publishes):

    GENERATED -> PENDING_REVIEW -> APPROVED | REJECTED | EDITED -> PUBLISHED

No raw PHI is stored. The ``metric_context`` JSON contains only the
de-identified aggregate metrics the AI was allowed to describe (entity
allow-list enforced — the AI may only reference metrics/labels supplied in the
context). The "AI was called" governance trail is also recorded via the Phase
7 ``AIAuditService``.
"""

from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class AiPopulationInsightModel(BaseModel):
    __tablename__ = "ai_population_insights"

    insight_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )
    # Reporting period the insight covers (ISO date range string).
    period_start: Mapped[str | None] = mapped_column(String(20), nullable=True)
    period_end: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # SDG target this insight relates to (e.g. "3.4", "3.8", "10") for
    # sdg_narrative; the equity dimension for "equity" (e.g. "language").
    target: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # The de-identified aggregate metric context the AI was allowed to
    # describe. Allow-listed: the AI's narrative may only reference labels/
    # metrics present here. No patient ids, names, or raw answers.
    metric_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # The AI-generated narrative/insight text.
    narrative: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Structured observed findings + possible interpretations + limitations.
    observed_findings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    possible_interpretations: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(
        nullable=False, default=True
    )

    # AI provenance + quality.
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )
    input_context_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    output_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quality_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="valid", index=True
    )
    quality_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Human-review lifecycle. AI may only set GENERATED/PENDING_REVIEW.
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    reviewer_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
