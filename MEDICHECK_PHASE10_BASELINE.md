# MediCheck Phase 10 — Read-Only Forensic Baseline

Produced before any Phase 10 source modification. All contracts verified
directly from source code, not documentation. This baseline establishes the
exact insertion points for the Interoperability, Health-System Integration &
Outcome Feedback layer.

## 1. Verified test baseline

| Suite | Status | Count |
|---|---|---|
| Backend tests collected | collected | 410 |
| Backend (Phase 6 + Phase 8 + auth subset) | PASS | 47 |
| Backend deps | installed | `pip install -e .` + pytest stack |
| Frontend | (verified in prior phases) | — |

Phase 9 only delivered **models + DTOs + migration** (Steps 2 of its plan).
There is **no referral service, no referral endpoint, no referral frontend**.
Phase 10 must build the referral service/endpoint layer on top of the Phase 9
models (the data contract already exists) and then add the interoperability,
facility, outcome, and SDG-export capabilities.

## 2. Existing referral lifecycle (Phase 9 — models only)

Phase 9 created the **data contract** but no service/endpoint. The models are:

- `app/infrastructure/persistence/models/referral.py` — `ReferralModel`
  (`referrals`). Fields: `patient_user_id`, `originating_session_id`,
  `originating_report_id`, `trace_id` (String(16)), `recommendation_id`,
  `referral_type` (String(30)), `status` (String(20), default `pending`),
  `due_at`, `assigned_chw_user_id`, `patient_acknowledged`, `notes`,
  `completed_at`. Relationships: `status_events`, `barriers`,
  `follow_up_tasks` (all `selectin`).
- `referral_status_event.py` — `ReferralStatusEventModel`
  (`referral_status_events`). Append-only transition audit: `referral_id`,
  `from_status`, `to_status`, `actor_user_id`, `actor_role`, `reason`.
- `referral_access_barrier.py` — `ReferralAccessBarrierModel`
  (`referral_access_barriers`). Non-clinical access barriers: `referral_id`,
  `barrier_type`, `recorded_by_user_id`, `recorded_by_role`, `detail`.
- `follow_up_task.py` — `FollowUpTaskModel` (`follow_up_tasks`).
  `referral_id`, `patient_user_id`, `assigned_chw_user_id`, `task_type`,
  `title`, `due_at`, `status`, `completed_at`, `notes`.

### Phase 9 DTO contract (already defined — `referral_dtos.py`)
- `ReferralType` Literal: `primary_care`, `specialist`, `laboratory`,
  `imaging`, `preventive_screening`, `follow_up_assessment`, `emergency_care`.
- `ReferralStatus` Literal: `pending`, `acknowledged`, `scheduled`,
  `attended`, `completed`, `declined`, `unable_to_access`, `cancelled`.
- `BarrierType` Literal: `transportation`, `cost`, `distance`, `language`,
  `appointment_unavailable`, `connectivity`, `caregiver_constraint`,
  `work_schedule`, `accessibility`, `other`.
- `ActorRole` Literal: `patient`, `chw`, `doctor`, `admin`, `system`.
- `FollowUpTaskStatus` Literal: `pending`, `in_progress`, `completed`,
  `cancelled`.
- DTOs: `ReferralResponse`, `ReferralListResponse`,
  `ReferralStatusEventResponse`, `ReferralDetailResponse`,
  `AcknowledgeRequest`, `ScheduleRequest`, `StatusUpdateRequest`,
  `BarrierRequest`, `BarrierResponse`, `FollowUpTaskResponse`,
  `FollowUpTaskListResponse`, `CompleteTaskRequest`,
  `ReferralExplanationRequest`, `ReferralExplanationResponse`.

