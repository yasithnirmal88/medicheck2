# Medical Adaptive Questionnaire Engine — Production Readiness Audit

**Date**: 2026-07-22
**Audit Scope**: Complete end-to-end review of the Questionnaire Engine (backend, frontend, database, APIs, security, performance, tests, deployment)
**Auditor**: Automated static analysis + code review

---

## Executive Summary

| Dimension | Score | Grade |
|-----------|-------|-------|
| **Overall Production Readiness** | **67/100** | **C+** |
| Architecture | 85/100 | B |
| Security | 60/100 | C |
| Performance | 55/100 | C |
| Maintainability | 70/100 | C+ |
| Test Coverage | 65/100 | C |
| Deployment Readiness | 40/100 | D |

**Recommendation**: **Ready for beta/internal testing only** — requires resolving 2 critical, 4 high, and 8 medium issues before production deployment.

---

## 1. Architecture Review (85/100)

### Verified Conformance

| Rule | Status | Notes |
|------|--------|-------|
| Domain has no framework imports | ✅ PASS | Domain entities are pure `@dataclass`, no FastAPI/SQLAlchemy imports |
| Application depends on abstractions | ✅ PASS | Service uses repository ABC interfaces |
| Infrastructure depends on application | ✅ PASS | Repositories implement domain interfaces |
| API depends on application | ✅ PASS | Endpoints call service layer |
| Dependency inversion maintained | ✅ PASS | All arrows point inward |
| No circular dependencies | ✅ PASS | Verified import graph is acyclic |

### Architecture Violations

| Severity | Location | Issue |
|----------|----------|-------|
| **HIGH** | `questionnaire_service.py:191` | ORM model `AssessmentAnswerModel` imported directly in application service method — breaks Clean Architecture |
| **MEDIUM** | `engine.py:149-167` | Raw SQL queries bypass repository layer (`_get_answers_map`, `_get_dependencies`) |
| **MEDIUM** | `engine.py` + `questionnaire_service.py` | Duplicate instantiation of `BranchingEvaluator`, `ValidationEngine`, `ScoringEngine` in both classes |
| **LOW** | `questionnaire_service.py:346-382` | `_serialize_question` returns raw dict, bypassing DTO layer |

---

## 2. Security Review (60/100)

### Findings

| Severity | Location | Issue |
|----------|----------|-------|
| **CRITICAL** | `deps.py:97,105` | `has_role()` called with hardcoded string sets `{"doctor", "admin", "super_admin"}` instead of user's actual roles — **authorization bypass** — any user passes these checks |
| **HIGH** | `deps.py:105` | `get_current_admin` calls `has_role({"admin", "super_admin"}, Role.ADMIN)` — same pattern, always returns True |
| **MEDIUM** | `cms/questions.py:133-134,270-271,395-396` | `__import__("datetime")` hack — code smell, potential import injection via environment |
| **MEDIUM** | `questions.py:96-99` | `__import__("app.application.services.questionnaire_service", ...)` inline — bypasses normal dependency resolution |
| **LOW** | `config.py:27` | Default `secret_key = "change-me-to-a-random-secret-key"` — must be changed in production |
| **LOW** | `config.py:32-33` | Default DB credentials in code — `.env` must override |
| **LOW** | `engine.py:55` | User attributes extracted from `session.metadata.get("user_attributes", {})` — trust boundary between client-controlled metadata and computed data not enforced |

### Verified OK

| Check | Result |
|-------|--------|
| SQL injection (parameterized queries) | ✅ All queries use bind parameters or ORM |
| Bandit SAST (questionnaire modules) | ✅ 0 issues across 644 LOC |
| Firebase JWT auth flow | ✅ Correct token verification flow |
| Question ownership verification | ✅ `save_answer` checks `session.user_id` matches |
| Input validation | ✅ `ValidationEngine` validates all responses |

---

## 3. Performance Review (55/100)

### Critical Issues

