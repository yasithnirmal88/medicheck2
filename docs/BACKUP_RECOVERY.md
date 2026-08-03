# Backup & Recovery Guide

## Backup Strategy

### Database Backups

#### PostgreSQL (Production)

```bash
# Daily full backup (cron: 0 2 * * *)
pg_dump -U postgres -d medicheck -F custom -f /backups/medicheck_$(date +%Y%m%d).dump

# Point-in-time recovery (WAL archiving)
# Configure in postgresql.conf:
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backups/wal/%f'

# Restore from backup
pg_restore -U postgres -d medicheck -F custom /backups/medicheck_20260723.dump
```

#### SQLite (Development)

```bash
# Backup
cp backend/test.db backend/test.db.backup

# Restore
cp backend/test.db.backup backend/test.db
```

### Redis Backups

```bash
# Save RDB snapshot
redis-cli SAVE
cp /var/lib/redis/dump.rdb /backups/redis_$(date +%Y%m%d).rdb

# Restore
cp /backups/redis_20260723.rdb /var/lib/redis/dump.rdb
redis-cli FLUSHALL
redis-server
```

### Configuration Backups

```bash
# Backup environment files
cp .env.production /backups/env/env.production.$(date +%Y%m%d)
```

## Recovery Procedures

### Full System Recovery

```bash
# 1. Restore database
pg_restore -U postgres -d medicheck -F custom /backups/medicheck_latest.dump

# 2. Run migrations (if backup is from older schema version)
alembic upgrade head

# 3. Restart services
docker-compose restart api

# 4. Verify health
curl http://localhost:8000/api/v1/health
```

### Database-Only Recovery

```bash
# 1. Stop application
docker-compose stop api

# 2. Drop and recreate database
dropdb medicheck
createdb medicheck

# 3. Restore from backup
pg_restore -U postgres -d medicheck /backups/medicheck_20260723.dump

# 4. Start application
docker-compose start api
```

### Point-in-Time Recovery

```bash
# 1. Restore base backup
pg_restore -U postgres -d medicheck /backups/medicheck_weekly.dump

# 2. Apply WAL segments up to target time
# Configure recovery.conf:
restore_command = 'cp /backups/wal/%f %p'
recovery_target_time = '2026-07-23 14:30:00'

# 3. Start PostgreSQL (will apply WAL and stop at target time)
pg_ctl start
```

## Disaster Recovery Plan

### Level 1: Minor Data Loss (last 1 hour)

- Restore from latest WAL segment
- Data loss: < 1 hour
- Recovery time: < 15 minutes

### Level 2: Moderate Data Loss (last 24 hours)

- Restore from daily backup + WAL
- Data loss: < 24 hours
- Recovery time: < 30 minutes

### Level 3: Major Failure (hardware/database corruption)

- Restore from last known good backup
- Data loss: up to 24 hours
- Recovery time: < 2 hours

### Level 4: Complete Site Failure

- Provision new infrastructure (Infrastructure as Code)
- Restore from off-site backup
- Data loss: up to 24 hours
- Recovery time: < 4 hours

## Backup Schedule

| Backup Type | Frequency | Retention | Location |
|------------|-----------|-----------|----------|
| Database (full) | Daily | 30 days | Local + S3 |
| WAL segments | Continuous | 7 days | Local |
| Redis RDB | Hourly | 24 hours | Local |
| Configuration | On change | 90 days | Git + S3 |
| Off-site | Daily | 90 days | S3 |

## Verification

```bash
# Verify backup integrity
pg_restore -l /backups/medicheck_20260723.dump | head -20

# Test restore in staging
# 1. Restore backup to staging database
# 2. Run health checks
# 3. Verify key records exist
# 4. Generate test report
```

## Rollback Procedure

See [Rollback Checklist](ROLLBACK_CHECKLIST.md) for detailed rollback steps.
