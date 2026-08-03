#!/usr/bin/env python3
"""Health check script for all MediCheck services."""

import json
import subprocess
import sys
import urllib.request
from datetime import UTC, datetime

SERVICES = {
    "backend": "http://localhost:8000/api/v1/health",
    "frontend": "http://localhost:80/nginx-health",
    "redis": lambda: subprocess.run(
        ["redis-cli", "-h", "localhost", "ping"],
        capture_output=True, text=True, timeout=5,
    ).stdout.strip() == "PONG",
    "db": lambda: subprocess.run(
        ["pg_isready", "-h", "localhost", "-U", "medicheck"],
        capture_output=True, text=True, timeout=5,
    ).returncode == 0,
}


def check_http(url: str) -> dict:
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read().decode())
        return {"status": "ok", "code": resp.getcode(), "body": data}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main() -> int:
    results = {}
    all_ok = True

    print(f"=== MediCheck Health Check: {datetime.now(UTC).isoformat()} ===")

    for name, check in SERVICES.items():
        try:
            if callable(check):
                ok = check()
                results[name] = {"status": "ok" if ok else "error"}
            else:
                results[name] = check_http(check)

            if results[name]["status"] != "ok":
                all_ok = False
                print(f"  FAIL  {name}: {results[name]}")
            else:
                print(f"  OK    {name}")

        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
            all_ok = False
            print(f"  FAIL  {name}: {e}")

    print(f"\nOverall: {'ALL OK' if all_ok else 'SOME SERVICES DOWN'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
