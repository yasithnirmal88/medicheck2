"""Phase 8 — CHW + offline/low-bandwidth access tables

Additive tables for the Community Health Worker mode and offline assessment
synchronization. All tables store only reference ids, status, hashes, and
version metadata — no raw PHI, no credentials, no access tokens.

- chw_assignments: explicit CHW↔patient authorization (least-privilege scope)
- consent_records: minimal consent attestation before a CHW assessment
- assessment_sync_records: idempotent offline-sync ledger (dedup by idempotency_key)
- offline_device_registrations: revocable device fingerprints (no secrets)

Revision ID: 20260810_chw_offline
Revises: 20260810_ai_interaction_audits
Create Date: 2026-08-10 00:00:02.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "20260810_chw_offline"
down_revision = "20260810_ai_interaction_audits"
branch_labels = None
depends_on = None

_TABLES = [
    "chw_assignments",
    "consent_records",
    "assessment_sync_records",
    "offline_device_registrations",
]


def _existing_tables(bind) -> set[str]:
    inspector = Inspector.from_engine(bind)
    return set(inspector.get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    existing = _existing_tables(bind)

    if "chw_assignments" not in existing:
        op.create_table(
            "chw_assignments",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("chw_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("patient_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("assigned_by", sa.String(32), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active", index=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_chw_assignments_deleted_at", "chw_assignments", ["deleted_at"])

    if "consent_records" not in existing:
        op.create_table(
            "consent_records",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("patient_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("chw_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("session_id", sa.String(32), nullable=True, index=True),
            sa.Column("consent_type", sa.String(40), nullable=False, index=True),
            sa.Column("language", sa.String(10), nullable=False, server_default="en", index=True),
            sa.Column("consent_text_version", sa.String(50), nullable=False, server_default="v1"),
            sa.Column("granted", sa.Boolean, nullable=False, server_default=sa.true()),
            sa.Column("attested_by", sa.String(20), nullable=False, server_default="chw"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_consent_records_deleted_at", "consent_records", ["deleted_at"])

    if "assessment_sync_records" not in existing:
        op.create_table(
            "assessment_sync_records",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("idempotency_key", sa.String(64), nullable=False, unique=True, index=True),
            sa.Column("chw_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("patient_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("session_id", sa.String(32), nullable=True, index=True),
            sa.Column("template_id", sa.String(32), nullable=True),
            sa.Column("content_version", sa.Integer, nullable=False, server_default="1"),
            sa.Column("sync_status", sa.String(20), nullable=False, server_default="pending", index=True),
            sa.Column("error_category", sa.String(40), nullable=True),
            sa.Column("error_detail", sa.String(500), nullable=True),
            sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_assessment_sync_records_deleted_at", "assessment_sync_records", ["deleted_at"])

    if "offline_device_registrations" not in existing:
        op.create_table(
            "offline_device_registrations",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("chw_user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("device_label", sa.String(100), nullable=False),
            sa.Column("device_fingerprint", sa.String(64), nullable=False, index=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active", index=True),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("registered_by", sa.String(32), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_by", sa.String(32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_offline_device_registrations_deleted_at", "offline_device_registrations", ["deleted_at"])


def downgrade() -> None:
    bind = op.get_bind()
    existing = _existing_tables(bind)
    for table in reversed(_TABLES):
        if table in existing:
            op.drop_table(table)
