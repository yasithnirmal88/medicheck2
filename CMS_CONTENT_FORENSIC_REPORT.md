# Doctor CMS content loss / shell audit — forensic report

Investigation only. No source, database, migration, or seed files were modified.
The only file created by this audit is this report. Verified with `git status`
(clean working tree at end).

## 1. Executive summary

The Doctor CMS is not a gutted shell and its content was not deleted. The full
CMS implementation — frontend pages, hooks, API client, types, backend routers,
services, repositories, and database models — is all still present in the
repository and all backend CMS routers are still registered.

The reason the CMS appears empty is that the frontend and backend were never
correctly wired together. Several independent integration bugs, present since
the CMS module was first added, combine to make every CMS screen render its
shell and skeletons but show no data:

1. Every CMS API call uses an absolute path (`/api/v1/cms/...`) against an axios
   instance whose `baseURL` already ends in `/api/v1`. Axios concatenates the
   strings, so every request goes to `/api/v1/api/v1/cms/...` and 404s.
2. Even if the prefix were fixed, the frontend sends short entity names
   (`indicator`, `lab_test`, `imaging`, `evidence`, `lifestyle`, `exercise`,
   `nutrition`, `guideline`, `medication`, `rule`, `template`, `question`,
   `question_group`, `body_system`) that the backend `ENTITY_REGISTRY` does not
   recognise — it expects `clinical_indicator`, `laboratory_test`,
   `imaging_test`, `medical_evidence`, `lifestyle_advice`, and so on. These
   would 404 with "Unknown entity type".
3. The router wires all 17 content-list routes to a single
   `ContentListPageWrapper` that is hardcoded to `QuestionsListPage`. The
   entity-specific list pages (`DiseasesListPage`, `SymptomsListPage`, etc.)
   exist but are never imported, so they are dead code.
4. The dashboard overview response keys do not match what the dashboard page
   reads, so the stat cards show 0 even when data exists.
5. The seed data populates `possible_conditions`, not the `diseases` table the
   CMS queries, so the diseases list would be empty even with a working
   connection.
6. RBAC blocks most real users: users created on first Firebase sign-in get no
   roles, `/auth/me` returns an empty role list, the frontend falls back to
   `patient`, and `RequireDoctor` redirects them away from `/cms`.

In short: the CMS is DISCONNECTED and PARTIALLY IMPLEMENTED, not deleted. The
surviving code is substantial and recoverable.

## 2. Confidence

HIGH.

The conclusions are based on direct reading of the router, every CMS page, the
hooks, the API client, the backend routers, the services, the RBAC module, the
auth DTOs, the seed files, and the axios configuration. The central finding
(doubled `/api/v1` prefix) is corroborated by the fact that the patient-facing
APIs use relative paths (`/profiles/me`) and are confirmed working in the
repository's own tests, while the CMS APIs use absolute `/api/v1/...` paths.

The only lower-confidence area is git timing: the clone was shallow (1 grafted
commit) and was deepened to 81 commits, but the entire CMS module already
existed in the oldest available commit, so the exact origin commit of the
integration bugs is not visible in the available history.

## 3. Current architecture

### Frontend

Entry point → router → guards → layout → page → hook → API client → backend.

- Entry: `frontend/src/main.tsx` renders the app.
- Router: `frontend/src/routes/router.tsx` defines all routes, lazy-loaded.
- Auth provider: `frontend/src/contexts/AuthContext.tsx` resolves the role from
  `GET /auth/me` and exposes `isPatient`, `canAccessCMS`.
- Guards: `frontend/src/guards/index.tsx` — `RequireDoctor` gates `/cms/*`.
- CMS layout: `frontend/src/layouts/DoctorLayout.tsx` (sidebar + topbar +
  `<Outlet/>`), with `frontend/src/features/cms/layouts/CMSLayout.tsx` also
  present.
- CMS pages: `frontend/src/features/cms/pages/*.tsx` (15 pages).
- CMS hooks: `frontend/src/features/cms/hooks/useCmsQueries.ts`.
- CMS API client: `frontend/src/features/cms/api/cmsApi.ts`.
- CMS types: `frontend/src/features/cms/types/index.ts`.
- HTTP client: `frontend/src/lib/api.ts` — axios instance, `baseURL` resolved
  to end in `/api/v1`.