| Severity | Location | Issue |
|----------|----------|-------|
| **CRITICAL** | `questionnaire_service.py:324-345` | **N+1 query pattern** in `_calculate_scores`: loops over answers and makes individual `find_by_id` queries for each question |
| **HIGH** | `questions.py:39-41` | N+1: loads all questions, then fetches options per question |
| **HIGH** | `cms/questions.py:48-51` | Same N+1 pattern in CMS question listing |
| **MEDIUM** | `engine.py:53-54` | `load_questions` called twice in `get_next_question` path — duplicate DB query |
| **MEDIUM** | `questionnaire_service.py:83-95` | `start_session`: loads questions to find first question, but also loads options separately — 2 additional DB round trips |
| **LOW** | `ProgressBar.tsx` | No React.memo on progress component — potentially re-renders on every keystroke |
| **LOW** | Frontend bundle | 638 KB monolithic JS chunk — no code-splitting |

### Bundle Analysis (Vite build)

| Asset | Size | Gzipped |
|-------|------|---------|
| `index.html` | 0.40 KB | 0.26 KB |
| CSS | 8.89 KB | 2.21 KB |
| JS | 637.99 KB | 174.24 KB |

---

## 4. Maintainability Review (70/100)

### Code Quality

| File | Lines | Assessment |
|------|-------|------------|
| `seed.py` | 942 | Too large — should be split into module-level seed files per body system |
| `cms/questions.py` | 543 | Too large — contains CRUD for 6 entity types in one file |
| `questionnaire_service.py` | 382 | Reasonable but contains both orchestration and serialization logic |
| `sql_questionnaire_repository.py` | 179 | Good — well-structured repository pattern |
| All engine modules | 644 total | Clean, well-separated, single-responsibility |

### Dead/Unused Code

| Severity | Location | Issue |
|----------|----------|-------|
| **MEDIUM** | `app/application/use_cases/` | Empty package — directory exists but contains no files |
| **MEDIUM** | `app/domain/aggregates/` | Empty package — directory exists but contains no files |
| **MEDIUM** | `app/domain/events/` | Empty package — directory exists but contains no files |
| **LOW** | `AssessmentProgressModel` | ORM model exists but never used in any repository — progress is computed in-memory |
| **LOW** | `EvidenceReferenceModel` | ORM model exists but no repository or service reads/writes it |
| **LOW** | `AssessmentProgress` `create()` classmethod | Has `estimated_time_remaining` parameter that's always computed in code, never persisted |

### Code Smells

| Severity | Location | Issue |
|----------|----------|-------|
| **MEDIUM** | `cms/questions.py` | Repeated `__import__("datetime")` pattern in 3+ methods — should import `from datetime import datetime, timezone` at module level |
| **MEDIUM** | `questions.py:96-99` | Dynamic `__import__` to get service class — should use normal import |
| **LOW** | `questionnaire_service.py` | `_serialize_question` duplicates `QuestionResponse` DTO fields in dict literal |
| **LOW** | `session.progress` typing | `AssessmentSession` TypeScript type always shows `progress: SessionProgress` but backend can return `null` |

---

## 5. Database Review (45/100)

### Schema Issues

| Severity | Issue |
|----------|-------|
| **CRITICAL** | **No foreign key constraints** on any questionnaire table — all relationships are implicit via string IDs |
| **HIGH** | **No Alembic migrations for questionnaire tables** — only 2 migration files exist (health_profile, admin). Tables created via `create_all` which is not safe for production schema evolution |
| **HIGH** | `sql_question_repository.find_by_questionnaire(questionnaire_id)` — **ignores the questionnaire_id parameter** — returns ALL non-deleted questions. Questionnaire-question M2M relationship is not implemented |
| **MEDIUM** | No cascade delete rules — deleting a session won't cascade to answers |
| **MEDIUM** | No composite indexes on common query patterns (e.g., `(question_id, depends_on_question_id)` for dependencies) |
| **LOW** | All UUIDs stored as `String(32)` — hex UUIDs work but `BINARY(16)` or `UUID` type would be more efficient |
| **LOW** | `branch_path: Mapped[list | None]` in AssessmentAnswerModel — missing generic type parameter |

