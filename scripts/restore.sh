#!/usr/bin/env bash
set -euo pipefail

# MediCheck Database Restore Script
# Usage: ./scripts/restore.sh <backup_file> [database_name]

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.sql.gz> [database_name]"
    exit 1
fi

BACKUP_FILE="$1"
DB_NAME="${2:-medicheck}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "=== MediCheck Restore: $(date) ==="
echo "Database: $DB_NAME"
echo "Backup:   $BACKUP_FILE"

# Confirm
read -rp "WARNING: This will DROP and recreate database '$DB_NAME'. Continue? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo "Dropping and recreating database..."
PGPASSWORD="${POSTGRES_PASSWORD:-medicheck_secret}" psql \
    -h "${POSTGRES_HOST:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-medicheck}" \
    -d postgres \
    -c "DROP DATABASE IF EXISTS \"$DB_NAME\";"
PGPASSWORD="${POSTGRES_PASSWORD:-medicheck_secret}" psql \
    -h "${POSTGRES_HOST:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-medicheck}" \
    -d postgres \
    -c "CREATE DATABASE \"$DB_NAME\";"

echo "Restoring from backup..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="${POSTGRES_PASSWORD:-medicheck_secret}" psql \
    -h "${POSTGRES_HOST:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-medicheck}" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    2>&1

echo "Running Alembic migrations to ensure schema is current..."
cd /app/backend && alembic upgrade head

echo "=== Restore complete ==="
