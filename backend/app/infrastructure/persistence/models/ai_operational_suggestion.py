"""Phase 11 — AI operational suggestion (CHW care-coordination assistance).

Additive model storing an AI-generated OPERATIONAL suggestion for a CHW's
follow-up work, together with its human-review lifecycle. The suggestion is
administrative assistance ONLY — it never determines clinical priority,
severity, or urgency (enforced by the provider's ``assert_non_clinical`` and
the operational-only context).

Review lifecycle (set ONLY by a human reviewer; AI never self-publishes):

    GENERATED -> PENDING_REVIEW -> APPROVED | REJECTED | EDITED -> PUBLISHED

The "AI was called" audit trail (provider/model/prompt_version/hashes) is
recorded BOTH here (for the reviewable insight) and via the Phase 7
``AIAuditService`` (request_type ``chw_operational_suggestion``) for the
governance dashboard. No raw PHI is stored — ``task_id`` is a referral id (a
reference), and the context is operational factors only.
"""

from __future__ import annotations

from sqlalchemy import JSON, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class AiOperationalSuggestionModel(BaseModel):
    __tablename__ = "ai_operational_suggestions"

    # The CHW the suggestion was generated for (reference id; not PHI itself).
    chw_user_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    # The referral / follow-up task the suggestion concerns (reference id).
    # Validated against an allow-list of the CHW's actual assigned task ids
    # before persistence — hallucinated ids are REJECTED, never stored here.
    task_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    # Operational reason codes (e.g. "overdue", "missing_follow_up",
    # "aged_referral", "unresolved_admin"). Never clinical codes.
    operational_reason_codes: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )
    # Operational explanation text. assert_non_clinical is enforced by the
    # provider before this is ever set.
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Operational priority score in [0,1]. Has NO clinical meaning — it only
    # ranks administrative workload. Documented as such in DTOs + UI.
    operational_priority_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    requires_human_review: Mapped[bool] = mapped_column(
        nullable=False, default=True
    )

    # AI provenance + quality (mirrors the governance audit pattern).
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
    # If the reviewer edits the output, the edited text is stored here.
    edited_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