### Missing Indexes

| Table | Suggested Index |
|-------|----------------|
| `assessment_answers` | `(session_id, question_id)` composite unique index |
| `question_dependencies` | `(question_id, depends_on_question_id)` composite index |
| `branch_rules` | `(body_system_id, priority)` composite index |

### Soft Delete Consistency

| Entity | Soft Delete | Notes |
|--------|-------------|-------|
| `QuestionnaireTemplateModel` | ✅ | Inherits from `BaseModel` |
| `QuestionModel` | ✅ | Inherits from `BaseModel` |
| `BodySystemModel` | ✅ | Inherits from `BaseModel` |
| `QuestionGroupModel` | ✅ | Inherits from `BaseModel` |
| `QuestionOptionModel` | ❌ | Uses `is_active` boolean instead |
| `QuestionDependencyModel` | ❌ | No soft delete — deleted directly |
| `BranchRuleModel` | ❌ | Has `is_active` but no soft delete |
| `AssessmentSessionModel` | ❌ | Uses status instead |
| `AssessmentAnswerModel` | ❌ | No soft delete |

### Foreign Key Analysis

| Referencing Column | Referenced Table | FK Defined? |
|--------------------|------------------|-------------|
| `questions.body_system_id` | `body_systems.id` | ❌ |
| `questions.question_group_id` | `question_groups.id` | ❌ |
| `question_groups.body_system_id` | `body_systems.id` | ❌ |
| `assessment_answers.session_id` | `assessment_sessions.id` | ❌ |
| `assessment_sessions.user_id` | `users.id` | ❌ |
| `question_dependencies.question_id` | `questions.id` | ❌ |
| `question_dependencies.depends_on_question_id` | `questions.id` | ❌ |

---

## 6. API Review (60/100)

### Endpoint Inventory

| Method | Path | Request DTO | Response DTO | Auth |
|--------|------|-------------|--------------|------|
| GET | `/api/v1/questionnaires` | Query params | `list[QuestionnaireTemplateResponse]` | User |
| GET | `/api/v1/questionnaires/{id}` | — | `QuestionnaireTemplateResponse` | User |
| POST | `/api/v1/questionnaires/{id}/start` | — | `StartSessionResponse` | User |
| GET | `/api/v1/questionnaires/sessions` | — | `list[AssessmentSessionResponse]` | User |
| GET | `/api/v1/questionnaires/sessions/{id}` | — | `AssessmentSessionResponse` | User |
| POST | `/api/v1/questionnaires/sessions/{id}/answer` | `SaveAnswerRequest` | `SaveAnswerResponse` | User |
| POST | `/api/v1/questionnaires/sessions/{id}/pause` | — | `SubmitSessionResponse` | User |
| POST | `/api/v1/questionnaires/sessions/{id}/resume` | — | `SubmitSessionResponse` | User |
| POST | `/api/v1/questionnaires/sessions/{id}/complete` | — | `SubmitSessionResponse` | User |
| GET | `/api/v1/questionnaires/sessions/{id}/progress` | — | `SessionProgressResponse` | User |
| GET | `/api/v1/questions` | Query params | `list[QuestionResponse]` | User |
| GET | `/api/v1/questions/search` | Query | `list[QuestionResponse]` | User |
| GET | `/api/v1/questionnaire/start` | Body | raw dict | User |
| GET | `/api/v1/questionnaire/resume/{id}` | — | raw dict | User |
| POST | `/api/v1/questionnaire/answer` | Body | raw dict | User |
| CMS CRUD | `/api/v1/cms/questions` | Body | Various | Admin |

### Issues

