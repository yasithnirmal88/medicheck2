#!/usr/bin/env bash
set -euo pipefail

# MediCheck Rollback Strategy
# Usage: ./scripts/rollback.sh [version|latest]
# Requires: docker, docker-compose, and previous image tags

echo "=== MediCheck Rollback ==="

VERSION="${1:-latest}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
BACKUP_FILE="${BACKUP_DIR:-./backups}/medicheck_latest.sql.gz"

echo "Target version: $VERSION"
echo "Compose file:   $COMPOSE_FILE"

# 1. Verify backup exists
if [ -f "$BACKUP_FILE" ]; then
    echo "> Backup found: $BACKUP_FILE"
else
    echo "> WARNING: No backup found at $BACKUP_FILE. Skipping DB restore."
fi

# 2. Rollback database to previous migration
if command -v alembic &> /dev/null; then
    echo "> Rolling back database migration..."
    alembic downgrade -1
    echo "> Database rolled back one revision."
fi

# 3. Determine previous image tag
if [ "$VERSION" = "latest" ]; then
    # Use the previous image (assumes :prev tag was set during deploy)
    API_IMAGE="medicheck-api:prev"
    FRONTEND_IMAGE="medicheck-frontend:prev"
else
    API_IMAGE="medicheck-api:$VERSION"
    FRONTEND_IMAGE="medicheck-frontend:$VERSION"
fi

echo "> Rolling back API to: $API_IMAGE"
echo "> Rolling back Frontend to: $FRONTEND_IMAGE"

# 4. Pull and restart with previous images
export API_IMAGE
export FRONTEND_IMAGE
docker-compose -f "$COMPOSE_FILE" up -d --no-deps api frontend

echo "> Waiting for health checks..."
sleep 10

# 5. Verify rollback
curl -sf http://localhost:80/api/v1/health && echo "Rollback verified." || echo "Rollback verification FAILED."

echo "=== Rollback complete ==="
