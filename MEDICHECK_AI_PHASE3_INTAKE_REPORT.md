# MediCheck — Phase 3: AI Clinical Intake + Candidate Indicator Extraction

## IMPLEMENTATION STATUS

**PASS** — The feature is complete: extracted information safely converges into the existing deterministic questionnaire / CDSE pipeline. The AI is an INPUT INTERPRETATION layer only; the deterministic CDSE remains the clinical decision layer.

## Executive Summary

Phase 3 introduces **AI-assisted conversational clinical intake and candidate clinical-indicator extraction** — the core AI differentiator of MediCheck. A patient describes what they are experiencing in natural language; the AI extracts structured observations (preserving negation, temporality, and uncertainty) and maps them to **EXISTING** clinical indicators in the knowledge graph. The graph then recommends relevant **existing** question groups. The patient proceeds into the normal questionnaire session → existing branching engine → existing deterministic CDSE → report.

The defining principle is preserved:

> **AI understands what the patient says.
> The knowledge graph determines what is relevant.
> The questionnaire asks what must be clarified.
> The deterministic engine decides what the answers mean.**

The AI never diagnoses, scores, sets severity, activates indicators, creates recommendations/evidence, invents indicators, modifies questionnaire definitions, or overrides the deterministic engine. Unknown / hallucinated indicator IDs are rejected by allow-list validation (same pattern as Phase 1/2).

## Architecture

```
      ┌─────────────────────┐
      │ Patient Natural Text│
      └──────────┬──────────┘
                 ↓
         ┌───────────────┐
         │   AI Intake   │  (AIIntakeService — orchestrator)
         └───────┬───────┘
                 ↓
         Structured Observations  (ObservationDTO — negation/temporality/certainty)
                 ↓
         Candidate Indicators    (CandidateIndicatorDTO — bounded confidence)
                 ↓
      ┌──────────────────────┐
      │ Knowledge Graph      │  (CandidateValidationService — DB is authoritative)
      │ Validation           │  unknown / inactive / deleted IDs → REJECTED
      └──────────┬───────────┘
                 ↓
         Existing Questions      (AIIntakeQuestionService — deterministic, batched)
         Existing Groups         (source = "cms")
                 ↓
         Existing Branching      (untouched — QuestionDependencyModel)
                 ↓
      ┌──────────────────────┐
      │ Deterministic CDSE   │  (untouched)
      └──────────┬───────────┘
                 ↓
              Report
                 ↓
         Phase 1 AI Explanation
                 ↓
          Phase 2 Evidence RAG
```

## AI Intake Flow

`text → bounded indicator catalog → AIClinicalIntakeProvider (stub) → parse JSON → build ObservationDTO → CandidateValidationService → AIIntakeQuestionService → IntakeResponse`.

1. **Bounded catalog** (`AIIntakeService._build_catalog`): deterministically retrieves active, non-deleted indicators (`is_active=True`, `deleted_at IS NULL`), ordered by name, capped at `CATALOG_LIMIT=60`. No vector DB; no full graph dump. The provider may ONLY cite IDs in this catalog.
2. **Provider extraction** (`AIClinicalIntakeProvider.extract_candidates`): returns a JSON string. The default `StubClinicalIntakeProvider` is deterministic — keyword + bounded synonym matching, negation/uncertainty/temporality/duration/frequency detection. No network, no external API key. A real vendor provider plugs in via the Protocol.
3. **Parse** (`parse_provider_json`): malformed JSON → `ValueError` → safe fallback.
4. **Observations** (`_build_observations`): converts raw provider observations into validated `ObservationDTO`, bounded to 30. Negation (`polarity=negative`), temporality (`historical`/`recurring`), and uncertainty (`certainty=uncertain`, lower confidence) are preserved so the deterministic engine never treats a negated/historical mention as a current positive finding.
5. **Validation** (`CandidateValidationService.validate`): the database is authoritative. Every candidate `indicator_id` must be in the catalog (active + non-deleted). Unknown/inactive/deleted IDs are rejected (never created, never inserted). Out-of-range confidence is rejected. Orphan observation references are dropped. Candidates are deterministically ordered (confidence desc, then id) and capped.
6. **Question discovery** (`AIIntakeQuestionService.discover`): validated candidate indicator IDs → batched `QuestionIndicatorLinkModel` (active) → batched `QuestionModel` (status=active, deleted_at IS NULL) → batched `QuestionGroupModel` (is_active, deleted_at IS NULL). No N+1. Deterministic ranking by group `display_order` then question `order_index`. Duplicates removed. Template scope respected when supplied.

