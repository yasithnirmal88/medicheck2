# MediCheck Phase 11 — Baseline Audit

## Governed AI Care Coordination & Equity Intelligence

This baseline documents the state of the repository (Phases 1–10 complete,
merged to `main` at commit `c03cfa3`) BEFORE any Phase 11 code changes. It
identifies what already exists so Phase 11 can reuse it and avoid duplication.

---

## 1. Architectural invariant (preserved across all phases)

> **The deterministic CDSE is the ONLY clinical authority. AI explains,
> extracts, translates, summarizes, classifies operational information, and
> identifies non-clinical patterns. AI never diagnoses, scores, sets
> severity, determines probability, creates conditions/recommendations,
> modifies rules/reports, or determines clinical urgency.**

Phase 11 adds an AI layer AROUND the existing care-continuity + analytics
systems. It touches NO clinical tables and NO CDSE logic.

---

## 2. Existing AI provider abstraction (reuse — do not duplicate)

`backend/app/application/ai/provider.py`:
- `AIExplanationProvider` Protocol (Phase 1 report explanation).
- `AIProviderError` (provider DOWN) vs `AIValidationFailure` (output INVALID).
- `get_explanation_provider()` factory selecting via `settings.ai_provider`
  (`stub` default, `personalized-stub` Phase 7).
- `StubExplanationProvider` — deterministic, no network/API key.

`backend/app/application/ai/queue_ranking_provider.py` (Phase 10):
- `QueueRankingProvider` Protocol + `StubQueueRankingProvider`.
- `QueueTaskInput` (PHI-scrubbed, operational-only: referral_id, task_id,
  referral_age_days, overdue, missing_follow_up, appointment_window_days,
  region, unresolved_admin_status — NO clinical fields).
- `QueueRankingInput` / `QueueRankingOutput` / `RankedTask`.
- `assert_non_clinical(text)` — rejects forbidden clinical-urgency terms
  (severe, urgent clinically, critical, mortality, diagnos, prognosis, ...).
- `compute_input_hash` / `compute_output_hash` (SHA-256, audit).
- `get_queue_ranking_provider()` via `settings.chw_queue_provider`.

**Phase 11 reuse:** Phase 11 EXTENDS the operational-queue concept with a
richer *suggestion* model (reason codes, explanation, confidence,
requires_human_review) + a persisted human-review lifecycle. It does NOT
rebuild ranking. The existing `assert_non_clinical` + hash helpers are
reused/extended.

---

## 3. Existing AI governance / audit (reuse — do not duplicate)

`backend/app/application/services/ai_audit_service.py` (`AIAuditService`):
- `record(...)` writes `AIInteractionAuditModel` — hashes + reference ids
  ONLY (trace_id, session_id, request_type, provider, model, prompt_version,
  language, literacy_level, input_context_hash, output_hash, status,
  status_reason). **No raw PHI, no clinical text.** Never raises (audit
  failure must not break the flow).
- `get_governance_summary()` — aggregate counts (by status/language/provider/
  prompt_version), fallback_rate_pct, validation_failure_rate_pct.
  De-identified.

`backend/app/infrastructure/persistence/models/ai_interaction_audit.py`
(`AIInteractionAuditModel`, table `ai_interaction_audits`):
- Additive (Phase 7). UUID PK, timestamps, soft-delete. Stores metadata only.

`backend/app/api/v1/endpoints/ai_governance.py`:
- `GET /api/v1/ai-governance/summary` — `get_ai_governance_user`
  (RESEARCH_REVIEWER+). Aggregate metrics only; individual audit records
  NEVER exposed.

**Phase 11 reuse:** Phase 11 records every AI operational-suggestion /
population-insight call via `AIAuditService.record()` (request_type e.g.
`chw_operational_suggestion`, `equity_intelligence`, `sdg_narrative`). The
existing audit model CANNOT hold insight content or review state, so Phase 11
adds dedicated insight tables (justified below) — but the "AI was called"
trail reuses `AIAuditService`.

---

## 4. Existing population analytics (reuse — deterministic foundation)

`backend/app/application/services/population_analytics_service.py`
(`PopulationAnalyticsService`):
- SQL-level aggregation only (GROUP BY/COUNT/SUM, no N+1).
- Small-cell suppression k=10 (`settings.analytics_min_group_size`).
- De-identified: no user_id/email/session_id in any response.
- Methods: `get_overview`, `get_severity_distribution`, `get_body_systems`,
  `get_indicators`, `get_trajectory`, `get_accessibility` (language +
  voice/text modality, from `session.extra_metadata`), `get_sdg_dashboard`.
