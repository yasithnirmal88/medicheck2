# Medicheck Test Architecture Audit

**Audit timestamp:** 2026-07-23 06:00 (project reference time)  
**Repository:** `C:\Users\DELL\Documents\GitHub\medicheck`  
**Scope:** Existing implementation and test architecture only. No production code, tests, runner configuration, dependencies, or CI files were rewritten. The only intended repository change from this audit is this document.

## 1. Executive summary

Medicheck is a FastAPI/SQLAlchemy async backend and a React/Vite/TypeScript frontend. The backend has a useful but narrow pytest foundation: 145 tests collect, 130 low-level unit tests pass reliably, and 15 database/API tests fail or error because of test-infrastructure defects. Measured backend coverage is **53%**, well below the requested 95%. The frontend has Vitest installed and an npm `test` command, but contains **zero first-party test files**, no configured browser-like test environment, no coverage provider/threshold, and no Playwright installation or configuration; therefore frontend coverage is effectively **0% measured/covered by tests**, versus the requested 90%.

The existing system should be extended, not replaced. Reuse pytest, pytest-asyncio, pytest-cov, the temporary SQLite `db_session`, HTTPX `ASGITransport` client, FastAPI dependency overrides, and the current domain-engine unit-test style. Repair the shared fixtures and database connection strategy first, then add category-specific tests around the current layered architecture. On the frontend, keep Vitest/Vite and add Testing Library, user-event, jsdom, MSW, axe, and Playwright around the current providers and React Query usage.

Immediate blockers are deterministic, not currently flaky:

- `backend/tests/conftest.py::client` calls `get_test_settings()` without its required `database_url`, causing all 10 auth API tests to error before execution.
- Five service/repository tests create SQLite `:memory:` engines with `NullPool`. Schema creation and test sessions use different connections, so each new connection sees an empty database (`no such table`).
- CI declares Python 3.11 although `pyproject.toml` requires Python >=3.12, and backend CI only echoes placeholders instead of linting/testing.
- Frontend `npm run test -- --run` exits 1 because no test files exist.
- Frontend typecheck fails with many React Query v5 signature/type errors; lint reports 95 errors.
- Production build succeeds but emits a 777.09 kB chunk warning.

## 2. Repository and framework inventory

### Backend

- Language/runtime contract: Python >=3.12 (`backend/pyproject.toml`). Local baseline actually ran on Python 3.14.6.
- Web framework: FastAPI with HTTPX ASGI testing.
- Validation/configuration: Pydantic v2 and pydantic-settings.
- Persistence: SQLAlchemy 2 async ORM, asyncpg for PostgreSQL, aiosqlite used in tests.
- Migrations: Alembic; two version files exist under `backend/alembic/versions`.
- Production database/services: PostgreSQL/PostGIS 16 and Redis 7 via `backend/docker-compose.yml`.
- Workers: Celery with Redis.
- Authentication: Firebase Admin/provider abstractions.
- Test runner: pytest with pytest-asyncio (`asyncio_mode = "auto"`).
- Coverage: pytest-cov is installed, but no source/omit rules, branch coverage, report policy, or fail-under threshold is configured.
- Static checks available: Ruff and mypy in dev requirements; neither is genuinely enforced by CI.

### Frontend

- UI: React 19, TypeScript, React Router 6, Tailwind CSS 4.
- Build/dev: Vite 5.
- Server state: TanStack React Query 5.
- Forms/validation: React Hook Form, Zod, `@hookform/resolvers`.
- HTTP/auth: Axios and Firebase.
- Test runner dependency: Vitest 1.6.1 resolved in the current lock/install.
- Missing test stack: no Testing Library, user-event, jsdom/happy-dom, jest-dom, MSW, axe, Playwright, or Vitest coverage provider.
- `vite.config.ts` configures React and the `@` alias only; there is no `test` section.
- No Playwright config, Playwright executable, E2E directory, or first-party E2E specs exist.

## 3. Test layout, fixtures, factories, and mocks

### Backend test directories and files

- `backend/tests/unit/`
  - `test_branching.py`: dependency and branching logic.
  - `test_domain.py`: user entity behavior.
  - `test_scoring.py`: questionnaire scoring.
  - `test_validation.py`: answer validation.
  - `test_value_objects.py`: email and phone value objects.
  - `conftest.py`: only an autouse no-op fixture.
