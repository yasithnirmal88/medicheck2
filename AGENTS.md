# Medicheck -- Agent Memory

Persistent context for the Medicheck healthcare SaaS audit. Update after each work pass.

## Project layout
- Backend: `backend/` (FastAPI + SQLAlchemy 2.0 async + Pydantic v2). Run tests with
  `ALLOW_MOCK_AUTH=true` (P0/P3 tests use `Bearer mock-firebase-id-token`).
  `DATABASE_URL=sqlite+aiosqlite:///./test.db`, `ENVIRONMENT=development`.
  No venv committed; install with `pip install -e .` + `pytest pytest-asyncio pytest-cov aiosqlite httpx`.
- Frontend: `frontend/` (Vite + React + TS + Tailwind v4 + TanStack Query).
  Scripts: `npm run typecheck|build|test|lint`. Tests use vitest + jsdom.

## Test commands (verified)
- Backend: `cd backend && ALLOW_MOCK_AUTH=true DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=development python -m pytest tests/ -q -W error::DeprecationWarning` -> 217 pass.
- Frontend: `cd frontend && npm run typecheck && CI=true npx vitest run` -> 33 pass, typecheck clean, build OK.

## AI Explanation layer (Phase 1 -- AI-Assisted Report Explanation)
An additive AI explanation layer on top of the deterministic CDSE reports. The
clinical engine, schemas, and existing flows are NOT modified. Full design:
`MEDICHECK_AI_PHASE1_REPORT.md`, baseline: `MEDICHECK_AI_BASELINE.md`.

## Evidence-grounded RAG (Phase 2 -- built ON TOP of Phase 1)
Evidence-grounded retrieval over MediCheck's approved evidence repository.
Deterministic CDSE/scoring/schemas/Phase-1 provider abstraction UNCHANGED.
Full design: `MEDICHECK_AI_PHASE2_RAG_REPORT.md`. Key facts to preserve:
- Actual evidence architecture (verified against source, NOT the baseline's
  conceptual `indicator_sources`/`MedicalEvidence`): the seeded, approved
  evidence is `EvidenceReferenceModel` (evidence_references: id, question_id,
  title, url, source, evidence_level, summary, + SoftDeleteMixin). It has NO
  status/is_active column -> eligibility = `deleted_at IS NULL` + active link.
  `MedicalEvidenceModel` (medical_evidence) has a draft/published lifecycle
  but is NOT seeded and NOT wired into the indicator->evidence link graph;
  `ClinicalEvidenceService` references nonexistent fields on EvidenceReferenceModel
  (dead/broken) -- NOT used for retrieval. Do not "fix" by pointing retrieval at
  MedicalEvidenceModel without first wiring link tables + fixing that service.
- Knowledge-graph edges (links.py): `IndicatorEvidenceLinkModel` (indicator<->
  evidence, `active`) is the PRIMARY grounding edge. NO direct condition<->evidence
  or recommendation<->evidence link tables -- they reach evidence TRANSITIVELY via
  their linked indicators (`IndicatorConditionLinkModel`,
  `IndicatorRecommendationLinkModel`, `ConditionRecommendationLinkModel`).
- `EvidenceRetrievalService` (app/application/services/evidence_retrieval_service.py):
  batched retrieval (in_() per id set, no N+1), 3 tiers (indicator-direct=0.9 >
  condition-transitive=0.7 > recommendation-transitive=0.6), dedup by evidence
  id (keep best), deterministic ranking (tier 60% + evidence_level 25% + recency
  <=5% via created_at + text-overlap 10%), per-entity cap (default 2) + global
  limit (default 5). Config via constructor overrides OR
  settings.ai_rag_{evidence_limit,per_entity_cap,excerpt_max_chars}. The LLM
  NEVER decides relevance.
- Citation anti-hallucination: `KeyFinding.evidence_ids` +
  `RecommendationExplanation.evidence_ids`; `AIExplanationResponse.bind_context`
  now takes `allowed_evidence_ids` (the retrieved set) and the validator REJECTS
  any cited evidence id not retrieved (-> UNAVAILABLE_FALLBACK). Structurally
  enforced, not just prompt. Phase-1 indicator/rec id validators still run.
- Prompt bumped to `PROMPT_VERSION="2.0"` (V1_SYSTEM_PROMPT preserved). v2.0
  grounds in supplied evidence, forbids inventing citations/evidence ids,
  requires stating insufficiency. Cache key (trace_id,prompt_version) auto-
  invalidates v1.0 entries.
- `AIExplanationService` now composes `EvidenceRetrievalService` + provider
  (abstraction intact). Response adds `retrieved_evidence` +
  `evidence_available` for traceability/transparency. Retrieval failure ->
  explain with no evidence + state none available (never breaks report).