### Frontend call chain (generic content list example)

`/cms/diseases` route → `ContentListPageWrapper` (hardcoded to
`QuestionsListPage`) → `ContentListPage` → `useContentList('question')` →
`cmsApi.questions.list` → `api.get('/api/v1/cms/content/question')` → axios
combines with baseURL → `http://localhost:8000/api/v1/api/v1/cms/content/question`
→ 404.

### Backend

- Entry: `backend/app/main.py` → `create_app()` → `_setup_routers()` includes
  `backend/app/api/v1/router.py`.
- Router registration: `backend/app/api/v1/router.py` includes all CMS routers
  (content, dashboard, questions, builder, rules, knowledge_graph, publishing,
  evidence, audit). All are registered.
- CMS routers: `backend/app/api/v1/cms/*.py`.
- CMS services: `backend/app/application/services/cms/*.py`.
- Generic repository: `backend/app/infrastructure/persistence/repositories/sql_generic_cms_repository.py`.
- Entity registry: `ENTITY_REGISTRY` in
  `backend/app/application/services/cms/content_service.py`.
- RBAC: `backend/app/core/security/rbac.py` (Role, Permission, role-permission
  map). CMS guard dependency: `get_cms_user` in `backend/app/api/deps.py`.

### Database

- ORM models: `backend/app/infrastructure/persistence/models/*.py` (70+ models,
  including all CMS tables: `diseases`, `clinical_indicators`, `symptoms`,
  `laboratory_tests`, `imaging_tests`, `medical_evidence`, `recommendations`,
  `knowledge_graph`, `publishing_jobs`, `approvals`, `workflows`,
  `version_snapshots`, `audit_logs`, `decision_rules`, etc.).
- Migrations: `backend/alembic/versions/` (3 files). The migration runner
  `init_db()` is commented out in `main.py`; tables are created via
  `Base.metadata.create_all`.
- Seed: `backend/app/infrastructure/seed.py` (called in lifespan) +
  `seed_medical.py`.

### Full chain for one feature (Diseases list)

| Layer | Location | Status |
|---|---|---|
| Route | `/cms/diseases` in `router.tsx` | Exists, but wired to `QuestionsListPage` |
| Page | `ContentListPages.tsx` `DiseasesListPage` | Exists, orphaned (never imported by router) |
| Hook | `useContentList('disease')` | Exists |
| API client | `cmsApi.diseases.list` → `/api/v1/cms/content/disease` | Path doubled → 404 |
| Backend route | `GET /cms/content/{entity_type}` in `content.py` | Exists, registered |
| Entity name | backend expects `disease` | Match (disease is one of the few that match) |
| Service | `CMSContentService.list_entities` | Exists |
| Repository | `SQLGenericCMSRepository(DiseaseModel)` | Exists |
| Table | `diseases` (`DiseaseModel`) | Table created, never seeded |

## 4. Missing content inventory

What the user perceives as "missing" — every CMS screen shows its shell and
skeletons but no data:

- Dashboard stat cards (Total Questions, Active Diseases, Pending Approvals,
  Published Versions) all show 0.
- Recent Activity table shows "No recent activity".
- All content-list screens (Questions, Diseases, Body Systems, Symptoms,
  Indicators, Lab Tests, Imaging, Recommendations, Lifestyle, Exercise,
  Nutrition, Evidence, Templates, Medications, Guidelines, Decision Rules,
  Thresholds) show empty tables.
- Question Builder, Rule Builder, Knowledge Graph editor show empty canvases.
- Publishing, Approvals, Version History show empty lists.
- Audit Logs, Users & Roles, Search show empty results.

## 5. Existing content inventory

All of the following code is present and intact:

- 15 CMS pages in `frontend/src/features/cms/pages/`.
- Full hooks module with ~30 queries/mutations
  (`frontend/src/features/cms/hooks/useCmsQueries.ts`).
- Full API client with 46 endpoint calls
  (`frontend/src/features/cms/api/cmsApi.ts`).
- Complete type definitions for ~40 entity types
  (`frontend/src/features/cms/types/index.ts`).
