# Medicheck ‚Äî Agent Memory

Persistent context for the Medicheck healthcare SaaS audit. Update after each work pass.

## Project layout
- Backend: `backend/` (FastAPI + SQLAlchemy 2.0 async + Pydantic v2). Run tests with
  `ALLOW_MOCK_AUTH=true` (P0/P3 tests use `Bearer mock-firebase-id-token`).
  `DATABASE_URL=sqlite+aiosqlite:///./test.db`, `ENVIRONMENT=development`.
  No venv committed; install with `pip install -e .` + `pytest pytest-asyncio pytest-cov aiosqlite httpx`.
- Frontend: `frontend/` (Vite + React + TS + Tailwind v4 + TanStack Query).
  Scripts: `npm run typecheck|build|test|lint`. Tests use vitest + jsdom.

## Test commands (verified working)
- Backend: `cd backend && ALLOW_MOCK_AUTH=true python -m pytest tests/ -q -W error::DeprecationWarning`
- Frontend: `cd frontend && CI=true npx vitest run` (18 tests) + `npm run typecheck` + `npm run build`

## Layout system (key P3-6/P3-4 findings ‚Äî read before touching layouts)
THREE sidebar layouts existed; after P3-4 only two remain and both are routed:
- `layouts/DashboardLayout.tsx` ‚Äî ROUTED. Used by router's `PatientLayoutWithContent`
  wrapper for nearly all patient pages AND by `features/dashboard/pages/Dashboard.tsx`
  (/app) directly. Sidebar is a flex sibling (sticky, shrink-0, w-64‚Üîw-[76px]), NOT an
  overlay ‚Äî so it never truly "blocks" content. Collapse state is shared + persisted
  across navigation via `features/dashboard/components/layout/sidebarCollapseStore.ts`
  (useSyncExternalStore + localStorage), because each patient route remounts
  DashboardLayout (so local useState would reset on every navigation).