### Phase 9 status machine — NOT YET IMPLEMENTED
The state machine (transition validation) is described in the Phase 9 baseline
but there is no `ReferralService`. Phase 10 must implement it. The Phase 9
DTO statuses are the contract; Phase 10 adds the receiving-side facility
states (`received`, `accepted`, `declined`, `expired`, `lost_to_followup`)
by EXTENDING the service's transition table, not by changing the Literal (to
avoid breaking the existing DTO contract). The `ReferralStatus` Literal in
`referral_dtos.py` will be extended additively with the new facility/outcome
states (see §6).

### Migration
`alembic/versions/20260810_referrals.py` (down_revision
`20260810_chw_offline`). Creates 4 tables idempotently. **Already applied**
(schema created via `Base.metadata.create_all` in tests).

## 3. Existing patient / report / session structure

### User
- `UserModel` (`users`): `firebase_uid`, `email`, `full_name`, `avatar_url`,
  `email_verified`, `is_active`, `last_login_at`. `roles` via `user_roles`
  join to `RoleModel`.

### Health profile (FHIR Patient source)
- `HealthProfileModel` (`health_profiles`): `user_id`, `draft`,
  `profile_metadata` (column `metadata`, exposed as `profile_metadata`).
- `PersonalInfoModel` (`personal_infos`): `profile_id`, `full_name`,
  `date_of_birth`, `sex`, `height_cm`, `weight_kg`, `blood_group`,
  `nationality`, `country`, `state`, `city`, `preferred_language`,
  `emergency_contact` (JSON), `occupation`, `industry`, `education_level`,
  `marital_status`, `children_count`.
- `SQLProfileRepository.get_by_user_id` eager-loads `personal_info`,
  `lifestyle`, `nutrition` via `selectinload`. **Reuse this** to load the
  FHIR Patient resource (no N+1).

### Assessment session / answers (FHIR QuestionnaireResponse source)
- `AssessmentSessionModel` (`assessment_sessions`): `user_id`,
  `questionnaire_template_id`, `questionnaire_version_id`, `status`,
  `current_question_id`, `current_group_id`, `answers_count`,
  `total_questions`, `completed_questions`, `started_at`, `paused_at`,
  `completed_at`, `expires_at`, `device_info`, `extra_metadata` (column
  `metadata` — Phase 5 stores `language`/`input_type` here).
- `AssessmentAnswerModel` (`assessment_answers`): `session_id`,
  `question_id`, `question_version`, `question_code`, `option_id`, `value`,
  `numeric_value`, `response_value` (JSON), `score_value`, `is_skipped`,
  `time_taken_seconds`, `branch_path`, `recorded_at`. Session.answers is
  `selectin`.

### CDSE result (FHIR Observation / DiagnosticReport source)
- `AssessmentResultModel` (`assessment_results`): `session_id`, `user_id`,
  `summary` (Text — contains `[trace:{trace_id}]` inline), `confidence_score`.
  Relationships: `activated_indicators`, `activated_conditions`,
  `generated_recommendations`, `generated_laboratory_tests`,
  `generated_screenings`, `explanations`.
- `ActivatedIndicatorModel`: `result_id`, `indicator_id`, `score`,
  `evidence_count`, `notes`.
- `ActivatedConditionModel`: `result_id`, `condition_id`, `score`,
  `confidence`, `notes`.
- `GeneratedRecommendationModel`: `result_id`, `recommendation_id`,
  `source` (`"condition:{cid}"`), `notes` (`"[trace:{trace_id}] ..."`).

### Report (FHIR DiagnosticReport source)
- `HealthAssessmentModel` (`health_assessments`): `session_id`, `user_id`,
  `summary`, `created_at`. Relationships: `body_systems`, `conditions`,
  `lifestyle`, `advices` (all `selectin`).
- `BodySystemAssessmentModel`: `assessment_id`, `body_system_id`, `category`
  (String(50) — `Normal`/`Monitor`/`Needs Attention`/`Recommend Screening`/
  `Urgent Medical Review`), `score` (String(50), float-as-string),
  `notes`.
- `ConditionAssessmentModel`: `assessment_id`, `condition_id`, `score`,
  `confidence`, `notes`.
