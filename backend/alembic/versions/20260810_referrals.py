"""Phase 9 — Referral, care follow-up & access-barrier tables

Additive tables for the referral/care-follow-up loop. All tables store only
reference ids, status, and navigation metadata — no clinical scores, no
severity, no recommendation text (those remain in CDSE/report tables). A
referral is derived from an existing deterministic recommendation; it never
duplicates clinical meaning.

- referrals: care-navigation record (originating session/report/trace/recommendation)
- referral_status_events: append-only transition audit
- referral_access_barriers: structured non-clinical access barriers (SDG 3.8/10)
- follow_up_tasks: deterministic tasks linked to a referral

Revision ID: 20260810_referrals
Revises: 20260810_chw_offline
Create Date: 2026-08-10 00:00:03.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "20260810_referrals"
down_revision = "20260810_chw_offline"
branch_labels = None
depends_on = None

_TABLES = [
    "follow_up_tasks",
    "referral_access_barriers",
    "referral_status_events",
    "referrals",
]


def _existing_tables(bind) -> set[str]:
    inspector = Inspector.from_engine(bind)
    return set(inspector.get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    existing = _existing_tables(bind)

    if "referrals" not in existing:
        op.create_table(
            "referrals",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("patient_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("originating_session_id", sa.String(32), nullable=False, index=True),
            sa.Column("originating_report_id", sa.String(32), nullable=True, index=True),
            sa.Column("trace_id", sa.String(16), nullable=True, index=True),
            sa.Column("recommendation_id", sa.String(32), nullable=False, index=True),
            sa.Column("referral_type", sa.String(30), nullable=False, index=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("assigned_chw_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("patient_acknowledged", sa.Boolean, nullable=False, server_default=sa.false()),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_referrals_deleted_at", "referrals", ["deleted_at"])

    if "referral_status_events" not in existing:
        op.create_table(
            "referral_status_events",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("referral_id", sa.String(32), sa.ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("from_status", sa.String(20), nullable=True),
            sa.Column("to_status", sa.String(20), nullable=False, index=True),
            sa.Column("actor_user_id", sa.String(32), nullable=False, index=True),
            sa.Column("actor_role", sa.String(40), nullable=False),
            sa.Column("reason", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_referral_status_events_deleted_at", "referral_status_events", ["deleted_at"])

    if "referral_access_barriers" not in existing:
        op.create_table(
            "referral_access_barriers",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("referral_id", sa.String(32), sa.ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("barrier_type", sa.String(40), nullable=False, index=True),
            sa.Column("recorded_by_user_id", sa.String(32), nullable=False, index=True),
            sa.Column("recorded_by_role", sa.String(40), nullable=False),
            sa.Column("detail", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_referral_access_barriers_deleted_at", "referral_access_barriers", ["deleted_at"])

    if "follow_up_tasks" not in existing:
        op.create_table(
            "follow_up_tasks",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("referral_id", sa.String(32), sa.ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("patient_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("assigned_chw_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("task_type", sa.String(40), nullable=False, index=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_follow_up_tasks_deleted_at", "follow_up_tasks", ["deleted_at"])


def downgrade() -> None:
    bind = op.get_bind()
    existing = _existing_tables(bind)
    for tbl in _TABLES:
        if tbl in existing:
            op.drop_table(tbl)
