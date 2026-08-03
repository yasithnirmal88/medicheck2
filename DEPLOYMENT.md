# MediCheck Deployment Guide

## Architecture

```
                           ┌─────────────────┐
                           │   Nginx (80/443) │
                           │  medicheck-ns    │
                           └──────┬──────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
            ┌───────▼──────┐ ┌───▼────┐ ┌──────▼──────┐
            │  FastAPI API  │ │ Celery │ │  Celery     │
            │  medicheck-api│ │ Worker │ │  Beat       │
            │  :8000        │ │        │ │             │
            └───────┬───────┘ └───┬────┘ └──────┬──────┘
                    │             │             │
                    │       ┌─────▼─────┐       │
                    │       │   Redis   │       │
                    │       │ :6379     │       │
                    │       └───────────┘       │
                    │                           │
            ┌───────▼───────┐                   │
            │  PostgreSQL   │◄──────────────────┘
            │  :5432        │
            └───────────────┘
```

## Prerequisites

- Docker & Docker Compose v2
- Git
- Make (optional, for convenience targets)
- 2 GB+ RAM, 10 GB+ disk for production

## Quick Start (Production)

### 1. Clone & Configure

```bash
git clone <repo-url> /opt/medicheck
cd /opt/medicheck

cp .env.production .env
# EDIT .env with your secrets:
#   SECRET_KEY       — generate: openssl rand -hex 32
#   POSTGRES_PASSWORD — generate: openssl rand -hex 16
#   FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON
#   CORS_ORIGINS     — your production domain
```

### 2. Deploy

```bash
# Build and start all services
docker compose up -d --build

# Verify health
curl http://localhost:80/health

# Check logs
docker compose logs -f api
```

### 3. SSL (Let's Encrypt)

```bash
# Run on the production server with port 80 accessible
./scripts/init-letsencrypt.sh your-domain.com

# Then uncomment SSL sections in nginx/default.conf
# Restart frontend: docker compose restart frontend
```

## Services

| Service     | Container          | Port   | Health Check                  |
|-------------|--------------------|--------|-------------------------------|
| Nginx       | medicheck-frontend | 80/443 | `/nginx-health`               |
| API         | medicheck-api      | 8000   | `GET /api/v1/health`          |
| Worker      | medicheck-worker   | —      | Celery ping                   |
| Beat        | medicheck-beat     | —      | —                             |
| PostgreSQL  | medicheck-db       | 5432   | `pg_isready`                  |
| Redis       | medicheck-redis    | 6379   | `redis-cli ping`              |

## Environment Variables

See `.env.production` for all required variables.

### Secrets to Generate

```bash
# Application secret key
openssl rand -hex 32 > /tmp/secret_key

# Database password
openssl rand -hex 16 > /tmp/db_password
```

### Firebase Setup

1. Download service account JSON from Firebase Console > Project Settings > Service Accounts
2. Mount it to the container or base64-encode it into `FIREBASE_CREDENTIALS_JSON`:
   ```bash
   export FIREBASE_CREDENTIALS_JSON=$(cat firebase-credentials.json | python -c 'import json,sys; print(json.dumps(json.load(sys.stdin)))')
   ```

## Database

### Migrations

Migrations run automatically on container start (`alembic upgrade head`).

```bash
# Manual execution
docker compose exec api alembic upgrade head

# Rollback (one step)
docker compose exec api alembic downgrade -1

# Generate new migration (after model changes)
docker compose exec api alembic revision --autogenerate -m "description"
docker compose exec api alembic upgrade head
```

### Backups

```bash
# Manual backup
docker compose exec db pg_dump -U medicheck medicheck | gzip > backup_$(date +%Y%m%d).sql.gz

# Using backup script
./scripts/backup.sh

# Restore
./scripts/restore.sh backup_20260723_120000.sql.gz
```

**Scheduled backups (crontab):**
```cron
0 2 * * * cd /opt/medicheck && ./scripts/backup.sh
```

## Monitoring

### Health Checks

All services include Docker HEALTHCHECK directives. The API exposes a consolidated health endpoint at `GET /api/v1/health` that reports database and Redis status.

### Logs

```bash
# All services
docker compose logs -f

# Individual service
docker compose logs -f api
docker compose logs -f worker
```

Logs are rotated (json-file driver, max 10MB per file, 3 files max).

### System Metrics

```bash
# Run monitoring script
./scripts/monitor.sh

# View container stats
docker stats $(docker ps --filter "name=medicheck" -q)
```

## CI/CD Pipeline

### Workflows

- **`ci.yml`**: Runs on every push/PR to `main`/`develop`
  - Backend lint (ruff + mypy)
  - Backend tests (pytest with PostgreSQL + Redis service containers)
  - Frontend lint + typecheck
  - Frontend build
  - Docker build check + integration smoke test

- **`deploy.yml`**: Runs on push to `main`
  - Builds & pushes Docker images to GitHub Container Registry
  - SSHes into production server and deploys via `docker compose up -d`

### Required GitHub Secrets

| Secret             | Description                                      |
|--------------------|--------------------------------------------------|
| `DEPLOY_HOST`      | Production server hostname/IP                    |
| `DEPLOY_USER`      | SSH user                                         |
| `DEPLOY_SSH_KEY`   | SSH private key for deployment                   |
| `GITHUB_TOKEN`     | Auto-provided, used for GHCR push                |

## Performance

### Database Indexing

All foreign key columns are indexed. Additional indexes exist on:
- `users`: firebase_uid, email, is_active
- `health_profiles`: user_id
- `audit_logs`: actor_id, entity_type, entity_id, action, changed_at
- All status columns for filtering
- All code/key columns for lookups

### Caching

Redis-based caching via `CacheService`:
- Automatic TTL-based caching for frequent queries
- Cache invalidation on data mutations
- Pattern-based cache clearing

### Background Workers

Celery handles:
- Assessment processing (`assessments` queue)
- Notifications (`notifications` queue)
- Session cleanup (scheduled via Celery Beat)

## Security

- CORS restricted to configured origins
- Trusted Host middleware enabled
- Rate limiting via `RateLimitMiddleware` (default: 100 req/min per IP)
- Firebase token verification for all authenticated endpoints
- Nginx security headers (X-Frame-Options, XSS-Protection, CSP, HSTS)
- GZip compression (min 1000 bytes)
- Request ID tracking for audit trail

## Rollback Procedure

```bash
# 1. Roll back database migration
docker compose exec api alembic downgrade -1

# 2. Revert to previous Docker image
docker compose stop api worker beat
docker compose up -d --pull always api worker beat

# 3. Restore database if needed
./scripts/restore.sh /backups/medicheck_latest.sql.gz

# 4. Verify health
curl http://localhost:80/health
```

## Troubleshooting

| Symptom                          | Likely Cause                    | Solution                                         |
|----------------------------------|---------------------------------|--------------------------------------------------|
| API won't start                  | Database not ready              | Check `depends_on` conditions, increase wait     |
| `relation "users" does not exist`| Migrations not run              | Run `alembic upgrade head` manually              |
| Redis connection refused         | Redis not healthy               | Check `docker compose logs redis`                |
| CORS errors                      | Wrong CORS_ORIGINS              | Update .env and restart                           |
| Firebase token invalid           | Wrong credentials               | Verify FIREBASE_CREDENTIALS_PATH/JSON            |
| 502 Bad Gateway from Nginx       | API unavailable                  | Check `docker compose logs api`                  |
