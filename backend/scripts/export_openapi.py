"""Export the FastAPI OpenAPI schema to a static JSON file.

The committed schema is what the frontend's Orval pipeline generates types from,
so codegen works offline and in CI without a running backend.

Usage:
    python scripts/export_openapi.py [output_path]

Default output: <repo>/frontend/openapi.json

Env:
    ALLOW_MOCK_AUTH=true   required when Firebase is unconfigured, otherwise
                           create_app() is fine but route registration may warn.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
DEFAULT_OUTPUT = REPO_ROOT / "frontend" / "openapi.json"

# Import app modules from the backend package root.
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT

    # create_app() only needs the DB URL at request time; the schema itself is
    # built statically. Defaults keep this runnable with no local .env.
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("ALLOW_MOCK_AUTH", "true")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./openapi_export.db")

    from app.main import create_app

    schema = create_app().openapi()

    output.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys keeps the committed file diff-stable across regenerations.
    output.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    paths = len(schema.get("paths", {}))
    schemas = len(schema.get("components", {}).get("schemas", {}))
    print(f"Wrote OpenAPI {schema.get('openapi')} -> {output}")
    print(f"  {paths} paths, {schemas} component schemas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())