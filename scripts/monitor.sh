#!/usr/bin/env bash
set -euo pipefail

# MediCheck System Monitoring Script
# Collects metrics and service status for observability

LOG_DIR="/var/log/medicheck/monitor"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$LOG_DIR"

echo "=== MediCheck Monitor: $(date) ==="

# ─── Docker Container Status ──────────────────────────────
echo "> Container Status"
docker ps --filter "name=medicheck" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" \
    > "$LOG_DIR/containers_$TIMESTAMP.log"

# ─── Resource Usage ───────────────────────────────────────
echo "> Resource Usage"
for container in $(docker ps --filter "name=medicheck" --format "{{.Names}}"); do
    stats=$(docker stats "$container" --no-stream --format \
        "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || true)
    echo "$stats" >> "$LOG_DIR/resources_$TIMESTAMP.log"
done

# ─── Health Endpoint ──────────────────────────────────────
echo "> Health Check"
curl -sf http://localhost:80/health > "$LOG_DIR/health_$TIMESTAMP.json" 2>&1 || \
    echo '{"status":"unreachable"}' > "$LOG_DIR/health_$TIMESTAMP.json"

# ─── Database Stats ───────────────────────────────────────
echo "> Database"
docker exec medicheck-db psql -U medicheck -d medicheck -c "
    SELECT count(*) as total_connections FROM pg_stat_activity;
" > "$LOG_DIR/db_connections_$TIMESTAMP.log" 2>&1 || true

docker exec medicheck-db psql -U medicheck -d medicheck -c "
    SELECT schemaname, tablename, n_live_tup as estimated_rows
    FROM pg_stat_user_tables
    ORDER BY n_live_tup DESC LIMIT 10;
" > "$LOG_DIR/db_tables_$TIMESTAMP.log" 2>&1 || true

# ─── Disk Usage ───────────────────────────────────────────
echo "> Disk"
df -h /var/lib/docker/volumes/medicheck_* | tee "$LOG_DIR/disk_$TIMESTAMP.log"

# ─── Cleanup old logs (7 days) ────────────────────────────
find "$LOG_DIR" -name "*.log" -mtime +7 -delete
find "$LOG_DIR" -name "*.json" -mtime +7 -delete

echo "=== Monitor complete: $LOG_DIR ==="