- Shared `ContentLayout` component with `DataTable`, `StatsCard`,
  `StatusBadge`, `Pagination`, `SearchInput`, `ConfirmAction`
  (`frontend/src/features/cms/components/ContentLayout.tsx`).
- Doctor layout with 30+ navigation entries across 5 groups
  (`frontend/src/layouts/DoctorLayout.tsx`).
- 10 backend CMS routers, all registered
  (`backend/app/api/v1/cms/*.py`).
- 8 backend CMS services (`backend/app/application/services/cms/*.py`).
- Generic CMS repository + entity registry with 41 entity types.
- 70+ ORM models including all CMS tables.
- RBAC with 9 roles, ~70 permissions, full role-permission maps.
- Seed data for body systems, questions, question groups, questionnaire
  templates, clinical indicators, laboratory tests, recommendations, evidence
  references, and possible conditions.

## 6. Orphaned components

| Component | File | Status |
|---|---|---|
| `DiseasesListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `BodySystemsListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `SymptomsListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `IndicatorsListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `LabTestsListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `ImagingTestsListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `RecommendationsListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `LifestyleAdviceListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `ExerciseProgramsListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `NutritionAdviceListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `EvidenceListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `TemplatesListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `MedicationsListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `ClinicalGuidelinesListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `DecisionRulesListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `SeverityThresholdsListPage` | `ContentListPages.tsx` | Exported, never imported by router |
| `ContentListPage` (generic) | `ContentListPage.tsx` | Used only via `QuestionsListPage` |
| `ContentFormPage` | `ContentFormPage.tsx` | Exported, no route references it |
| `CMSLayout` | `features/cms/layouts/CMSLayout.tsx` | Not imported by router (DoctorLayout used instead) |
| `Providers/AuthProvider` | `frontend/src/providers/AuthProvider.tsx` | Duplicate of AuthContext (contexts/AuthContext.tsx is the live one) |

All 17 content-list routes point to `ContentListPageWrapper`, which is hardcoded
to `QuestionsListPage`:

```
const ContentListPageWrapper = React.lazy(() =>
  import('../features/cms/pages/ContentListPages').then(m => ({ default: m.QuestionsListPage }))
)
```

## 7. Broken routes

| CMS route | Routed component | Expected component | Reachable | Notes |
|---|---|---|---|---|
| `/cms/dashboard` | `CMSDashboardPage` | same | Yes | Data 404s (doubled prefix) |
| `/cms/questions` | `QuestionsListPage` | same | Yes | Data 404s |
| `/cms/diseases` | `QuestionsListPage` | `DiseasesListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/body-systems` | `QuestionsListPage` | `BodySystemsListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/symptoms` | `QuestionsListPage` | `SymptomsListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/indicators` | `QuestionsListPage` | `IndicatorsListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/lab-tests` | `QuestionsListPage` | `LabTestsListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/imaging` | `QuestionsListPage` | `ImagingTestsListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/recommendations` | `QuestionsListPage` | `RecommendationsListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/lifestyle` | `QuestionsListPage` | `LifestyleAdviceListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/exercise` | `QuestionsListPage` | `ExerciseProgramsListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/nutrition` | `QuestionsListPage` | `NutritionAdviceListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/evidence` | `ClinicalEvidencePage` | same | Yes | Data 404s |
| `/cms/templates` | `QuestionsListPage` | `TemplatesListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/medications` | `QuestionsListPage` | `MedicationsListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/guidelines` | `QuestionsListPage` | `ClinicalGuidelinesListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/rules` | `QuestionsListPage` | `DecisionRulesListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/thresholds` | `QuestionsListPage` | `SeverityThresholdsListPage` | Yes (wrong page) | Wrong entity, data 404s |
| `/cms/question-groups` | `Navigate to /cms/questions` | — | Redirect | Question groups page removed |
| `/cms/builder` | `QuestionnaireBuilderPage` | same | Yes | `GET /builder/groups` 404s (no such backend route) |
| `/cms/rules-builder` | `RuleBuilderPage` | same | Yes | `GET /cms/rules` 404s (no GET route on rules router) |
| `/cms/graph` | `KnowledgeGraphEditorPage` | same | Yes | Data 404s (doubled prefix) |
| `/cms/publishing` | `PublishingWorkflowsPage` | same | Yes | Data 404s |
| `/cms/approvals` | `ApprovalQueuePage` | same | Yes | Data 404s |
| `/cms/history` | `VersionHistoryPage` | same | Yes | Data 404s |
| `/cms/audit` | `AuditViewerPage` | same | Yes | Data 404s |
| `/cms/users` | `UsersRolesPage` | same | Yes | `/admin/users` and `/admin/roles` 404 (do not exist) |
| `/cms/search` | `SearchPage` | same | Yes | Data 404s |
| `/cms/settings` | `SettingsPage` | same | Yes | Static page |

## 8. Broken API connections

### 8.1 Doubled `/api/v1` prefix (affects all 46 CMS calls)

`frontend/src/lib/api.ts` resolves `baseURL` to end in `/api/v1` (dev:
`http://localhost:8000/api/v1`; prod: `/api/v1`). Axios ^1.5.0 combines
`baseURL` and the request URL by string concatenation
(`baseURL.replace(/\/+$/,'') + '/' + url.replace(/^\/+/,'')`), not by URL
resolution.