## Observation Contract

`ObservationDTO` (Pydantic v2, `extra="forbid"`): `id`, `source_text`, `normalized_concept`, `observation_type` (symptom|history|behavior|measurement|context|other), `certainty` (reported|suspected|uncertain), `temporality` (current|recent|historical|recurring|unknown), `polarity` (positive|negative|uncertain), `severity_description` (patient wording, NOT clinical severity), `duration`, `frequency`, `context`, `body_system`, `confidence` (extraction confidence ∈ [0,1]).

## Candidate Indicator Contract

`CandidateIndicatorDTO` (Pydantic v2, `extra="forbid"`): `indicator_id` (MUST exist + be active + not deleted), `confidence` ∈ [0,1] (extraction confidence — NOT clinical probability), `observation_ids` (from the same intake), `reason`, `uncertainty`, `source` (`ai_extraction`). The AI cannot assign deterministic score values or clinical severity.

## Knowledge Graph Validation

`CandidateValidationService` never trusts the AI's knowledge of the DB. It re-validates every candidate against the catalog built from active+non-deleted indicators. A `ValidationTrace` records `accepted`, `rejected_unknown_indicator`, `rejected_inactive_indicator`, `rejected_deleted_indicator`, `rejected_invalid_confidence`, `rejected_orphan_observations` for observability.

## Question Selection

`AIIntakeQuestionService`:
- receives validated candidate indicator IDs;
- finds related question groups via active `QuestionIndicatorLinkModel` → `QuestionModel` → `QuestionGroupModel`;
- ranks deterministically (group `display_order`, then question `order_index`);
- removes duplicate questions;
- respects existing dependencies (the branching engine is untouched);
- respects assessment template scope when supplied;
- returns `CandidateQuestionDTO` / `CandidateQuestionGroupDTO` with `source="cms"`.

The AI does NOT determine final question order — the deterministic branching engine does at runtime.

## Security

- Reuses existing `get_current_user` authentication (RBAC preserved).
- If `session_id` is supplied, ownership is verified; another user's session → 404 (no information leak).
- AI extraction is scoped to the authenticated user/session — no cross-patient intake.
- Candidate indicator IDs are validated against the current application catalog. Client-supplied IDs are never trusted.
- No PHI beyond the patient's own message is sent to the provider (no auth tokens, passwords, unrelated records, or DB credentials).

## RBAC

Patient AI intake does NOT require CMS permissions. CMS roles remain the authors of the knowledge graph. AI references the CMS knowledge graph; only published/active content influences patient-facing intake (the catalog filters `is_active=True`, `deleted_at IS NULL`).

## Safety Boundaries

The AI MUST NEVER (and structurally cannot): diagnose; declare a condition; assign clinical severity; calculate CDSE scores; activate indicators in the global graph; create recommendations/evidence; modify questionnaire definitions/branching; publish CMS content; alter clinical thresholds; override the deterministic engine; bypass RBAC; modify assessment history without deterministic validation.

The AI MAY: extract observations; normalize natural language; identify candidate existing indicators; estimate extraction confidence; identify uncertainty/negation/temporality; suggest relevant existing question groups; suggest informational clarification questions; explain why an indicator may be relevant; identify ambiguity.

`IntakeResponse` has a validator that rejects candidate `reason` text reading as a diagnosis (`you have`, `diagnosed`, `confirmed condition`, `disease confirmed`). AI failure → `available=false` with a safe fallback message; the standard questionnaire remains functional.

## Provider Architecture

`AIClinicalIntakeProvider` Protocol (`intake_provider.py`) with `extract_candidates(context) -> str`. The service depends on the Protocol, not a vendor SDK. `StubClinicalIntakeProvider` (default, deterministic, no network) is selected via `settings.ai_provider`. A real vendor provider implements the Protocol — no service-layer change. `AIIntakeProviderError` maps any failure to a single safe fallback.

## API Contract

`POST /api/v1/ai/intake/extract`

Request:
```json
{ "session_id": "...", "text": "I get tired when climbing stairs..." }
```
`session_id` is optional; when present, ownership is verified.

