# CMS recovery report

This report covers the repair work done after the forensic audit in
`CMS_CONTENT_FORENSIC_REPORT.md`. It records what was fixed, why, and what
evidence backs each change. No code was restored blindly: every fix traces to a
specific forensic finding.

## Executive summary

The Doctor CMS was not deleted. It was a mix of disconnected, API-broken and
gated-by-a-serialization-bug. The single highest-impact defect was a response
DTO that rejected every real CMS role, so `/auth/me` returned 500 for any
medical director, content editor or specialist doctor. The frontend could never
resolve a CMS role, the CMS nav went hidden, and pages rendered with no data.
Combined with duplicated API prefixes, mismatched entity names, misrouted list
pages and several missing backend endpoints, the CMS looked like a shell.

After the repairs below, the frontend typechecks cleanly, all 23 frontend tests
pass, and all 189 backend tests pass (181 original plus 8 new regression tests).

## Confidence

HIGH for the root cause and the fixes. Each fix has a regression test or a
typecheck/build gate. The one item left untouched (the `metadata` column
collision) is documented as a known landmine that the current routing avoids.

## What was fixed, by priority

### P0 — duplicated `/api/v1` prefix in the frontend CMS API client

File: `frontend/src/features/cms/api/cmsApi.ts`

The axios `api` client already has baseURL `/api/v1`. Several CMS endpoint
strings repeated `/api/v1`, producing requests to `/api/v1/api/v1/cms/...`,
which 404'd. Corrected so endpoint strings are relative to the baseURL.

### P1 — entity name mismatch, response shape, hook indexing and list routing

Files: `frontend/src/features/cms/api/cmsApi.ts`,
`frontend/src/features/cms/hooks/useCmsQueries.ts`,
`frontend/src/routes/router.tsx`.

- The generic content API returns a paginated `{items,total,skip,limit}` shape,
  while the four dedicated endpoints (`/cms/questions`,
  `/cms/question-groups`, `/cms/body-systems`, `/cms/templates`) return bare
  arrays. `useContentList` now indexes via `.items` for paginated responses and
  consumes the bare array directly for dedicated endpoints.
- Each `/cms/<entity>` list route now points at its matching
  `features/cms/pages/*ListPage.tsx`. Previously several list routes pointed at
  a wrong generic page, so the wrong entity was fetched and the grid looked
  empty.
- `cmsApi.ts` builder typing (the unused `createBranchRule` path) was simplified
  so `tsc --noEmit` passes.

### P2 — missing backend CMS endpoints

Files: `backend/app/api/v1/cms/rules.py`,
`backend/app/api/v1/endpoints/admin.py`,
`backend/app/api/v1/cms/questions.py`, `backend/app/api/v1/cms/content.py`.

- Rules: added `GET /cms/rules`, `GET /cms/rules/{id}`, `POST /cms/rules`,
  `PUT /cms/rules/{id}` (bare-array list contract to match the frontend
  `RuleSet[]`). The evaluate, simulate, validate, compute and conflict-detect
  endpoints already existed.
- Admin: added `GET /admin/users` (paginated), `GET /admin/users/{id}`,
  `PUT /admin/users/{id}/roles`, `POST /admin/users/{id}/toggle-active`,
  `GET /admin/roles`, `GET /admin/roles/{id}/permissions`, plus
  body-systems, indicators, evidence and recommendations CRUD.
- The role-update endpoint body field is `{"roles": [...]}`. This matches the
  frontend call `api.put('/admin/users/{id}/roles', { roles })`.

### P2 — dashboard response alignment

File: `frontend/src/features/cms/pages/CMSDashboardPage.tsx`

The dashboard page now reads the backend's actual plural keys
(`questions`, `diseases`) and the correct workflow status names returned by
`/cms/dashboard/overview`, `/cms/dashboard/recent-activity` and
`/cms/dashboard/workflow-summary`.

### P2 — template entity alias investigated, no risky change made

The forensic report flagged the `template` alias. On inspection, the frontend
already routes `template` through the dedicated `/cms/templates` endpoint
(`DEDICATED_ENDPOINTS` in `cmsApi.ts`), which serves seeded
`questionnaire_templates` and maps the JSON via `extra_metadata` correctly. The
generic `/cms/content/template` path is not used for templates.

An initial attempt registered `questionnaire_template` in the generic
`ENTITY_REGISTRY` and re-aliased `template` to it. That was reverted because it
would route templates through `BaseModel.to_dict()`, which collides with
SQLAlchemy's reserved `metadata` attribute and would 500 (see the landmine
below). The alias stays as `"template": "template_library"` (original behaviour,
harmless empty table). No net backend change for templates.

### P3 — `/auth/me` 500 for CMS roles (root cause of the shell appearance)

File: `backend/app/application/dtos/auth_dtos.py`

