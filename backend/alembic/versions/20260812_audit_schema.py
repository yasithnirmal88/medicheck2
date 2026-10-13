"""Move high-volume audit tables into the dedicated audit schema.

Physical separation (PostgreSQL only): ``ai_interaction_audits`` and
``audit_logs`` move from ``public`` to the ``audit`` schema so growth in AI
interaction logs and admin audit trails cannot degrade the hot clinical
tables (separate namespace for vacuum/backup/retention policies, and no
clinical query ever needs to touch them — both tables are FK-free with only
soft id references, and are read solely via aggregate/admin queries).

SQLite has no schemas: the migration is a no-op there, and the models
resolve ``AUDIT_SCHEMA`` to ``None`` so ``create_all`` (tests, local dev)
behaves exactly as before.

Revision ID: 20260812_audit_schema
Revises: 5037a1e583da
Create Date: 2026-08-12 00:00:01.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260812_audit_schema"
down_revision = "5037a1e583da"
branch_labels = None
depends_on = None

_AUDIT_SCHEMA = "audit"
_TABLES = ("ai_interaction_audits", "audit_logs")


def _is_sqlite(bind) -> bool:
    return bind.dialect.name == "sqlite"


def upgrade() -> None:
    bind = op.get_bind()
    if _is_sqlite(bind):
        # No schemas on SQLite; models already resolve to the default
        # namespace there. Nothing to do.
        return

    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS audit"))

    inspector = sa.inspect(bind)
    public_tables = set(inspector.get_table_names())
    audited_tables = set(inspector.get_table_names(schema=_AUDIT_SCHEMA))
    for table in _TABLES:
        if table in public_tables and table not in audited_tables:
            op.execute(sa.text(f'ALTER TABLE "{table}" SET SCHEMA {_AUDIT_SCHEMA}'))


def downgrade() -> None:
    bind = op.get_bind()
    if _is_sqlite(bind):
        return

    inspector = sa.inspect(bind)
    public_tables = set(inspector.get_table_names())
    audited_tables = set(inspector.get_table_names(schema=_AUDIT_SCHEMA))
    for table in _TABLES:
        if table in audited_tables and table not in public_tables:
            op.execute(sa.text(f'ALTER TABLE {_AUDIT_SCHEMA}."{table}" SET SCHEMA public'))
    # The schema itself is intentionally kept: future audit objects may live
    # there, and dropping a non-empty schema would fail.