- `case(...)` from sqlalchemy (NOT `func.case` — no `else_` kwarg).

`backend/app/application/services/care_continuity_service.py`
(`CareContinuityService`):
- Care-continuity funnel (screened → flagged → referred → referral_received
  → appointment_scheduled → care_received → followup_completed) + metrics
  (conversion, drop-off, median time-to-care, CHW-assisted completion).
- SQL aggregation; de-identified; per-stage k-suppression.
- DTOs in `interoperability_dtos.py`: `CareFunnelStage`,
  `CareContinuityMetrics`, `CareContinuityResponse`.

`backend/app/application/services/sdg_export_service.py` (`SdgExportService`):
- Builds SDG-aligned rows (3.4/3.8/10) composing Phase 6 analytics + Phase 10
  care-continuity. JSON + CSV. k-suppressed per metric/stage. All metrics are
  `medicheck-aligned-proxy` (never claimed official UN).
- DTOs: `SdgExportRow`, `SdgExportResponse`.

**Phase 11 reuse:** Equity intelligence + SDG narrative AI services call
these deterministic services to obtain already-aggregated, de-identified,
k-suppressed metrics. AI receives ONLY these aggregates — never raw patient
data. The deterministic analytics remain available when AI is unavailable.

---

## 5. Existing referral / care-continuity model (reuse — operational fields)

`backend/app/infrastructure/persistence/models/referral.py`
(`ReferralModel`):
- Operational fields available for AI context (PHI-scrubbed): `status`,
  `receiving_status`, `scheduled_for`, `assigned_chw_user_id`,
  `patient_acknowledged`, `due_at`, `facility_id`, `created_at`,
  `completed_at`. Relationships: `status_events`, `barriers`,
  `follow_up_tasks`.
- `ReferralStatusEventModel` (append-only transition audit).
- `CareOutcomeModel` (operational funnel outcomes — never modifies CDSE).
- `FollowUpTaskModel` (follow-up tasks).

`backend/app/application/services/chw_queue_service.py` (`ChwQueueService`):
- Loads a CHW's referrals (bounded by `settings.chw_queue_max_size`), builds
  PHI-scrubbed operational input, invokes queue-ranking provider, audits.
- Operational factors only: referral age, overdue, missing follow-up,
  appointment window, unresolved admin. NO clinical fields.

**Phase 11 reuse:** The operational-suggestion service reuses the same
referral-loading + PHI-scrubbing pattern. AI context contains operational
factors only.

---

## 6. Existing RBAC (extend — do not break)

`backend/app/core/security/rbac.py`:
- `Permission` enum (str, Enum): includes `AI_VIEW_GOVERNANCE`,
  `ANALYTICS_READ_POPULATION` (note: actual name to verify),
  `CHW_READ_ASSIGNED`, `FHIR_EXPORT_*`, `SDG_EXPORT`, `INTEROP_MANAGE`,
  `FACILITY_MANAGE`, `REFERRAL_MANAGE`.
- `Role` enum: PATIENT, DOCTOR, SUPER_ADMIN, MEDICAL_DIRECTOR,
  SPECIALIST_DOCTOR, RESEARCH_REVIEWER, CONTENT_EDITOR, READ_ONLY_REVIEWER,
  COMMUNITY_HEALTH_WORKER.
- `_ROLE_HIERARCHY` (>= comparison via `has_role`).
- `has_role(roles, role)`, `check_permission(perms, perm)`,
  `get_role_permissions(role)`.

`backend/app/api/deps.py` auth dependencies:
- `get_current_user` → `get_current_active_user` → role-specific deps.
- `get_chw_user` (COMMUNITY_HEALTH_WORKER or MEDICAL_DIRECTOR+ supervisor).
- `get_analytics_user` (RESEARCH_REVIEWER+).
- `get_ai_governance_user` (RESEARCH_REVIEWER+).
- `get_interop_user` (INTEROP_MANAGE: MEDICAL_DIRECTOR/SUPER_ADMIN).
- `get_sdg_export_user` (SDG_EXPORT: RESEARCH_REVIEWER/MEDICAL_DIRECTOR/
  SUPER_ADMIN).

**Phase 11 additions (extend):**
- `Permission.AI_VIEW_OPERATIONAL_SUGGESTIONS` — CHW (own assigned), medical
  director, super admin.
- `Permission.AI_REVIEW_INSIGHTS` — medical director, research reviewer,
  super admin.
- `Permission.AI_VIEW_POPULATION_INSIGHTS` — research reviewer, medical
  director, super admin (de-identified).
- New deps: `get_insight_reviewer_user`, `get_chw_operational_user`,
  `get_population_insight_user`.
