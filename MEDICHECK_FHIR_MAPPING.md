# MediCheck FHIR R4 Mapping

Phase 10 — Interoperability, Health-System Integration & Outcome Feedback.

This document describes how MediCheck deterministic clinical data maps to
FHIR R4 resources for standards-based export. It is a **read-only export**:
FHIR generation never modifies clinical records and never introduces a
second clinical calculation engine.

## Endpoints

| Method | Path | Purpose | RBAC |
|--------|------|---------|------|
| GET | `/api/v1/interoperability/fhir/patient/{patient_id}` | Patient-scoped FHIR Bundle | `get_current_user`; IDOR + consent checked in service |
| GET | `/api/v1/interoperability/fhir/session/{session_id}` | Session-scoped FHIR Bundle | `get_current_user`; session ownership checked |
| GET | `/api/v1/interoperability/exports` | Export history (audit metadata only) | `get_interop_user` |

All exports are consent-aware, audited, and deterministic. The export
manifest records `export_id`, timestamp, requesting user, resource types,
source trace IDs, FHIR schema version, status, and consent ID.

## Resource Mappings

### Patient (`Patient`)

| FHIR field | MediCheck source | Notes |
|------------|------------------|-------|
| `id` | `User.id` (UUID hex) | Not the internal DB row id; stable patient identifier |
| `identifier` | derived from user id | `system` = MediCheck patient id namespace |
| `name` | `PersonalInfoModel` | Given/family; **omitted if absent** — never fabricated |
| `telecom` | email only | No phone unless explicitly stored |
| `gender` | `PersonalInfoModel.gender` | Administrative gender if present |
| `birthDate` | `PersonalInfoModel.date_of_birth` | Only if present |
| `extension` | region / locale | Minimal demographic, no unnecessary PHI |

**Safety:** No passwords, auth tokens, AI provider credentials, or unrelated
patient records ever appear in a Patient resource.

### Consent (`Consent`)

A `Consent` resource is included when a FHIR export is consent-gated. Export
is **denied** if the required consent scope is absent.

### QuestionnaireResponse (`QuestionnaireResponse`)

| FHIR field | MediCheck source |
|------------|------------------|
| `id` | session id |
| `questionnaire` | questionnaire template reference |
| `subject` | `Patient/{patient_user_id}` |
| `authored` | session created timestamp |
| `item` | answers from the session (answer code + value) |

Represents the patient's questionnaire session and answers as recorded by
the deterministic questionnaire engine.

### Observation (`Observation`)

| FHIR field | MediCheck source |
|------------|------------------|
| `status` | `final` |
| `code` | body-system or measurement code |
| `subject` | `Patient/{patient_user_id}` |
| `valueQuantity` / `valueCodeableConcept` | body-system score or category |
| `interpretation` | severity category mapping (Normal / Monitor / Needs Attention / Recommend Screening / Urgent Medical Review) |

**Critical safety rule:** AI-generated interpretations are **never** exported
as clinical Observations. Only deterministic measurable observations
(body-system score, structured assessment observation) become Observations.
Possible conditions are exported as Observations with a clearly labelled
"screening finding" interpretation — **never** as confirmed diagnoses.

### DiagnosticReport (`DiagnosticReport`)

| FHIR field | MediCheck source |
|------------|------------------|
| `id` | report id |
| `status` | `final` |
| `code` | "MediCheck screening / risk assessment report" |
| `subject` | `Patient/{patient_user_id}` |
| `effectiveDateTime` | report created timestamp |
| `result` | references to the Observations in the same bundle |
| `conclusion` | deterministic overall severity category (categorical label, not an invented numeric "health score") |

**Distinction enforced:** the report is a *screening/risk assessment*. A
possible condition is **never** exported as a confirmed diagnosis. The
`conclusionCode` clearly distinguishes screening findings from possible
conditions from confirmed diagnoses.

### ServiceRequest (`ServiceRequest`)

Represents a referral.

| FHIR field | MediCheck source |
|------------|------------------|
| `id` | referral id |
| `status` | mapped from referral lifecycle status |
| `intent` | `plan` / `order` |
| `code` | referral type + recommendation category |
| `subject` | `Patient/{patient_user_id}` |
| `performer` | facility reference (if facility assigned) |

### Task (`Task`)

Represents a follow-up action / operational task.

| FHIR field | MediCheck source |
|------------|------------------|
| `id` | follow-up task id |
| `status` | mapped from task status |
| `intent` | `plan` |
| `for` | `Patient/{patient_user_id}` |
| `owner` | assigned CHW reference |

### CarePlan (`CarePlan`)

Represents the operational care-continuity plan (referral + follow-up tasks).

| FHIR field | MediCheck source |
|------------|------------------|
| `id` | derived from referral |
| `status` | `active` / `completed` |
| `subject` | `Patient/{patient_user_id}` |
| `activity` | references to ServiceRequest / Task |

## Bundle Structure

```
Bundle (type=collection)
  ├── Patient
  ├── Consent (when consent-gated)
  ├── DiagnosticReport (one per report)
  │     └── result -> Observation[] (body-system scores, findings)
  ├── QuestionnaireResponse (one per session)
  ├── ServiceRequest (one per referral)
  ├── Task (one per follow-up task)
  └── CarePlan (operational care-continuity plan)
```

## ID Safety

- Internal database row ids are **not** exposed; patient/session/report
  identifiers are stable UUID hex values already used across MediCheck.
- Source trace IDs (CDSE / Phase 1 explanation trace ids) are carried in the
  export manifest for traceability.
- **IDOR prevention:** a patient can only export their own bundle. A user
  with `FHIR_EXPORT_ANY` permission (admin/research roles) may export any
  patient's bundle, but every such export is audited.

## What FHIR Export Does NOT Do

- Does not diagnose.
- Does not calculate clinical scores (scores come from the existing CDSE).
- Does not represent AI explanations as clinical observations.
- Does not export possible conditions as confirmed diagnoses.
- Does not modify any clinical record.
- Does not expose passwords, tokens, secrets, or unrelated patient data.
