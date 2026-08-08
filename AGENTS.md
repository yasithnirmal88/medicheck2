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