The CMS API client uses absolute paths:

```
api.get('/api/v1/cms/dashboard/overview')
```

Result: `http://localhost:8000/api/v1/api/v1/cms/dashboard/overview` (dev) or
`/api/v1/api/v1/cms/...` (prod) — 404.

Corroboration: the patient-facing APIs that are confirmed working in the
repository tests use relative paths (`/profiles/me`, `/auth/me`,
`/questionnaires`), which combine correctly to
`http://localhost:8000/api/v1/profiles/me`.

### 8.2 Entity-name mismatch (would 404 even with correct prefix)

Frontend `cmsApi` entity-type strings vs backend `ENTITY_REGISTRY` keys:

| Frontend sends | Backend expects | Result |
|---|---|---|
| `question` | (not in registry; separate `/cms/questions` router) | 404 on `/cms/content/question` |
| `question_group` | (not in registry; separate `/cms/question-groups`) | 404 |
| `body_system` | (not in registry; separate `/cms/body-systems`) | 404 |
| `template` | `template_library` | 404 |
| `indicator` | `clinical_indicator` | 404 |
| `lab_test` | `laboratory_test` | 404 |
| `imaging` | `imaging_test` | 404 |
| `evidence` | `medical_evidence` / `evidence_collection` | 404 |
| `lifestyle` | `lifestyle_advice` | 404 |
| `exercise` | `exercise_program` | 404 |
| `nutrition` | `nutrition_advice` | 404 |
| `guideline` | `clinical_guideline` | 404 |
| `medication` | `medication_recommendation` | 404 |
| `rule` | `decision_rule` | 404 |
| `tag` | `medical_tag` | 404 |
| `specialty` | `medical_specialty` | 404 |
| `disease` | `disease` | Match |
| `symptom` | `symptom` | Match |
| `recommendation` | `recommendation` | Match |
| `severity_threshold` | `severity_threshold` | Match |
| `scoring_profile` | `scoring_profile` | Match |
| `risk_category` | `risk_category` | Match |
| `disease_category` | `disease_category` | Match |
| `body_system_category` | `body_system_category` | Match |
| `recommendation_category` | `recommendation_category` | Match |
| `lab_panel` | `lab_panel` | Match |
| `biomarker` | `biomarker` | Match |
| `question_category` | `question_category` | Match |
| `question_tag` | `question_tag` | Match |

15 of the 18 entity types the frontend actually calls would 404.

### 8.3 Missing backend routes for frontend calls

| Frontend call | Backend route | Status |
|---|---|---|
| `GET /cms/builder/groups` (`useBuilderGroups`) | none | 404 — builder has no `GET /groups` |
| `GET /cms/builder/versions?template_id=` | `GET /cms/builder/versions/{questionnaire_id}` | 404 — path param vs query param |
| `GET /cms/rules` (`useRuleSets`) | none | 404 — rules router has only POST routes |
| `GET /cms/rules/{id}` (`useRuleSets` getSet) | none | 404 |
| `POST /cms/rules` (createSet) | none | 404 — only `/evaluate`, `/simulate`, etc. exist |
| `GET /admin/users` (`useUsers`) | none | 404 — admin router has only `/body-systems`, `/indicators`, `/evidence`, `/recommendations`, `/audit` |
| `GET /admin/roles` (`useRoles`) | none | 404 |
| `PUT /admin/users/{id}/roles` | none | 404 |
| `GET /admin/roles/{id}/permissions` | none | 404 |

