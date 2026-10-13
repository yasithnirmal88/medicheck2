"""Phase 10 — Interoperability, facility, care-outcome & export tables

Additive schema for the Phase 10 interoperability / health-system-integration
/ outcome-feedback layer. Creates:
- facilities: health-service destination metadata (operational only).
- facility_services: discrete services a facility offers.
- care_outcomes: operational care-continuity states per referral. NEVER feeds
  back into CDSE scoring (no FK to scoring tables).
- interoperability_exports: append-only export manifest/audit.

Adds additive (nullable) columns to the existing Phase 9 ``referrals`` table:
- facility_id (FK facilities.id, ondelete SET NULL)
- receiving_status (facility handoff status)
- scheduled_for (appointment/service time)

No existing clinical table is modified. No seed data is altered.

Revision ID: 20260811_interop_phase10
Revises: 20260810_referrals
Create Date: 2026-08-11 00:00:01.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "20260811_interop_phase10"
down_revision = "20260810_referrals"
branch_labels = None
depends_on = None


def _existing_tables(bind) -> set[str]:
    inspector = Inspector.from_engine(bind)
    return set(inspector.get_table_names())


def _existing_columns(bind, table: str) -> set[str]:
    inspector = Inspector.from_engine(bind)
    if table not in inspector.get_table_names():
        return set()
    return {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    existing = _existing_tables(bind)

    if "facilities" not in existing:
        op.create_table(
            "facilities",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("code", sa.String(100), nullable=False, unique=True, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("service_type", sa.String(50), nullable=True, index=True),
            sa.Column("region", sa.String(100), nullable=True, index=True),
            sa.Column("contact_channel", sa.String(255), nullable=True),
            sa.Column("availability_status", sa.String(30), nullable=False, server_default="unknown", index=True),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_facilities_deleted_at", "facilities", ["deleted_at"])

    if "facility_services" not in existing:
        op.create_table(
            "facility_services",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("facility_id", sa.String(32), sa.ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("service_type", sa.String(50), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_facility_services_deleted_at", "facility_services", ["deleted_at"])

    if "care_outcomes" not in existing:
        op.create_table(
            "care_outcomes",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("referral_id", sa.String(32), sa.ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("patient_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("outcome_category", sa.String(40), nullable=False, index=True),
            sa.Column("recorded_by_user_id", sa.String(32), nullable=False, index=True),
            sa.Column("recorded_by_role", sa.String(40), nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column("source", sa.String(30), nullable=False, server_default="manual"),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_care_outcomes_deleted_at", "care_outcomes", ["deleted_at"])

    if "interoperability_exports" not in existing:
        op.create_table(
            "interoperability_exports",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("export_type", sa.String(20), nullable=False, index=True),
            sa.Column("format", sa.String(20), nullable=False, server_default="json"),
            sa.Column("requested_by_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("patient_user_id", sa.String(32), nullable=True, index=True),
            sa.Column("resource_types", sa.JSON, nullable=False),
            sa.Column("source_trace_ids", sa.JSON, nullable=False),
            sa.Column("schema_version", sa.String(20), nullable=False, server_default="4.0.1"),
            sa.Column("status", sa.String(20), nullable=False, server_default="completed", index=True),
            sa.Column("status_reason", sa.Text, nullable=True),
            sa.Column("consent_id", sa.String(32), nullable=True),
            sa.Column("item_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_interoperability_exports_deleted_at", "interoperability_exports", ["deleted_at"])

    # Additive columns on referrals (Phase 9 table). Safe: all nullable.
    referral_cols = _existing_columns(bind, "referrals")
    if "facility_id" not in referral_cols:
        op.add_column(
            "referrals",
            sa.Column("facility_id", sa.String(32), sa.ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True, index=True),
        )
    if "receiving_status" not in referral_cols:
        op.add_column(
            "referrals",
            sa.Column("receiving_status", sa.String(20), nullable=True, index=True),
        )
    if "scheduled_for" not in referral_cols:
        op.add_column(
            "referrals",
            sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    existing = _existing_tables(bind)
    referral_cols = _existing_columns(bind, "referrals")
    for col in ("scheduled_for", "receiving_status", "facility_id"):
        if col in referral_cols:
            op.drop_column("referrals", col)
    for tbl in ("interoperability_exports", "care_outcomes", "facility_services", "facilities"):
        if tbl in existing:
            op.drop_table(tbl)
