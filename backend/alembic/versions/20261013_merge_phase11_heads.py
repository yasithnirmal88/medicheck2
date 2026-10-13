"""Merge the Phase 11 insight and audit-schema migration branches."""

from __future__ import annotations

from typing import Sequence, Union

revision: str = "20261013_merge_phase11_heads"
down_revision: Union[str, Sequence[str], None] = (
    "20260812_ai_insights_phase11",
    "20260812_audit_schema",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