- No DB migration; read-only over existing evidence/link tables. Reuses trace_id.
- Frontend: same `ReportExplanation.tsx` extended -- dedicated visually-distinct
  Evidence section (FileText icon, white card) + per-finding citation markers
  `[n]` linking only to retrieved ids (fabricated id -> no marker). No-evidence
  state shows "No supporting evidence was available...". No fake links.
- Tests: backend `tests/test_ai_rag_phase2.py` (15: retrieval 8 + AI validation
  4 + security 2 + integrity 1); frontend 3 new. Test seeding uses UNIQUE
  body-system/question/indicator keys per call (uuid suffix) to avoid UNIQUE
  collisions on the shared test DB; do NOT use fixed codes across tests.
  `EvidenceRetrievalService` ranking must be timezone-safe (SQLite stores naive
  datetimes -- normalise both sides to naive UTC; never use datetime.utcnow()
  -- it trips `-W error::DeprecationWarning`).

## Layout system (key P3-6/P3-4 findings -- read before touching layouts)
THREE sidebar layouts existed; after P3-4 only two remain and both are routed:
- `layouts/DashboardLayout.tsx` -- ROUTED. Used by router's `PatientLayoutWithContent`
  wrapper for nearly all patient pages AND by `features/dashboard/pages/Dashboard.tsx`
  (/app) directly. Sidebar is a flex sibling (sticky, shrink-0, w-64--Üîw-[76px]), NOT an
  overlay -- so it never truly "blocks" content. Collapse state is shared + persisted
  across navigation via `features/dashboard/components/layout/sidebarCollapseStore.ts`
  (useSyncExternalStore + localStorage), because each patient route remounts
  DashboardLayout (so local useState would reset on every navigation).
