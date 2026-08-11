# Medicheck — Phase 2: Evidence-Grounded RAG for Clinical Report Explanation

Status: **Phase 2 complete.** Evidence-grounded retrieval-augmented
generation (RAG) added on top of the Phase 1 AI explanation layer. The
deterministic CDSE, scoring, schemas, and Phase 1 provider abstraction are
**unchanged**.

> Phase 2 does **not** perform diagnosis, prediction, symptom extraction,
> adaptive question generation, or autonomous clinical decision-making. The
> deterministic clinical decision-support engine remains the source of truth;
> RAG only supplies approved supporting evidence and explanatory context.

## 1. Objective

Allow the AI explanation layer to explain clinical findings using **approved
evidence already stored in MediCheck's clinical evidence repository**, so the
patient can see *why* a finding was highlighted and *what evidence* supports a
recommendation — grounded in MediCheck's own evidence, never invented.

## 2. Existing Evidence Architecture (verified against source)

The baseline's conceptual structure (`indicator_sources`, `MedicalEvidence`)
did **not** match the actual source. Inspection of the code found:

- **`EvidenceReferenceModel`** (`evidence_references` table) — the seeded,
  approved clinical evidence (guidelines such as ACC/AHA, KDIGO, ESC, NICE).
  Fields: `id, question_id, title, url, source, evidence_level, summary` +
  `SoftDeleteMixin` (`deleted_at`) + `TimestampMixin`. It has **no** `status`
  or `is_active` column. **Eligibility = `deleted_at IS NULL`** (not
  soft-deleted). This is the evidence store wired into the knowledge graph.
- **`MedicalEvidenceModel`** (`medical_evidence` table) — a richer parallel
  entity with a `draft`/`published` lifecycle, `is_active`,
  `indicator_ids`, `disease_ids`, `body_system_id`. It is **not seeded** and
  **not wired** into the indicator→evidence link graph (the link table's
  `evidence_id` is typed generically). It is therefore **not used** for
  Phase 2 retrieval. The CMS `ClinicalEvidenceService` references fields that
  do not exist on `EvidenceReferenceModel` (`citation`, `pmid`, `doi`,
  `confidence_score`, `is_active`) — pre-existing dead/broken code, not
  touched here. Wiring `MedicalEvidenceModel` into retrieval is a documented
  future item (would require fixing that service + the link graph).
- **Knowledge-graph link tables** (`links.py`):
  - `IndicatorEvidenceLinkModel` (indicator ↔ evidence, `active` flag) — the
    **primary grounding edge**.
  - `IndicatorConditionLinkModel`, `ConditionRecommendationLinkModel`,
    `IndicatorRecommendationLinkModel`, `ConditionLaboratoryTestLinkModel`,
    `BodySystemConditionLinkModel`.
  - There is **no** direct condition↔evidence or recommendation↔evidence link
    table. Conditions/recommendations reach evidence **transitively** via
    their linked indicators.

## 3. Retrieval Architecture

```
Report (AssessmentResultModel) — activated indicators / conditions / recs
        │
        ▼
EvidenceRetrievalService.retrieve(...)
        │
        ├─ Tier 1: IndicatorEvidenceLinkModel(active) → EvidenceReferenceModel(deleted_at IS NULL)
        ├─ Tier 2: conditions → IndicatorConditionLinkModel → indicators → evidence
        └─ Tier 3: recommendations → (IndicatorRecommendationLinkModel
                   | ConditionRecommendationLinkModel → IndicatorConditionLinkModel)
                   → indicators → evidence
        │
        ▼
dedup by evidence_id (keep best tier/score) → rank → per-entity cap → global limit
        │
        ▼
RetrievalResult(evidence: list[RetrievedEvidenceContext])
        │
        ▼
AIExplanationService._build_context → ReportExplanationContext.evidence
```

All retrieval is **batched** (`in_()` per id set) to avoid N+1 queries. The
service is wired into `AIExplanationService` (which keeps the Phase 1
provider abstraction intact):

```
AIExplanationService
   ├── EvidenceRetrievalService   (NEW — Phase 2)
   └── AIExplanationProvider      (unchanged abstraction; stub updated)
```

Retrieval never bypasses repositories to query the DB from the route; it
lives in the application service layer, consistent with the existing
architecture.

## 4. Evidence Eligibility Rules

Only evidence appropriate for patient-facing explanation is retrieved:

- `EvidenceReferenceModel.deleted_at IS NULL` (not soft-deleted).
- Reached only via an **active** link (`IndicatorEvidenceLinkModel.active == True`).
- Inactive links and soft-deleted evidence are excluded.

**Never exposed:** draft/rejected/archived evidence, internal CMS notes,
unpublished content. (Note: `EvidenceReferenceModel` has no status field, so
the draft/published distinction does not apply to the store actually wired
into the graph; the richer `MedicalEvidenceModel` lifecycle is unused — see
§2/§16.)

## 5. Ranking Logic (deterministic — the LLM never decides relevance)

