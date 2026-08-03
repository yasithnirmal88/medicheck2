#!/usr/bin/env bash
set -euo pipefail

# MediCheck Docker Entrypoint
# Runs before the application starts

echo "=== MediCheck Entrypoint ==="

# Run database migrations
echo "> Running Alembic migrations..."
alembic upgrade head
echo "> Migrations complete."

# Start the application
exec "$@"
