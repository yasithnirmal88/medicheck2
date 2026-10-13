"""Rename questionnaire_templates metadata to template_metadata

Revision ID: 5037a1e583da
Revises: 20260811_interop_phase10
Create Date: 2026-10-01 23:13:33.171575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5037a1e583da'
down_revision: Union[str, None] = '20260811_interop_phase10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "questionnaire_templates"
_OLD_COLUMN = "metadata"
_NEW_COLUMN = "template_metadata"


def _column_names() -> set[str]:
    """Columns currently present on the target table (empty if table absent)."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(_TABLE)}


def upgrade() -> None:
    # Fresh databases are built by 20260723_initial_schema via
    # ``Base.metadata.create_all`` from the CURRENT models, which already
    # declare ``template_metadata`` -- there is no legacy ``metadata`` column
    # to rename. Older production databases still carry ``metadata`` (the
    # model was renamed after they were created). Only rename when the old
    # name is present and the new name is absent, so this migration is a safe
    # no-op on fresh databases and still performs the rename on legacy ones.
    columns = _column_names()
    if _OLD_COLUMN in columns and _NEW_COLUMN not in columns:
        op.alter_column(_TABLE, _OLD_COLUMN, new_column_name=_NEW_COLUMN)


def downgrade() -> None:
    # Mirror of ``upgrade``: only rename back when the new name exists and the
    # legacy name does not, so downgrading a fresh database is a no-op too.
    columns = _column_names()
    if _NEW_COLUMN in columns and _OLD_COLUMN not in columns:
        op.alter_column(_TABLE, _NEW_COLUMN, new_column_name=_OLD_COLUMN)