- `GeneratedAdviceModel`: `assessment_id`, `recommendation_id`, `category`,
  `text`.

### trace_id (existing, NOT a column)
trace_id is `uuid.uuid4().hex[:16]`, generated per CDSE run, stored INLINE in
`AssessmentResultModel.summary` and `ExplanationRecordModel.text` as
`"[trace:{trace_id}] ..."`. Reuse the Phase 1/4 extraction pattern
(`_extract_trace_id` from summary). The referral model has a dedicated
`trace_id` column populated once at referral creation.

## 4. Existing consent model (Phase 8 — REUSE)

- `ConsentRecordModel` (`consent_records`): `patient_user_id`,
  `chw_user_id`, `session_id`, `consent_type` (String(40)), `language`,
  `consent_text_version`, `granted`, `attested_by`.
- Phase 8 `consent_type` values: `assessment_assist`. Phase 9 baseline
  proposed `care_navigation`, `ai_navigation_explanation`.
- **Phase 10 adds**: `consent_type = "fhir_export"` (and
  `"data_sharing"`) for FHIR/external sharing. No new table — reuse
  `ConsentRecordModel`. The FHIR export service checks for a granted
  `fhir_export` consent for the patient before producing a bundle.
- `ChwService._verify_consent` is the reusable verification pattern.

## 5. Existing RBAC (REUSE + minimal extension)

`app/core/security/rbac.py`:
- `Role` enum: PATIENT, DOCTOR, SUPER_ADMIN, MEDICAL_DIRECTOR,
  SPECIALIST_DOCTOR, GENERAL_PHYSICIAN, RESEARCH_REVIEWER, CONTENT_EDITOR,
  READ_ONLY_REVIEWER, COMMUNITY_HEALTH_WORKER.
- Hierarchy: PATIENT=0, CHW=3, READ_ONLY_REVIEWER=5, GENERAL_PHYSICIAN=10,
  DOCTOR=10, CONTENT_EDITOR=15, SPECIALIST_DOCTOR=20, RESEARCH_REVIEWER=25,
  MEDICAL_DIRECTOR=30, SUPER_ADMIN=40.
- Existing permissions relevant to Phase 10:
  `ANALYTICS_VIEW_POPULATION` (RESEARCH_REVIEWER+, level 25),
  `AI_VIEW_GOVERNANCE` (RESEARCH_REVIEWER+), CHW_* (CHW level 3).
- `app/api/deps.py` dependencies: `get_current_user`,
  `get_current_active_user`, `get_current_doctor`, `get_current_admin`,
  `get_current_super_admin`, `get_cms_user` (>=READ_ONLY_REVIEWER),
  `get_analytics_user` (RESEARCH_REVIEWER+), `get_ai_governance_user`
  (RESEARCH_REVIEWER+), `get_chw_user` (CHW or MEDICAL_DIRECTOR+).
- **Phase 10 adds** (additive permissions, granted to appropriate roles):
  - `FHIR_EXPORT_OWN` (patient — export own bundle) + `FHIR_EXPORT_ANY`
    (clinician/admin — export a patient's bundle, still IDOR-guarded +
    consent-guarded).
  - `INTEROP_MANAGE` (admin — manage facilities/interoperability config).
  - `REFERRAL_MANAGE` (CHW/clinician — manage referrals for assigned
    patients). Patient gets `REFERRAL_READ_OWN`.
  - `SDG_EXPORT` (RESEARCH_REVIEWER+ — export SDG aggregates, reuses
    ANALYTICS_VIEW_POPULATION-equivalent gating).
- New deps: `get_interop_user` (INTEROP_MANAGE / admin),
  `get_referral_user` (REFERRAL_MANAGE or CHW or clinician),
  `get_sdg_export_user` (RESEARCH_REVIEWER+).

## 6. Existing analytics (EXTEND)