- `layouts/DoctorLayout.tsx` ‚Äî ROUTED for /cms/* (layout route with <Outlet/>). Does NOT
  remount on /cms sub-navigation, so its local useState collapse persists. Independent
  collapse preference from patient sidebar (intentional ‚Äî different roles). KEPT (not
  symmetric with patient) because CMS routing relies on a persistent <Outlet/>.
- `layouts/AppLayout.tsx` ‚Äî NOT dead: imported by ~18 page components, but is now a
  passthrough (`<>{children}</>`, no chrome) since P3-6. Keeping it is low-risk;
  removing it would be a large mechanical edit of 18 importers for no functional gain.
  The `AppLayout passthrough` test pins its no-chrome behavior.
- `layouts/PatientLayout.tsx` ‚Äî REMOVED in P3-4. Was NOT routed (only its own test
  imported it); the router uses `PatientLayoutWithContent` ‚Üí `DashboardLayout`, NOT
  PatientLayout. Had a duplicate dead SidebarContent + inline nav. Removed file + its
  2 tests; fixed the stale `navConfig.ts` comment (patient nav lives in navConfig.ts,
  consumed by Sidebar/DashboardLayout).
- `shared/ui/TopNav.tsx` is dead code (no importers) after AppLayout became a passthrough.

## Pydantic v2 (P3-1)
- `HealthProfileDTO` has `model_config = ConfigDict(from_attributes=True)` + a
  `validation_alias=AliasChoices("profile_metadata", "metadata")` because the ORM column
  is `profile_metadata` (the model attr `metadata` is SQLAlchemy's MetaData object).
- `PersonalInfoDTO` ALSO has `from_attributes=True` (added P3-2): without it,
  `HealthProfileDTO.personal_info` could never be populated from the ORM (the nested
  PersonalInfoModel wasn't coercible). This was latent — existing tests only had
  personal_info=None.
- Use `HealthProfileDTO.model_validate(orm_obj)` (NOT `from_orm`) and `dto.model_dump()`
  (NOT `.dict()`). Backend tests run with `-W error::DeprecationWarning` to enforce.

## emergency_contact (P3-2 — RESOLVED)
- `PersonalInfoModel.emergency_contact` is now `Mapped[dict | None] = mapped_column(JSON,
  nullable=True)` (was `Text` — writing a dict raised on SQLite / stored a repr elsewhere).
- Migration `20260808_emergency_contact_json` (TEXT→JSON alter, safe: no legacy non-NULL
  data existed). Idempotent (skips if already JSON / table absent).
- Two enabling bug fixes in the same read path: `snapshot_profile` referenced
  `profile.extra_metadata` (typo → `profile.profile_metadata`); `PersonalInfoDTO` lacked
  `from_attributes=True`. Without these, emergency_contact (and all personal_info) could
  never serialize via /profiles/me.
- Regression tests: `backend/tests/test_emergency_contact_p3.py` (5 tests: populated dict
  round-trip, NULL, snapshot dict-not-repr, /profiles/me populated object, /profiles/me null).

## Known pre-existing issues (not yet addressed — deferred)
- `UserResponse` DTO role literal only allows `patient|doctor|researcher|administrator`
  but `Role` enum has more — schema mismatch.
- Mock auth uses fixed `mock@example.com` → email collision on second user creation in tests.
- Frontend wizard sends `emergency_contact` as a STRING vs backend dict (profileService.ts/
  profileApi.ts/defaults.ts/fieldSpecs.ts) — would 422 on submit. Backend now stores dict
  correctly; frontend type alignment is a separate frontend-schema item (not touched in P3-2).

## Workflow rules
- Do NOT commit/stage until the whole P0‚ÜíP3 series is done + final audit clean.
- Preserve RBAC; don't expose user data during loading. Preserve UI/functionality.
- Backend deps NOT preinstalled in sandbox ‚Äî must `pip install` before running tests.

## Assessments pages (two distinct routes ‚Äî keep straight)
- `/assessments` ‚Üí `features/questionnaire/pages/AssessmentSelectionPage.tsx`. The REAL
  working flow: uses `useNavigate` + `useStartSession` (TanStack mutation) to call the
  backend `startSession(templateId)` and navigate to `/questionnaires/:sessionId`.
  Backed by `features/questionnaire/data/assessments.ts` catalog + `useTemplates()`.
- `/assessments/dashboard` ‚Üí `features/dashboard/pages/Assessments.tsx`. A mock-data
  dashboard view (uses `features/dashboard/assessments/mockData.ts`, NOT backend). Was
  shipped with stub handlers that only `console.log` (handlePrimary/handleEdit/
  handleDiscard + AssessmentHistoryTable onView/onRetake/onDownload/onCompare), so every
  "Start Assessment"/"Resume"/"Review Report" button did nothing. Fixed by wiring
  `useNavigate`: completed ‚Üí `/assessments/:slug` (ReportViewer), requires_profile ‚Üí
  `/profile`, locked ‚Üí no-op, everything else (not_started/recommended/in_progress/
  expired/needs_review) ‚Üí `/assessments` (the real selection page). When adding new
  buttons on this page, route via navigate ‚Äî do NOT reintroduce console.log stubs.
- Routes that matter for navigation: `/assessments/:id`=ReportViewer,
  `/assessments/:id/results`=ResultsDashboard, `/questionnaires/:id`=session,
  `/timeline/compare`=ComparePage, `/profile`=HealthProfilePage.

## Doctor CMS recovery (P0-P3 series — read before touching the CMS)
The Doctor CMS appeared to be a "shell" after modularization. Forensic + repair work
found it was DISCONNECTED + API-BROKEN + one critical RBAC serialization bug, not deleted.
Full findings: `CMS_CONTENT_FORENSIC_REPORT.md`. Key facts to preserve:

### Frontend CMS architecture
- `frontend/src/features/cms/` is the (only) live CMS module. Two API layers:
  - `cmsApi.ts` `contentApi` — generic CRUD. `DEDICATED_ENDPOINTS` map routes 4 entity
    types to dedicated routers (`question`->`/cms/questions`, `question_group`->
    `/cms/question-groups`, `body_system`->`/cms/body-systems`, `template`->`/cms/templates`)
    which return BARE ARRAYS, wrapped client-side into `{items,total,skip,limit}`. All
    other entity types hit the generic `/cms/content/{entity}` (paginated). DO NOT route
    `template` through the generic content endpoint — it 500s on the `metadata` column
    collision (see below); the dedicated `/cms/templates` endpoint is correct.
  - `cmsApi.ts` `builder`/`dashboard`/`admin`/`roles`/`users` — dedicated endpoints.
- All CMS API paths are prefixed via the axios `api` client baseURL (`/api/v1`); endpoint
  strings must NOT repeat `/api/v1` (was a P0 bug: double `/api/v1/api/v1/cms/...`).
- `useCmsQueries.ts` is the canonical hook layer. `useContentList(entityType)` indexes the
  paginated response via `.items` (NOT the bare array). Dedicated-list hooks
  (`useQuestions` etc.) consume the bare array directly.
- Router (`routes/router.tsx`): `/cms/*` is a layout route using `DoctorLayout` + `<Outlet/>`.
  Each content-list route (`/cms/diseases`, `/cms/symptoms`, ...) must point at its matching
  `features/cms/pages/*ListPage.tsx`. A P1 bug had several list routes pointing at a wrong
  generic page -> wrong entity fetched -> empty grid.

### Backend CMS architecture
- Generic content router: `app/api/v1/cms/content.py` — `ENTITY_ALIASES`,
  `_READ_PERM_MAP`, `_WRITE_PERM_MAP`, dispatches to `content_service.ENTITY_REGISTRY`
  (entity<->model pairs) + `SqlGenericCmsRepository`. Aliases map abbreviated frontend names
  (`disease`, `symptom`, `template`...) to canonical model keys. Permission deps via
  `Permission` enum (`CMS_READ_*` / `CMS_WRITE_*`).
- Dedicated routers: `cms/questions.py` (questions/groups/body-systems/templates — seeded
  data, bare arrays), `cms/rules.py` (rule-set CRUD + evaluate/simulate/validate), and
  `cms/dashboard.py` (overview/recent-activity/workflow-summary).
- Admin router: `app/api/v1/endpoints/admin.py` — body-systems/indicators/evidence/
  recommendations CRUD, `GET /admin/users` (paginated `{items,total,skip,limit}`),
  `GET/PUT /admin/users/{id}/roles` (body field is `{"roles": [...]}` — NOT `role_codes`),
  `POST /admin/users/{id}/toggle-active`, `GET /admin/roles` (bare array).
- All CMS GET endpoints depend on `get_cms_user`; admin write depends on
  `get_current_admin`. `has_role` uses `_ROLE_HIERARCHY` (>=), so `get_cms_user`
  (`has_role(roles, READ_ONLY_REVIEWER)`=level 5) admits ANY CMS role (level>=5), denying
  only patients/roleless users. This is CORRECT — do not "fix" it by auto-granting roles.

### Critical bug fixed: /auth/me 500 for CMS roles (P3, ROOT CAUSE of shell look)
- `UserResponse.roles` (and `AuthenticatedUserResponse.roles`) was
  `list[Literal["patient","doctor","researcher","administrator"]]`. The Role enum
  (`app/core/security/rbac.py`) is patient, doctor, super_admin, medical_director,
  specialist_doctor, general_physician, research_reviewer, content_editor,
  read_only_reviewer. So ANY user with a real CMS role made `UserResponse.from_entity`
  raise Pydantic ValidationError -> /auth/me returned 500 -> the frontend `meQuery` failed
  -> `AuthContext.role` fell back to localStorage/`'patient'` -> `checkCanAccessCMS=false`
  -> CMS nav hidden / pages rendered with no resolved role -> looked like an empty shell.
- Fix: `roles: list[str] = []` in both DTOs (`auth_dtos.py`). Serialization-only; RBAC
  still uses DB roles via `get_cms_user`. Regression: `tests/test_user_response_roles.py`
  (all 9 roles serialize; /auth/me returns 200 with `["medical_director"]`).

### `metadata` column collision (NOT fixed — known landmine, avoided)
- `QuestionnaireTemplateModel` stores its JSON in a DB column named `metadata` but exposes
  it via Python attr `extra_metadata` (because `metadata` is reserved by SQLAlchemy's
  `MetaData`). `BaseModel.to_dict()` does `getattr(self, "metadata")` -> returns the
  SQLAlchemy `MetaData` object, NOT the column value. The generic content router would
  500 if `questionnaire_template` were registered there. This is why templates MUST use
  the dedicated `/cms/templates` endpoint (which maps via `extra_metadata` correctly),
  NOT the generic `/cms/content/template` path. Do NOT register `questionnaire_template`
  in `ENTITY_REGISTRY` without first fixing `to_dict()` for that model.
- `SQLQuestionnaireRepository._to_entity()` correctly maps `extra_metadata`->entity field;
  that is the working pattern.

### CMS access in dev (mock auth)
- Mock auth (`ALLOW_MOCK_AUTH=true`, token `mock-firebase-id-token`) auto-creates a user
  with NO roles (`User.create` takes no roles). So a fresh dev user has `roles=set()` ->
  `get_cms_user` 403s on every CMS endpoint AND /auth/me returns `roles:[]` -> frontend
  sees `patient`. CMS access requires an admin to assign a CMS role via
  `PUT /admin/users/{id}/roles` (now implemented). This is correct security posture; do
  NOT auto-grant CMS roles on signup.

### Test commands (verified)
- Backend: `cd backend && ALLOW_MOCK_AUTH=true DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=development python -m pytest tests/ -q -W error::DeprecationWarning` -> 189 pass.
- Frontend: `cd frontend && npm run typecheck && CI=true npx vitest run` -> 23 pass, typecheck clean.