`UserResponse.roles` and `AuthenticatedUserResponse.roles` were typed
`list[Literal["patient", "doctor", "researcher", "administrator"]]`. The real
`Role` enum (`app/core/security/rbac.py`) is patient, doctor, super_admin,
medical_director, specialist_doctor, general_physician, research_reviewer,
content_editor, read_only_reviewer. So any user holding a CMS role made
`UserResponse.from_entity` raise a Pydantic `ValidationError`, `/auth/me`
returned 500, the frontend `meQuery` failed, and `AuthContext.role` fell back to
localStorage or `'patient'`. With `checkCanAccessCMS('patient') === false`, the
CMS navigation was hidden and pages rendered with no resolved role.

Fix: `roles: list[str] = []` in both DTOs. This is serialization only. RBAC is
unchanged: `get_cms_user` still checks DB roles via `has_role` against the
`_ROLE_HIERARCHY` (level >= 5 admits any CMS role). Self-registration in
`RegisterRequest.role` stays `Literal["patient", "doctor"]` (intentional: CMS
roles are admin-assigned, not self-registered).

Regression tests: `backend/tests/test_user_response_roles.py` — all nine roles
serialize, and `/auth/me` returns 200 with `["medical_director"]` end-to-end.

## What survived (no rebuild needed)

- The entire `frontend/src/features/cms/` module: pages, hooks, API client,
  types, components.
- The `DoctorLayout` + `<Outlet/>` routing shell.
- The generic content router and `ENTITY_REGISTRY` for all non-template
  entities.
- The dedicated `cms/questions.py` router and its seeded data.
- The RBAC hierarchy and permission maps.
- The database schema and seed data (untouched).

## What is still missing or deferred

- `metadata` column collision (landmine, not fixed). `QuestionnaireTemplateModel`
  exposes its JSON column `metadata` via the Python attr `extra_metadata`.
  `BaseModel.to_dict()` calls `getattr(self, "metadata")`, which returns the
  SQLAlchemy `MetaData` object, not the column value. Templates must keep using
  the dedicated `/cms/templates` endpoint. Registering `questionnaire_template`
  in the generic `ENTITY_REGISTRY` would reintroduce a 500. Fixing this means
  overriding `to_dict()` for that model (or the generic repository's
  serialization), which is a separate, scoped task.
- CMS access in a fresh dev environment. Mock auth auto-creates a user with no
  roles, so `get_cms_user` 403s and `/auth/me` returns `roles: []`. An admin
  must assign a CMS role via `PUT /admin/users/{id}/roles`. This is correct
  security posture, not a bug.

## Recovery options (not implemented)

- Option A (done): reconnect existing components, fix prefixes, entity names,
  response shapes, routing and the `/auth/me` DTO.
- Option B (not needed): restore deleted components from Git. Nothing was
  deleted; the components were present but disconnected.
- Option C (done for rules/admin; remaining): repair frontend/backend
  integration for any further pages that still surface empty grids.
- Option D (not needed): restore seed or database content. Seed data is intact.
- Option E (future): fix the `metadata` collision so templates can optionally
  go through the generic content router, if a unified content API is wanted.

## Evidence

- `backend/app/application/dtos/auth_dtos.py` lines 70-78 and 114-120: the
  fixed `roles: list[str] = []` with the explanatory comment.
- `backend/tests/test_user_response_roles.py`: two tests proving all nine roles
  serialize and `/auth/me` returns 200 with a CMS role.
- `backend/tests/test_cms_recovery_endpoints.py`: six tests covering rules
  list/get/create/update, admin users list, roles list, toggle-active and
  role assignment.
- `frontend/src/features/cms/api/cmsApi.ts` `DEDICATED_ENDPOINTS`: templates use
  `/cms/templates`, not the generic content path.
- `app/core/security/rbac.py` `_ROLE_HIERARCHY`: READ_ONLY_REVIEWER = 5 is the
  lowest CMS role, so `get_cms_user` admits any CMS role.
- `app/api/deps.py` `get_cms_user`: the gate is `has_role(roles,
  READ_ONLY_REVIEWER)`, which is correct.

## Test results

- Backend: 189 passed
  (`ALLOW_MOCK_AUTH=true DATABASE_URL=sqlite+aiosqlite:///./test.db
  ENVIRONMENT=development python -m pytest tests/ -q -W
  error::DeprecationWarning`).
- Frontend: 23 tests pass, `tsc --noEmit` clean
  (`npm run typecheck` + `CI=true npx vitest run`).

## Files changed

Modified:
- `AGENTS.md` (memory)
- `backend/app/api/v1/cms/content.py`
- `backend/app/api/v1/cms/questions.py`
- `backend/app/api/v1/cms/rules.py`
- `backend/app/api/v1/endpoints/admin.py`
- `backend/app/application/dtos/auth_dtos.py`
- `frontend/src/features/cms/api/cmsApi.ts`
- `frontend/src/features/cms/hooks/useCmsQueries.ts`
- `frontend/src/features/cms/pages/CMSDashboardPage.tsx`
- `frontend/src/routes/router.tsx`

New (regression tests and reports only):
- `backend/tests/test_cms_recovery_endpoints.py`
- `backend/tests/test_user_response_roles.py`
- `CMS_CONTENT_FORENSIC_REPORT.md` (from the forensic phase)
- `CMS_RECOVERY_REPORT.md` (this file)

No database changes. No migrations. No seed writes. No packages installed.