- `backend/tests/integration/test_api/test_auth.py`: 10 auth/health API tests.
- Root-level mixed tests:
  - `test_admin_service.py`
  - `test_clinical_decision_service.py`
  - `test_knowledge_graph.py`
  - `test_profile_repository.py`
  - `test_report_service.py`
- `backend/tests/fixtures/` exists but contains only `__init__.py`; there are no fixture data files.

### Shared backend fixtures

`backend/tests/conftest.py` provides:

- `test_settings`: session-scoped settings using a temporary file-backed SQLite database.
- `event_loop`: explicit session loop (potential compatibility risk with newer pytest-asyncio loop management).
- `db_session`: async SQLAlchemy session; creates and drops all metadata around each test.
- `client`: HTTPX `AsyncClient` over `ASGITransport`, FastAPI `get_db` override, and mutation/reset of module-level settings/engine globals.
- `sample_user` and `sample_inactive_user`: hand-built domain entities.
- `mock_firebase_token`: string token only.

### Factories and mocks

- No Factory Boy/model-bakery/custom object factory layer exists.
- No reusable repository/service fakes exist.
- API auth tests do not visibly patch Firebase verification/provider behavior; once the broken client fixture is repaired, Firebase integration assumptions must be validated.
- No backend `unittest.mock`, pytest `monkeypatch`, responses/respx, freezegun, or external-service mock infrastructure is established.
- Frontend `src/test/mocks/` exists but is empty.
- There is no frontend render helper, provider wrapper, QueryClient factory, request mock server, fixture builder, or fake timer policy.

## 4. Database and migration test setup

Production uses PostgreSQL/PostGIS through Docker Compose and Alembic. Current automated tests use SQLite only. The shared `db_session` correctly chooses a temporary file, which allows multiple connections to share schema state, although it recreates and drops the entire large metadata set per test and may become slow.

Five root tests bypass the shared fixture and use:

```python
create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=NullPool)
```

This is invalid for their usage: `NullPool` opens a fresh connection after schema creation, and each SQLite in-memory connection has its own database. The observed missing-table failures are expected. Reuse the file-backed fixture, or use a shared connection/`StaticPool` where SQLite parity is acceptable.

Additional risks:

- SQLite does not validate PostgreSQL/PostGIS behavior, isolation, locking, JSON/array semantics, server defaults, or migrations.
- No Alembic upgrade/downgrade test exists.
- No clean PostgreSQL schema integration lane exists.
- A root `test.db` exists, but current shared fixtures use temporary databases; do not make tests depend on this persistent file.
- `Base.metadata.create_all()` tests model metadata, not the deployable Alembic migration chain.

## 5. Coverage configuration and baseline

### Existing configuration

Backend `pyproject.toml` has only:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

There is no `[tool.coverage.*]`, branch coverage, fail-under, path normalization, or CI coverage artifact. Frontend has no Vitest coverage configuration or coverage package. CI has no coverage command or threshold.

### Backend measured baseline

Command:

```bat
set PYTHONPATH=C:\Users\DELL\Documents\GitHub\medicheck\backend&& python -m pytest -q --cov=app --cov-report=term-missing "C:\Users\DELL\Documents\GitHub\medicheck\backend\tests"
```

Result:

- 145 collected/executed.
- 130 passed, 5 failed, 10 errors, 3 warnings.
- Total: 10,907 statements, 5,155 missed, **53% coverage**.
- Requested backend target: 95%; current gap: **42 percentage points**.

Notable low/zero areas from the coverage report:

- Core events 0%, rate limiting 0%, Firebase provider 0%, seed 0%.
- Multiple domain repository interfaces and SQL implementations 0%.
- SQL assessment repository 0%; recommendation repository 0%.
- Rule engine service 10%.
- CMS audit 17%, questionnaire service 17%, knowledge graph SQL repository 17%.
- Publishing service 19%.
- Clinical decision, profile, report, and knowledge-graph editor services around 21%.
- Most API endpoint modules are approximately 26–63% because imports/router construction count as covered while behavior is largely untested.
- Questionnaire engine 28%; branching/scoring are the strongest tested areas.

### Frontend coverage baseline

Command:

```bat
npm --prefix "C:\Users\DELL\Documents\GitHub\medicheck\frontend" run test -- --run
```

Result: Vitest exits code 1 with `No test files found`. No coverage command can currently run because no tests/configured coverage provider exist. Operational baseline is **0 first-party tests and no measurable coverage**, a full gap to the requested 90%.

## 6. Baseline commands and results

### Discovery

```bat
set PYTHONPATH=C:\Users\DELL\Documents\GitHub\medicheck\backend&& python -m pytest --collect-only -q "C:\Users\DELL\Documents\GitHub\medicheck\backend\tests"
```

Result: **145 tests collected in 0.58s**, with three Pydantic migration warnings.

### Full backend suite

```bat
set PYTHONPATH=C:\Users\DELL\Documents\GitHub\medicheck\backend&& python -m pytest -q "C:\Users\DELL\Documents\GitHub\medicheck\backend\tests"
```

Result: **130 passed, 5 failed, 10 errors, 3 warnings in 83.12s**.

### Stable backend unit subset

```bat
set PYTHONPATH=C:\Users\DELL\Documents\GitHub\medicheck\backend&& python -m pytest -q "C:\Users\DELL\Documents\GitHub\medicheck\backend\tests\unit"
```

Result: **130 passed, 3 warnings in 0.28s**. This fast pure-unit lane is valuable and should be preserved.

### Frontend test

```bat
npm --prefix "C:\Users\DELL\Documents\GitHub\medicheck\frontend" run test -- --run
```

Result: exit 1, no test files.

### Frontend typecheck

```bat
npm --prefix "C:\Users\DELL\Documents\GitHub\medicheck\frontend" run typecheck
```

Result: failed. Errors are concentrated in outdated React Query call signatures, unsafe generic CMS API casts, resulting `{}`/`unknown` data types in dashboard/timeline/profile pages, mutation variable typing, and a React Hook Form/Zod resolver type mismatch.

### Frontend lint

```bat
npm --prefix "C:\Users\DELL\Documents\GitHub\medicheck\frontend" run lint
```

Result: failed with **95 errors**. Main classes: explicit `any`, unused imports/variables, two React prop-types findings on TypeScript components, and one unescaped entity.

### Frontend build

```bat
npm --prefix "C:\Users\DELL\Documents\GitHub\medicheck\frontend" run build
```

Result: passed in 11.43s. Output includes a **777.09 kB** minified JS chunk (201.62 kB gzip) and Vite's >500 kB warning. Build does not run `tsc`, so it succeeds despite type errors.

### Playwright discovery

```bat
if exist "C:\Users\DELL\Documents\GitHub\medicheck\frontend\playwright.config.ts" (type "C:\Users\DELL\Documents\GitHub\medicheck\frontend\playwright.config.ts") else (echo NO_PLAYWRIGHT_CONFIG)
if exist "C:\Users\DELL\Documents\GitHub\medicheck\frontend\node_modules\.bin\playwright.cmd" ("C:\Users\DELL\Documents\GitHub\medicheck\frontend\node_modules\.bin\playwright.cmd" test --list) else (echo PLAYWRIGHT_NOT_INSTALLED)
```

Result: `NO_PLAYWRIGHT_CONFIG`; `PLAYWRIGHT_NOT_INSTALLED`.

## 7. Failing and potentially flaky tests

### Deterministic errors

All tests in `backend/tests/integration/test_api/test_auth.py` error during `client` fixture setup because line 84 calls a function without its required URL argument. Affected tests: health check; register success/duplicate/missing fields/empty name; login new/existing; authenticated/unauthenticated `me`; delete account.

### Deterministic failures

- `test_admin_create_indicator_and_evidence`: missing `clinical_indicators` table.
- `test_cdse_process_simple_flow`: missing `clinical_indicators` table.
- `test_links_and_graph_build`: missing `possible_conditions` table.
- `test_profile_repository_create_and_personal_upsert`: missing `health_profiles` table.
- `test_report_generation_flow`: missing `clinical_indicators` table.

All share the `:memory:` + `NullPool` connection-isolation defect.

### Flakiness assessment

No test changed outcome during representative runs; current failures are reproducible. However, likely future flake sources are:

- Global mutation of `config_module.settings`, `app_main.settings`, and database engine globals without restoring original values.
- Shared file DB at session scope combined with create/drop per function and a custom event loop fixture.
- Tests using `datetime.now()` rather than a controlled clock.
- Persistent pytest `lastfailed` includes an older `test_min_length_validation` node not present in current collection, indicating suite drift/stale cache.
- Auth tests rely on token strings without an explicit deterministic Firebase fake.
- No isolation conventions for concurrent or xdist execution.

## 8. Requested backend category map

Status terms: **covered** means meaningful current tests; **partial** means narrow/smoke coverage; **missing** means no identifiable category coverage.

- **Unit Tests — partial/strong core:** 130 passing tests cover user entity, email/phone, branching/dependency operators, scoring, and validation. Most services, DTO edge cases, core utilities, entities, and body-system modules remain uncovered.
- **Repository Tests — partial/broken:** profile and knowledge-graph repository flows exist but fail from SQLite pooling. Many SQL repositories are 0–32% and have no CRUD/filter/pagination/transaction tests.
- **Service Tests — partial/broken:** admin, clinical decision, knowledge graph, and report smoke flows exist but fail; CMS services, auth, profile, questionnaire, dashboard, publishing, rule engine, and editor services lack comprehensive behavior tests.
- **API Tests — partial/broken:** only auth/health tests exist and all error in fixture setup. Most public and CMS routes have no request/response/error-contract tests.
- **Permission Tests — missing:** no endpoint permission matrix.
- **RBAC Tests — missing behavior coverage:** `rbac.py` is imported/high statement coverage (83%) but there is no explicit role/permission/denial test suite; role entity is 0%.
- **Publishing Workflow Tests — missing:** service/API/entity transitions, approvals, rollback/versioning, invalid transitions, and audit side effects untested.
- **Knowledge Graph Tests — partial/broken:** one graph/link smoke test fails; editor service, traversal, cycle handling, validation, delete constraints, and API behavior missing.
- **Rule Engine Tests — missing:** service is 10%; no operator/action execution, priority, conflict, invalid expression, or deterministic evaluation suite.
- **Recommendation Engine Tests — missing:** SQL recommendation repository is 0%; no recommendation ranking/filtering/evidence tests identified.
- **Questionnaire Engine Tests — partial:** branching, scoring, and validation are strong; orchestration/session persistence, autosave/resume, ordering, completion, versioning, and API flows are missing.
- **Assessment Engine Tests — missing:** assessment endpoint is only import-covered; assessment repositories/workers and end-to-end scoring persistence lack tests.
- **Timeline Tests — missing:** no backend timeline module behavior tests identified (directory exists but no implemented/tested files surfaced).
- **Dashboard Tests — missing:** no dashboard service/API aggregation, empty-state, authorization, or query-efficiency tests.
- **Performance Tests — missing:** no pytest-benchmark/load budgets/query-count assertions.
- **Concurrency Tests — missing:** no simultaneous submissions, optimistic locking, duplicate publish, idempotency, or transaction isolation tests.
- **Migration Tests — missing:** no Alembic clean upgrade, schema parity, downgrade, or data migration tests.

## 9. Requested frontend category map

There are zero first-party test files, so every requested category is currently missing:

- **Component Tests — missing:** shared UI, questionnaire inputs, CMS pages, forms, dashboards.
- **Hook Tests — missing:** auth, profile, questionnaire, timeline, CMS, dashboard hooks.
- **React Query Tests — missing:** query keys, caching, invalidation, retry/error/loading behavior; current production hooks also misuse v5 signatures.
- **Accessibility Tests — missing:** no axe/jest-axe, semantic keyboard/focus tests, or Playwright accessibility checks.
- **Integration Tests — missing:** no provider/router/API-backed user-flow tests.
- **Playwright E2E Tests — missing:** dependency, config, browsers, fixtures, and specs absent.
- **Responsive Tests — missing:** no viewport projects or layout assertions/screenshots.
- **Dark Mode Tests — missing:** ThemeProvider exists, but no persistence/class/contrast/visual checks.
- **Form Validation Tests — missing:** React Hook Form/Zod profile and questionnaire input validation untested.

## 10. CI and package-manager audit

Package manager is npm with `frontend/package-lock.json`; use `npm ci` in CI and `npm run ...` scripts. Backend uses pip requirements plus PEP 621 metadata; no lockfile or tox/nox environment matrix exists.