| Severity | Location | Issue |
|----------|----------|-------|
| **HIGH** | Legacy `questionnaire.py` endpoints | `/questionnaire/start`, `/questionnaire/answer`, etc. return raw dicts without consistent DTO serialization |
| **HIGH** | Duplicate endpoint paths | Two sets of endpoints (`/questionnaires/` and `/questionnaire/`) do overlapping things — confusion risk |
| **MEDIUM** | `questionnaire.py:91` | `GET /search` uses `Body("")` with GET request — should use Query parameter |
| **MEDIUM** | `questionnaires.py:32` | `QuestionnaireTemplateResponse.from_attributes(t)` — `from_attributes` is Pydantic v1 API; Pydantic v2 uses `model_validate` |
| **MEDIUM** | Missing error response models | No endpoints declare `responses` with error schemas in decorators |
| **LOW** | `Assessments` endpoint | Only has 1 route — could be merged into `questionnaires` |
| **LOW** | `questionnaire.py` endpoints | Uses generic `dict = Body(...)` instead of request DTOs |

---

## 7. Frontend Review (65/100)

### Verified Working

| Feature | Status |
|---------|--------|
| Vite build | ✅ Passes (3.75s) |
| TypeScript (questionnaire) | ✅ 0 errors |
| ESLint (questionnaire) | ✅ 0 errors |
| TanStack Query v5 API | ✅ Correct options-object syntax |
| Dark mode | ✅ Tailwind `dark:` variants throughout |
| Loading states | ✅ Skeleton placeholders |
| Error states | ✅ Error banners with retry |
| Empty states | ✅ Empty state for no templates, no sessions |
| Keyboard navigation | ✅ Enter for next, Shift+Enter for back |
| Responsive design | ✅ Grid layout adapts `md:` and `lg:` breakpoints |
| Auto-save indicator | ✅ Saving/saved/error states |
| Progress bar | ✅ Color-coded by completion % |

### Issues

| Severity | Location | Issue |
|----------|----------|-------|
| **MEDIUM** | `QuestionnaireSessionPage.tsx:154` | `score` prop hardcoded to `null` — score data not piped from backend to completion screen |
| **MEDIUM** | `useQuestionnaireSession.ts:22` | `questions` array only contains `session.current_question` — only 1 question visible at a time, review screen shows only current question |
| **MEDIUM** | `ReviewScreen.tsx:14-16` | Review unanswered check references local `questions` which is 1-element — only checks current question |
| **MEDIUM** | `SessionCard.tsx:78` | `formatDate` is displayed under "Updated" label but the grid cell says "Updated" — this is in the `grid grid-cols-3` which has "Answered", "Total", "Updated" — the third column shows a date, which should be labeled "Last Updated" not "Updated" |
| **LOW** | `QuestionnaireSessionPage.tsx:211` | `onSearch` function creates new array every render — should use `useCallback` |
| **LOW** | `SectionHeader` component | Imported but `groupName` and `groupDescription` are always `null` — no real data passed |
| **LOW** | Accessibility | No `aria-describedby` on form inputs, no `role="alert"` on error messages |
| **LOW** | `SessionCard.tsx:45` | Static "Session" label — should show template name |

---

## 8. Test Coverage Assessment (65/100)

### Unit Tests

| Suite | Tests | Pass Rate | Lines of Test Code |
|-------|-------|-----------|-------------------|
| Branching | 33 | 100% | 243 |
| Scoring | 16 | 100% | 139 |
| Validation | 36 | 100% | 191 |
| Domain | 1 | 100% (after `deactivate` fix) | — |
| **Total Engine Tests** | **86** | **100%** | **573** |

### Coverage Gaps

