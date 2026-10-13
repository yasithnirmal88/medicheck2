"""Add lookup indexes for Phase 10 referral fields.

Revision ID: 20261013_referral_lookup_indexes
Revises: 20261013_merge_phase11_heads
Create Date: 2026-10-13 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261013_referral_lookup_indexes"
down_revision = "20261013_merge_phase11_heads"
branch_labels = None
depends_on = None

_REFERRAL_INDEXES = (
    ("ix_referrals_facility_id", "facility_id"),
    ("ix_referrals_receiving_status", "receiving_status"),
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "referrals" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("referrals")}
    indexes = {index["name"] for index in inspector.get_indexes("referrals")}
    for index_name, column_name in _REFERRAL_INDEXES:
        if column_name in columns and index_name not in indexes:
            op.create_index(index_name, "referrals", [column_name])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "referrals" not in inspector.get_table_names():
        return

    indexes = {index["name"] for index in inspector.get_indexes("referrals")}
    for index_name, _ in _REFERRAL_INDEXES:
        if index_name in indexes:
            op.drop_index(index_name, table_name="referrals")
