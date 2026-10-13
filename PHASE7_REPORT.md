# Phase 7 Report — AI-Powered Personalized Risk Communication, Transparency & AI Governance

**Branch:** feat/ai-phase7-personalized
**Base:** `main` @ 486cdff (Phase 6 merged)
**Status:** Complete — backend 29 new tests pass (238 total), frontend 11 new tests pass (80 total), typecheck clean, build OK.

## Summary

Phase 7 adds a multilingual (English/Sinhala/Tamil), health-literacy-aware
personalized risk communication layer on top of the existing deterministic
clinical engine, with full source transparency and an AI governance audit
trail. **The AI remains strictly an explanation layer** — it never diagnoses,
scores, sets severity, creates recommendations, or modifies the deterministic
assessment.

### Constraints honored
- No clinical decision engine (CDSE) changes
- No database schema migrations of existing tables (additive table only)
- No LLM APIs added directly (deterministic local provider; pluggable Protocol)
- AI is explanation/extraction layer ONLY
- Supports EN/SI/TA

---

## Features delivered

### Feature A — Personalized Risk Communication
- `PersonalizedExplanationProvider` (deterministic local provider): builds
  explanations strictly from supplied context, adapted to language (EN/SI/TA)
  and literacy level (Simple/Standard/Detailed).
- The SAME deterministic result produces equivalent explanations across all
  languages and literacy levels. Translation NEVER upgrades certainty
  (possible -> confirmed, monitor -> urgent, risk -> diagnosis are FORBIDDEN).
- `POST /api/v1/report/{session_id}/explanation` now accepts `language` and
  `literacy_level` query params.

### Feature B — "Why was I asked this?" (Question Explanation)
- `QuestionExplanationService.explain_question()`: explains why a question
  was included using ONLY existing knowledge-graph relationships
  (question -> indicator -> condition, question -> evidence).
- Never invents medical relationships. If no link exists, returns
  "Explanation unavailable." — never hallucinates.
- Ownership: the caller must own the session (cross-patient isolation).
- `GET /api/v1/report/{session_id}/question-explanation?question_id=...`

### Feature F — "Show the source" (Source Breakdown)
- `source_breakdown` field on `AIExplanationResponse`: every finding cites
  the deterministic finding, contributing answer refs, knowledge-graph
  relationship, evidence ids, deterministic score, and trace_id.
- Frontend renders a "Show the source" section with traceable source chains
  linking findings to evidence records.

### Feature G — AI Transparency Notice
- `transparency_notice` field: patient-facing text stating that the clinical
  assessment was calculated by the deterministic engine and that AI was used
  only to explain and communicate — not to diagnose, score, or modify.
- Rendered in a dedicated, visually distinct section on the frontend.

### Feature H — AI Governance Audit Trail
- `AIInteractionAuditModel` (additive table): stores metadata about every AI
  explanation — provider, model, prompt_version, language, literacy_level,
  input_context_hash (SHA-256), output_hash (SHA-256), status.
- **No raw PHI**: only reference ids and hashes. No free-text patient data.
- Every `explain_report()` call writes an audit record on every outcome
  (success, provider_unavailable, validation_failed).
- `GET /api/v1/ai-governance/summary`: aggregate AI quality metrics
  (fallback rate, validation failure rate, by-language, by-provider,
  by-prompt-version). RBAC: RESEARCH_REVIEWER+. Individual audit records are
  NEVER exposed — only de-identified aggregates.

### Feature I — AI Quality Status
- `AIQualityStatus` enum: `valid`, `evidence_unavailable`, `fallback`,
  `validation_failed`, `provider_unavailable`.
- Each response carries its quality status, rendered as a badge on the frontend.
- Split `AIProviderError` (provider DOWN) from `AIValidationFailure`
  (output INVALID) so the audit trail distinguishes the two failure modes.

### Feature J — Deterministic Integrity + Patient Ownership
- AI explanation never modifies the CDSE result. Verified across all 3
  languages and 3 literacy levels: indicators, scores, and summary unchanged.
- Cross-patient isolation: a patient cannot access another patient's
  explanation. The AI is never invoked for an unauthorized session.

---

## Files

### New backend files (8)
1. `backend/app/application/ai/personalized_provider.py`
2. `backend/app/application/ai/phase7_prompts.py`
3. `backend/app/application/services/ai_audit_service.py`
4. `backend/app/application/services/question_explanation_service.py`
5. `backend/app/infrastructure/persistence/models/ai_interaction_audit.py`
6. `backend/alembic/versions/20260810_ai_interaction_audits.py`
7. `backend/app/api/v1/endpoints/ai_governance.py`
8. `backend/tests/test_ai_phase7.py` (29 tests)

