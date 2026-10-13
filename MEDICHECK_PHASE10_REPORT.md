# MediCheck Phase 10 Report — Interoperability, Health-System Integration & Outcome Feedback

## Objective

Move MediCheck from a technically complete screening platform toward a
health-system-ready, interoperable, SDG-aligned digital health platform by
adding four additive capabilities:

A. **FHIR R4 interoperability** — standards-based export of MediCheck clinical information.
B. **SDG / population-health export** — secure, de-identified aggregate exports.
C. **Referral → facility interoperability** — referral lifecycle + receiving-side feedback.
D. **Outcome feedback** — care-continuity outcome measurement (without altering CDSE).

## Architectural Principle (Non-Negotiable)

> **The CDSE decides. AI explains, extracts, translates, summarizes, or
> assists with operational tasks.**

Phase 10 adds NO second clinical calculation engine. FHIR/SDG/trajectory
outputs are generated read-only from existing deterministic data. AI-assisted
CHW queue ranking uses **operational factors only** (referral age, overdue
status, missing follow-up) — never disease severity, probability, or medical
urgency. Outcome data never feeds back into CDSE scoring.

## Baseline Findings

See `MEDICHECK_PHASE10_BASELINE.md` for the full forensic audit. Key findings:

- **Referral lifecycle (Phase 9):** `ReferralModel` existed with a status
  field, follow-up tasks, and access barriers. Phase 10 extends the status
  enum with facility handoff states (`sent`/`received`/`accepted`) and
  terminal operational states (`expired`/`lost_to_followup`), plus an
  append-only `ReferralStatusEventModel` for auditable transitions.
- **Patient/report structure:** `User`, `HealthProfile`, `AssessmentSession`,
  `HealthAssessmentModel` (report), CDSE results — all reused read-only.
- **Consent model (Phase 8):** `ConsentModel` with scope-based consent.
  FHIR exports are consent-gated; absent consent → export denied.
- **RBAC:** `Permission` enum extended with Phase 10 permissions
  (`FHIR_EXPORT_OWN`, `FHIR_EXPORT_ANY`, `SDG_EXPORT`, `INTEROP_MANAGE`,
  `FACILITY_MANAGE`). Granted to appropriate roles; patients denied admin
  endpoints.
- **Analytics (Phase 6):** `PopulationAnalyticsService` (SQL-level
  aggregation, small-cell suppression k=10). Phase 10 SDG export reuses +
  composes this.
- **Audit architecture:** `AuditLogModel` + Phase 7 `AIInteractionAuditModel`.
  Phase 10 adds `InteroperabilityExportModel` (export audit metadata) and
  records AI governance metadata for the CHW queue.
- **Trace IDs:** CDSE / Phase 1 explanation trace IDs are carried into FHIR
  export manifests and SDG rows for traceability.

## Architecture

### Backend (additive — no existing clinical tables modified)

**New models** (`app/infrastructure/persistence/models/`):
- `facility.py` — `FacilityModel` (code, name, service_type, region,
  contact_channel, availability_status) + soft-delete.
- `facility_service.py` — `FacilityServiceModel` (facility ↔ service type).
- `referral.py` — extended `ReferralModel` (facility_id, receiving_status,
  scheduled_for, completed_at) — additive columns only.
- `referral_status_event.py` — append-only status transition audit.
- `referral_access_barrier.py` — barriers to care (Phase 9, reused).
- `care_outcome.py` — `CareOutcomeModel` (operational outcome per
  referral/patient: SCREENED → ... → CARE_RECEIVED → FOLLOWUP_COMPLETED /
  LOST_TO_FOLLOWUP). **Never modifies CDSE score.**
- `interoperability_export.py` — `InteroperabilityExportModel` (export audit:
  export_id, type, format, requesting user, patient, resource_types,
  source_trace_ids, schema_version, status, consent_id, item_count). No PHI
  payloads stored.

**New services** (`app/application/services/`):
- `fhir_export_service.py` — `FhirExportService`. Generates FHIR R4 Bundles
  (Patient, Consent, QuestionnaireResponse, Observation, DiagnosticReport,
  ServiceRequest, Task, CarePlan) from deterministic data. IDOR-guarded +
  consent-gated. Records an `InteroperabilityExportModel` audit row per
  export. No N+1 (batched loads).
- `sdg_export_service.py` — `SdgExportService`. Composes Phase 6
  `PopulationAnalyticsService` + Phase 10 `CareContinuityService` into
  SDG-aligned rows (3.4, 3.8, 10). k-anonymity-suppressed per metric/stage.
  JSON + CSV.
