"""Phase 7 — AI interaction audit trail.

Additive model: stores hashes and metadata ONLY. No raw patient PHI, no
clinical text, no indicator/condition/recommendation content. Every field
is a reference id or a hash, so an administrator can answer "which model and
prompt generated this explanation?" and "what deterministic result was the
explanation based on?" without ever accessing patient information.

Follows existing conventions: UUID PK (BaseModel), timestamps, soft-delete.
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class AIInteractionAuditModel(BaseModel):
    __tablename__ = "ai_interaction_audits"

    trace_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    request_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )
    language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en", index=True
    )
    literacy_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="standard", index=True
    )
    input_context_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    output_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="valid", index=True
    )
    # Short human-readable reason for non-valid statuses (e.g. "timeout",
    # "validation_failed:unknown_indicator_id"). Never contains PHI.
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
