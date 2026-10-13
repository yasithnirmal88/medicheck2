"""Make users.email nullable.

Firebase phone-auth tokens carry no ``email`` claim. ``get_current_user``
previously stored ``""`` for those users, which later made every auth DTO
serialization raise a Pydantic ValidationError (``EmailStr`` rejects ``""``)
-> 500 on /auth/me - and violated the unique constraint for the second
phone-only user. The entity/ORM now normalize an empty email to NULL;
this migration drops the NOT NULL (and thereby permits multiple phone-only
users) on Postgres. SQLite deployments recreate the schema via ``create_all``
(the model is already nullable), so it is a no-op there.

Revision ID: 20261013_users_email_nullable
Revises: 20261013_referral_lookup_indexes
Create Date: 2026-10-13 00:00:01.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

from alembic import op

revision = "20261013_users_email_nullable"
down_revision = "20261013_referral_lookup_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite has no ALTER COLUMN DROP NOT NULL; schema is recreated via
        # create_all where the model is already nullable.
        return
    insp = Inspector.from_engine(bind)
    if "users" not in insp.get_table_names():
        return
    for col in insp.get_columns("users"):
        if col["name"] == "email":
            if col["nullable"]:
                return
            break
    op.alter_column("users", "email", existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    insp = Inspector.from_engine(bind)
    if "users" not in insp.get_table_names():
        return
    for col in insp.get_columns("users"):
        if col["name"] == "email":
            if not col["nullable"]:
                return
            break
    # Downgrade requires non-null values first; existing NULLs are left intact
    # by this idempotent migration (emit warning is deliberately avoided since
    # re-adding NOT NULL over NULL rows would fail).
    op.alter_column("users", "email", existing_type=sa.String(255), nullable=False)
