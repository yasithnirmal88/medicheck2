# MediCheck Production Runbook

Concise operator guide: deploy, migrate, observe, recover. Backend is
FastAPI + PostgreSQL + Redis (see `docker-compose.yml`); frontend is a Vite
SPA behind Nginx (see `Dockerfile.frontend`, `vercel.json`).

## 1. Deploy

**Docker Compose (VPS / self-hosted):**
```bash
cp .env.example .env   # then fill SECRET_KEY, POSTGRES_PASSWORD, FIREBASE_*, CORS_ORIGINS, AI_* as needed
docker compose up -d --build
```
The API entrypoint runs `alembic upgrade head` automatically before
Uvicorn starts. Health: `GET http://<host>/api/v1/health` (via Nginx).

**Render (blueprint `render.yaml`):** provision PostgreSQL + Redis from the
dashboard, set `SECRET_KEY`, `FIREBASE_CREDENTIALS_JSON`, `CORS_ORIGINS`,
`ALLOWED_HOSTS`, `REDIS_URL` on the web service. `healthCheckPath` is
`/api/v1/health`. For Kubernetes-style orchestration use `/api/v1/ready`
as the readiness gate (see §3).

**Frontend (Vercel):** `npm run build` → `frontend/dist`. `VITE_API_URL`
is baked at build time — rebuilding is required to point at a different
backend.

## 2. Migrations

- Applied automatically at container start (`backend/entrypoint.sh`).
- Manual: `cd backend && alembic upgrade head` (uses `DATABASE_URL` from
  settings/env). Check chain: `alembic heads` must show exactly one head
  (`20260812_audit_schema` at time of writing).
- New migration rules: keep them idempotent (Inspector pre-checks, as in
  existing versions); PG-only DDL must no-op on SQLite (tests use
  `create_all`, never alembic).
- Downgrades are supported per-migration but are **not** the rollback
  strategy (see §7).

## 3. Health / readiness

| Endpoint | Auth | Semantics |
|---|---|---|
| `GET /api/v1/health` | none | Liveness + overview. **Always 200** (`healthy`/`degraded` + per-dep fields). |
| `GET /api/v1/ready` | none | Readiness. **200 `ready`** only when DB *and* Redis answer; else **503 `not_ready`**. Route traffic on this. |
| `GET /api/v1/ai/health` | RESEARCH_REVIEWER+ | AI/STT provider wiring (impl, credential presence — never values). `?probe=true` does a live vendor check (no PHI/tokens). |
| `GET /api/v1/ai-governance/summary` | RESEARCH_REVIEWER+ | Aggregate AI quality (`by_status`, fallback/validation rates, budget rejections). De-identified. |

API docs (`/docs`, `/redoc`, `/openapi.json`) are **off in production** by
default (`DOCS_ENABLED` overrides). If docs 404 in prod, that is intended.

## 4. Secrets — rotate

Secrets live **only** in environment (Render dashboard / `.env`, never in
git; `.env.example` holds placeholders). Rotation:

1. `SECRET_KEY` — currently unused by app code (Firebase owns auth; key is
   reserved for future use). Rotate freely; restart API.
2. `POSTGRES_PASSWORD` — change at the provider, update service env, restart.
   The app refuses to boot in production with the default value.
3. `FIREBASE_CREDENTIALS_JSON` — replace service-account key in GCP,
   update env, restart. Missing creds in production = boot refusal.
4. `AI_API_KEY` / `STT_API_KEY` — rotate at the vendor, update env,
   restart. Verify with `/ai/health?probe=true` (expect `healthy`).
5. `REDIS_PASSWORD` — update Redis + `REDIS_URL`/service env, restart.

After any rotation: hit `/ready` (200) and, for AI keys, `/ai/health?probe=true`.

## 5. AI audit logs — investigate

Audit tables live in the **`audit` PostgreSQL schema**
(`audit.ai_interaction_audits`, `audit.audit_logs`); raw SQL must qualify
the schema. Rows hold **hashes + ids + statuses only — no PHI, ever**.