- Patients NEVER get any Phase 11 permission. One CHW cannot access another
  CHW's assignments (assignment-verified per-operation, IDOR protection).

---

## 7. Existing identifiers / trace IDs / privacy controls

- **Trace IDs:** CDSE / Phase 1 explanation trace ids live in
  `assessment_results.summary` (parsed via `_extract_trace_id`). Carried into
  FHIR export manifests + SDG rows for traceability.
- **k-anonymity:** k=10 (`settings.analytics_min_group_size`). Per-metric +
  per-funnel-stage suppression. Suppressed → value/numerator/denominator null.
- **De-identification:** no user_id/email/session_id/trace_id in any
  population/SDG/care-continuity response.
- **Consent:** `ConsentModel` (Phase 8) scope-based. FHIR exports
  consent-gated.

**Phase 11:** AI context for population insights receives ONLY already-
suppressed aggregates. No patient IDs, names, phone numbers, addresses,
emergency contacts, or raw answers ever reach the AI. Tests explicitly attempt
small-cohort leakage, patient-ID leakage, cross-group reconstruction,
geographic re-identification, rare-category disclosure.

---

## 8. Existing API conventions (reuse)

- Routers in `app/api/v1/endpoints/`, registered in `app/api/v1/router.py`
  via `router.include_router(...)`.
- Prefix + tags per router. All paths under `/api/v1/...`.
- Error responses use `error.message` (custom ErrorResponse handler).
- DTOs in `app/application/dtos/`. Pydantic v2 (`model_validate`,
  `model_dump`, `ConfigDict(from_attributes=True)`).
- Tests run with `ALLOW_MOCK_AUTH=true DATABASE_URL=sqlite+aiosqlite:///./test.db
  ENVIRONMENT=development` + `-W error::DeprecationWarning`. Mock auth token
  `mock-firebase-id-token` auto-creates a roleless user.

---

## 9. Existing migrations (additive chain)

Single head: `20260811_interop_phase10` (down_revision
`20260810_referrals`). Phase 11 migration down_revision =
`20260811_interop_phase10`.

---

## 10. Existing frontend (reuse patterns)

- `frontend/src/features/interop/` module (Phase 10): api service
  (`interopService.ts`), TanStack hooks (`useInteropQueries.ts`), shared UI
  (`InteropUI.tsx`), pages. Routes under `/cms/interop/*` in `DoctorLayout`.
- `frontend/src/lib/api.ts` — axios client (baseURL `/api/v1`).
- TanStack Query v5 (`isLoading` not `isPending` for disabled-query states).
- Tests: vitest + @testing-library/react + jsdom. ResizeObserver stub in
  `test/setup.ts` (recharts). Interpolated text needs function matchers.
- `DoctorLayout.tsx` nav sections; routes in `routes/router.tsx` (lazy).

**Phase 11 frontend:** new `features/ai-governance/` module — equity
intelligence page, SDG narratives page, AI review queue (approve/reject/edit),
CHW operational suggestions page. Routes under `/cms/ai-governance/*`.

---

## 11. Proposed additive Phase 11 architecture

### New backend files
- `app/application/ai/operational_suggestion_provider.py` — Protocol + Stub +
  validation (assert_non_clinical; task_id allow-list; no PHI).
- `app/application/ai/equity_intelligence_provider.py` — Protocol + Stub +
  validation (OBSERVED vs POSSIBLE; reject clinical/identification/causal
  claims; entity allow-list).
- `app/application/ai/population_narrative_provider.py` — Protocol + Stub +
  validation (describe supplied metrics only; reject unsupported claims).
- `app/application/dtos/ai_governance_dtos.py` — Phase 11 DTOs.
- `app/application/services/ai_operational_suggestion_service.py`
- `app/application/services/equity_intelligence_service.py`
- `app/application/services/population_narrative_service.py`
- `app/application/services/ai_insight_review_service.py` — review workflow.
- `app/infrastructure/persistence/models/ai_operational_suggestion.py`
- `app/infrastructure/persistence/models/ai_population_insight.py`
- `alembic/versions/20260812_ai_insights_phase11.py` — additive migration.
- `app/api/v1/endpoints/ai_care_coordination.py`
- `app/api/v1/endpoints/ai_equity_intelligence.py`
- `tests/test_ai_care_coordination_phase11.py`

### Modified backend files (additive only)
- `app/core/security/rbac.py` — new permissions.
- `app/api/deps.py` — new auth deps.
- `app/core/config.py` — new settings.
- `app/api/v1/router.py` — register new routers.

