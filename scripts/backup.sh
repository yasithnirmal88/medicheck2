#!/usr/bin/env bash
set -euo pipefail

# MediCheck Database Backup Script
# Usage: ./scripts/backup.sh [database_name] [output_dir]

DB_NAME="${1:-medicheck}"
BACKUP_DIR="${2:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/medicheck_${TIMESTAMP}.sql.gz"
LATEST_LINK="${BACKUP_DIR}/medicheck_latest.sql.gz"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "=== MediCheck Backup: $(date) ==="
echo "Database: $DB_NAME"
echo "Backup:   $BACKUP_FILE"

# Perform backup
PGPASSWORD="${POSTGRES_PASSWORD:-medicheck_secret}" pg_dump \
    -h "${POSTGRES_HOST:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-medicheck}" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    --compress=9 \
    --verbose \
    > "$BACKUP_FILE" 2>&1

echo "Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Create / update latest symlink
ln -sf "$BACKUP_FILE" "$LATEST_LINK"

# Rotate old backups
find "$BACKUP_DIR" -name "medicheck_*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "Removed backups older than ${RETENTION_DAYS} days"

# Verify backup integrity
gunzip -t "$BACKUP_FILE" && echo "Backup integrity: OK" || echo "Backup integrity: FAILED"

echo "=== Backup complete ==="
