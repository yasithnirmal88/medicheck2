# MediCheck AI — Phase 4: Longitudinal Risk Trajectory & AI Change Explanation

## 1. Executive Summary

Phase 4 adds a **deterministic longitudinal health trajectory** layer to
MediCheck. It compares a patient's completed deterministic assessments over
time, classifies trends (improving / stable / worsening / new / removed /
persistent) using explicit deterministic rules, and lets the AI explanation
layer **explain** — never decide — those observed changes.

The implementation is **additive**: no clinical scoring logic was replaced, no
database schema changed, no new infrastructure introduced. The trajectory is
computed purely from existing immutable, timestamped, trace-ID-bearing
deterministic assessment results/reports. The deterministic CDSE remains the
clinical source of truth; the AI is an explanation/extraction layer only.

**Results:** 286 backend tests pass (252 prior + 34 new), 59 frontend tests
pass (43 prior + 16 new), typecheck clean, build succeeds, zero regressions.

---

## 2. Existing Architecture Used

The audit (STEP 1) found that the existing schema fully supports trajectory
computation — **no new tables were required**:

| Existing table | Role in trajectory |
| --- | --- |
| `assessment_sessions` | Chronological ordering + ownership (user_id, completed_at, status) |
| `assessment_results` | CDSE output; `summary` carries `trace_id`; `created_at` |
| `activated_indicators` | Per-assessment activated indicator ids + float scores |
| `activated_conditions` | Per-assessment possible-condition ids + scores/confidence |
| `generated_recommendations` | Per-assessment recommendation ids |
| `health_assessments` | The report (session_id, user_id, created_at) |
| `body_system_assessments` | Per-report body-system category label + score |
| `condition_assessments` | Per-report possible-condition label + confidence |
| `generated_advices` | Per-report recommendation text |

**Reused Phase 1/2/3 patterns:**
- `AIExplanationProvider` Protocol pattern → mirrored as
  `LongitudinalExplanationProvider` (Protocol + deterministic stub).
- `EvidenceRetrievalService.retrieve(...)` (Phase 2 RAG) → reused unchanged for
  trajectory evidence grounding (deterministic; AI never chooses evidence).
- `bind_context()` allow-list validation pattern → mirrored in
  `LongitudinalExplanationResponse` (rejects hallucinated
  indicator/condition/recommendation/evidence ids).
- `_extract_trace_id()` pattern → reused for traceability.

**Gap closed:** the existing `ReportService.compare_reports()` only diffed row
IDs. Phase 4 introduces a proper `LongitudinalAnalysisService` that computes
score/severity deltas, trend classification, and structured change events.

---

## 3. Longitudinal Data Model

Defined in `backend/app/application/dtos/longitudinal_dtos.py`:

- `LongitudinalAssessmentPoint` — one completed assessment (assessment_id,
  session_id, trace_id, completed_at, overall_severity, body_systems,
  activated_indicators, possible_conditions, recommendations).
- `BodySystemPoint` — body_system_id, name, score (float), category (label).
- `TrajectoryComparison` — previous/current points + overall_change +
  body_system_changes + indicator/condition/recommendation change sets +
  change_events.
- `ChangeEvent` — scope, ref_id, label, previous/current value/score, delta,
  trend.
- `IndicatorChanges` / `ConditionChanges` / `RecommendationChanges` —
  new/resolved(removed)/persistent lists.
- `HealthTrajectory` — assessments[], comparisons[], sufficient_data, summary.
- `LongitudinalExplanationContext` — the deterministic context supplied to the
  AI (trace_ids, dates, all change sets, retrieved_evidence) with computed
  `allowed_*_ids` allow-lists.
- `LongitudinalExplanationResponse` — validated AI output with allow-list
  enforcement (rejects hallucinated ids).

No DB models were created — these are read-only DTOs derived from existing
rows.

---

## 4. Deterministic Change Engine