- `app/application/services/population_analytics_service.py` —
  `PopulationAnalyticsService`. SQL-level aggregation, `_suppress_count(k)`,
  `_effective_cohort_size`, `_compute_rate`, `get_overview`,
  `get_severity_distribution`, `get_body_systems`, `get_indicators`,
  `get_trajectory`, `get_accessibility`, `get_sdg_dashboard`.
  `settings.analytics_min_group_size` (k=10 default),
  `settings.analytics_max_date_range_days` (365).
- `analytics_dtos.py`: full DTO set (SuppressedValue, TimeSeriesPoint,
  OverviewMetrics, SeverityBucket, BodySystemMetric, IndicatorTrendEntry,
  TrajectoryBucket, LanguageMetric, AccessibilityMetrics, SDGMetric,
  SDGSection, SDGDashboardResponse, etc.).
- Endpoints `app/api/v1/endpoints/analytics.py`: `/analytics/overview`,
  `/severity`, `/body-systems`, `/indicators`, `/trajectory`,
  `/accessibility`, `/sdg`. All gated by `get_analytics_user`.
- **Phase 10 extends**: a new `CareContinuityAnalyticsService` (or methods on
  PopulationAnalyticsService) for the screening→referral→care funnel + a
  dedicated `SdgExportService` for CSV/JSON export. Reuse `_suppress_count`
  + `_compute_rate`. New SDG metrics (care completion, time-to-care, equity
  gaps) added as new sections/exports — existing metrics unchanged.

## 7. Existing audit architecture (REUSE)

- `AuditLogModel` (`audit_logs`): `actor_id`, `actor_role`, `entity_type`,
  `entity_id`, `action`, `changed_at`, `old_value`, `new_value`, `reason`,
  `ip_address`, `user_agent`, `session_id`, `request_id`, `status_code`,
  `method`, `path`. **Reuse for referral status transitions + FHIR export
  audit + facility feedback audit.**
- `AIInteractionAuditModel` (`ai_interaction_audits`, Phase 7): trace_id,
  session_id, request_type, provider, model, prompt_version, language,
  literacy_level, input_context_hash, output_hash, status, status_reason.
  **Reuse for AI-assisted CHW queue ranking** (`request_type =
  "chw_queue_ranking"`). No PHI.
- `AIAuditService.record()` + `get_governance_summary()`.
- `AuditLogMiddleware` (app/api/middleware.py) logs requests.

## 8. Reusable services / patterns

- `ReportService.get_report_by_session(session_id, user_id)` — ownership
  check (`rpt.user_id != user_id` → None). **Reuse for FHIR referral/source
  verification.**
- `ChwService._assert_assigned(chw_id, patient_id)` — CHW authorization
  guard. **Reuse for CHW referral/facility/outcome operations.**
- `EvidenceRetrievalService` (Phase 2) — deterministic evidence retrieval.
  **Reuse for any AI output that references evidence.**
- Provider abstraction (`app/application/ai/provider.py`): Protocol +
  StubExplanationProvider + `AIProviderError`/`AIValidationFailure`. **Reuse
  pattern for AI queue-ranking provider.**
- `to_dict()` on BaseModel returns column values. The `metadata`-column
  collision (QuestionnaireTemplateModel exposes `metadata` as
  `extra_metadata`) is a known landmine — FHIR Questionnaire generation must
  use `extra_metadata`, NOT `metadata`.

## 9. Existing identifiers / trace IDs

- All PKs are `uuid.uuid4().hex` (String(32)). FHIR logical IDs will reuse
  these (stable, opaque). **No internal DB id exposed unnecessarily** —
  FHIR resources will use the existing UUID id but NOT expose firebase_uid,
  email (unless consented + minimal), or raw session internals beyond what
  each resource requires.
- trace_id: 16-char hex, in result summary. Carried onto referrals at
  creation. FHIR DiagnosticReport will carry trace_id in an extension for
  traceability.

## 10. Privacy controls (existing)

- k-anonymity: `settings.analytics_min_group_size` (k=10). Cohorts < k →
  `suppressed=True`. Combination-attack protection via
  `_effective_cohort_size`.