| Missing Test Area | Risk |
|-------------------|------|
| `QuestionnaireEngineImpl` (engine.py) | **HIGH** — `get_next_question`, `evaluate_branching`, `calculate_progress`, `validate_answer` not unit tested |
| `QuestionnaireService` (service.py) | **HIGH** — `start_session`, `save_answer`, `resume_session`, `pause_session`, `complete_session`, `get_session_progress` not tested |
| All SQL repository classes | **HIGH** — none of the 14 repository classes have tests |
| API endpoints | **HIGH** — no integration/API tests for any questionnaire endpoint |
| `QuestionnaireEngine` (`load_questions`, `get_next_question`) | **HIGH** — branching logic at engine level not integration-tested |
| Edge cases: empty templates, expired sessions, version mismatch | **MEDIUM** |
| `ModuleRegistry` (body systems) | **LOW** — discovery and registration not tested |
| Frontend components | **NONE** — no frontend tests exist at all |

---

## 9. Remaining Technical Debt

### Critical (Must Fix Before Production)

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| C1 | `find_by_questionnaire` ignores questionnaire_id filter | `sql_question_repository.py:53-62` | Returns all questions regardless of template — breaks questionnaire isolation |
| C2 | Authorization bypass in `has_role` calls | `deps.py:97,105` | Hardcoded role sets instead of user's actual roles — any authenticated user passes admin role checks |
| C3 | N+1 queries in score calculation and question listing | `questionnaire_service.py:324-345`, `questions.py:39-41`, `cms/questions.py:48-51` | O(n) DB calls per entity — will cause timeout on large assessments |
| C4 | No Alembic migrations for questionnaire tables | `alembic/versions/` | `create_all` is unsafe for production schema evolution |

### High (Fix Before Beta)

| # | Issue | Location |
|---|-------|----------|
| H1 | Duplicate legacy `/questionnaire/` endpoints with raw dict responses | `questionnaire.py` |
| H2 | Missing FK constraints across all questionnaire tables | All ORM models |
| H3 | ORM model imported in application service layer | `questionnaire_service.py:191` |
| H4 | Engine + Service duplicate instantiation of evaluators | `engine.py:38-41`, `questionnaire_service.py:43-45` |
| H5 | No integration tests for any service or repository | Entire `tests/` |
| H6 | Frontend `useQuestionnaireSession` only tracks 1 question | `useQuestionnaireSession.ts:22` |

### Medium (Address Within 3 Months)

| # | Issue | Location |
|---|-------|----------|
| M1 | `__import__("datetime")` pattern in CMS endpoints | `cms/questions.py` |
| M2 | Dynamic `__import__` for service class | `questions.py:96-99` |
| M3 | Missing cascade delete rules | All ORM relationship definitions |
| M4 | Missing composite indexes | `assessment_answers`, `question_dependencies`, `branch_rules` |
| M5 | `AssessmentProgressModel` unused ORM model | `models/assessment_progress.py` |
| M6 | `EvidenceReferenceModel` unused | `models/evidence_reference.py` |
| M7 | Empty `use_cases/`, `aggregates/`, `events/` packages | Application layer |
| M8 | `SectionHeader` component receives `null` group data | `QuestionnaireSessionPage.tsx:199-201` |
| M9 | No React.memo on frequently re-rendering components | `ProgressBar`, `AutoSaveIndicator` |
| M10 | Score not passed to completion screen | `QuestionnaireSessionPage.tsx:154` |

### Low (Nice-to-Have)

| # | Issue |
|---|-------|
| L1 | UUIDs stored as `String(32)` — `BINARY(16)` would be more efficient |
| L2 | 638 KB JS bundle — implement code-splitting |
| L3 | Default secret key and DB credentials in config |
| L4 | Missing `aria-*` accessibility attributes |
| L5 | `SessionCard` shows "Session" instead of template name |

---