`backend/app/application/services/longitudinal_analysis_service.py` —
**independent of any LLM**.

Responsibilities:
1. Load the caller's most-recent N completed reports (bounded; `limit` clamped
   to 1–100, default 20) via the existing `list_reports_by_user` (DESC by
   `created_at`).
2. Re-order oldest→newest for chronological comparison.
3. Batch-load body-system names (single query).
4. For each report, load the matching `AssessmentResultModel` and build a
   `LongitudinalAssessmentPoint` (indicators/conditions/recommendations from
   the CDSE result; body-system category/score from the report).
5. Compare adjacent points:
   - **Body systems**: category-transition rank + conservative numeric delta
     (`SCORE_DELTA_THRESHOLD = 1.0`). Same rank + small delta → STABLE.
   - **Indicators**: set difference → new / resolved / persistent.
   - **Conditions**: set difference → new / removed / persistent.
   - **Recommendations**: set difference → new / removed / persistent.
   - **Overall**: highest-severity body-system category transition.
6. `compare_specific(user_id, prev_session, curr_session)` for arbitrary owned
   pairs (ownership-verified; cross-user → None → 404).

It never writes, never diagnoses, and never invents an overall numeric
"health score" (overall_severity is a categorical label only, read from
existing output).

---

## 5. Trend Classification

Explicit deterministic labels (`TrendLabel`) — the LLM never chooses these:

| Label | Meaning |
| --- | --- |
| `improving` | Severity rank decreased (or meaningful score decrease) |
| `stable` | Same category rank + delta below threshold |
| `worsening` | Severity rank increased (or meaningful score increase) |
| `new` | Entity present in current, absent in previous |
| `removed` | Entity absent in current, present in previous |
| `persistent` | Entity present in both |
| `insufficient_data` | < 2 completed assessments |

Classification uses the existing CDSE `ReportService` severity ordering
(`Normal < Monitor < Needs Attention < Recommend Screening < Urgent Medical
Review`) — derived from the existing threshold mapping, **not** invented
thresholds. Per the spec: categorical severity transitions are used because the
existing score semantics support them safely.

---

## 6. AI Explanation Architecture

`backend/app/application/services/longitudinal_explanation_service.py` — builds
on the Phase 1/2 provider abstraction, **not** a separate unrelated stack.