`_rank_score` produces a deterministic score in `[0,1]`:

- **Tier weight** (60%): indicator-direct (0.9) > condition-transitive (0.7) >
  recommendation-transitive (0.6).
- **Evidence-level weight** (25%): A(1.0) > B(0.8) > C(0.6) > D(0.4); "Level I/II…"
  mapped; unknown → neutral 0.5.
- **Recency** (≤0.05, weak tiebreaker): `EvidenceReferenceModel` has no
  publication date, so `created_at` is used as a proxy (timezone-safe).
- **Text relevance** (10%): deterministic keyword-overlap between the evidence
  title and the linked entity's name — **not** semantic/vector similarity.

After dedup (keep best candidate per evidence id), a **per-linked-entity cap**
(`ai_rag_per_entity_cap`, default 2) prevents one indicator from monopolising
the budget, then a **global limit** (`ai_rag_evidence_limit`, default 5).

## 6. AI Context

`ReportExplanationContext` now carries `evidence: list[RetrievedEvidenceContext]`
plus `evidence_available: bool` and `prompt_version`. Each
`RetrievedEvidenceContext` includes `id, title, source, url, evidence_level,
summary, excerpt, relevance, retrieval_tier, linked_entity_type,
linked_entity_id` — **only** retrieved, eligible evidence. No unrelated DB
content, no PHI, no auth tokens are sent to the AI.

## 7. Citation Validation (anti-hallucination)

`AIExplanationResponse` was extended:

- `KeyFinding.evidence_ids` and `RecommendationExplanation.evidence_ids`.
- `bind_context()` now also accepts `allowed_evidence_ids` (the retrieved
  set). The `model_validator` **rejects** any cited evidence id not in the
  retrieved allow-list. A hallucinated `EV-999` → `ValueError` → safe
  `UNAVAILABLE_FALLBACK`. This is enforced structurally, not just by prompt.
- The Phase 1 indicator/recommendation id validators continue to run unchanged.

## 8. Safety Boundaries

- AI only **explains** the deterministic result; it never diagnoses, scores,
  sets severity, creates recommendations, or invents evidence.
- The prompt (v2.0) forbids inventing citations/evidence ids and requires
  stating insufficiency ("no supporting evidence was available") rather than
  fabricating.
- **Retrieval failure never breaks the clinical report**: on any retrieval
  error the service explains with no evidence and the AI states that none was
  available. The report endpoint still surfaces the deterministic report.
- **Zero evidence is explicit**: `evidence_available=False` and the stub
  emits `NO_EVIDENCE_AVAILABLE_MESSAGE`; the AI never pretends evidence exists.
- The AI preserves the distinction between finding / possible condition /
  risk indicator / recommendation / confirmed diagnosis.

## 9. API Changes

No new endpoints. The existing `POST /api/v1/report/{session_id}/explanation`
now returns the enriched response (additive fields):

```json
{
  "summary": "...",
  "key_findings": [
    {"title": "...", "explanation": "...", "source_indicator_ids": [],
     "evidence_ids": ["<retrieved id>"]}
  ],
  "recommendation_explanations": [
    {"recommendation_id": "...", "explanation": "...", "evidence_ids": []}
  ],
  "evidence_notes": [...],
  "limitations": "...",
  "disclaimer": "...",
  "available": true,
  "prompt_version": "2.0",
  "trace_id": "...",
  "retrieved_evidence": [
    {"id": "...", "title": "...", "source": "...", "url": "...",
     "evidence_level": "A", "excerpt": "...", "relevance": 0.91,
     "retrieval_tier": 1, "linked_entity_type": "indicator",
     "linked_entity_id": "..."}
  ],
  "evidence_available": true
}
```

The existing `/api/v1/assessment/{session_id}/explanation` (CDSE raw
explanations) is distinct and unaffected.

## 10. Frontend Changes

`ReportExplanation.tsx` (the same Phase 1 component, not a competing UI) was
extended:

- A dedicated, visually-distinguishable **Evidence** section (white card,
  `FileText` icon) renders retrieved evidence: `[n]` index, title, evidence
  level, source, relevance %, excerpt, and an approved `url` link
  (`rel="noopener noreferrer"`). A note states these references are
  retrieved from the approved repository and are **not** AI-generated.
- Per-finding **citation markers** (`[1]`, `[2]`…) link findings to their
  cited retrieved evidence; markers only resolve for ids that were actually
  retrieved (a fabricated id renders nothing).
- When `evidence_available` is false, the section states **"No supporting
  evidence was available from the MediCheck evidence repository."** — no fake
  citation links.
- The deterministic report remains fully visible; the AI card is additive.
- The AI-generated label + disclaimer are always present.

## 11. Testing