Response (`IntakeResponse`):
```json
{
  "trace_id": "...",
  "prompt_version": "1.0",
  "observations": [ { "id": "...", "source_text": "...", "normalized_concept": "...",
    "observation_type": "symptom", "certainty": "reported", "temporality": "current",
    "polarity": "positive", "severity_description": null, "duration": null,
    "frequency": null, "context": null, "body_system": "...", "confidence": 0.6 } ],
  "candidate_indicators": [ { "indicator_id": "...", "confidence": 0.8,
    "observation_ids": ["..."], "reason": "...", "uncertainty": null, "source": "ai_extraction" } ],
  "candidate_question_groups": [ { "question_group_id": "...", "code": "...", "name": "...",
    "body_system_id": "...", "linked_indicator_ids": ["..."], "question_count": 3, "source": "cms" } ],
  "candidate_questions": [ { "question_id": "...", "question_code": "...", "text": "...",
    "question_group_id": "...", "question_group_name": "...", "body_system_id": "...",
    "linked_indicator_ids": ["..."], "source": "cms" } ],
  "clarifications": [ { "text": "...", "source": "ai_generated", "observation_id": "...",
    "linked_indicator_id": null, "linked_question_id": null } ],
  "available": true,
  "message": null
}
```
On any failure: `available=false`, empty candidates, safe `message`. Internal provider details are not exposed.

## Frontend Flow

- New route `/assessments/intake` (`IntakePage.tsx`) — an OPTIONAL assisted entry point. The standard questionnaire (`/assessments`) remains fully available.
- An "AI intake" banner on `AssessmentSelectionPage` links to it.
- The patient describes symptoms in a textarea; the result shows extracted observations (with negated/uncertain/ temporality/duration/frequency badges), candidate indicator count, clarifying questions, and recommended existing question groups.
- The user can: edit the description; reject an interpreted observation; skip AI intake; or continue to a recommended/standard assessment, which starts a NORMAL questionnaire session (`useStartSession`) → existing branching → existing CDSE.
- Language is non-diagnostic: "we identified some information that may be relevant", "let's ask a few more questions", "your answers will be evaluated using MediCheck's clinical assessment system", "this is not a diagnosis".

## Testing

### Backend (`tests/test_ai_intake_phase3.py` — 35 tests)

Extraction (9): positive symptom, multiple observations, negation, historical, uncertain, duration, frequency, malformed provider, unavailable provider.

Candidate indicators (7): valid ID accepted, unknown ID rejected, inactive ID rejected, deleted ID rejected, hallucinated ID rejected, invalid confidence rejected, orphan observations dropped.

Question discovery (6): candidate → existing group, inactive question excluded, deleted question excluded, branching rules preserved, duplicate questions removed, template scope respected.

Security (4): unauthorized → 401/403, another user's session → 404, missing session → 404, invalid session → 404; plus happy-path endpoint.

Deterministic integrity (4): CDSE scores/indicator scoring unchanged, report generation unchanged (read-only).

Safety (4): AI cannot set severity, cannot create indicators, cannot create recommendations, cannot bypass published knowledge; plus the diagnostic-language validator.

### Frontend (`__tests__/IntakePage.test.tsx` — 10 tests)

Intake renders, text submission, loading state, unavailable state, extracted observations, user rejection, question transition, skip AI, edit description, clarifying questions, non-diagnostic language.

### Results

| Suite | Before | After |
|---|---|---|
| Backend | 217 | **252** (+35 Phase 3) |
| Frontend | 33 | **43** (+10 Phase 3) |
| TypeScript | clean | **clean** |
| Build | OK | **OK** (10.95s) |

## Performance

- Bounded indicator catalog (limit 60) — never the whole graph.
- Batched queries (indicator→questions, questions→groups) — no N+1.
- Deterministic ranking — no LLM relevance calls.
- No vector DB introduced (intentional; slots into the same contract later if justified).

## Observability

`IntakeTrace` records safe metrics per run: `trace_id`, prompt_version, provider, model, observations/candidates/validated counts, rejected counts, question_groups/questions/clarifications counts, `available`, `error`. Logged via `logger.info`. **Raw patient text is NOT logged.**

## Traceability

Every intake run carries a `trace_id` (`new_trace_id`). The trace captures intake request, prompt version, provider, model, candidate observations, candidate indicators, rejected candidates, selected question groups, clarifications, and validation result.

## Persistence Trade-off