- `layouts/DoctorLayout.tsx` -- ROUTED for /cms/* (layout route with <Outlet/>). Does NOT
  remount on /cms sub-navigation, so its local useState collapse persists. Independent
  collapse preference from patient sidebar (intentional -- different roles). KEPT (not
  symmetric with patient) because CMS routing relies on a persistent <Outlet/>.
- `layouts/AppLayout.tsx` -- NOT dead: imported by ~18 page components, but is now a
  passthrough (`<>{children}</>`, no chrome) since P3-6. Keeping it is low-risk;
  removing it would be a large mechanical edit of 18 importers for no functional gain.
  The `AppLayout passthrough` test pins its no-chrome behavior.
- `layouts/PatientLayout.tsx` -- REMOVED in P3-4. Was NOT routed (only its own test
  imported it); the router uses `PatientLayoutWithContent` --Üí `DashboardLayout`, NOT
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
  PersonalInfoModel wasn't coercible). This was latent -- existing tests only had
  personal_info=None.
- Use `HealthProfileDTO.model_validate(orm_obj)` (NOT `from_orm`) and `dto.model_dump()`
  (NOT `.dict()`). Backend tests run with `-W error::DeprecationWarning` to enforce.

## emergency_contact (P3-2 -- RESOLVED)
- `PersonalInfoModel.emergency_contact` is now `Mapped[dict | None] = mapped_column(JSON,
  nullable=True)` (was `Text` -- writing a dict raised on SQLite / stored a repr elsewhere).
- Migration `20260808_emergency_contact_json` (TEXT->JSON alter, safe: no legacy non-NULL
  data existed). Idempotent (skips if already JSON / table absent).
- Two enabling bug fixes in the same read path: `snapshot_profile` referenced
  `profile.extra_metadata` (typo -> `profile.profile_metadata`); `PersonalInfoDTO` lacked
  `from_attributes=True`. Without these, emergency_contact (and all personal_info) could
  never serialize via /profiles/me.
- Regression tests: `backend/tests/test_emergency_contact_p3.py` (5 tests: populated dict
  round-trip, NULL, snapshot dict-not-repr, /profiles/me populated object, /profiles/me null).

## Known pre-existing issues (not yet addressed -- deferred)
- `UserResponse` DTO role literal only allows `patient|doctor|researcher|administrator`
  but `Role` enum has more -- schema mismatch.
- Mock auth uses fixed `mock@example.com` -> email collision on second user creation in tests.
- Frontend wizard sends `emergency_contact` as a STRING vs backend dict (profileService.ts/
  profileApi.ts/defaults.ts/fieldSpecs.ts) -- would 422 on submit. Backend now stores dict
  correctly; frontend type alignment is a separate frontend-schema item (not touched in P3-2).

## Workflow rules
- Do NOT commit/stage until the whole P0--ÜíP3 series is done + final audit clean.
- Preserve RBAC; don't expose user data during loading. Preserve UI/functionality.
- Backend deps NOT preinstalled in sandbox -- must `pip install` before running tests.

## Assessments pages (two distinct routes -- keep straight)
- `/assessments` --Üí `features/questionnaire/pages/AssessmentSelectionPage.tsx`. The REAL
  working flow: uses `useNavigate` + `useStartSession` (TanStack mutation) to call the
  backend `startSession(templateId)` and navigate to `/questionnaires/:sessionId`.
  Backed by `features/questionnaire/data/assessments.ts` catalog + `useTemplates()`.
- `/assessments/dashboard` --Üí `features/dashboard/pages/Assessments.tsx`. A mock-data
  dashboard view (uses `features/dashboard/assessments/mockData.ts`, NOT backend). Was
  shipped with stub handlers that only `console.log` (handlePrimary/handleEdit/
  handleDiscard + AssessmentHistoryTable onView/onRetake/onDownload/onCompare), so every
  "Start Assessment"/"Resume"/"Review Report" button did nothing. Fixed by wiring
  `useNavigate`: completed --Üí `/assessments/:slug` (ReportViewer), requires_profile --Üí
  `/profile`, locked --Üí no-op, everything else (not_started/recommended/in_progress/
  expired/needs_review) --Üí `/assessments` (the real selection page). When adding new
  buttons on this page, route via navigate -- do NOT reintroduce console.log stubs.
- Routes that matter for navigation: `/assessments/:id`=ReportViewer,
  `/assessments/:id/results`=ResultsDashboard, `/questionnaires/:id`=session,
  `/timeline/compare`=ComparePage, `/profile`=HealthProfilePage.

## Doctor CMS recovery (P0-P3 series -- read before touching the CMS)
The Doctor CMS appeared to be a "shell" after modularization. Forensic + repair work
found it was DISCONNECTED + API-BROKEN + one critical RBAC serialization bug, not deleted.
Full findings: `CMS_CONTENT_FORENSIC_REPORT.md`. Key facts to preserve:

### Frontend CMS architecture
- `frontend/src/features/cms/` is the (only) live CMS module. Two API layers:
  - `cmsApi.ts` `contentApi` -- generic CRUD. `DEDICATED_ENDPOINTS` map routes 4 entity
    types to dedicated routers (`question`->`/cms/questions`, `question_group`->
    `/cms/question-groups`, `body_system`->`/cms/body-systems`, `template`->`/cms/templates`)
    which return BARE ARRAYS, wrapped client-side into `{items,total,skip,limit}`. All
    other entity types hit the generic `/cms/content/{entity}` (paginated). DO NOT route
    `template` through the generic content endpoint -- it 500s on the `metadata` column
    collision (see below); the dedicated `/cms/templates` endpoint is correct.
  - `cmsApi.ts` `builder`/`dashboard`/`admin`/`roles`/`users` -- dedicated endpoints.
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
- Generic content router: `app/api/v1/cms/content.py` -- `ENTITY_ALIASES`,
  `_READ_PERM_MAP`, `_WRITE_PERM_MAP`, dispatches to `content_service.ENTITY_REGISTRY`
  (entity<->model pairs) + `SqlGenericCmsRepository`. Aliases map abbreviated frontend names
  (`disease`, `symptom`, `template`...) to canonical model keys. Permission deps via
  `Permission` enum (`CMS_READ_*` / `CMS_WRITE_*`).
- Dedicated routers: `cms/questions.py` (questions/groups/body-systems/templates -- seeded
  data, bare arrays), `cms/rules.py` (rule-set CRUD + evaluate/simulate/validate), and
  `cms/dashboard.py` (overview/recent-activity/workflow-summary).
- Admin router: `app/api/v1/endpoints/admin.py` -- body-systems/indicators/evidence/
  recommendations CRUD, `GET /admin/users` (paginated `{items,total,skip,limit}`),
  `GET/PUT /admin/users/{id}/roles` (body field is `{"roles": [...]}` -- NOT `role_codes`),
  `POST /admin/users/{id}/toggle-active`, `GET /admin/roles` (bare array).
- All CMS GET endpoints depend on `get_cms_user`; admin write depends on
  `get_current_admin`. `has_role` uses `_ROLE_HIERARCHY` (>=), so `get_cms_user`
  (`has_role(roles, READ_ONLY_REVIEWER)`=level 5) admits ANY CMS role (level>=5), denying
  only patients/roleless users. This is CORRECT -- do not "fix" it by auto-granting roles.

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

### `metadata` column collision (NOT fixed -- known landmine, avoided)
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
- Backend: `cd backend && ALLOW_MOCK_AUTH=true DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=development python -m pytest tests/ -q -W error::DeprecationWarning` -> 252 pass.
- Frontend: `cd frontend && npm run typecheck && CI=true npx vitest run` -> 43 pass, typecheck clean.

## Phase 3 -- AI Clinical Intake + Candidate Indicator Extraction (ADDITIVE)
AI-assisted conversational intake is an INPUT INTERPRETATION layer ONLY. It feeds INTO
the untouched deterministic CDSE; it never diagnoses/scores/sets severity/activates
indicators/creates content. Patient text -> AI extraction -> structured observations ->
validated candidate indicators -> existing questions -> existing branching -> CDSE.
Full design: `MEDICHECK_AI_PHASE3_INTAKE_REPORT.md`.

### Backend intake architecture
- DTOs: `app/application/dtos/intake_dtos.py` -- `ObservationDTO` (negation/temporality/
  certainty preserved), `CandidateIndicatorDTO`, `CandidateQuestionDTO`,
  `CandidateQuestionGroupDTO`, `ClarificationDTO`, `IntakeResponse`, bounded
  `IndicatorCatalog`/`IndicatorCatalogEntry`. `IntakeResponse` validator rejects candidate
  `reason` text reading as a diagnosis. `safe_intake_response()` is the fallback.
- Provider: `app/application/ai/intake_provider.py` -- `AIClinicalIntakeProvider` Protocol
  + deterministic `StubClinicalIntakeProvider` (keyword + bounded synonym map, negation/
  uncertainty/temporality/duration/frequency detection, no network/API key).
  `get_intake_provider()` selects via `settings.ai_provider`. `AIIntakeProviderError` ->
  safe fallback. Prompt: `intake_prompts.py` (`INTAKE_PROMPT_VERSION="1.0"`).
- Services:
  - `ai_intake_service.py` `AIIntakeService` (orchestrator): bounded catalog (active +
    non-deleted indicators, limit 60) -> provider -> parse -> observations ->
    validation -> question discovery -> `IntakeResponse`. `IntakeTrace` records safe
    metrics; raw patient text is NOT logged.
  - `intake_validation_service.py` `CandidateValidationService`: DB is authoritative.
    Rejects unknown/inactive/deleted indicator IDs (allow-list, never creates/inserts),
    invalid confidence, orphan observations. `ValidationTrace` for observability.
  - `intake_question_service.py` `AIIntakeQuestionService`: validated candidate indicator
    IDs -> batched `QuestionIndicatorLinkModel` (active) -> `QuestionModel`
    (status=active, deleted_at IS NULL) -> `QuestionGroupModel` (is_active, deleted_at
    IS NULL). No N+1. Deterministic ranking (group display_order, then question
    order_index). Dedup. Template scope respected. `source="cms"` only.
- Endpoint: `app/api/v1/endpoints/ai_intake.py` -- `POST /api/v1/ai/intake/extract`.
  Reuses `get_current_user`; verifies session ownership (other user -> 404). Scoped to
  caller; no cross-patient intake. Registered in `router.py` as `ai_intake_router`.

### Persistence (NONE)
Phase 3 is session-scoped/in-memory. No new tables, no migrations, no schema changes.
Intake is read-only w.r.t. the clinical schema. trace_id returned for client correlation;
observability via structured logs. If replay is later needed, add additive
`ai_intake_*` tables WITHOUT touching CDSE tables.

### Frontend intake architecture
- API: `features/questionnaire/api/intakeService.ts` -- `extractIntake`, typed
  `IntakeResponse`/`IntakeObservation`/etc. Never throws on AI unavailability.
- Page: `features/questionnaire/pages/IntakePage.tsx` -- OPTIONAL assisted entry point
  at `/assessments/intake`. Textarea -> observations (with negated/uncertain/temporality
  badges) + candidate indicators + clarifications + recommended existing question groups.
  User can edit/reject/skip/continue. Non-diagnostic language. Starts a NORMAL
  questionnaire session (`useStartSession`) -> existing branching -> existing CDSE.
- Entry point: "Try AI intake" banner on `AssessmentSelectionPage.tsx`.
- Route: `/assessments/intake` in `routes/router.tsx`. Standard `/assessments` unchanged.

### Phase 3 test commands (verified)
- Backend: `... python -m pytest tests/test_ai_intake_phase3.py -q` -> 35 pass.
- Frontend: `CI=true npx vitest run src/features/questionnaire/pages/__tests__/IntakePage.test.tsx` -> 10 pass.
- Full suites: backend 252 pass, frontend 43 pass, typecheck clean, build OK.

### Phase 3 safety invariants (do NOT regress)
- AI may ONLY cite `indicator_id` values in the bounded catalog (active + non-deleted).
  Unknown/inactive/deleted/hallucinated IDs are REJECTED, never created/inserted.
- `IntakeResponse` validator rejects diagnostic language in candidate reasons.
- AI failure -> `available=false` safe fallback; standard questionnaire always works.
- Intake is read-only w.r.t. CDSE/questionnaire/branching/CMS. RBAC + session ownership
  preserved. No cross-patient intake.
