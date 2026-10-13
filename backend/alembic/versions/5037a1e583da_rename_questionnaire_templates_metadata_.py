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


def upgrade() -> None:
    op.alter_column('questionnaire_templates', 'metadata', new_column_name='template_metadata')


def downgrade() -> None:
    op.alter_column('questionnaire_templates', 'template_metadata', new_column_name='metadata')