- `care_continuity_service.py` — `CareContinuityService`. Care-continuity
  funnel + metrics (conversion, drop-off, median time-to-care, CHW-assisted
  completion). SQL aggregation; de-identified; k-suppressed.
- `facility_service.py` — `FacilityService`. CRUD over facility registry
  (admin-gated).
- `referral_service.py` — extended `ReferralService`. Referral lifecycle
  transitions (deterministic, auditable), facility feedback recording,
  outcome recording, follow-up task completion. Every transition →
  `ReferralStatusEventModel` + audit log.
- `chw_queue_service.py` — `ChwQueueService`. AI-assisted operational queue
  ranking (operational factors ONLY). Provider abstraction +
  `AIInteractionAuditModel` governance record. Clinical urgency never
  derived by AI.

**New endpoints** (`app/api/v1/endpoints/`):
- `interoperability.py` — FHIR patient/session bundles, export history, SDG
  JSON/CSV, care-continuity.
- `facilities.py` — facility registry CRUD.
- `referrals.py` — extended referral lifecycle + facility feedback + outcomes.
- `chw.py` — extended with `/chw/queue` (AI-assisted operational ranking).

**Migration:** `20260811_interop_phase10.py` (additive, idempotent) — creates
`facilities`, `facility_services`, `care_outcomes`, `interoperability_exports`
tables + referral additive columns. No existing clinical table altered.

### Frontend (additive)

New `features/interop/` module:
- `api/interopService.ts` — typed API client (FHIR, SDG, care continuity,
  facilities, referrals, CHW queue).
- `hooks/useInteropQueries.ts` — TanStack Query hooks.
- `components/InteropUI.tsx` — shared presentational components
  (PrivacyBadge, SuppressedBadge, TransparencyNotice, MetricCard, etc.).
- `pages/`:
  - `InteroperabilityDashboardPage.tsx` — FHIR export + export history.
  - `SdgDashboardPage.tsx` — SDG indicators + privacy badges + CSV download.
  - `CareContinuityPage.tsx` — care funnel + metrics.
  - `FacilitiesPage.tsx` — facility registry + referral status + feedback.
  - `ChwQueuePage.tsx` — AI-assisted operational queue.
- Routes registered under `/cms/interop/*` (DoctorLayout, doctor/admin
  gated). Nav section "Interoperability" added to `DoctorLayout.tsx`.
- Patients do not see admin/research functionality.

## FHIR Mappings

See `MEDICHECK_FHIR_MAPPING.md` for the full mapping. Summary:

| FHIR resource | MediCheck source | Safety |
|---------------|------------------|--------|
| Patient | User + HealthProfile | No unnecessary PHI; no passwords/tokens |
| Consent | ConsentModel | Export denied if consent absent |
| QuestionnaireResponse | session + answers | deterministic |
| Observation | body-system score / finding | AI interpretations NEVER clinical Observations |
| DiagnosticReport | report | screening/risk assessment; possible condition ≠ confirmed diagnosis |
| ServiceRequest | referral | facility reference |
| Task | follow-up task | CHW owner |
| CarePlan | operational care plan | operational only |

### FHIR R4 Validation

The export is validated two ways:

1. **In-app deterministic structural validator** —
   `app/application/services/fhir_validation.py`
   (`validate_fhir_resource` / `validate_fhir_bundle` /
   `validate_fhir_payload`). Dependency-free, no network /
   terminology-server calls. Enforces: exported-resource whitelist,
   forbidden `Condition` (possible conditions are NEVER confirmed
   diagnoses), R4 required elements per resource, enum value sets,
   Observation single `value[x]` (exactly one of
   valueQuantity/valueCodeableConcept/valueString/…), Reference
   format (`ResourceType/id`), CodeableConcept/Identifier/HumanName
   structure, id/date/dateTime/instant/uri formats, namespaced
   extensions only (`https://medicheck.org/fhir/StructureDefinition/`),
   and `Consent.provision` as a 0..1 single object
   (`type`: permit|deny).
2. **Official FHIR R4 model library** (offline, dev-time) —
   `fhir.resources==6.5.0` (pydantic v1) in an isolated venv.
   Generated patient bundle (9 entries) and session bundle
   (6 entries) both validate with **0 errors**.

Conformance issues found and fixed during validation:

- Body-system Observation previously emitted **both**
  `valueQuantity` and `valueString` — violates R4's exactly-one
  `value[x]` constraint. Now: category → `valueCodeableConcept`
  (MediCheck body-system-category code system), numeric score →
  standard `Observation.component` (`valueQuantity`, code
  `risk-score`).
- `DiagnosticReport.code` used a fake LOINC code (`testing` under
  `http://loinc.org`). Now uses MediCheck's own report-type code
  system (`code: clinical-report`).