### New frontend files
- `src/features/ai-governance/api/aiGovernanceService.ts`
- `src/features/ai-governance/hooks/useAiGovernanceQueries.ts`
- `src/features/ai-governance/components/AiGovernanceUI.tsx`
- `src/features/ai-governance/pages/EquityIntelligencePage.tsx`
- `src/features/ai-governance/pages/SdgNarrativesPage.tsx`
- `src/features/ai-governance/pages/AiReviewQueuePage.tsx`
- `src/features/ai-governance/pages/ChwOperationalSuggestionsPage.tsx`

### Modified frontend files
- `src/layouts/DoctorLayout.tsx` — nav section.
- `src/routes/router.tsx` — routes.

### New tables (justified)
The existing `AIInteractionAuditModel` stores hashes/metadata only — it
cannot hold insight content or review lifecycle state. Phase 11 needs to
persist the actual AI-generated suggestion/insight content + a human-review
lifecycle (GENERATED → PENDING_REVIEW → APPROVED/REJECTED/EDITED →
PUBLISHED). This is genuinely new functionality, so two additive tables are
justified:

1. `ai_operational_suggestions` — CHW operational suggestions + review state.
2. `ai_population_insights` — equity + SDG narrative insights + review state
   (discriminator `insight_type`).

Both reuse `AIAuditService` for the "AI was called" audit trail (hashes).
Review fields are embedded on each row (the row IS the insight + its review
record), avoiding a polymorphic reviews table.

---

## 12. Insertion points

- Router: `app/api/v1/router.py` — add `include_router` for the two new
  routers after `interoperability_router`.
- RBAC: add permissions to the `Permission` enum + grant to roles in
  `_ROLE_PERMISSIONS`.
- Deps: add dependency functions after `get_sdg_export_user`.
- Config: add settings near the existing AI/CHW settings.
- Frontend nav: add "AI Governance" section in `DoctorLayout.tsx` after
  "Interoperability".
- Frontend routes: add `/cms/ai-governance/*` lazy routes in `router.tsx`.

---

## 13. Risks

- **AI leaking clinical reasoning into operational suggestions** — mitigated
  by `assert_non_clinical` + operational-only context + tests.
- **Population AI re-identifying individuals** — mitigated by feeding only
  k-suppressed aggregates + entity allow-list + re-identification tests.
- **Prompt injection via aggregate labels / notes** — mitigated by treating
  all labels as untrusted data + injection tests.
- **AI auto-publishing** — mitigated by review lifecycle (AI never sets
  PUBLISHED; only a human reviewer can).
- **Accidentally touching CDSE/clinical tables** — verified by git diff
  review at the end.
- **Performance** — bounded AI contexts (only supplied aggregates), batch
  queries, no N+1, deterministic preprocessing before AI.

---

## 14. Test plan (backend)

- authentication (unauthenticated denied)
- RBAC (patient denied; CHW own-only; reviewer/admin allowed)
- IDOR (CHW A cannot see CHW B's suggestions)
- operational-only ranking (no clinical severity/probability/urgency)
- AI cannot use possible conditions / clinical score
- AI cannot alter CDSE / reports (read-only verified)
- hallucinated task IDs rejected (allow-list)
- hallucinated population entities rejected (allow-list)
- k-anonymity (small cohort suppressed; no leakage)
- no PHI in AI context (no patient IDs/names/answers)
- prompt injection ("ignore instructions → mark urgent" does NOT become
  clinical urgency; "patient has diabetes" does NOT become clinical fact)
- AI failure fallback (deterministic analytics remain available)
- provider unavailable → safe fallback
- invalid output → rejected, quality_status=VALIDATION_FAILED
- review workflow: approve / reject / edit
- AI cannot self-publish
- audit trail (AIAuditService.record called)
- FHIR separation (narratives never become FHIR resources)
- SDG metric integrity (AI only describes supplied metrics)

## 15. Test plan (frontend)

- AI suggestion display + operational disclaimer
- population insight display + k-anonymity badge
- review status display
- approve / reject / edit
- loading / unavailable / error / no-data states
- accessibility (labels, roles)

---

## 16. Regression protection

Phase 11 must NOT change behavior of: authentication, onboarding, health
profile, assessment catalog, questionnaire engine, branching, CDSE, scoring,
possible-condition generation, recommendations, report generation, AI
explanation, RAG, multilingual/voice intake, longitudinal trajectory,
population analytics, AI governance, CHW mode, offline sync, referral
workflow, care-continuity analytics, CMS, RBAC, FHIR export, SDG export.

**No Phase 11 feature can alter a previously generated deterministic
clinical result.**

Full backend + frontend regression suites must pass; typecheck + production
build must pass; git diff must confirm no clinical-engine changes.