## 10. Deployment Readiness Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| `.env` configuration | ⚠️ Default creds in code | Must override `secret_key`, DB, Redis, Firebase in production |
| Alembic migrations | ❌ Missing | Need migrations for all ~18 questionnaire tables |
| Docker compose | ❌ Not present | No Dockerfile or docker-compose.yml found |
| Health check endpoint | ✅ Present | `/api/v1/health` exists |
| Production logging | ✅ `core/logging.py` | Structured JSON logging configured |
| CORS configuration | ✅ Configurable via env | `cors_origin_list` property |
| Rate limiting | ⚠️ `rate_limit.py` exists | Not wired into questionnaire endpoints |
| Redis for sessions | ⚠️ Redis infrastructure exists | Not used for questionnaire sessions — sessions are DB-only |
| CI/CD pipeline | ❌ Not verified | No CI config in repo root |

---

## 11. Feature Completeness Audit

| Feature | Status | Evidence |
|---------|--------|----------|
| Question loading | ✅ | `load_questions` in engine.py, repository `find_active`/`find_by_questionnaire` |
| Body system registration | ✅ | `ModuleRegistry` + seed.py with 17 body systems |
| Adaptive branching | ✅ | `BranchingEvaluator` with AND/OR/NOT groups, condition trees |
| Dependency evaluation | ✅ | `DependencyEvaluator` with 13+ operators, computed fields |
| Rule evaluation | ✅ | `evaluate_branch_rules` with priority, is_active, condition trees |
| Session lifecycle | ✅ | draft → active → paused → completed → expired state machine |
| Auto-save | ✅ | `triggerAutoSave` with 3s debounce in `useQuestionnaireSession` |
| Resume | ✅ | `resume_session` endpoint + `SessionStatus.PAUSED` → `ACTIVE` |
| Scoring | ✅ | `ScoringEngine` with group/body-system/overall aggregation |
| Severity thresholds | ✅ | 5 levels: none/mild/moderate/severe/critical |
| Versioning | ✅ | `QuestionnaireVersion` entity + CMS version CRUD endpoints |
| Progress calculation | ✅ | `calculate_progress` with percentage, estimated remaining time |
| Validation | ✅ | `ValidationEngine` covering all 11+ question types |
| Report generation integration | ⚠️ | `complete_session` triggers scoring but no report entity linkage |

---

## 12. Detailed Scoring Breakdown

### Overall: 67/100

```
Architecture      ████████████░░░░░░  85  B
Security          ████████░░░░░░░░░░  60  C
Performance       ████████░░░░░░░░░░  55  C
Maintainability   ██████████░░░░░░░░  70  C+
Test Coverage     █████████░░░░░░░░░  65  C
Deployment        █████░░░░░░░░░░░░░  40  D
```

---

## 13. Summary and Next Steps

### What Works Well
- Clean Architecture with strict dependency inversion
- Domain entities are pure dataclasses with zero framework coupling
- Engine modules (branching, scoring, validation) are well-isolated, fully tested, and correct
- Frontend has good UX patterns (loading, error, empty states, dark mode, keyboard nav)
- Auto-save and resume flows are properly implemented
- Comprehensive question type coverage (13 types)
- 86 unit tests pass 100%

### Critical Path to Production

```
Week 1-2:    Fix C1 (questionnaire filter), C2 (auth bypass), C3 (N+1 queries)
             Write Alembic migrations for all questionnaire tables (C4)

Week 3-4:    Add FK constraints (H2), clean up duplicate endpoints (H1)
             Fix architecture violations (H3, H4)
             Remove __import__() hacks (M1, M2)

Week 5-6:    Write integration tests for services and repositories (H5)
             Add composite indexes (M4)
             Fix frontend single-question bug (H6)
             Pipe score data to completion screen (M10)

Week 7:      Performance optimization (React.memo, bundle splitting)
             Add Docker setup
             Security hardening (rate limiting, input sanitization)
             
Week 8:      Load testing, final security audit, documentation
             Production deployment
```

**Gate Criteria for Production:**
1. All Critical and High issues resolved
2. Integration test suite covers all service and repository methods
3. Load testing shows <500ms p95 response time for all endpoints
4. Security audit finds 0 authorization bypass vulnerabilities
5. Alembic migrations exist for all tables with rollback support
