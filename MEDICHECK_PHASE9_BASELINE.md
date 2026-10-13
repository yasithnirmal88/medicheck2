# MediCheck Phase 9 — Read-Only Forensic Baseline (Step 1)

Produced before any Phase 9 source modification. All contracts verified directly
from source code, not documentation.

## 1. Verified baselines

| Suite | Status | Count |
|---|---|---|
| Backend tests (Phase 8 subset verified) | PASS | 23 (test_chw_phase8.py) |
| Backend CMS/auth regression subset | PASS | 36 |
| Frontend vitest | PASS | 86 (84 pre-existing + 4 role-chw fixed) |
| Frontend typecheck | clean | — |

Full backend suite (368 tests) was not re-run in this pass (several files are
slow ~1–2 min each); the Phase 8 + CMS/auth regression subset is green. Full
suite will be run in Step 10 final regression.

## 2. Clinical core — existing contracts (DO NOT modify)

### Clinical Decision Service (CDSE)
- `app/application/services/clinical_decision_service.py`
- `process_assessment(session_id, user_id)` → produces `AssessmentResultModel` +
  `ActivatedIndicatorModel` + `ActivatedConditionModel` +
  `GeneratedRecommendationModel` + `GeneratedLaboratoryTestModel` +
  `ExplanationRecordModel`.
- **trace_id**: `uuid.uuid4().hex[:16]` generated per assessment. Stored
  *inline* in `ExplanationRecordModel.text` as `"[trace:{trace_id}] ..."` and
  in the result `summary` JSON string. **There is no dedicated trace_id column.**
  Phase 9 must extract trace_id from the summary/notes, not assume a column.
- Recommendation source recorded as `GeneratedRecommendationModel.source` =
  `"condition:{cid}"` and `.notes` = `"[trace:{trace_id}] Score {sc} ..."`.

### Recommendation model — THE key referral-eligibility signal
- `app/infrastructure/persistence/models/recommendation.py` — `RecommendationModel`
- Fields: `key`, `body_system_id`, `disease_id`, `category` (String(100)),
  `title`, `text`, `priority` (int), `urgency` (String(20)), `evidence_level`,
  `is_active`, `version`, `status`.
- **`category` is CMS-authored and seeded with**: `referral`, `testing`,
  `monitoring`, `medication`, `lifestyle`, `education`.
- **`urgency` seeded with**: `routine`, `urgent`. (No `emergency` in seed data,
  though the domain entity default is `routine`.)
- **GAP (resolved without schema change)**: There is no boolean
  `is_referral_eligible` field. The safe, deterministic eligibility signal is
  `category == "referral"` (CMS-controlled). Phase 9 will also treat `testing`
  and `monitoring` categories as follow-up-eligible (lab/imaging/monitoring
  follow-up), mapping to referral types `laboratory`/`imaging`/`follow_up_assessment`.
  This is documented in `ReferralEligibility` and is the **only** eligibility
  rule. AI never participates in eligibility. No recommendation schema change
  required — this is the documented gap resolution.

### Report service
- `app/application/services/report_service.py` — `generate_report(session_id, user_id)`
  → `HealthAssessmentModel` + `BodySystemAssessmentModel` +
  `ConditionAssessmentModel` + `LifestyleAssessmentModel` +
  `GeneratedAdviceModel`.
- `GeneratedAdviceModel.recommendation_id` + `.category` link back to the
  originating recommendation. **This is the join point** for referral creation:
  a referral is derived from a `GeneratedRecommendationModel` (CDSE output) which
  references a `RecommendationModel` (CMS content) with an eligible `category`.
- Reports are owned by `user_id`; `get_report`/`get_report_by_session` enforce
  ownership. Phase 9 referrals reuse this ownership pattern.

### Traceability chain (verified)
```
AssessmentSessionModel (id, user_id)
  → AssessmentResultModel (session_id, user_id, summary[trace_id], confidence_score)
    → GeneratedRecommendationModel (result_id, recommendation_id, source, notes[trace_id])
      → RecommendationModel (id, category, urgency, title, text)  [CMS content]
  → HealthAssessmentModel (session_id, user_id)  [the "report"]
    → GeneratedAdviceModel (assessment_id, recommendation_id, category)
```
A referral traces: `assessment_session → result → generated_recommendation →
recommendation(CMS) → referral`. trace_id is carried from the result summary.

## 3. Phase 8 CHW infrastructure (REUSE, do not duplicate)