Pipeline (mirrors the spec's diagram):
```
Deterministic trajectory (LongitudinalAnalysisService)
  → relevant indicator/condition/recommendation ids
  → EvidenceRetrievalService (Phase 2, deterministic)
  → approved evidence allow-list
  → LongitudinalExplanationContext
  → LongitudinalExplanationProvider (Protocol → StubLongitudinalProvider)
  → parse + validate against allow-lists
  → LongitudinalExplanationResponse (or safe fallback)
```

**Safety boundaries enforced:**
- AI failure / validation failure → `trajectory_unavailable_fallback`
  (`available=False`); the deterministic trajectory remains fully available.
- Insufficient data (< 2 assessments) → AI is **not called**; a safe
  insufficient-data response is returned.
- Hallucinated indicator/condition/recommendation/evidence ids are **rejected**
  via `bind_context()` allow-list validation (same pattern as Phase 1/2).
- No PHI in the context (no names, emails, demographics, raw answers); only
  trace_ids, dates, change dicts, and already-allow-listed evidence.
- Non-diagnostic language guard (`assert_non_diagnostic`) rejects explanations
  that read as a diagnosis or prediction.

Provider: `backend/app/application/ai/longitudinal_provider.py`
(`LongitudinalExplanationProvider` Protocol + `StubLongitudinalProvider`
deterministic default — builds valid JSON strictly from the supplied context,
never invents entities/ids/evidence).

---

## 7. Evidence / RAG Integration

The existing Phase 2 `EvidenceRetrievalService.retrieve(...)` is reused
unchanged. Evidence retrieval is derived ONLY from the caller's deterministic
trajectory entities (their indicators/conditions/recommendations across the two
compared assessments), so:

- A user can never receive evidence from another patient's context.
- The retrieved evidence ids form the AI's citation allow-list; a hallucinated
  evidence id causes safe fallback.
- Retrieval failure never breaks the trajectory (caught → empty evidence → AI
  states none was available).

---

## 8. API Changes

All endpoints enforce `get_current_user` + ownership; trajectory is scoped to
the caller — no cross-user access.

| Endpoint | Purpose | Auth | Ownership | Data Source |
| --- | --- | --- | --- | --- |
| `GET /api/v1/trajectory?limit=N` | Deterministic trajectory (latest N) | Bearer token | caller-scoped | existing reports + CDSE results |
| `GET /api/v1/trajectory/compare/{prev}/{curr}` | Compare two specific owned assessments | Bearer token | verified per session (404 if not owned) | existing reports + CDSE results |
| `POST /api/v1/trajectory/explanation` | AI explanation of trajectory (defaults to latest two) | Bearer token | caller-scoped | deterministic trajectory + Phase 2 evidence |

Request body for explanation: `{"previous_session_id": "...",
"current_session_id": "..."}` (both optional). The deterministic trajectory is
always returned even when the AI is unavailable.

---

## 9. Frontend Changes

- `frontend/src/features/health-timeline/api/trajectoryService.ts` — typed API
  client + types mirroring backend DTOs.
- `frontend/src/features/health-timeline/hooks/useTrajectory.ts` — TanStack
  Query hooks (`useTrajectory`, `useTrajectoryExplanation`).
- `frontend/src/features/health-timeline/pages/TrajectoryPage.tsx` — new page
  with: assessment timeline, body-system score trend chart (recharts, existing
  dep), body-system change cards (with trend icons), finding changes (new /
  persistent / no-longer-detected / possible conditions / recommendations),
  AI explanation (clearly separated, labelled "AI-generated"), supporting
  evidence, disclaimer, and all empty states.
- `frontend/src/routes/router.tsx` — new route `/timeline/trajectory` (patient
  gated).
- `frontend/src/features/health-timeline/pages/TimelinePage.tsx` — added "View
  trajectory" link.
- `frontend/src/test/setup.ts` — added `ResizeObserver` stub (jsdom doesn't
  implement it; recharts needs it).

The UI clearly separates "AI Explanation" (indigo-bordered card, labelled)
from the deterministic "Clinical Assessment" sections, and the disclaimer
reads: *"AI-generated explanations summarize changes in your assessment
history. They do not diagnose conditions or replace professional medical
advice."*

---

## 10. Security

- Authentication: all endpoints reuse `get_current_user`.
- Patient ownership: trajectory query is caller-scoped; specific-pair compare
  verifies ownership per session (cross-user → 404, no leak).
- No cross-user trajectory access (verified by
  `test_patient_cannot_access_other_trajectory`,
  `test_cross_user_specific_compare_404`).
- No PHI sent to AI (context contains only trace_ids, dates, change dicts,
  allow-listed evidence).
- No auth tokens / env sent to AI (provider Protocol receives only the context).
- RBAC unchanged; no security modules modified.
- AI not called for unauthorized requests (401/403 before service) nor for
  insufficient data (provider.calls == 0).

---

## 11. Medical Safety

The system explicitly distinguishes **assessment finding / possible condition /
recommendation / confirmed diagnosis**. The stub provider and prompt enforce:
- Never states a disease is present/progressing/resolving.
- Never predicts future disease ("will develop", "chance of developing").
- Always labels conditions as "possible condition", never "diagnosis".
- Never upgrades certainty level.

Example acceptable output: *"Your cardiovascular assessment findings were
higher in severity across your recent assessments."* — NOT *"Your
cardiovascular disease is getting worse."*

---

## 12. Test Results

### Backend (`tests/test_longitudinal_phase4.py`) — 34 new tests
- Deterministic (15): two/three-assessment compare, body-system score changes,
  severity transitions, new/persistent/removed indicators, new/persistent/
  removed conditions, recommendation changes, no fabricated overall score,
  one-assessment insufficient-data, empty history, chronological ordering,
  same-date determinism.
- Security (5): own access, cross-user denied, unauthorized rejected, AI not
  called for unauthorized, cross-user specific compare 404.
- AI (14): valid explanation, hallucinated indicator/condition/recommendation/
  evidence rejected, AI-unavailable safe fallback, empty history does not call
  AI, insufficient-data safe response, prompt version preserved, trace ids
  preserved, evidence limited to allow-list, endpoint happy path, non-diagnostic
  language.

**Full backend suite: 286 passed (252 prior + 34 new), 0 failures, 0
regressions.**

### Frontend (`TrajectoryPage.test.tsx`) — 16 new tests
Loading, empty timeline, single assessment, multiple assessments, increasing /
decreasing / stable score, new / persistent / removed finding, AI unavailable,
AI success, evidence display, disclaimer, no-session AI-not-fetched.

**Full frontend suite: 59 passed (43 prior + 16 new), 0 failures. Typecheck
clean. Build succeeds.**

---

## 13. Performance

- Bounded loading: at most `limit` (default 20, max 100) most-recent reports per
  user — no full-history scan.
- Batched queries: body-system names loaded in a single `IN` query; the existing
  repositories already use `selectin` eager-loading for report relationships.
- No N+1: indicator/condition/recommendation ids come from the already-loaded
  `AssessmentResultModel` relationships.
- No new infrastructure (no Redis, vector DB, queues, or microservices).

---

## 14. Database Changes

**None.** No new tables, no migrations, no schema modifications. The trajectory
is derived read-only from existing immutable, timestamped, trace-ID-bearing
deterministic assessment results/reports. This preserves all clinical history
integrity.

---

## 15. Known Limitations

- The longitudinal AI ships with a deterministic stub provider (no external LLM
  configured). A real vendor provider can implement the
  `LongitudinalExplanationProvider` Protocol with no service-layer change.
- Body-system trend classification uses the existing severity category ordering
  (Normal→Urgent Medical Review) plus a conservative numeric delta; it does not
  invent new score semantics.
- The trajectory compares adjacent completed assessments; non-adjacent pairs are
  supported via the dedicated compare endpoint but the default trajectory view
  shows adjacent transitions.
- Evidence retrieval reuses Phase 2 semantics; if no eligible evidence exists,
  the AI states none was available (never fabricates).

---

## 16. Future Work

- **Phase 5 — Multilingual + Low-Literacy AI Clinical Intake**: English /
  Sinhala / Tamil / voice → speech-to-text feeding the same structured clinical
  pipeline. The Phase 4 architecture remains compatible (the core stays:
  natural language → structured observations → knowledge graph → questions →
  CDSE → report → trajectory → AI explanation).
- Wire a real longitudinal LLM vendor provider behind the Protocol.
- Add longitudinal SDG-3 measurement hooks (3.4 / 3.8 / 3.d) once baseline
  metrics are defined — without making unsupported impact claims.

---

## Acceptance Criteria — all met

- Existing deterministic assessment history reused ✅
- No clinical scoring logic replaced ✅
- Longitudinal comparison deterministic ✅
- Body-system / indicator / condition / recommendation trends work ✅
- Single- and multiple-assessment states work ✅
- AI explanation additive; cannot alter results / invent entities / invent
  evidence ✅
- Phase 2 evidence retrieval intact ✅
- Traceability intact (trace_ids + prompt_version preserved) ✅
- Patient ownership enforced ✅
- No PHI sent to AI ✅
- AI failure never breaks deterministic trajectory ✅
- Frontend clearly separates deterministic results from AI explanation ✅
- Existing tests pass; new tests cover the feature ✅
- No unnecessary infrastructure ✅
- Documentation complete ✅