- `ServiceRequest.code` / `Task.code` were text-only (no
  `coding`). Now carry MediCheck-namespaced codings
  (referral-type / task-type code systems).
- `DiagnosticReport` trace-id extension was built but never
  attached (DTO lacked the field) — the source trace id is now
  actually present on the resource, matching the manifest's
  `source_trace_ids`.
- `export_session_bundle` loaded the session via `session.get()`,
  which can return an identity-map object whose `selectin`
  relationships (`answers`) were never loaded → synchronous lazy
  load (`MissingGreenlet`) in async context. Now loads via
  `select(...)` (consistent with `_load_sessions`), which always
  triggers selectin loading.

Validation tests: `tests/test_fhir_r4_validation.py` — **19 pass**
(structural validation, clinical mapping, safety invariants:
no PHI leakage, no confirmed-diagnosis claim, extension
namespacing, references resolve within the bundle).

Note: the main environment's `fhir.resources` (8.3.0) models
**FHIR R5** (e.g. `Consent.scope`/`patient` renamed/removed,
`provision` as a list). R5-validator complaints about R4-shaped
fields are version differences, not R4 bugs — always validate R4
payloads against `fhir.resources==6.5.0`.

## SDG Mappings

See `MEDICHECK_SDG_INDICATOR_MAPPING.md` for the full mapping. All metrics
are **MediCheck-aligned proxies** (never claimed as official UN SDG
indicators). Covers SDG 3.4 (assessment coverage, NCD risk distribution,
screening completion, referral rate), SDG 3.8 (screening coverage, referral
completion, time-to-care, care funnel, language accessibility, CHW-assisted),
SDG 10 (completion equity, modality equity).

## Referral Lifecycle

Deterministic, auditable status flow:

```
pending → acknowledged → sent → received → accepted → scheduled → attended → completed
                                                                         ↘ declined
terminal: cancelled | expired | lost_to_followup | unable_to_access
```

- Receiving-side / authorized CHW explicitly provides status (never inferred
  from a timestamp).
- Every transition → append-only `ReferralStatusEventModel` + audit log.
- Facility feedback recorded via `PATCH /referrals/{id}/feedback`
  (`receiving_status` + notes).
- Outcomes are operational/care-continuity states — **never modify CDSE
  score, condition probability, severity, or recommendation generation.**

## Outcome Model

`CareOutcomeModel` tracks the operational funnel:

```
SCREENED → REFERRED → REFERRAL_RECEIVED → APPOINTMENT_SCHEDULED → CARE_RECEIVED → FOLLOWUP_COMPLETED
                                                                                ↘ LOST_TO_FOLLOWUP
```

Care-continuity analytics: conversion rates, drop-off rates, median
time-to-care, referral completion, follow-up completion, CHW-assisted
completion, language/modality differences. All population-level outputs are
de-identified + k-anonymity-suppressed.

## Privacy Model

- k-anonymity threshold `k = 10` (`settings.analytics_min_group_size`).
- Per-metric + per-funnel-stage suppression; suppressed cohorts return null
  values + `suppression_status = "suppressed"`.
- No user_id / email / session_id / patient identifier in any SDG or
  care-continuity response.
- Suppression cannot be bypassed via filters, narrow ranges, individual
  dimensions, or endpoint combination.
- FHIR exports carry only the requested patient's data (IDOR-guarded).

## Consent Model

- FHIR exports are consent-gated: absent required consent → export denied
  (403).
- Every consent-sensitive action is audited.
- Consent never bypassed for administrative convenience.

## AI Boundaries

- **CHW queue ranking** uses operational factors ONLY (referral age, overdue,
  missing follow-up, geographic grouping, appointment window). AI never
  ranks by disease severity, probability, medical urgency, predicted
  mortality, or clinical risk. Clinical urgency remains deterministic /
  explicitly assigned by the clinical workflow.
- AI governance (Phase 7 reuse): every AI-assisted output records provider,
  model, prompt version, timestamp, quality status, input context hash,
  output hash, trace/reference ID. No raw PHI logged unnecessarily.
- AI-generated text is clearly labelled. AI never silently modifies referral
  records.

## Security

Dedicated Phase 10 security tests cover:
- Authentication: unauthenticated users denied all protected exports.
- Authorization: only authorized roles access patient FHIR exports,
  population/SDG exports, facility/referral administration.
- IDOR: User A cannot export User B's FHIR bundle.
- Consent: export without required consent rejected.
- Privacy: population queries cannot bypass k-anonymity.
- Data leakage: FHIR exports contain no passwords, tokens, secrets,
  unrelated patient data, or AI provider credentials.