### 8.4 Dashboard response-shape mismatch

`CMSDashboardService.get_overview` returns `by_type` with keys `questions`,
`diseases`, `symptoms`, `indicators`, `recommendations` (plural) and
`by_status` keyed the same way with statuses `draft/active/archived/pending`.

`CMSDashboardPage` reads:

```
overview?.by_type?.question      // undefined — backend key is 'questions'
overview?.by_type?.disease       // undefined — backend key is 'diseases'
overview?.by_status?.question?.published  // undefined — backend key is 'questions', status is not 'published'
```

So all four stat cards render 0 regardless of data.

## 9. RBAC problems

### 9.1 Users created on first sign-in get no roles

`get_or_create_user` in `backend/app/application/services/auth_service.py` and
the auto-create path in `get_current_user` (`backend/app/api/deps.py`) call
`User.create(...)` without a role. `User.create` defaults `roles=set()`
(empty). Only `register_user` accepts and sets a role, and it only allows
`patient` or `doctor`.

There is no seed for roles or user-role assignments. The `roles` table is
populated lazily only when a user with roles is created.

### 9.2 Role does not reach the frontend

`/auth/me` returns `UserResponse`, whose `roles` field is typed as
`list[Literal["patient", "doctor", "researcher", "administrator"]]`. The
backend `Role` enum includes `medical_director`, `specialist_doctor`,
`general_physician`, `research_reviewer`, `content_editor`,
`read_only_reviewer`, `super_admin`. A user holding any of these CMS roles
would fail Pydantic literal validation in `UserResponse.from_entity`, so
`/auth/me` could error (500) for CMS users. (Not executed here because
pydantic is not installed in the sandbox, but the type mismatch is clear in
`backend/app/application/dtos/auth_dtos.py`.)

The frontend reads `data.role || data.roles?.[0]`. `UserResponse` has no
`role` field, only `roles`. For a user with empty roles, this resolves to
`undefined`, and `AuthContext` falls back to `localStorage` or `'patient'`.

### 9.3 RequireDoctor blocks CMS access

`RequireDoctor` requires `role !== null && !isPatient && canAccessCMS`. For a
user with no role resolved (falls back to `patient`), `isPatient` is true and
`canAccessCMS` is false, so the guard redirects to `/app`. The CMS is
unreachable for any user whose role was not explicitly set in the database.

### 9.4 Backend CMS guard

`get_cms_user` requires `has_role(roles, Role.READ_ONLY_REVIEWER)`, which
passes for any role with hierarchy level >= 5 (all CMS roles). So the backend
guard itself is permissive — the block is on the frontend side, before any CMS
request is made.

## 10. Database status

Tables are created from model metadata via `Base.metadata.create_all`
(`init_db()`/alembic is commented out in `main.py`). All CMS tables exist.

Read-only assessment of seed coverage (no database was queried; this is from
reading `seed.py` and `seed_medical.py`):

| Table (CMS entity) | Created | Seeded | Notes |
|---|---|---|---|
| `body_systems` | Yes | Yes | Seeded in `seed.py` |
| `questions` | Yes | Yes | Seeded in `seed.py` |
| `question_groups` | Yes | Yes | Seeded in `seed.py` |
| `questionnaire_templates` | Yes | Yes | Seeded in `seed.py` |
| `clinical_indicators` | Yes | Yes | Seeded in `seed_medical.py` |
| `laboratory_tests` | Yes | Yes | Seeded in `seed_medical.py` |
| `recommendations` | Yes | Yes | Seeded in `seed_medical.py` |
| `evidence_references` | Yes | Yes | Seeded in `seed_medical.py` |
| `possible_conditions` | Yes | Yes | Seeded in `seed_medical.py` — but this is NOT the `diseases` table the CMS queries |
| `diseases` | Yes | No | Never seeded — the CMS "Diseases" list would be empty |
| `symptoms` | Yes | No | Not seeded |
| `imaging_tests` | Yes | No | Not seeded |
| `medical_evidence` | Yes | No | Not seeded |
| `lifestyle_advice` | Yes | No | Not seeded |
| `exercise_program` | Yes | No | Not seeded |
| `nutrition_advice` | Yes | No | Not seeded |
| `clinical_guideline` | Yes | No | Not seeded |
| `medication_recommendation` | Yes | No | Not seeded |
| `decision_rule` | Yes | No | Not seeded |
| `knowledge_graph` | Yes | No | Not seeded |
| `publishing_jobs` | Yes | No | Not seeded |
| `approvals` | Yes | No | Not seeded |
| `workflows` | Yes | No | Not seeded |
| `version_snapshots` | Yes | No | Not seeded |
| `audit_logs` | Yes | No | Populated only by audit middleware at runtime |