- De-identification: no user_id/email/session_id/trace_id in any analytics
  response. SDG export will follow the same rule.
- Soft-delete: `SoftDeleteMixin.deleted_at`. All queries filter
  `deleted_at IS NULL`.
- Patient ownership + CHW assignment guards (IDOR protection by
  identity-in-query, not id-in-URL-only).

## 11. Exact insertion points

| Capability | Insertion point |
|---|---|
| Facility/facility-service/care-outcome/interop-export models | `app/infrastructure/persistence/models/` (new files) |
| Migration | `alembic/versions/20260811_interoperability_phase10.py` (down_revision `20260810_referrals`) |
| Referral service (state machine + facility + outcomes) | `app/application/services/referral_service.py` (NEW — Phase 9 left this absent) |
| FHIR export service + DTOs | `app/application/services/fhir_export_service.py` + `app/application/dtos/fhir_dtos.py` (NEW) |
| SDG export service | `app/application/services/sdg_export_service.py` (NEW) |
| Care-continuity analytics | `app/application/services/care_continuity_service.py` (NEW) or methods on PopulationAnalyticsService |
| AI queue ranking | `app/application/ai/queue_ranking_provider.py` + `app/application/services/chw_queue_service.py` (NEW) |
| Endpoints | `app/api/v1/endpoints/interoperability.py`, `referral.py`, `facility.py` (NEW) |
| RBAC | `app/core/security/rbac.py` (additive permissions + role grants) |
| Deps | `app/api/deps.py` (new dependency functions) |
| Router | `app/api/v1/router.py` (register new routers) |
| Config | `app/core/config.py` (Phase 10 settings) |
| Frontend | `frontend/src/features/interoperability/` (NEW module) + routes in `router.tsx` |
| Consent | reuse `ConsentRecordModel` + `consent_type="fhir_export"` |

## 12. Risks

1. **Phase 9 service absent**: the referral service must be built from
   scratch on the existing models. The DTO contract is fixed; the status
   machine must honor the existing Literal statuses and add new
   facility/outcome states additively.
2. **trace_id extraction**: parse from result summary (deterministic). The
   referral model already has a `trace_id` column — populate at creation.
3. **metadata-column collision**: QuestionnaireTemplateModel exposes JSON
   as `extra_metadata`. FHIR Questionnaire must use that attr.
4. **FHIR PHI minimisation**: Patient resource must NOT expose firebase_uid,
   password (none stored), tokens. Only consented minimal demographics.
5. **IDOR on FHIR export**: the endpoint must verify caller identity against
   the patient (own data) OR clinician/admin authority + consent — never
   trust the path id alone.
6. **Consent enforcement**: FHIR export denied without granted
   `fhir_export` consent. Auditable.
7. **k-anonymity bypass**: SDG/care-continuity exports must use
   `_effective_cohort_size` so dimension-drill-downs cannot reveal small
   cohorts. CSV export must suppress too.
8. **Outcome data must not feed CDSE**: care outcomes are operational only.
   No schema/foreign-key path from outcomes back into scoring tables.
9. **AI queue ranking boundary**: AI ranks by operational factors only
   (referral age, overdue, missing follow-up, geographic grouping,
   appointment window). NEVER severity/probability/urgency. Enforced in
   provider + validated.
10. **N+1**: FHIR bundle must batch-load (reuse selectin relationships +
    bounded queries). Population analytics must stay SQL-level.

## 13. Proposed additive architecture (Phase 10)

### New tables (additive, all BaseModel: UUID PK, timestamps, soft-delete)
1. `facilities` — facility/service metadata (id, code, name, service_type,
   region, contact_channel, availability_status, is_active). Seeded demo
   facilities only.
2. `facility_services` — services offered by a facility (facility_id,
   service_type, name, is_active).
