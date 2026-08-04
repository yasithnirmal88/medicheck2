# MediCheck — Render Deployment Guide (Backend)

This document prepares the **FastAPI backend** for deployment on
[Render.com](https://render.com). It does **not** deploy — it provisions the
repository so that deployment succeeds cleanly.

---

## 1. What was verified / changed

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Dockerfile | ✅ OK (1 fix) | Multi-stage `python:3.12-slim`. `CMD` now binds to `${PORT:-8000}` (Render injects `$PORT`). |
| 2 | docker-compose | ✅ OK | For local/full-stack (PostGIS + Redis + Celery worker/beat). **Not** used by Render. |
| 3 | requirements | ✅ OK (1 fix) | `requirements.txt` now pins `-r requirements/base.txt` + `gunicorn` so build == declared deps. |
| 4 | Startup command | ✅ OK | `entrypoint.sh` runs `alembic upgrade head` then `exec`. |
| 5 | Health endpoint | ✅ OK | `GET /api/v1/health` — returns 200 and DB/Redis status. |
| 6 | PostgreSQL | ✅ OK (robustness fix) | Config normalizes plain `postgres://` → `postgresql+asyncpg://` for async engine. |
| 7 | Redis | ✅ OK | Non-blocking; `redis_health_check()` fails soft and app still starts. |
| 8 | Alembic migrations | ✅ OK | `env.py` overrides `sqlalchemy.url` from settings; `entrypoint.sh` auto-runs `upgrade head`. |
| 9 | Environment variables | ✅ OK | See section 2. All `sync: false` secrets must be set in Render dashboard. |
| 10 | CORS | ⚠️ Must configure | `CORS_ORIGINS` and `ALLOWED_HOSTS` must match your deployed domains. |
| 11 | Production logging | ✅ OK | `structlog`-style console handler to stdout; `LOG_LEVEL=INFO`. |

---

## 2. Required Render Environment Variables

Set these on the Render **Web Service** (Dashboard → your service → Environment).

### Auto-provisioned by Render (do **not** create manually)
| Variable | Source |
|----------|--------|
| `PORT` | Injected automatically. |
| `DATABASE_URL` | From Render PostgreSQL (see section 5). |

### Application / Security
| Variable | Example | Required |
|----------|---------|----------|
| `ENVIRONMENT` | `production` | ✅ |
| `LOG_LEVEL` | `INFO` | ✅ |
| `SECRET_KEY` | `<generate 64-char random>` | ✅ |
| `ALLOW_MOCK_AUTH` | `false` | ✅ |
| `PROJECT_NAME` | `MediCheck` | optional |
| `API_V1_PREFIX` | `/api/v1` | optional |
| `CORS_ORIGINS` | `https://your-app.onrender.com` | ✅ |
| `ALLOWED_HOSTS` | `medicheck-api.onrender.com,your-app.onrender.com` | ✅ |

### Firebase
| Variable | Example | Required |
|----------|---------|----------|
| `FIREBASE_CREDENTIALS_JSON` | full service-account JSON string | ✅ (auth breaks without it) |
| `ALLOW_MOCK_AUTH` | `false` | ✅ |

### Celery (only if you run a background worker service)
| Variable | Example |
|----------|---------|
| `CELERY_BROKER_URL` | `redis://:<pw>@<redis-host>:6379/1` |
| `CELERY_RESULT_BACKEND` | `redis://:<pw>@<redis-host>:6379/1` |

> Generate a secret key: `openssl rand -hex 32`

---

## 3. Build Command

Using Docker runtime on Render:

```text
dockerfilePath: ./backend/Dockerfile
```

No custom build command is needed — Render builds the Docker image from
`backend/Dockerfile` and runs the image's `CMD`.

---

## 4. Start Command

Render uses the image's `CMD` (already updated in the Dockerfile):

```text
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-4} --limit-max-requests 10000
```

- `PORT` is injected by Render.
- `entrypoint.sh` runs `alembic upgrade head` (migrations) before the app starts.

> To maximize free-tier memory, set `WEB_CONCURRENCY=1`.

---

## 5. PostgreSQL configuration

- Use **Render PostgreSQL** (Dashboard → New → PostgreSQL).
- The Render service injects `DATABASE_URL` automatically in the form
  `postgres://USER:pass@HOST:5432/db` (**sync scheme**).
- The backend uses an **async** engine, so `app/core/config.py` now normalizes
  the scheme to `postgresql+asyncpg://` automatically. Do **not** paste
  `DATABASE_URL` manually with an asyncpg string unless it already matches.
- The managed Postgres instance ships with the `postgis` extension available;
  if you require it, enable it via `CREATE EXTENSION IF NOT EXISTS postgis;`.

> Security: Render PostgreSQL exposes an internal and external URL. Use the
> internal URL on deployed services.

---

## 6. Redis configuration

- Create **Render Redis** (Dashboard → New → Redis).
- Set the app's `REDIS_URL` to the instance's **Internal Connection String**
  — e.g. `redis://default:<password>@host:6379`.
- The app's `redis_url` setting supports:
  - `REDIS_URL` (full URL), **or**
  - `REDIS_HOST` + `REDIS_PORT` + `REDIS_PASSWORD` (built automatically).
- Redis is non-blocking: if it is unreachable, the app still boots and the
  `/api/v1/health` endpoint reports `redis_status: "unhealthy"` while the
  service returns HTTP 200. Fix the connection to restore full functionality.

> On a free Render instance you may not run Celery reliably; the web service
> itself does **not** require Celery to serve requests.

---

## 7. Health check path

```text
/api/v1/health
```

- Returns HTTP `200` with JSON:
  `{"status":"healthy","db_status":"healthy","redis_status":"healthy",...}`
- If DB is down → `db_status: "unhealthy"`, overall `"degraded"`.
- If Redis is down → `redis_status: "unhealthy"`, overall `"degraded"`.
- Render treats any HTTP 200 as healthy; 2xx-3xx accepted.

---

## 8. Deployment checklist

### Pre-deploy
- [ ] `SECRET_KEY` generated (≥ 32 bytes; blank/`change-me...` is rejected).
- [ ] `ALLOW_MOCK_AUTH=false`.
- [ ] `FIREBASE_CREDENTIALS_JSON` set (service account) — otherwise prod auth fails.
- [ ] `CORS_ORIGINS` = your real frontend origin(s).
- [ ] `ALLOWED_HOSTS` includes the Render API hostname + frontend hostname.
- [ ] Provision Render PostgreSQL and Redis.
- [ ] Confirm Render web service env vars are set (no reliance on `.env` file — it is git-ignored).

### Build / run
- [ ] Docker provides `backend/Dockerfile` at path `./backend/Dockerfile`.
- [ ] Health check path set to `/api/v1/health`.

### Post-deploy
- [ ] Visit `https://<your-app>.onrender.com/api/v1/health` and confirm `"healthy"`.
- [ ] Confirm `/api/v1/docs` (Swagger) loads.
- [ ] Test an authenticated request (Firebase token) end-to-end.
- [ ] Confirm DB is seeded (seed runs idempotently on startup).

### Common pitfalls
- `Invalid host header` / 400 → `ALLOWED_HOSTS` does not include your Render host.
- `DATABASE_URL` with plain `postgres://` → fixed automatically; verify it became `postgresql+asyncpg://`.
- Auth 401/403 on all routes → Firebase creds missing or `ALLOW_MOCK_AUTH` left true.