Key mismatch: the seed writes disease data to `possible_conditions`
(`PossibleConditionModel`), but the CMS content service maps `disease` to
`diseases` (`DiseaseModel`). These are separate tables with separate columns.

## 11. Seed status

`seed_database` in `backend/app/infrastructure/seed.py` is called from the app
lifespan in `main.py` on startup. It is guarded by "already seeded" (checks
`BodySystemModel` count > 0). It seeds body systems, questions, question
groups, questionnaire templates, then calls `seed_medical` for clinical
indicators, laboratory tests, recommendations, evidence references, and
possible conditions.

No seed exists for: diseases (the CMS table), symptoms, imaging tests,
medical evidence, lifestyle/exercise/nutrition advice, clinical guidelines,
medications, decision rules, knowledge graphs, publishing workflow entities,
roles, or user-role assignments.

## 12. Git timeline

The clone was shallow (1 grafted commit). It was deepened to 81 commits during
this audit (read-only `git fetch --deepen=50`). No commits were modified.

Key findings from history:

- The entire CMS module (frontend `features/cms/` and backend `api/v1/cms/` +
  `services/cms/`) was introduced in the oldest available commit `4116fc9`
  ("Add Assessments management page wired to FastAPI..."). It was added
  complete in a single commit.
- No CMS file has been deleted or modified since that commit
  (`git log --diff-filter=D -- features/cms/ api/v1/cms/ services/cms/`
  returns empty; `cmsApi.ts` and `types/index.ts` show only the one creation
  commit).