- **Backend: 217 passed** (202 prior + 15 new), no regression.
  `tests/test_ai_rag_phase2.py`:
  - Retrieval: direct indicator, condition-transitive, inactive link
    excluded, soft-deleted excluded, ranking (tier+level), evidence limit,
    zero evidence, duplicate removal. (Condition/recommendation transitive
    both exercised via the seeded indicator→condition link.)
  - AI validation: valid citation accepted, hallucinated citation rejected,
    hallucinated indicator rejected, no-evidence states insufficiency.
  - Security: unauthorized assessment → AI never called; no cross-patient
    evidence (User A never sees User B's evidence).
  - Deterministic integrity: RAG is read-only (scores/indicators/conditions/
    recommendations unchanged after explanation).
- **Frontend: 33 passed** (30 prior + 3 new), typecheck clean, build succeeds.
  New `ReportExplanation.test.tsx` cases: evidence section renders with
  retrieved evidence + citation marker linking to the approved URL; no-evidence
  state; fabricated evidence id renders no citation marker.

## 12. Performance

- Retrieval is **batched** with `in_()` per id set (one query per tier/traversal
  step), so no N+1 across indicators/conditions/recommendations.
- The `_select` dedup/rank/limit pass is in-memory over the candidate set
  (bounded by the global limit after the per-entity cap), so it is O(n) with
  a small constant.
- No external infrastructure (no vector DB, no cache service) was added.
- The in-memory explanation cache (Phase 1) is keyed by
  `(trace_id, prompt_version)`; the prompt bump to `2.0` invalidates stale
  v1.0 entries automatically.

## 13. Security

- Authorisation + ownership are reused from Phase 1 (`get_current_user` +
  `SQLReportRepository.get_report_by_session`). Unauthorized access → 404
  and the AI/retrieval are never invoked.
- **No cross-patient evidence**: retrieval is seeded exclusively from the
  caller's own deterministic `AssessmentResultModel` (their activated
  indicators/conditions/recommendations). Evidence itself is shared clinical
  content, but the retrieval context is derived from the authorised report.
- No PHI is sent to the AI: the input context carries only ids, names,
  severities, scores, evidence references.

## 14. Database Impact

**None.** No migrations, no new tables, no schema changes. Phase 2 is
read-only over the existing `evidence_references`, `indicator_evidence_links`,
`indicator_condition_links`, `indicator_recommendation_links`, and
`condition_recommendation_links` tables. Traceability reuses the existing
`trace_id` and the response's `retrieved_evidence` + `prompt_version`.

## 15. Phase 1 Compatibility

- The provider abstraction is intact: `AIExplanationService` now composes
  `EvidenceRetrievalService` + `AIExplanationProvider`. A future real provider
  plugs in by implementing the `AIExplanationProvider` Protocol — no
  service/DTO/schema changes required.
- The Phase 1 prompt is preserved as `V1_SYSTEM_PROMPT`; `PROMPT_VERSION`
  is `2.0`.
- All 13 Phase 1 tests still pass unchanged.
- The cache key includes `prompt_version`, so v1.0 and v2.0 entries do not
  collide.

## 16. Known Limitations

- Only the deterministic **stub** provider ships; a real vendor provider is a
  follow-up (implement the Protocol; no schema/service changes).
- `EvidenceReferenceModel` has **no publication date**; recency ranking uses
  `created_at` as a weak proxy.
- `EvidenceReferenceModel` has **no full-text** fields; the excerpt is the
  (already short) `summary`, bounded by `ai_rag_excerpt_max_chars`.
- `MedicalEvidenceModel`'s richer draft/published lifecycle is **not** wired
  into the retrieval graph (see §2). Using it would require fixing the broken
  `ClinicalEvidenceService` and adding/pointing link tables — a separate
  CMS/evidence-management follow-up.
- No direct condition↔evidence or recommendation↔evidence link tables exist;
  those reach evidence transitively via indicators.
- Cache is process-local (Phase 1 behaviour); a shared cache is a later
  enhancement requiring no schema change.
- No semantic/vector retrieval (intentional — see §17).

## 17. Future Vector/Semantic Retrieval

Phase 2 deliberately uses **structured retrieval + metadata filtering +
deterministic ranking** (no vector DB). Rationale: MediCheck's evidence store
is already structured and graph-linked, which gives simpler deployment,
easier auditing, lower cost, deterministic retrieval, and easier clinical
governance. Semantic/vector retrieval (pgvector etc.) can be added later if
justified — it would slot into `EvidenceRetrievalService` behind the same
contract, with no change to the AI/service/DTO layers.

## Run commands

```bash
# Backend
cd backend && ALLOW_MOCK_AUTH=true \
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=development \
  python -m pytest tests/ -q -W error::DeprecationWarning

# Frontend
cd frontend && npm run typecheck && CI=true npx vitest run && npm run build
```

## Next Phase

The next major phase is **AI Clinical Intake + Candidate Indicator
Extraction** (the patient describes symptoms → AI extracts observations →
candidate indicators → knowledge graph → targeted follow-up questions →
existing branching engine → deterministic CDSE). **Not implemented in Phase
2.** Per spec, the AI discovers what the patient may not realise is
clinically relevant; the deterministic clinical engine decides what those
observations mean.
