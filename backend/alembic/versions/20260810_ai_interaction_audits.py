"""Phase 7 — AI interaction audit trail table

Additive table for AI governance. Stores ONLY hashes, reference ids, and
metadata — no raw patient PHI. Enables administrators to trace which model
and prompt generated a given AI explanation, and which deterministic result
it was based on, without accessing patient information.

Revision ID: 20260810_ai_interaction_audits
Revises: 20260808_emergency_contact_json
Create Date: 2026-08-10 00:00:01.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "20260810_ai_interaction_audits"
down_revision = "20260808_emergency_contact_json"
branch_labels = None
depends_on = None

_TABLE = "ai_interaction_audits"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_tables = set(inspector.get_table_names())

    if _TABLE in existing_tables:
        # Idempotent: table already exists (e.g. test DB created via
        # Base.metadata.create_all). Nothing to do.
        return

    op.create_table(
        _TABLE,
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "trace_id", sa.String(64), nullable=True, index=True
        ),
        sa.Column(
            "session_id", sa.String(32), nullable=True, index=True
        ),
        sa.Column(
            "request_type", sa.String(50), nullable=False, index=True
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column(
            "model", sa.String(100), nullable=False, server_default=""
        ),
        sa.Column(
            "prompt_version",
            sa.String(50),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "language",
            sa.String(10),
            nullable=False,
            server_default="en",
            index=True,
        ),
        sa.Column(
            "literacy_level",
            sa.String(20),
            nullable=False,
            server_default="standard",
            index=True,
        ),
        sa.Column("input_context_hash", sa.String(64), nullable=True),
        sa.Column("output_hash", sa.String(64), nullable=True),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="valid",
            index=True,
        ),
        sa.Column("status_reason", sa.Text(), nullable=True),
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
    op.create_index(
        f"ix_{_TABLE}_deleted_at",
        _TABLE,
        ["deleted_at"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_tables = set(inspector.get_table_names())
    if _TABLE not in existing_tables:
        return
    op.drop_table(_TABLE)
