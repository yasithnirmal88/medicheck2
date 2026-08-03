"""add missing profile_id indexes on health profile section tables

Revision ID: 20260723_add_profile_indexes
Revises: 20260723_initial_schema
Create Date: 2026-07-23 00:00:01.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260723_add_profile_indexes"
down_revision = "20260723_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_lifestyles_profile_id ON lifestyles (profile_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nutritions_profile_id ON nutritions (profile_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_personal_infos_profile_id ON personal_infos (profile_id)")


def downgrade() -> None:
    op.drop_index("ix_lifestyles_profile_id", table_name="lifestyles")
    op.drop_index("ix_nutritions_profile_id", table_name="nutritions")
    op.drop_index("ix_personal_infos_profile_id", table_name="personal_infos")