```sql
-- recent failures by status (governance mirror of /ai-governance/summary)
SELECT status, count(*) FROM audit.ai_interaction_audits
GROUP BY status ORDER BY count(*) DESC;
-- trace one explanation end-to-end (trace_id from the API response)
SELECT * FROM audit.ai_interaction_audits WHERE trace_id = '<trace_id>';
-- budget rejections (spend guardrail trips)
SELECT session_id, status_reason FROM audit.ai_interaction_audits
WHERE status = 'budget_exceeded' ORDER BY created_at DESC LIMIT 50;
-- admin action trail
SELECT * FROM audit.audit_logs ORDER BY changed_at DESC LIMIT 50;
```

Logs: text by default, `LOG_FORMAT=json` for aggregation. Every log line
carries `request_id` (also returned as `X-Request-ID`). Request/response
bodies are never logged; paths may contain resource UUIDs (not PHI).

## 6. Failure modes — what to do

| Symptom | Likely cause | Action |
|---|---|---|
| Container restarts / boot loop | Prod fail-fast trip (`ALLOW_MOCK_AUTH`, Firebase creds, default DB password) | Read startup logs; fix the named env var. Never enable mock auth in prod. |
| `/ready` 503, `db_status` unhealthy | PostgreSQL down/migrating/creds | Check DB health, `DATABASE_URL`, run `alembic current`; see §7 if a migration is stuck. |
| `/ready` 503, `redis_status` unhealthy | Redis down | App still serves clinical paths (Redis is cache/budgets with local fallback); AI budgets enforce approximately per-process until Redis returns. Restore Redis, no restart needed. |
| `/ai/health?probe=true` → `auth_failed` | Rotated/revoked vendor key | Rotate AI/STT keys (§4), re-probe. |
| 429 `ai_budget_exceeded` spike | Runaway client or too-tight budget | Check governance `by_status`; raise `AI_BUDGET_*` envs or revoke the abusive credential; budgets reset on UTC hour/day rollover. |
| 429 `rate_limit_exceeded` | Per-IP burst (100/min default, **per worker process** — 4 workers ≈ 4× effective) | Normally self-heals; raise `RATE_LIMIT_*` or fix the client loop. Global Redis-backed limiting is a planned follow-up. |
| 5xx spike with Sentry quiet | Sentry not configured | Set `SENTRY_DSN` (requires `sentry-sdk` installed) and restart; until then, tail container logs (`max-size 10m × 3` rotation in compose). |
| AI explanations unavailable (`available=false`) | Vendor down / bad output / budget | Check `/ai/health?probe=true` + governance fallback rates; deterministic reports are unaffected. No action needed for the clinical path. |
| Migration failure at deploy | Partial/failed DDL | Entrypoint is `set -euo pipefail`: container stops before serving. Inspect `alembic current`, fix forward (see §7); never hand-edit `alembic_version` except to unstick a **proven-no-op** step. |

## 7. Rollback

- **Code/config:** redeploy the previous image / Render deploy (blueprint
  pins `branch: main`; use Render's rollback or `git revert`). No API
  contract changed by recent hardening work, so rollbacks are config-safe.
- **Database:** roll **forward**, not back. Downgrades exist per migration
  but data-loss risk (e.g. moving tables between schemas) makes
  restore-from-backup the supported path:
  `pg_dump -Fc` before deploys that touch the DB; restore with `pg_restore`.
  Managed Postgres (Render) point-in-time recovery is preferred where
  available. There is **no automated backup job in-repo** (compose only
  mounts `./scripts/backups`) — schedule one before relying on this path.
- Frontend: redeploy the previous Vercel deployment / Nginx image.

## 8. Known production notes (by design)

- Rate limiting is in-memory per worker (multiplier + reset on recycle);
  CSRF middleware stays off (stateless Bearer-token API — no cookies to
  forge); `VITE_API_URL` is build-time baked; AI budgets are request-count
  (not token) based; SI/TA diagnostic screening is narrow by design with
  romanized script out of scope (see `MEDICHECK_AI_PROVIDERS.md` §7).