Current `.github/workflows/ci.yml`:

- Frontend: Node 20, `npm ci`, typecheck, build. It omits lint, Vitest, coverage, Playwright, artifact upload, and dependency caching.
- Backend: Python 3.11 (incompatible with declared >=3.12), installs `requirements.txt`, then echoes `No linter configured` and `No tests configured yet`. It omits dev requirements, pytest, coverage, Ruff, mypy, Alembic, PostgreSQL/Redis services, and artifacts.
- There are no coverage gates at 95%/90%.

Existing commands:

```text
Frontend: npm run dev | build | preview | lint | typecheck | test
Backend: python -m pytest; python -m pytest --cov=app; ruff; mypy; alembic
```

## 11. Reusable infrastructure recommendations

1. **Keep pytest/pytest-asyncio/pytest-cov.** Repair `client` to consume `test_settings`, and preserve the fast `tests/unit` lane.
2. **Standardize DB fixtures.** Replace per-file engine setup with shared `engine`, `connection`, `db_session`, and schema fixtures. Use transaction/savepoint rollback for speed. Keep SQLite for pure repository smoke tests where portable, but add PostgreSQL integration/migration lanes for production fidelity.
3. **Import model metadata explicitly.** Ensure all model modules are registered before `create_all`; centralize this rather than relying on incidental imports.
4. **Add deterministic fakes, not broad mocks.** Firebase token verifier/user provider, Redis/cache, Celery task dispatch, and clock/UUID helpers should have reusable fakes. Mock network boundaries, not core domain behavior.
5. **Add builders/factories incrementally.** Lightweight typed factories for users, roles, questionnaires, questions/options, assessment sessions, rules, graph nodes/edges, recommendations, and publishing workflows will remove repetitive setup without rewriting tests.
6. **Use current FastAPI dependency overrides.** Extend them for authenticated users/roles and external providers; create permission-matrix helpers.
7. **Keep Vitest integrated with Vite.** Add a test section with jsdom, setup file, globals policy, alias reuse, coverage include/exclude and 90% thresholds.
8. **Add a frontend `renderWithProviders`.** Wrap Router, QueryClient (retry disabled, fresh per test), ThemeProvider, and AuthProvider. Add MSW handlers matching existing API services.
9. **Add Playwright beside Vitest.** Use webServer with Vite, isolated auth fixtures, API seeding, Chromium/Firefox/WebKit plus mobile projects, trace/screenshot/video on retry only.
10. **Separate test tiers.** Unit on every change; SQLite/service/API integration on PR; PostgreSQL migrations/concurrency and Playwright on PR/nightly according to duration.

## 12. Likely production defects exposed by the audit

These are candidates requiring confirmation with focused tests, not assertions that all are already user-visible:

- React Query v5 is called with v4-style positional arguments throughout profile/dashboard/timeline/auth hooks. TypeScript rejects these calls, and runtime query behavior may be incorrect.
- Generic CMS query hooks use unsafe casts across incompatible service shapes, risking wrong method/response assumptions.
- Derived hook data is typed as `{}`/`unknown`, causing pages to access arrays/properties unsafely.
- Profile mutations/invalidation use obsolete React Query signatures; cache invalidation and payload delivery may fail.
- ProfileWizard resolver types do not align with `PersonalInfo`; form coercion/submission may be incorrect.
- Backend Pydantic configuration uses deprecated `GenericModel`, class `Config`, and `orm_mode`; these are migration hazards for Pydantic 3.
- The build pipeline does not couple TypeScript checking to Vite build, allowing a deployable bundle despite compile-time defects.
- The oversized frontend bundle suggests missing route-level code splitting and avoidable initial-load cost.
- Production PostgreSQL behavior and Alembic history are untested; `create_all` success cannot establish deployability.
- Global settings/engine singleton mutation can leak across application/test contexts and complicate parallel execution.

## 13. Actionable implementation plan

### Phase 0 — Freeze and reproduce

- Preserve this baseline and add no feature changes until failures are classified.
- Pin supported local/CI Python to 3.12 (or explicitly broaden/test the matrix) and Node 20.
- Make clean-install commands reproducible: backend dev dependencies and frontend `npm ci`.

### Phase 1 — Repair existing infrastructure and failures