### New frontend files (1)
9. `frontend/src/features/dashboard/components/__tests__/ReportExplanationPhase7.test.tsx` (11 tests)

### Modified backend files (7)
1. `backend/app/application/dtos/ai_dtos.py` — added `language`,
   `literacy_level`, `quality_status`, `source_breakdown`,
   `transparency_notice`, `provider`, `model` + `LiteracyLevel`,
   `AIQualityStatus`, `SourceBreakdownItem`.
2. `backend/app/application/services/ai_explanation_service.py` —
   `explain_report()` accepts language + literacy_level, writes audit
   records, builds source_breakdown, sets transparency_notice + quality_status.
3. `backend/app/application/ai/provider.py` — split AIProviderError /
   AIValidationFailure; `get_explanation_provider()` supports "personalized-stub".
4. `backend/app/api/v1/endpoints/report.py` — explanation endpoint accepts
   language + literacy_level; added question-explanation endpoint.
5. `backend/app/core/security/rbac.py` — added `Permission.AI_VIEW_GOVERNANCE`;
   granted to RESEARCH_REVIEWER, MEDICAL_DIRECTOR, SUPER_ADMIN.
6. `backend/app/api/deps.py` — added `get_ai_governance_user`.
7. `backend/app/core/config.py` — added `ai_audit_enabled`,
   `ai_default_language`, `ai_default_literacy_level`.

### Modified frontend files (2)
8. `frontend/src/features/dashboard/api/patientService.ts` — extended
   `AIExplanation` interface; `fetchReportExplanation()` accepts params;
   added `fetchQuestionExplanation()`, `QuestionExplanation`,
   `AISourceBreakdownItem`, `AIQualityStatus`, `LiteracyLevel`.
9. `frontend/src/features/dashboard/components/ReportExplanation.tsx` —
   language + literacy selectors, source breakdown section, transparency
   notice, quality status badge.

### Modified router files (1)
10. `backend/app/api/v1/router.py` — registered `ai_governance_router`.

---

## Test results

### Backend (29 new Phase 7 tests, 238 total)
```
tests/test_ai_phase7.py: 29 passed
```
Covers: personalized explanation (EN/SI/TA, simple/standard/detailed),
translation non-upgrade of certainty, question explanation happy path +
unauthorized + no-link, source breakdown presence, transparency notice,
audit record creation + no-PHI + fallback + validation failure, quality
status (valid/provider_unavailable/validation_failed), deterministic
integrity with personalization, cross-patient isolation, prompt version +
trace ID, HTTP endpoints (language + literacy + question explanation),
governance RBAC (patient denied, roleless denied, RESEARCH_REVIEWER allowed,
aggregate metrics).

### Frontend (11 new Phase 7 tests, 80 total)
```
ReportExplanationPhase7.test.tsx: 11 passed
```
Covers: language + literacy selectors render, params passed to fetch,
refetch on language change, refetch on literacy change, transparency notice,
source breakdown section, quality status badges (valid/provider_unavailable/
validation_failed/evidence_unavailable), source breakdown evidence links.

```
typecheck: clean
build: OK (11.32s)
```

---

## Architecture decisions

1. **Deterministic local provider, not a network LLM.** Phase 7 uses a
   `PersonalizedExplanationProvider` that builds explanations from phrase
   tables + literacy-adapted text generators. This keeps the AI layer
   fully testable, auditable, and free of network dependencies — while the
   `AIExplanationProvider` Protocol remains ready for a future vendor
   provider.

2. **Additive-only schema.** The `ai_interaction_audits` table is new; no
   existing table is modified. The migration is idempotent (skips if the
   table exists, e.g. when test DB uses `Base.metadata.create_all`).

3. **PHI minimization in audit trail.** The audit model stores only
   reference ids and SHA-256 hashes — never raw patient text, clinical
   content, or free-text PHI. The governance API returns only aggregates;
   individual audit records are never exposed.

4. **Translation safety.** Phrase tables ensure the same clinical concept is
   expressed in all three languages without upgrading certainty. Severity
   labels (deterministic categories) remain in English across all languages,
   with a local-language explanation that they are assessment labels, not
   diagnoses.

5. **RBAC.** `Permission.AI_VIEW_GOVERNANCE` is granted to RESEARCH_REVIEWER,
   MEDICAL_DIRECTOR, and SUPER_ADMIN — the same roles that already have
   population analytics access. Patients and roleless users are denied (403).