3. `care_outcomes` — operational care-continuity state per referral
   (referral_id, patient_user_id, outcome_category
   [SCREENED/REFERRED/REFERRAL_RECEIVED/APPOINTMENT_SCHEDULED/CARE_RECEIVED/
   FOLLOWUP_COMPLETED/LOST_TO_FOLLOWUP], recorded_by_user_id,
   recorded_by_role, recorded_at, source). **No clinical fields. No FK to
   scoring tables.**
4. `interoperability_exports` — export audit/manifest (requested_by_user_id,
   patient_user_id, export_type [fhir/sdg], format, resource_types,
   source_trace_ids, fhir_version, status, consent_id, created_at).
   Append-only audit of every export.

### Referral facility connection
- Add `facility_id` (nullable FK to facilities) + `receiving_status`
  (String) to the referral via a NEW additive column OR a side table. To
  avoid altering the Phase 9 `referrals` table schema unnecessarily, Phase
  10 adds `facility_id` + `receiving_status` as additive columns via a new
  migration (additive ALTER — safe, nullable). This is the minimal change
  to wire referral→facility.

### Services
- `ReferralService`: state machine (Phase 9 statuses + facility/outcome
  transitions), create-from-recommendation, list/get (ownership-guarded),
  acknowledge/schedule/status-update (server-validated transitions),
  barrier recording, follow-up task CRUD, facility assignment, receiving
  feedback. Every transition writes a `ReferralStatusEventModel` +
  `AuditLogModel`.
- `FhirExportService`: builds a FHIR Bundle (R4) from deterministic data.
  Consent-aware, IDOR-guarded, auditable (writes
  `interoperability_exports`). Reuses ReportService/ProfileRepository.
- `SdgExportService`: CSV + JSON export of SDG-aligned aggregates.
  k-anonymity via `_suppress_count`. Methodology documented in
  `MEDICHECK_SDG_INDICATOR_MAPPING.md`.
- `CareContinuityService`: funnel analytics (screened→flagged→referred→
  received→appointment→care→followup), conversion/drop-off rates, median
  time-to-care, CHW-assisted completion, language/modality differences.
  All privacy-safe.
- `ChwQueueService` + `QueueRankingProvider`: operational task ranking
  (deterministic stub). AI never ranks by clinical factors. Audited via
  `AIAuditService`.

### Endpoints (all RBAC + ownership + consent guarded)
- `GET /api/v1/interoperability/fhir/patient/{patient_id}` — FHIR Bundle.
- `GET /api/v1/interoperability/fhir/session/{session_id}` — FHIR Bundle
  for one assessment session.
- `GET /api/v1/interoperability/exports` — export history (caller-scoped).
- `GET /api/v1/interoperability/sdg?format=json|csv` — SDG export.
- `GET /api/v1/interoperability/care-continuity` — care-continuity funnel.
- `GET/POST /api/v1/referrals` — referral CRUD (patient/CHW/clinician).
- `POST /api/v1/referrals/{id}/status` — status transition.
- `POST /api/v1/referrals/{id}/feedback` — receiving-side facility feedback.
- `POST /api/v1/referrals/{id}/outcomes` — care outcome recording.
- `GET/POST /api/v1/facilities` — facility metadata (admin manage, others
  read).
- `GET /api/v1/chw/queue` — operational CHW queue (AI-assisted ranking).

## 14. What MUST NOT change (verified list)

- CDSE (`clinical_decision_service.py`) — scoring, indicators, conditions.
- `ReportService` report generation (read-only consumption).
- `RecommendationModel` schema (read `category` only).
- Knowledge graph repositories / CMS content.
- Phase 1 AI explanation / Phase 2 evidence retrieval / Phase 3 intake /
  Phase 4 trajectory / Phase 5 multilingual / Phase 6 k-anonymity /
  Phase 7 AI governance / Phase 8 CHW security.
- Existing seed data.
- Existing analytics metrics (Phase 10 ADDS, does not alter).
- The Phase 9 referral DTO contract (extended additively only).
