"""CI guard for the deploy path: ``alembic upgrade head`` must succeed.

``backend/entrypoint.sh`` runs ``alembic upgrade head`` before the app starts.
These tests reproduce that against databases built from scratch so a broken
migration fails in CI rather than on deploy.

Regression covered: migration ``5037a1e583da`` used to unconditionally rename
``questionnaire_templates.metadata`` -> ``template_metadata``. On a fresh
database ``20260723_initial_schema`` (which builds tables from the *current*
models via ``Base.metadata.create_all``) already creates ``template_metadata``,
so the rename died with ``no such column: metadata`` and the deploy failed.
Existing installs were unaffected, which is why it went unnoticed.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Revision immediately before the rename migration (legacy pre-rename state).
_PRE_RENAME_REVISION = "20260811_interop_phase10"

_TABLE = "questionnaire_templates"
_OLD_COLUMN = "metadata"
_NEW_COLUMN = "template_metadata"


def _expected_head() -> str:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return ScriptDirectory.from_config(config).get_current_head()


def _run_alembic(database_url: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["ENVIRONMENT"] = env.get("ENVIRONMENT", "development")
    env["ALLOW_MOCK_AUTH"] = "true"
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
    )


def _sqlite_url(db_file: Path) -> str:
    return f"sqlite+aiosqlite:///{db_file.as_posix()}"


def _columns(db_file: Path, table: str) -> set[str]:
    connection = sqlite3.connect(str(db_file))
    try:
        return {
            row[1] for row in connection.execute(f"PRAGMA table_info({table})")
        }
    finally:
        connection.close()


def test_alembic_upgrade_head_succeeds_on_empty_database(tmp_path: Path) -> None:
    """A brand-new database must reach head (this failed on the old migration)."""
    db_file = tmp_path / "fresh.db"

    result = _run_alembic(_sqlite_url(db_file), "upgrade", "head")
    assert result.returncode == 0, (
        "alembic upgrade head failed on an empty database:\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    columns = _columns(db_file, _TABLE)
    assert _NEW_COLUMN in columns
    assert _OLD_COLUMN not in columns

    connection = sqlite3.connect(str(db_file))
    try:
        row = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    assert row[0] == _expected_head()


def test_alembic_upgrade_preserves_legacy_metadata_column(tmp_path: Path) -> None:
    """Existing installs (column still named ``metadata``) upgrade without data loss."""
    db_file = tmp_path / "legacy.db"
    url = _sqlite_url(db_file)

    pre = _run_alembic(url, "upgrade", _PRE_RENAME_REVISION)
    assert pre.returncode == 0, (
        f"could not build legacy database:\n{pre.stdout}\n{pre.stderr}"
    )

    template_id = uuid.uuid4().hex
    payload = '{"legacy": true}'
    connection = sqlite3.connect(str(db_file))
    try:
        connection.execute(
            f"""
            INSERT INTO {_TABLE}
                (id, code, name, target_audience, estimated_time_minutes,
                 is_active, is_template, version, {_NEW_COLUMN})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                template_id,
                "legacy-code",
                "Legacy Template",
                "all",
                10,
                1,
                1,
                1,
                payload,
            ),
        )
        # Simulate a pre-rename install where the column is still ``metadata``.
        connection.execute(
            f"ALTER TABLE {_TABLE} RENAME COLUMN {_NEW_COLUMN} TO {_OLD_COLUMN}"
        )
        connection.commit()
    finally:
        connection.close()

    result = _run_alembic(url, "upgrade", "head")
    assert result.returncode == 0, (
        "alembic upgrade head failed on a legacy database:\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    columns = _columns(db_file, _TABLE)
    assert _NEW_COLUMN in columns
    assert _OLD_COLUMN not in columns

    connection = sqlite3.connect(str(db_file))
    try:
        row = connection.execute(
            f"SELECT {_NEW_COLUMN} FROM {_TABLE} WHERE id = ?", (template_id,)
        ).fetchone()
    finally:
        connection.close()
    assert row is not None and row[0] == payload
