"""initial schema - create all tables from model definitions

Revision ID: 20260723_initial_schema
Revises:
Create Date: 2026-07-23 00:00:00.000000
"""

from __future__ import annotations

import importlib
import pkgutil

from sqlalchemy import Connection

from alembic import op
from app.infrastructure.database import Base

# revision identifiers, used by Alembic.
revision = "20260723_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _import_all_models() -> None:
    """Import all model modules so Base.metadata is fully populated."""
    models_path = "app.infrastructure.persistence.models"
    models_pkg = importlib.import_module(models_path)
    for _finder, name, _is_pkg in pkgutil.iter_modules(models_pkg.__path__):
        if not _is_pkg:
            importlib.import_module(f"{models_path}.{name}")


def upgrade() -> None:
    _import_all_models()
    bind = op.get_bind()
    Base.metadata.create_all(bind)


def downgrade() -> None:
    _import_all_models()
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