- The portal separation happened in `1b04b0b` ("feat: implement complete RBAC
  with patient/doctor portal separation", 4 Aug 2026), which added
  `DoctorLayout`, `PatientLayout`, guards, and `AuthContext`.
- `099c342` ("Fix blank patient dashboard and doctor CMS pages", 8 Aug 2026)
  fixed a layout `<Outlet/>` rendering bug, not the data layer.

The integration bugs (doubled prefix, entity-name mismatch, hardcoded
`ContentListPageWrapper`, dashboard key mismatch, missing backend routes,
empty-role auto-create) have been present since the CMS module was first
committed. They were never introduced by a later deletion or refactor visible
in the available history.

## 13. Most likely root cause (ranked)

P0 — Doubled `/api/v1` prefix in every CMS API call. A single
`frontend/src/features/cms/api/cmsApi.ts` uses absolute `/api/v1/...` paths
against an axios instance whose `baseURL` already ends in `/api/v1`. This
alone makes 100% of CMS data requests 404. Highest impact, simplest to locate.

P1 — Entity-name mismatch between frontend and backend. 15 of 18 entity types
the frontend calls are not in the backend `ENTITY_REGISTRY`. Even with the
prefix fixed, those lists would still 404.

P1 — Router hardcodes `ContentListPageWrapper` to `QuestionsListPage` for all
17 content-list routes. The correct entity-specific pages are dead code.

P2 — Missing backend routes for several frontend calls: `GET /cms/rules`,
`GET /cms/builder/groups`, `GET /cms/builder/versions?template_id=`,
`GET /admin/users`, `GET /admin/roles`, and the role-permission endpoints.

P2 — Dashboard response-shape mismatch (`by_type`/`by_status` keys and status
values do not match what the page reads), so stat cards show 0.

P2 — Seed/data mismatch: diseases seeded into `possible_conditions`, not
`diseases`; many CMS tables never seeded.

P3 — RBAC: users auto-created on first sign-in get no roles; `UserResponse`
literal rejects CMS role strings; frontend falls back to `patient` and
`RequireDoctor` blocks `/cms`.

## 14. Evidence

| Conclusion | File | Line / symbol |
|---|---|---|
| Doubled prefix | `frontend/src/features/cms/api/cmsApi.ts` | lines 44, 46, 48, 22 (`contentBase`) and all `entityApi` calls |
| baseURL ends in `/api/v1` | `frontend/src/lib/api.ts` | `getApiBaseUrl()` returns `.../api/v1` |
| Working relative-path APIs | `frontend/src/features/profile/api/profileApi.ts` | `/profiles/me` etc. |
| Entity-name mismatch | `frontend/src/features/cms/api/cmsApi.ts` lines 55-72 vs `backend/app/application/services/cms/content_service.py` `ENTITY_REGISTRY` |
| Hardcoded wrapper | `frontend/src/routes/router.tsx` lines 55-57 and 282-299 |
| Orphaned list pages | `frontend/src/features/cms/pages/ContentListPages.tsx` (exports never imported by router) |
| Dashboard key mismatch | `frontend/src/features/cms/pages/CMSDashboardPage.tsx` (`by_type.question`, `by_status.question.published`) vs `backend/app/application/services/cms/dashboard_service.py` (`by_type` keys `questions`/`diseases`, statuses `draft/active/archived/pending`) |
| Missing `GET /cms/rules` | `backend/app/api/v1/cms/rules.py` (only POST routes) vs `frontend/src/features/cms/api/cmsApi.ts` `rules.getSets` |
| Missing `GET /cms/builder/groups` | `backend/app/api/v1/cms/builder.py` (no `/groups` GET) vs `cmsApi.builder.getGroups` |
| Missing admin user/role routes | `backend/app/api/v1/endpoints/admin.py` (only body-systems/indicators/evidence/recommendations/audit) vs `cmsApi.users`/`cmsApi.roles` |
| Users auto-created with no roles | `backend/app/application/services/auth_service.py` `get_or_create_user` + `backend/app/api/deps.py` `get_current_user` (call `User.create()` with no role) |
| `User.create` defaults empty roles | `backend/app/domain/entities/user.py` line 42 (`roles={role} if role else set()`) |
| `UserResponse` role literal mismatch | `backend/app/application/dtos/auth_dtos.py` (`list[Literal["patient","doctor","researcher","administrator"]]`) vs `backend/app/core/security/rbac.py` `Role` enum |
| `RequireDoctor` blocks no-role users | `frontend/src/guards/index.tsx` `RequireDoctor` (`role === null || isPatient || !canAccessCMS`) |
| Diseases seeded into wrong table | `backend/app/infrastructure/seed_medical.py` writes `PossibleConditionModel` (table `possible_conditions`); CMS maps `disease` to `DiseaseModel` (table `diseases`) |
| `init_db` disabled | `backend/app/main.py` line 97 (`# init_db()`) |
| All CMS routers registered | `backend/app/api/v1/router.py` (includes all cms routers) |
| CMS module added complete in one commit, never deleted | `git log --diff-filter=A -- features/cms/ api/v1/cms/ services/cms/` → `4116fc9`; `git log --diff-filter=D` → empty |

## 15. Recovery options (not implemented)

Option A — Fix the API path prefix (P0). Change `cmsApi.ts` to use relative
paths (`/cms/...` instead of `/api/v1/cms/...`), matching the working profile
API. This alone would restore data flow to the routes whose entity names match.

Option B — Align entity names (P1). Either add short-name aliases to the
backend `ENTITY_REGISTRY` and permission maps, or change the frontend
`cmsApi`/`ENTITY_TYPES` to use the backend's full names.

Option C — Wire the router to the correct list pages (P1). Replace the single
hardcoded `ContentListPageWrapper` with per-route imports of the existing
`DiseasesListPage`, `SymptomsListPage`, etc.

Option D — Add the missing backend routes (P2). Implement `GET /cms/rules`,
`GET /cms/builder/groups`, `GET /cms/builder/versions` (with `template_id`
query), and the admin user/role endpoints, or repoint the frontend to existing
equivalent endpoints.

Option E — Align the dashboard response shape (P2). Make the dashboard service
return `by_type`/`by_status` keys and status values the frontend expects, or
update the frontend to read the backend's actual keys.

Option F — Fix RBAC (P3). Assign a default CMS role on user creation (or via
an admin role-assignment screen), widen the `UserResponse` role literal to
include all `Role` enum values, and ensure `/auth/me` returns a role the
frontend accepts.

Option G — Fix the seed/data mismatch (P2). Seed the `diseases` table (or
point the CMS `disease` entity at `possible_conditions`), and seed the other
empty CMS tables.

Option E (combined) — Complete the new CMS architecture using surviving
components. The components, hooks, services, and models all survive; the work
is integration, not rebuilding.

## Final verdict

ROOT CAUSE:
The CMS frontend and backend were both built complete but never integrated.
The dominant bug is a doubled `/api/v1` prefix in every CMS API call
(`frontend/src/features/cms/api/cmsApi.ts` uses absolute `/api/v1/...` paths
against an axios baseURL that already ends in `/api/v1`), so 100% of CMS data
requests 404. This is compounded by an entity-name mismatch, a router that
wires all content routes to the wrong page, missing backend routes, a
dashboard response-shape mismatch, a seed/table mismatch, and RBAC that blocks
no-role users.

CONTENT STATUS:
MIXED — components DISCONNECTED (frontend never reaches backend), data
PRESENT-but-UNREACHABLE for some tables (clinical_indicators,
laboratory_tests, recommendations, evidence_references, body_systems,
questions are seeded but unreachable), data MISSING for others (diseases,
symptoms, imaging_tests, etc. are never seeded), and several pages
PARTIALLY IMPLEMENTED on the backend (rules, builder groups, admin users).

WHAT SURVIVED:
- All 15 CMS pages and the DoctorLayout shell with full navigation
- The complete hooks and API client modules
- All 10 backend CMS routers (registered) and 8 CMS services
- The generic CMS repository and 41-entry entity registry
- All 70+ ORM models and CMS database tables
- The RBAC module with 9 roles and ~70 permissions
- Seed data for body systems, questions, clinical indicators, lab tests,
  recommendations, evidence references, and possible conditions
- The full git history of the CMS module (never deleted)

WHAT IS MISSING:
- A working frontend-to-backend connection (doubled prefix)
- Aligned entity names between frontend and backend
- Correct per-entity route wiring (router uses one page for all lists)
- Several backend endpoints the frontend calls (GET /cms/rules,
  GET /cms/builder/groups, GET /admin/users, GET /admin/roles)
- A dashboard response shape matching the page
- Seed data for diseases, symptoms, imaging tests, and most CMS tables
- A role-assignment path so real users can reach the CMS

WHEN IT HAPPENED:
Present since the CMS module was first committed (`4116fc9`, the oldest
available commit). No later deletion or refactor introduced it; the available
git history shows no CMS file deletions or modifications after creation.

MOST LIKELY RECOVERY PATH:
Fix the API path prefix in `cmsApi.ts` first (P0) — this is the single
highest-impact change and immediately restores data flow to matching entity
routes — then align entity names, wire the router to the correct list pages,
and add the missing backend routes.

CONFIDENCE:
HIGH

FILES MOST IMPORTANT FOR RECOVERY:
- `frontend/src/features/cms/api/cmsApi.ts` (path prefix + entity names)
- `frontend/src/routes/router.tsx` (per-entity route wiring)
- `frontend/src/features/cms/types/index.ts` (entity type definitions)
- `backend/app/application/services/cms/content_service.py` (ENTITY_REGISTRY)
- `backend/app/api/v1/cms/content.py` (permission maps + entity name handling)
- `backend/app/application/services/cms/dashboard_service.py` (response shape)
- `backend/app/application/dtos/auth_dtos.py` (UserResponse role literal)
- `backend/app/api/deps.py` (get_cms_user / role assignment on auto-create)
- `backend/app/infrastructure/seed.py` and `seed_medical.py` (disease table seed)
- `frontend/src/lib/api.ts` (axios baseURL — reference for correct relative paths)