Phase 3 uses **session-scoped in-memory state** — AI observations/candidates are NOT persisted to the database. Rationale:
- AI intake is an input interpretation aid, not a clinical record. The clinical record is the deterministic assessment/report (already persisted by the existing pipeline).
- No new tables means zero migration risk and zero chance of AI content polluting CDSE tables.
- `trace_id` is returned for client-side correlation; observability is via structured logs.
- Trade-off: intake runs are not replayable from the DB. If persistence/replay is later required, additive tables (`ai_intake_sessions`, `ai_observations`, `ai_candidate_indicators`, `ai_intake_traces`) can be introduced without touching CDSE tables — the service contract already separates these concerns.

## Database Status

- **No migrations created.**
- **No tables changed.**
- **No existing data modified.**
- **No seed data changed.**
- Intake is fully read-only w.r.t. the clinical schema (verified by regression tests: indicator count, indicator scoring weights, assessment session count all unchanged after intake).

## Regression Status

- **Phase 1** (AI Explanation): unchanged — intact and passing.
- **Phase 2** (Evidence RAG): unchanged — intact and passing.
- **CDSE**: unchanged — `ClinicalDecisionService` untouched; intake never invokes it.
- **Questionnaire**: unchanged — branching engine, `QuestionDependencyModel` untouched (test-verified).
- **CMS**: unchanged — knowledge graph remains the source of truth; AI references it read-only.
- **RBAC**: unchanged — patient intake needs no CMS permissions; ownership verified.
- Full backend suite: 252 pass (0 regressions). Full frontend suite: 43 pass.

## Known Limitations

- Only the deterministic stub provider ships; a real vendor provider plugs in via the Protocol (no schema/service changes).
- The stub uses a bounded synonym map for common indicator keywords; a real LLM provider would generalize this. The map is not a clinical knowledge base.
- Question discovery recommends existing groups by `code`; the frontend maps group codes to assessment templates by best match and falls back to `/assessments` if no backend template matches.
- Intake is session-scoped/in-memory (no DB persistence) — see Persistence Trade-off.
- No semantic/vector retrieval (intentional).
- No multilingual or voice intake (future).

## Future Semantic Retrieval

The bounded catalog retrieval is deterministic. A future phase could add coarse semantic candidate sub-selection (embedding-based) before the provider, then AI extraction/ranking. The architecture already supports this: the catalog is the controlled vocabulary; the provider contract is unchanged; the validation service still rejects unknown IDs. No vector DB is introduced unless justified.

## Future Multilingual Intake

The provider Protocol is language-agnostic; a multilingual provider can normalize any language into the same observation contract. The validation + question-discovery layers are language-independent (they operate on indicator IDs and graph links).

## Future Voice Intake

Voice intake would add a speech-to-text front-end producing the same `text` input; the rest of the pipeline is unchanged. No clinical-safety boundary changes.

## Next Phase (recommended)

The safest next AI capability is **AI-assisted adaptive question surfacing hints** — using the validated candidate indicators to surface *existing* clarifying questions already in the graph earlier in the questionnaire flow (purely additive UX hints; the branching engine still decides). This reuses the Phase 3 validation + discovery services and introduces no new clinical authority.

## ROOT ARCHITECTURE

Additive AI intake layer feeding the untouched deterministic CDSE. Patient text → AI extraction → validated candidate indicators → existing questions → existing branching → existing CDSE → report → Phase 1 explanation → Phase 2 evidence RAG.

## AI ROLE

Input interpretation only: extract observations, normalize language, map to EXISTING indicators, estimate extraction confidence, identify uncertainty/negation/temporality, suggest existing question groups, suggest informational clarifications. Proposes; never decides.

## DETERMINISTIC ROLE

The knowledge graph validates (DB authoritative); the questionnaire + branching ask/clarify; the CDSE scores and decides conditions/recommendations/severity. Unchanged.

## CONTENT STATUS

The CMS knowledge graph is the sole authoritative clinical knowledge source. AI references it read-only; it never creates or duplicates clinical knowledge.

## SAFETY STATUS

Every boundary is structurally enforced: allow-list validation rejects unknown/inactive/deleted IDs; the response validator rejects diagnostic language; AI failure → safe fallback; the standard questionnaire always works; intake is read-only w.r.t. the clinical schema; RBAC + session ownership preserved.

## TEST STATUS

Backend 252 pass (217 prior + 35 new). Frontend 43 pass (33 prior + 10 new). TypeScript clean. Build OK. Zero regressions across Phase 1, Phase 2, CDSE, questionnaire, CMS, RBAC.

## DATABASE STATUS

No migrations. No tables changed. No data modified. No seed changes. Read-only w.r.t. clinical schema.

## CONFIDENCE

**HIGH**
