# MediCheck Security Audit

Audit date: 2026-08-04
Scope: Backend (FastAPI) + Frontend (React/Vite) + Docker/Infra
Classification: Internal — contains findings about protected health data handling.

---

## Executive Summary

Two **critical** broken-access-control (IDOR) vulnerabilities were found and **fixed**:
any authenticated user could read another user's health assessment results and
generated medical reports by guessing/session/report IDs. Both fixes enforce
data ownership at the service layer and are covered by new regression tests.

No SQL injection or stored/reflected XSS sinks were found. Secrets are correctly
excluded from git. Authentication uses Firebase ID tokens verified via the
Firebase Admin SDK (no bespoke JWT in the application code path).

---

## Findings

### CRITICAL — Fixed

#### 1. Broken Object Level Authorization in report endpoints (IDOR)
- **Files:** `backend/app/api/v1/endpoints/report.py`,
  `backend/app/application/services/report_service.py`
- **Endpoints:** `GET /report/{session_id}`, `GET /report/id/{report_id}`,
  `POST /report/generate`, `GET /report/compare/{id1}/{id2}`
- **Issue:** Endpoints only authenticated (`get_current_user`) but never verified
  that the target report/session belonged to the caller. Any logged-in user could
  read or generate the medical report of any other user.
- **Fix:** `ReportService.get_report_by_session`, `get_report`, `compare_reports`
  now take an optional `user_id` and return `None` (→ 404) when the record's
  `user_id` does not match. `generate_report` rejects foreign sessions. Endpoints
  pass `current_user.id`.
- **Tests:** `tests/test_report_service.py::test_report_getters_enforce_ownership`

#### 2. Broken Object Level Authorization in CDSE endpoints (IDOR)
- **Files:** `backend/app/api/v1/endpoints/cdse.py`,
  `backend/app/application/services/clinical_decision_service.py`
- **Endpoints:** `GET /assessment/results/{session_id}`, `GET /assessment/result/{result_id}`,
  `GET /assessment/{session_id}/explanation`, `/recommendations`, `/laboratory-tests`, `/screenings`,
  `POST /assessment/process`
- **Issue:** Same pattern — read/process access was not bound to the owner.
- **Fix:** `ClinicalDecisionService.process_assessment` rejects sessions whose
  `user_id` differs; `get_result_by_session` / `get_result` take `user_id` and
  return `None` (→ 404) for foreign records. Endpoints pass `current_user.id`.
- **Tests:** `tests/test_clinical_decision_service.py::test_cdse_result_getters_enforce_ownership`

---

### MEDIUM — Recommended follow-up (not blocking)

#### 3. Rate limiter is in-memory and per-process
- `backend/app/core/security/rate_limit.py`
- `RateLimitMiddleware` stores per-IP request timestamps in a process-local dict.
  With `WEB_CONCURRENCY > 1` (or multiple dynos) each worker enforces its own
  budget, so the effective limit scales with process count. It also keys on
  `request.client.host` (not `X-Forwarded-For`), so behind a proxy the limiter
  sees the proxy IP. **Recommendation:** migrate to the Redis-backed
  `RateLimiter` in the same module for distributed, accurate limiting.

#### 4. CSRF middleware is defined but not registered
- `backend/app/api/middleware.py::CSRFProtectMiddleware` is commented out in
  `backend/app/main.py`. Risk is mitigated because authentication is a
  `Bearer` token in the `Authorization` header (not cookies), so classic
  cross-site form POSTs cannot carry the token. **Recommendation:** enable it
  in production to defend against CSRF via any future cookie-based flows.

#### 5. Default DB password in compose
- `backend/docker-compose.yml` falls back to `POSTGRES_PASSWORD:-medicheck_secret`.
  Fine for local dev only. **Recommendation:** never ship/run this default in a
  shared or internet-facing environment.

#### 6. No Docker secrets
- Compose passes secrets via `.env` / `environment`. This is acceptable for
  Render/one-host deployments. **Recommendation:** prefer the Docker secrets
  mechanism or a managed secret store (e.g., Render env vars) and rotate
  secrets periodically. Do not commit `.env*`.

#### 7. New users are created with an empty role set
- `backend/app/domain/entities/user.py::User.create` assigns `roles=set()`.
  This is not a privilege escalation (no role ⇒ no elevated access), but a
  role should be assigned at registration so `get_cms_user` / role checks
  behave consistently for normal patients.

---

### LOW / Informational

- **Unauthenticated knowledge-graph GETs** — `backend/app/api/v1/endpoints/graph.py`
  exposes `GET /graph/question/{id}`, `GET /graph/indicator/{id}`,
  `GET /graph/condition/{id}` without auth. These return public clinical
  knowledge-base data only (no user data). Consider protecting if this content
  is considered proprietary.
- **CSP `'unsafe-inline'`** — `script-src` includes `'unsafe-inline'` (required by
  some Firebase tooling). Recommend tightening once feasible and removing
  `'unsafe-inline'` from `script-src` for defense-in-depth against XSS.
- **`test_uat.py` and some integration tests require external services** and
  time out in CI without them; auth integration tests assume
  `allow_mock_auth=True` in test settings.

---

## Areas verified and CLEAN

| Area | Result |
|------|--------|
| Authentication (Firebase) | Tokens verified via Firebase Admin SDK; mock auth gated by `ALLOW_MOCK_AUTH`; prod blocks unconfigured auth |
| JWT | No bespoke JWT in app code path (`python-jose` present but unused) |
| RBAC | `Permission`/`Role` enums + `check_permission`; CMS content endpoints enforce per-entity permissions |
| SQL Injection | No string-built SQL; all SQLAlchemy ORM/Core with bound params |
| XSS (frontend) | No `dangerouslySetInnerHTML`/`eval`/`document.write`; auth token held in memory only (not localStorage) |
| Secrets / env vars | `.env*`, `*.pem`, service-account JSON gitignored; none tracked in git history |
| CORS | Origin allowlist (no wildcard in prod default), `allow_credentials=True`, trusted-host middleware |
| Security headers | HSTS, nosniff, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy, CSP |
| Audit logging | Sensitive-path request audit log via `AuditLogMiddleware` |

---

## Verification

- `pytest tests/test_report_service.py tests/test_clinical_decision_service.py` — 4 passed
- `pytest tests/test_knowledge_graph.py tests/test_profile_repository.py tests/unit` — 132 passed
- `pytest tests/test_admin_service.py` — 1 passed
- Imports verified: `app.api.v1.endpoints.report`, `cdse`, and both services.
- Ruff: no new violations introduced by the fixes.
