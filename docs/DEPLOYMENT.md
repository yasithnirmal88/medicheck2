# Deployment Guide

## Architecture Overview

```
                        ┌─────────────┐
                        │   Nginx      │
                        │  (Reverse    │
                        │   Proxy)     │
                        └──────┬──────┘
                               │
                  ┌────────────┴────────────┐
                  │                         │
          ┌───────┴───────┐         ┌───────┴───────┐
          │   Frontend     │         │   Backend      │
          │  (React/Vite)  │         │ (FastAPI/Uvicorn)
          └───────────────┘         └───────┬───────┘
                                            │
                  ┌─────────────────────────┼─────────────────────────┐
                  │                         │                         │
          ┌───────┴───────┐         ┌───────┴───────┐         ┌───────┴───────┐
          │   PostgreSQL   │         │   Redis        │         │   Firebase    │
          │   (Database)   │         │   (Cache)      │         │   (Auth)      │
          └───────────────┘         └───────────────┘         └───────────────┘
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- Redis 7+
- Firebase project (for authentication)
- Nginx (for production reverse proxy)

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/medicheck
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<generate-random-64-char-key>
ENVIRONMENT=development  # development | staging | production

# Firebase
FIREBASE_CREDENTIALS_PATH=/path/to/service-account.json
FIREBASE_PROJECT_ID=medicheck-xxxxx

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
VITE_FIREBASE_CONFIG=...
```

## Docker Deployment

### Build Images

```bash
# Backend
docker build -f backend/Dockerfile -t medicheck-api:latest .

# Frontend
docker build -f frontend/Dockerfile -t medicheck-ui:latest .
```

### Docker Compose

```bash
docker-compose up -d
```

Services: api, ui, postgres, redis, nginx, prometheus, grafana

### Zero-Downtime Deployment

```bash
# Deploy backend with rolling update
docker service update --image medicheck-api:latest medicheck_api

# Health check endpoint
curl -f http://localhost:8000/api/v1/health
```

## Manual Deployment

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed database
python -m app.infrastructure.seed

# Start with uvicorn
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd frontend
npm install
npm run build
# Serve dist/ via Nginx
```

## Monitoring Stack

- **Prometheus**: Metrics collection at `:9090`
- **Grafana**: Dashboards at `:3000` (admin/admin)
- **Health Endpoint**: `GET /api/v1/health`
  - Returns DB, Redis, Firebase status
  - Used by Docker health checks and load balancers

## Production Checklist

- [ ] PostgreSQL connection pooling configured (pgbouncer recommended)
- [ ] Redis password set
- [ ] CORS origins restricted to known domains
- [ ] Rate limiting configured (100 req/60s default)
- [ ] Security headers enabled (CSP, HSTS, X-Frame-Options)
- [ ] Firebase service account secured
- [ ] Logging level set to WARNING in production
- [ ] Database backups configured (daily)
- [ ] SSL/TLS certificates configured
- [ ] Monitoring alerts configured
- [ ] Rollback procedure documented
