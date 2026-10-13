"""Phase 11 — Governed AI care-coordination & equity intelligence tables

Additive schema for the Phase 11 governed-AI layer. Creates:
- ai_operational_suggestions: AI-generated CHW operational suggestions + their
  human-review lifecycle. Operational/administrative ONLY — never clinical
  priority. Stores reference ids + hashes; no raw PHI.
- ai_population_insights: AI-generated population/equity/SDG insights over
  DE-IDENTIFIED aggregated analytics + their human-review lifecycle. The
  metric_context JSON contains only already-suppressed aggregates.

No existing clinical table is modified. No seed data is altered. The "AI was
called" governance trail is ALSO recorded via the Phase 7 AIInteractionAuditModel
(request_type chw_operational_suggestion / equity_intelligence / sdg_narrative);
these tables hold the reviewable insight content + review state, which the
audit model (hashes/metadata only) cannot.

Revision ID: 20260812_ai_insights_phase11
Revises: 20260811_interop_phase10
Create Date: 2026-08-12 00:00:01.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

revision = "20260812_ai_insights_phase11"
down_revision = "20260811_interop_phase10"
branch_labels = None
depends_on = None


def _existing_tables(bind) -> set[str]:
    inspector = Inspector.from_engine(bind)
    return set(inspector.get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    existing = _existing_tables(bind)

    if "ai_operational_suggestions" not in existing:
        op.create_table(
            "ai_operational_suggestions",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("chw_user_id", sa.String(32), nullable=False, index=True),
            sa.Column("task_id", sa.String(32), nullable=False, index=True),
            sa.Column("operational_reason_codes", sa.JSON, nullable=False),
            sa.Column("explanation", sa.Text, nullable=False),
            sa.Column("operational_priority_score", sa.Float, nullable=False),
            sa.Column("requires_human_review", sa.Boolean, nullable=False),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("model", sa.String(100), nullable=False),
            sa.Column("prompt_version", sa.String(50), nullable=False),
            sa.Column("input_context_hash", sa.String(64), nullable=True),
            sa.Column("output_hash", sa.String(64), nullable=True),
            sa.Column("quality_status", sa.String(30), nullable=False, index=True),
            sa.Column("quality_reason", sa.Text, nullable=True),
            sa.Column("review_status", sa.String(30), nullable=False, index=True),
            sa.Column("reviewer_id", sa.String(32), nullable=True),
            sa.Column("reviewer_comment", sa.Text, nullable=True),
            sa.Column("edited_output", sa.Text, nullable=True),
            sa.Column("approved_at", sa.String(40), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    if "ai_population_insights" not in existing:
        op.create_table(
            "ai_population_insights",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("insight_type", sa.String(30), nullable=False, index=True),
            sa.Column("period_start", sa.String(20), nullable=True),
            sa.Column("period_end", sa.String(20), nullable=True),
            sa.Column("target", sa.String(20), nullable=True),
            sa.Column("metric_context", sa.JSON, nullable=True),
            sa.Column("narrative", sa.Text, nullable=False),
            sa.Column("observed_findings", sa.JSON, nullable=True),
            sa.Column("possible_interpretations", sa.JSON, nullable=True),
            sa.Column("limitations", sa.Text, nullable=True),
            sa.Column("requires_human_review", sa.Boolean, nullable=False),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("model", sa.String(100), nullable=False),
            sa.Column("prompt_version", sa.String(50), nullable=False),
            sa.Column("input_context_hash", sa.String(64), nullable=True),
            sa.Column("output_hash", sa.String(64), nullable=True),
            sa.Column("quality_status", sa.String(30), nullable=False, index=True),
            sa.Column("quality_reason", sa.Text, nullable=True),
            sa.Column("review_status", sa.String(30), nullable=False, index=True),
            sa.Column("reviewer_id", sa.String(32), nullable=True),
            sa.Column("reviewer_comment", sa.Text, nullable=True),
            sa.Column("edited_output", sa.Text, nullable=True),
            sa.Column("approved_at", sa.String(40), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    existing = _existing_tables(bind)
    if "ai_population_insights" in existing:
        op.drop_table("ai_population_insights")
    if "ai_operational_suggestions" in existing:
        op.drop_table("ai_operational_suggestions")
