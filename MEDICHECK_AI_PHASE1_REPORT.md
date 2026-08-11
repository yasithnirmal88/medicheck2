# Medicheck — Phase 1: AI-Assisted Report Explanation

Status: **Phase 1 complete.** AI explanation layer added on top of the existing
deterministic clinical assessment reports. The clinical decision engine,
database schemas, and existing flows are **unchanged**.

## Goal

Add an AI-generated explanation for an already-generated deterministic
MediCheck report. The AI explains the report; it never diagnoses, scores,
sets severity, creates recommendations, or invents evidence. The
deterministic report is the source of truth and remains fully visible to the
patient whether or not the AI explanation succeeds.

## Safety boundaries (enforced)

1. **Deterministic engine untouched.** No CDSE, schema, or clinical-flow
   changes. The AI reads the existing `HealthAssessmentModel` +
   `AssessmentResultModel`; it never re-runs the assessment.
2. **AI never breaks the clinical report.** On any AI failure (timeout, network,
   malformed output, validation failure) the endpoint returns HTTP 200 with
   `available=false` and a safe fallback. It never returns 500 for a valid
   report.
3. **No hallucinated entities.** The output DTO validator rejects any
   `source_indicator_ids` or `recommendation_id` that is not present in the
   supplied deterministic context. Hallucinated ids → validation failure →
   safe fallback.
4. **No PHI to the AI.** The input contract (`ReportExplanationContext`)
   carries only trace id, severities, indicator/condition/recommendation names,
   evidence references, scores. No authentication tokens, no unrelated patient
   records, no database internals.
5. **Authentication + ownership reused.** The endpoint uses the same
   `get_current_user` dependency and report-ownership check as the other
   report endpoints. Unauthorized access returns 404 (no information leak) and
   the AI is never called.
6. **Bounded output.** Length validators cap summary/disclaimer (5000 chars),
   evidence_notes (50 × 2000 chars), and total payload (50000 chars).

## Architecture

```
POST /api/v1/report/{session_id}/explanation   (auth + ownership)
        │
   AIExplanationService.explain_report(session_id, user_id)
        │
        ├─ ownership check (reuse SQLReportRepository.get_report_by_session)
        ├─ _extract_trace_id(AssessmentResultModel.summary)   # CDSE trace
        ├─ in-memory cache lookup (trace_id, prompt_version)
        ├─ _build_context(report, result, kg_repo)  → ReportExplanationContext
        ├─ AIExplanationProvider.explain(context)    → raw JSON string
        ├─ _parse_and_validate(raw, context)         → AIExplanationResponse
        │      └─ bind_context() runs the id allow-list validator
        ├─ on failure → UNAVAILABLE_FALLBACK (available=false)
        └─ cache + return
```

### Backend files (new)

- `app/application/ai/prompts.py` — versioned system prompt
  (`PROMPT_VERSION = "1.0"`). Binds the AI to explaining only; requires a
  single JSON object matching the output contract.
- `app/application/ai/provider.py` — `AIExplanationProvider` Protocol,
  `StubExplanationProvider` (deterministic default, no external API), and
  `get_explanation_provider()` factory. A real vendor provider can be plugged
  in here without changing the service layer.
- `app/application/dtos/ai_dtos.py` — input contract
  (`ReportExplanationContext` + entity context DTOs) and output contract
  (`AIExplanationResponse` with the hallucination-rejecting
  `bind_context()` validator) + `UNAVAILABLE_FALLBACK`.
- `app/application/services/ai_explanation_service.py` —
  `AIExplanationService` (context assembly, provider call, validation, cache,
  graceful fallback) + process-local `_ExplanationCache` keyed by
  `(trace_id, prompt_version)`.

### Backend files (modified)

- `app/core/config.py` — `ai_provider`, `ai_model`, `ai_api_key`,
  `ai_request_timeout_seconds` settings (default `stub`).
- `app/api/v1/endpoints/report.py` — new
  `POST /report/{session_id}/explanation` route.
- `.env.example` — `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY`.

### Frontend files

- `features/dashboard/api/patientService.ts` — `AIExplanation` types +
  `fetchReportExplanation(sessionId)`.
- `features/dashboard/components/ReportExplanation.tsx` — clearly separated,
  additive `AI Explanation` card with loading / success / unavailable / empty
  states and a disclaimer. Never replaces the deterministic report.
- `features/dashboard/pages/ReportViewer.tsx` — renders `<ReportExplanation>`
  **after** the deterministic report card, only when the report loaded.

## Provider model

The default provider is the deterministic `StubExplanationProvider`. It builds
a valid explanation JSON strictly from the supplied context (indicator names,
severity, recommendations, evidence) and never calls a network service. This
makes the feature work in dev/tests/production-without-keys and never breaks
the report. To wire a real LLM later: implement the `AIExplanationProvider`
Protocol, select it via `AI_PROVIDER`, and add it to
`get_explanation_provider()`. No service-layer or DTO changes are required —
the validation + fallback machinery already protects the report.

## Test results

- Backend: **202 passed** (189 prior + 13 new), no regression.
  New: `tests/test_ai_explanation_phase1.py` — happy path, AI unavailable,
  invalid output, hallucinated indicator id, hallucinated recommendation id,
  unauthorized (AI never called), no report (AI never called), deterministic
  integrity (scores/indicators/conditions/recommendations/answers unchanged),
  cache hit (provider not recalled), endpoint happy path, endpoint
  unauthorized → 404, endpoint missing report → 404, endpoint requires auth.
- Frontend: **30 passed** (23 prior + 7 new), typecheck clean, build succeeds.
  New: `ReportExplanation.test.tsx` — loading then success, AI-generated
  label + disclaimer, unavailable fallback, request-error fallback,
  empty-but-available, no-sessionId no-call, accessible loading text.

## Run commands

```bash
# Backend
cd backend && ALLOW_MOCK_AUTH=true \
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=development \
  python -m pytest tests/ -q -W error::DeprecationWarning

# Frontend
cd frontend && npm run typecheck && CI=true npx vitest run && npm run build
```

## Known limitations / future phases

- **Provider:** only the stub provider ships. A real vendor provider is a
  follow-up (implement the Protocol; no schema/service changes needed).
- **Cache:** in-memory, process-local. Adequate for Phase 1; a shared cache
  (Redis) is a later enhancement — no schema change required.
- **Evidence:** Phase 1 attaches evidence references linked to activated
  indicators. Full RAG retrieval is out of scope for Phase 1 by design.
- **Frontend schema alignment for `emergency_contact`** (pre-existing, see
  AGENTS.md) is unrelated and not touched here.
- Prompt versioning is in place; a prompt bump invalidates the cache
  automatically via the cache key.