- Fix `client` to use injected `test_settings.database_url`; restore globals after each test.
- Replace `:memory:` + `NullPool` in five tests with the shared DB fixture or a single shared connection/StaticPool.
- Add an explicit Firebase verifier fake and verify existing auth expectations against actual endpoint dependencies.
- Re-run all 145 tests repeatedly and with randomized order before labeling stability.
- Fix Pydantic warnings where behavior is clear.

Exit criterion: current 145 backend tests pass repeatedly with no errors/warnings attributable to obsolete config.

### Phase 2 — Establish enforceable coverage and CI

- Configure backend branch coverage, source paths, sensible omissions, XML/terminal reports, then ratchet to 95%.
- Configure Vitest jsdom/setup/coverage at 90% and add `test:run`/`test:coverage` scripts while retaining `npm run test` for developer watch mode if desired.
- Make CI execute Ruff, mypy, pytest+coverage, npm lint/typecheck/test+coverage/build, and Playwright.
- Add PostgreSQL/Redis service containers and Alembic upgrade on CI.

### Phase 3 — Backend expansion by risk

- Unit: uncovered services/utilities/entities and failure branches.
- Repositories: CRUD, filtering, pagination, soft-delete, uniqueness, transaction rollback for every SQL repository.
- Services/APIs: success, validation, not-found, conflict, provider failure, and serialization contracts.
- Authorization: table-driven permission/RBAC matrices for every protected endpoint and tenant/object ownership.
- Domain workflows: publishing transition tables; graph integrity/traversal; rule evaluation; recommendation ranking; questionnaire/assessment lifecycle; timeline/dashboard aggregation.
- Operational: Celery task idempotency, Redis degradation, rate limits, query counts, latency budgets, concurrent writes, Alembic clean upgrade/schema parity.

### Phase 4 — Frontend foundation and expansion

- First resolve React Query v5, generic typing, and form resolver production defects so tests exercise supported contracts.
- Add Vitest setup, Testing Library, user-event, jest-dom, MSW, axe, provider render helper, typed fixtures.
- Test shared UI and every questionnaire input; then hooks and React Query states; then page integrations and form validation.
- Add accessibility assertions for roles/names/errors/focus/keyboard and axe checks for critical pages.
- Cover ThemeProvider/dark mode and responsive behavior at component and E2E levels.

### Phase 5 — Playwright and stability

- Implement critical journeys: auth, profile wizard, questionnaire autosave/resume/complete, assessment/report/recommendations, CMS RBAC/publishing/rules/graph.
- Add desktop/mobile projects, dark-mode project, accessibility smoke, deterministic API seeding, and cleanup.
- Remove fixed sleeps; use web-first assertions. Run repeated/shuffled tests and quarantine nothing without an owner and expiry.

### Phase 6 — Final gates

Run from a clean checkout/install and require all to pass:

```bat
set PYTHONPATH=C:\Users\DELL\Documents\GitHub\medicheck\backend&& python -m pytest "C:\Users\DELL\Documents\GitHub\medicheck\backend\tests" --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=95
npm --prefix "C:\Users\DELL\Documents\GitHub\medicheck\frontend" run test -- --run
npm --prefix "C:\Users\DELL\Documents\GitHub\medicheck\frontend" run lint
npm --prefix "C:\Users\DELL\Documents\GitHub\medicheck\frontend" run typecheck
npm --prefix "C:\Users\DELL\Documents\GitHub\medicheck\frontend" run build
npx --prefix "C:\Users\DELL\Documents\GitHub\medicheck\frontend" playwright test
```

Add the frontend coverage script/config in Phase 2 and enforce 90% statements/branches/functions/lines. Require repeat runs of concurrency- and browser-sensitive suites before completion.

## 14. Audit conclusion

The project already has a high-value, very fast pure backend unit-test core and appropriate async API/database libraries. It does **not** yet have a production-complete testing suite. The fastest safe path is to repair and reuse the existing fixtures, add PostgreSQL fidelity where needed, then expand category coverage around the current architecture. Frontend test infrastructure must be completed around the already-installed Vitest rather than replaced. Baseline gates are currently red: backend 53% with 15 broken tests, frontend zero tests, typecheck failure, 95 lint errors, no Playwright, and placeholder backend CI.
