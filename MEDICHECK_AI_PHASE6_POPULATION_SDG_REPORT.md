# MediCheck AI — Phase 6: Population Health & SDG Analytics Foundation

**Status:** Complete
**Date:** 2026-08-10
**Constraints honored:** No clinical decision engine changes · No database schema migrations · No LLM APIs · AI is explanation/extraction layer only · Multilingual EN/SI/TA (SDG 3.8)

---

## 1. Objective

Provide a privacy-preserving, de-identified population health analytics layer on top of existing Phase 1–5 data, aligned to UN Sustainable Development Goal (SDG) health indicators (3.4, 3.8, 3.d, 10). The layer surfaces aggregate trends for authorized research/medical-director users without exposing any patient-level data.

## 2. Architecture

```
React AnalyticsDashboardPage
  └─ TanStack Query hooks (useAnalyticsQueries.ts)
       └─ analyticsApi.ts (axios /api/v1/analytics/*)
            └─ FastAPI analytics router (5 routes)
                 └─ PopulationAnalyticsService (aggregation + privacy)
                      └─ SQLAlchemy async queries (SQL-level GROUP BY/COUNT)
```

All aggregation happens in SQL (`func.count`, `func.sum`, `GROUP BY`). No patient rows are loaded into application memory.

## 3. Backend Implementation

### 3.1 Permission (RBAC)

- Added `Permission.ANALYTICS_READ_POPULATION` to `app/core/security/rbac.py`.
- Granted to: `RESEARCH_REVIEWER` (level 5), `MEDICAL_DIRECTOR` (level 30), `SUPER_ADMIN` (level 40).
- Denied to: `PATIENT`, `DOCTOR`, roleless users — defense in depth.
- Dependency: `get_analytics_user` in `app/api/deps.py` — checks the user has the permission via `has_role()` (level >= 5).

### 3.2 Service Layer (`population_analytics_service.py`)

| Method | Purpose | Privacy |
|--------|---------|---------|
| `get_overview` | Total/completed/in-progress assessments, unique participants, completion rate | Completion rate suppressed if cohort < k=10 |
| `get_severity_distribution` | Assessment findings by category (Normal/Monitor/Needs Attention/Recommend Screening/Urgent Medical Review) | Per-bucket suppression; disclaimer: "not population prevalence" |
| `get_body_systems` | Assessment counts per body system | Suppression per system |
| `get_indicator_trends` | Clinical indicator activation counts | Suppression per indicator; disclaimer: "not confirmed diagnosis" |
| `get_trajectory` | Phase 4 trend labels (improving/stable/worsening/new/resolved) | Suppression per trend; disclaimer: "not proof of disease progression" |
| `get_accessibility` | Phase 5 language/input_type (voice vs text) counts | Suppression per language; disclaimer: "do not infer demographics" |
| `get_sdg_dashboard` | Aggregated SDG-aligned metrics | Per-metric suppression; disclaimer: "do not prove SDG achievement" |

### 3.3 Small-Cell Suppression (k-anonymity)

- Threshold `k=10` (configurable in `config.py`).
- Any cohort smaller than k reports `suppressed: true` and `value: null` / `count: 0`.
- Prevents re-identification of rare conditions or small demographic groups.

### 3.4 De-Identification

- No `user_id`, `email`, `session_id`, or `firebase_uid` appears in any response.
- All responses contain only aggregate counts, percentages, and de-identified entity names (body systems, indicators).
- Tests verify no patient identifiers leak (string scan of full JSON response).

### 3.5 Date-Range Validation

- Maximum range: 365 days (configurable).
- Inverted ranges (end < start) rejected with HTTP 400.
- Over-large ranges rejected with HTTP 400.

## 4. API Endpoints

| Route | Method | Permission | Returns |
|-------|--------|------------|---------|
| `/api/v1/analytics/overview` | GET | `ANALYTICS_READ_POPULATION` | Overview metrics + trend time series |
| `/api/v1/analytics/severity` | GET | `ANALYTICS_READ_POPULATION` | Severity distribution |
| `/api/v1/analytics/body-systems` | GET | `ANALYTICS_READ_POPULATION` | Body system assessment counts |
| `/api/v1/analytics/indicators` | GET | `ANALYTICS_READ_POPULATION` | Indicator activation trends |
| `/api/v1/analytics/trajectory` | GET | `ANALYTICS_READ_POPULATION` | Phase 4 trajectory distribution |
| `/api/v1/analytics/accessibility` | GET | `ANALYTICS_READ_POPULATION` | Phase 5 language/voice metrics |
| `/api/v1/analytics/sdg` | GET | `ANALYTICS_READ_POPULATION` | SDG-aligned dashboard |

All routes accept optional `start_date`, `end_date`, `body_system_id`, `language`, `input_type` query params.

## 5. Phase 4/5 Integration

### Phase 4 (Longitudinal Trajectory)
- `get_trajectory` reuses the Phase 4 `TrendLabel` enum (improving/stable/worsening/new/resolved).
- Trajectory is computed from sequential assessments per user, then aggregated.
- Disclaimer: "A worsening trajectory is an assessment trend, not proof of disease progression."

### Phase 5 (Multilingual + Voice Intake)
- `ai_intake.py` was extended (minimal additive change) to persist `language` and `input_type` to `session.extra_metadata` (existing JSON column — no migration).
- `get_accessibility` reads these fields via SQL JSON extraction (`extra_metadata["language"].as_string()`).
- SDG 3.8 (Universal Health Coverage & Access) section surfaces:
  - Completion rate by language (EN/SI/TA)
  - Voice vs text intake counts (accessibility modality)
  - Disclaimer: "Language is a user preference; do not infer demographics."

