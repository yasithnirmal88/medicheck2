# MediCheck — Healthcare Risk Assessment Platform

Full-stack healthcare platform with FastAPI backend, React frontend, PostgreSQL, Redis, and Celery workers.

## Quick Start (Development)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements/dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

## Production Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for the complete production deployment guide.

Quick production start:

```bash
cp .env.production .env
# Edit .env with your secrets
docker compose up -d --build
```

## Architecture

```
Nginx (reverse proxy) → React (static files)
                     → FastAPI (API server)
                     → Celery (background workers)
                     → PostgreSQL (primary database)
                     → Redis (cache + message broker)
```

## Project Structure

```
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # REST endpoints
│   │   ├── core/      # Config, logging, security, events
│   │   ├── domain/    # Business logic, entities, services
│   │   └── infrastructure/
│   │       ├── persistence/models/   # SQLAlchemy models (70+ tables)
│   │       └── persistence/repositories/
│   ├── alembic/       # Database migrations
│   ├── workers/       # Celery background tasks
│   └── tests/
├── frontend/          # React + Vite + TypeScript
│   └── src/
│       ├── features/  # Feature modules (cms, auth, dashboard, etc.)
│       └── routes/    # Route definitions
├── nginx/             # Nginx configuration
├── scripts/           # Backup, restore, monitoring scripts
├── docker-compose.yml # All services
└── Dockerfile.frontend
```

## CI/CD

GitHub Actions workflows in `.github/workflows/`:
- **ci.yml** — Lint, test, build on every PR/push
- **deploy.yml** — Build & deploy on push to `main`