- Audit: sensitive exports create audit records.

## Performance

- FHIR generation uses batched loads (no N+1).
- Population/SDG analytics use SQL-level aggregation (GROUP BY/COUNT/SUM);
  never loads entire population into application memory.
- Bounded queries + deterministic ordering; export history is paginated.

## Migrations

- `20260811_interop_phase10.py` — additive, idempotent. Creates
  `facilities`, `facility_services`, `care_outcomes`, `interoperability_exports`
  + referral additive columns. No existing clinical table altered.
- No seed data altered beyond demo/seeded facilities where appropriate.

## Test Results

### Backend
- Phase 10 suite: `tests/test_interoperability_phase10.py` — **50 pass**
  (FHIR generation, bundle integrity, export authorization, consent
  enforcement, IDOR prevention, SDG aggregation, k-anonymity, suppression,
  CSV/JSON export, referral lifecycle, facility feedback, care outcomes,
  care-continuity calculations, AI queue ranking boundaries, audit logging,
  security).
- FHIR R4 validation suite: `tests/test_fhir_r4_validation.py` —
  **19 pass** (structural R4 validation via the in-app validator,
  clinical mapping, safety invariants).
- Combined run: `tests/test_interoperability_phase10.py
  tests/test_fhir_r4_validation.py` — **69 pass**.
- Full regression suite (run in batches): auth/RBAC, profile, emergency
  contact, CHW Phase 8, population analytics Phase 6, AI Phase 7, AI RAG
  Phase 2, longitudinal Phase 4, intake Phase 5, AI intake Phase 3, CMS
  recovery, report service — **all pass, no regressions**.

Run command:
```
cd backend && ALLOW_MOCK_AUTH=true DATABASE_URL=sqlite+aiosqlite:///./test.db \
  ENVIRONMENT=development python -m pytest tests/test_interoperability_phase10.py -q -W error::DeprecationWarning
```

### Frontend
- Phase 10 suite: `features/interop` — **16 pass** (FHIR export UI, export
  authorization states, SDG dashboard, privacy badges, referral status,
  facility feedback, CHW queue, error/empty states).
- Full frontend suite: **100 pass** (16 new + 84 existing), typecheck clean,
  production build OK.

Run commands:
```
cd frontend && npm run typecheck && CI=true npx vitest run && npm run build
```

## Known Limitations

- FHIR export is a controlled subset of FHIR R4 (Patient, Consent,
  QuestionnaireResponse, Observation, DiagnosticReport, ServiceRequest,
  Task, CarePlan). Not every FHIR resource is implemented; the
  `FhirQuestionnaire` DTO exists but no Questionnaire resource is
  currently emitted (questionnaires are referenced by canonical
  URL `Questionnaire/{template_id}`).
- FHIR validation is structural (in-app validator) plus official-R4-
  model validation of generated bundles; it does not perform
  terminology-server validation (codes come from MediCheck's own
  namespaced code systems, not LOINC/SNOMED).
- Care-continuity median time-to-care clamps sub-second negative
  deltas to zero: SQLite's second-granular `CURRENT_TIMESTAMP`
  (server_default) can otherwise make an outcome appear to
  predate its referral by a fraction of a second (precision skew,
  not a real impossible timeline). Materially negative deltas are
  still discarded.
- Facility registry uses seeded/demo facilities; no real hospital
  integrations (real integrations require real APIs/specs — documented as
  integration points, not built).
- AI CHW queue uses a deterministic stub provider (operational factors only);
  real LLM provider wiring is a configuration point, not a Phase 10 deliverable.
- Outcome data is NOT fed back into CDSE scoring by design. It may become a
  quality/calibration dataset for future clinician-reviewed work.
- Geographic equity metrics require sufficiently aggregated geo data
  (suppressed otherwise).

## Future Work

- Wire a real FHIR server / external health-system adapter behind the
  standards-compatible interface (mock adapter documented as integration
  point).
- Clinician-reviewed outcome calibration dataset (never automatic CDSE
  modification).
- Additional FHIR resources as integration partners require them.
- Real LLM provider for CHW queue ranking (operational factors only,
  governance retained).

## Regression Protection

Verified unchanged in behavior: authentication, onboarding, health profile,
assessment catalog, questionnaire engine, branching, CDSE, scoring,
possible-condition generation, recommendations, report generation, AI
explanation, RAG, multilingual intake, voice intake, longitudinal
trajectory, population analytics, AI governance, CHW mode, offline sync,
referral workflow, care-continuity analytics, CMS, RBAC.

**No Phase 10 feature can alter a previously generated deterministic
clinical result.**