## 6. SDG Dashboard Sections

| Goal | Title | Metrics |
|------|-------|---------|
| SDG 3.4 | NCD Prevention & Risk Reduction | NCD-related assessment activity, severity distribution, trajectory trends |
| SDG 3.8 | Universal Health Coverage & Access | Completion rate, language coverage, voice accessibility |
| SDG 3.d | Health Emergency Readiness | Assessment volume trend, body system coverage |
| SDG 10 | Reduced Inequalities | Language distribution equity, accessibility modality equity |

All metrics are platform-derived monitoring indicators — they do not prove SDG achievement.

## 7. Frontend Implementation

### 7.1 API Layer (`analyticsApi.ts`)
- Typed interfaces for all 7 endpoints.
- Axios client with `baseURL=/api/v1` (no double-prefix bug).

### 7.2 Hooks (`useAnalyticsQueries.ts`)
- 7 TanStack Query hooks, one per endpoint.
- Query keys include filters for cache invalidation.

### 7.3 Dashboard Page (`AnalyticsDashboardPage.tsx`)
- Route: `/cms/analytics` (under DoctorLayout, requires CMS access at UX level, backend enforces RESEARCH_REVIEWER+).
- Nav item: "Population Analytics" with BarChart3 icon, in the Overview group.
- Sections:
  1. Overview metric cards (total/completed/participants/completion rate)
  2. Severity distribution bar chart
  3. Trajectory distribution bar chart (Phase 4)
  4. Accessibility metrics (Phase 5 — voice count, language count)
  5. SDG dashboard grid (4 goal cards)
- Language filter dropdown (All/EN/SI/TA) — passes filter to all queries.
- Suppressed cohorts show a "Suppressed" badge instead of a count.
- All disclaimers rendered in italic text below each section title.

## 8. Testing

### 8.1 Backend Tests (`test_population_analytics_phase6.py` — 22 tests)
- RBAC: patient/roleless/doctor denied (403); research_reviewer/medical_director/super_admin allowed (200).
- De-identification: no patient identifiers in any response.
- Small-cell suppression: cohort < k reports suppressed; cohort >= k reports value.
- Disclaimers present on all 5 response types.
- Phase 4 trend labels present in trajectory.
- Phase 5 voice vs text counts correct.
- SDG dashboard has all 4 goal sections + metrics.
- Date-range validation: inverted and over-large ranges rejected.
- Phase 5 language persistence to `extra_metadata` verified.

### 8.2 Frontend Tests (`AnalyticsDashboardPage.test.tsx` — 7 tests)
- Page title and overview metrics render.
- Severity distribution with disclaimer renders.
- Suppressed badges appear for small cohorts.
- Trajectory distribution with disclaimer renders.
- Accessibility metrics with disclaimer render.
- SDG dashboard sections render.
- Language filter dropdown present.

### 8.3 Regression
- All existing backend tests pass (intake, roles, longitudinal, CMS recovery).
- All existing frontend tests pass (69 tests).
- Typecheck clean. Build succeeds.

## 9. Performance

- All queries use SQL-level aggregation (`GROUP BY`, `COUNT`, `SUM`) — no N+1.
- All queried columns are indexed: `user_id`, `status`, `started_at`, `session_id`, `body_system_id`, `condition_id`, `assessment_id`.
- Date-range filtering uses `started_at` (indexed).
- Result sets are small (aggregated rows only).

## 10. Constraints Compliance

| Constraint | Status |
|-----------|--------|
| No clinical decision engine changes | ✅ Engine untouched |
| No database schema migrations | ✅ Uses existing `extra_metadata` JSON column |
| No LLM APIs | ✅ AI is explanation layer only; analytics is pure aggregation |
| AI is explanation/extraction only | ✅ Analytics extracts/counts existing data |
| Multilingual EN/SI/TA (SDG 3.8) | ✅ Language metrics from Phase 5 sessions |
| FastAPI/Python backend | ✅ |
| React/TypeScript frontend | ✅ |

## 11. Files Changed/Created

### Backend (new)
- `app/application/dtos/analytics_dtos.py`
- `app/application/services/population_analytics_service.py`
- `app/api/v1/endpoints/analytics.py`
- `tests/test_population_analytics_phase6.py`

### Backend (modified)
- `app/core/config.py` — analytics settings
- `app/core/security/rbac.py` — `Permission.ANALYTICS_READ_POPULATION`
- `app/api/deps.py` — `get_analytics_user`
- `app/api/v1/router.py` — registered `analytics_router`
- `app/api/v1/endpoints/ai_intake.py` — persist language/input_type to `extra_metadata`

### Frontend (new)
- `src/features/analytics/api/analyticsApi.ts`
- `src/features/analytics/hooks/useAnalyticsQueries.ts`
- `src/features/analytics/pages/AnalyticsDashboardPage.tsx`
- `src/features/analytics/components/__tests__/AnalyticsDashboardPage.test.tsx`

### Frontend (modified)
- `src/routes/router.tsx` — `/cms/analytics` route
- `src/layouts/DoctorLayout.tsx` — nav item + BarChart3 icon import

## 12. What This Enables

This Phase 6 foundation gives healthcare researchers and medical directors a privacy-preserving window into population health trends — without ever exposing individual patient data. It surfaces SDG-aligned indicators that can inform public health resource allocation, NCD screening program effectiveness, and digital health accessibility — all derived from existing clinical assessment data that was already being collected.