### Models (additive, all verified importing cleanly)
- `chw_assignment.py` → `ChwAssignmentModel` (chw_user_id, patient_user_id,
  assigned_by, status, expires_at). **The authorization boundary** for all
  CHW↔patient operations.
- `consent_record.py` → `ConsentRecordModel` (patient_user_id, chw_user_id,
  session_id, consent_type, language, consent_text_version, granted,
  attested_by). **Reuse for CHW-assisted care navigation consent** — new
  `consent_type` values: `care_navigation`, `ai_navigation_explanation`.
  No new consent table needed.
- `assessment_sync_record.py` → `AssessmentSyncRecordModel` (idempotency_key,
  chw_user_id, patient_user_id, session_id, sync_status, error_category).
  **Pattern to mirror** for referral offline sync (idempotency_key anchor).
- `offline_device_registration.py` → device fingerprint hashing pattern.

### Service + endpoint
- `app/application/services/chw_service.py` — `ChwService`. Key method
  `_assert_assigned(chw_id, patient_id)` is the reusable authorization guard.
  Sync uses idempotency_key dedup + `begin_nested()` savepoint for failure
  ledger (pattern to reuse for referral sync).
- `app/api/v1/endpoints/chw.py` — uses `get_chw_user` dependency.
- `app/api/deps.py` → `get_chw_user` admits COMMUNITY_HEALTH_WORKER +
  MEDICAL_DIRECTOR+ (supervision). `get_current_admin` for admin ops.
  `get_analytics_user` for population analytics.

### RBAC
- `app/core/security/rbac.py`: `Role.COMMUNITY_HEALTH_WORKER` (level 3),
  permissions `CHW_CREATE_ASSESSMENT`, `CHW_READ_ASSIGNED`,
  `CHW_RECORD_CONSENT`, `CHW_SYNC_OFFLINE`. Below READ_ONLY_REVIEWER (5) →
  CMS denied. **Phase 9 adds**: `CHW_MANAGE_REFERRALS` (scoped to assigned
  patients) + `REFERRAL_READ_OWN` (patient) + `REFERRAL_READ_ASSIGNED` (CHW).
  Patient gets `REFERRAL_READ_OWN` + `REFERRAL_UPDATE_OWN`. Doctors get
  `REFERRAL_READ_ASSIGNED` (via hierarchy). Admins/analytics retain
  `ANALYTICS_VIEW_POPULATION`.

## 4. AI layers (REUSE Phase 1/2/7 infrastructure)

### Provider abstraction
- `app/application/ai/provider.py` — `AIExplanationProvider` Protocol,
  `StubExplanationProvider` (deterministic, default),
  `AIProviderError`, `AIValidationFailure`. `get_explanation_provider()`
  selects via `settings.ai_provider`.
- **Phase 9 reuses**: implement a `ReferralNavigationProvider` (or extend stub)
  that produces navigation explanations. Same Protocol; new `request_type`
  in audit.

### Audit (Phase 7)
- `app/infrastructure/persistence/models/ai_interaction_audit.py` —
  `AIInteractionAuditModel` stores hashes + reference ids ONLY (no PHI).
  Fields: trace_id, session_id, request_type, provider, model, prompt_version,
  language, literacy_level, input_context_hash, output_hash, status,
  status_reason.
- `app/application/services/ai_audit_service.py` — `AIAuditService.record()`
  + `get_governance_summary()`. **Reuse directly** for referral navigation
  AI audit; `request_type="referral_navigation"`.

### Context contract pattern
- `app/application/dtos/ai_dtos.py` — `ReportExplanationContext` is the
  minimal PHI-scrubbed context. Phase 9 adds `ReferralNavigationContext`
  (trace_id, recommendation_id, recommendation title/type, referral type,
  referral status, deterministic severity, evidence IDs, language,
  literacy level). **No raw patient records, no tokens.**

### Validation pattern
- AI output validated against deterministic allow-lists (existing
  recommendation/evidence/indicator ids). Hallucinated IDs →
  `AIValidationFailure` → `UNAVAILABLE_FALLBACK`. **Reuse for referral
  navigation**: validate referenced recommendation_id / referral_id /
  evidence_id against DB.

## 5. Phase 6 population analytics (EXTEND)

- `app/application/services/population_analytics_service.py` —
  `PopulationAnalyticsService`. SQL-level aggregations, small-cell
  suppression via `_suppress_count()` using `settings.analytics_min_group_size`
  (k-anonymity). `_compute_rate()`, `_effective_cohort_size()`.
