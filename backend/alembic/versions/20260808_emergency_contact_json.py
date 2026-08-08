"""emergency_contact column type Text -> JSON

The personal_infos.emergency_contact column was declared as SQLAlchemy Text but
typed (Mapped/DTO) as dict. Writing a dict to a Text column raises on SQLite
(``type 'dict' is not supported``) and stores an invalid Python repr on other
dialects, so the field could never be persisted. No rows ever held a value
(all values are NULL), so converting to JSON is safe. This matches the pattern
already used by other dict-typed columns (workflow.steps,
questionnaire_template.extra_metadata, profile_version.snapshot).

Revision ID: 20260808_emergency_contact_json
Revises: 20260723_add_profile_indexes
Create Date: 2026-08-08 00:00:01.000000
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import JSON, Text
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "20260808_emergency_contact_json"
down_revision = "20260723_add_profile_indexes"
branch_labels = None
depends_on = None

_TABLE = "personal_infos"
_COLUMN = "emergency_contact"


def _column_type(bind) -> str | None:
    insp = Inspector.from_engine(bind)
    if _TABLE not in insp.get_table_names():
        return None
    for col in insp.get_columns(_TABLE):
        if col["name"] == _COLUMN:
            return str(col["type"]).upper()
    return None


def upgrade() -> None:
    bind = op.get_bind()
    current = _column_type(bind)
    if current is None:
        # Table managed by create_all elsewhere / not present - nothing to alter.
        return
    if "JSON" in current:
        # Already JSON (or jsonb) - idempotent, nothing to do.
        return
    # Existing values are all NULL (the dict->Text write never succeeded), so the
    # cast is safe. Postgres: TEXT -> JSON. SQLite lacks ALTER COLUMN TYPE; SQLite
    # deployments recreate schema via create_all, so this migration targets Postgres.
    op.alter_column(
        _TABLE,
        _COLUMN,
        existing_type=Text(),
        type_=JSON(),
        postgresql_using=f"{_COLUMN}::json",
        existing_nullable=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    current = _column_type(bind)
    if current is None or "JSON" not in current:
        return
    op.alter_column(
        _TABLE,
        _COLUMN,
        existing_type=JSON(),
        type_=Text(),
        postgresql_using=f"{_COLUMN}::text",
        existing_nullable=True,
    )