- SDG dashboard: `get_sdg_dashboard()` returns SDG 3.4 / 3.8 / 3.d / 10
  sections.
- **Phase 9 extends**: add `get_care_continuity()` — screening-to-referral,
  referral acknowledgement/scheduling/completion rates, access-barrier rates,
  unresolved referral rate. All de-identified, k-anonymity enforced via
  existing `_suppress_count`. New SDG metrics added to existing sections
  (3.8 care completion, 10 equity gaps). **No change to existing metrics.**

## 6. Existing referral/follow-up concepts — NONE FOUND

- Searched all models, entities, services, endpoints. **No existing
  `referral`, `follow_up_task`, or `care_status` concept exists.** This is a
  genuinely new domain. The only related concept is
  `GeneratedScreeningModel` (a screening name + reason in a report) — not a
  referral. Phase 9 is additive with no duplication risk.

## 7. Potential schema additions (additive only)

New tables (all follow `BaseModel`: UUID PK, timestamps, soft-delete):
1. `referrals` — the care-navigation record (derived from a
   `GeneratedRecommendationModel`).
2. `referral_status_events` — append-only audit of every status transition.
3. `referral_access_barriers` — structured barrier records.
4. `follow_up_tasks` — deterministic tasks linked to a referral.

No existing CDSE/report/recommendation table is modified. The
`recommendation.category` field is read-only (CMS-authored) and used as the
eligibility signal — no schema change.

## 8. Security boundaries (verified)

- Patient ownership: `ReportService.get_report(report_id, user_id)` returns
  None if `user_id != rpt.user_id`. Phase 9 referrals reuse this: patient
  can only read their own referrals.
- CHW assignment: `ChwService._assert_assigned(chw_id, patient_id)`. Phase 9
  reuses for all CHW referral operations.
- No cross-patient access: referral list endpoints filter by `user_id`
  (patient) or assignment join (CHW). ID-in-URL attacks fail because the
  query includes the caller's identity, not just the resource id.
- CMS RBAC unchanged. Doctors view referrals via a new
  `get_referral_clinician` dependency (MEDICAL_DIRECTOR+).

## 9. Risks

1. **trace_id extraction**: trace_id lives in the result `summary` JSON
   string and `ExplanationRecordModel.text`, not a column. Phase 9 will
   parse it from the summary (deterministic, the CDSE writes it). Low risk
   but adds a parse step. Alternative: store trace_id on the referral at
   creation time (the referral service reads the result summary once).
2. **Recommendation category as eligibility**: `category="referral"` is the
   primary signal. If CMS authors a referral-type recommendation with a
   non-referral category, it won't auto-create a referral. This is
   **conservative and correct** — the spec requires CMS-controlled
   eligibility, not text-guessing. Documented in the eligibility ruleset.
3. **Offline referral sync**: must be idempotent + conflict-safe. Reuse the
   `AssessmentSyncRecordModel` idempotency-key pattern. Status transitions
   are server-validated, so an offline client can never set an invalid
   status — the server rejects it on sync.
4. **AI validation**: referral navigation AI output must be validated
   against existing referral/recommendation/evidence IDs. The referral must
   exist before AI explains it (AI never creates).

## 10. Implementation plan (Steps 2–10)

- **Step 2**: Backend referral domain — 4 models + migration + DTOs.
- **Step 3**: Status machine (controlled transitions) + audit events +
  referral service.
- **Step 4**: Patient + CHW endpoints (reuse ownership/assignment guards).
- **Step 5**: Offline sync (idempotency-key pattern from Phase 8).
- **Step 6**: AI navigation explanation (reuse provider/audit/validation).
- **Step 7**: SDG analytics extension (care-continuity metrics).
- **Step 8**: Frontend (patient care-follow-up page, CHW follow-up list,
  doctor view, analytics funnel).
- **Step 9**: Security & privacy audit (dedicated review).
- **Step 10**: Full regression + MEDICHECK_PHASE9_REPORT.md + AGENTS.md.

## 11. What MUST NOT change (verified list)

- CDSE (`clinical_decision_service.py`) — scoring, indicators, conditions.
- `ReportService` report generation (read-only consumption by referral svc).
- `RecommendationModel` schema (read `category` only).
- Knowledge graph repositories.
- Phase 1 AI explanation contract / Phase 2 evidence retrieval /
  Phase 3 intake / Phase 4 trajectory / Phase 5 multilingual /
  Phase 6 k-anonymity / Phase 7 AI governance / Phase 8 CHW security.
- Existing seed data.
