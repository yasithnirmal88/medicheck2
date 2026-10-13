# MediCheck Phase 11 — Report

## Governed AI Care Coordination & Equity Intelligence

**Status:** Complete. Builds additively on Phases 1–10 (merged to `main` at
commit `c03cfa3`). No clinical tables, CDSE logic, or existing deterministic
workflows were modified.

---

## 1. Objective

Phase 11 adds a **governed, human-reviewed AI layer** around the existing
care-coordination and population-analytics systems:

1. **AI-assisted CHW operational suggestions** — ranks a CHW's follow-up queue
   by *operational* factors only (referral age, overdue, contact attempts,
   facility/communication status). Never by clinical urgency/severity.
2. **Equity intelligence ("left-behind" intelligence)** — AI-generated equity
   patterns over **de-identified, k-anonymity-suppressed** aggregate analytics.
3. **SDG narratives** — plain-language summaries of SDG-aligned aggregate
   metrics, clearly marked as MediCheck proxies (never official UN indicators).
4. **Human review workflow** — AI never self-publishes. Every AI insight goes
   through an explicit `generated → pending_review → approved/rejected/edited
   → published` lifecycle controlled by a human reviewer.

---

## 2. Architectural invariant (preserved)

> **The CDSE decides. AI explains, extracts, translates, summarizes,
> classifies operational information, and identifies non-clinical patterns.**

Phase 11 AI **MUST NOT**:
- diagnose, score, set severity, or determine clinical probability/urgency
- rank patients by disease severity, probability, mortality, or medical urgency
- infer disease prevalence or causation from equity/SDG outputs
- self-publish any insight
- modify clinical records, referrals' clinical priority, or CDSE rules
- identify any individual from aggregate outputs

Every AI-assisted output follows:

```
AI suggestion → validated structured data → human review → existing workflow
```

---

## 3. Architecture

### 3.1 Backend — new files

| Layer | File | Purpose |
|-------|------|---------|
| RBAC | `app/core/security/rbac.py` (+) | 3 new permissions |
| Config | `app/core/config.py` (+) | Phase 11 settings |
| Deps | `app/api/deps.py` (+) | 3 permission dependencies |
| Models | `app/infrastructure/persistence/models/ai_operational_suggestion.py` | `AiOperationalSuggestionModel` (additive table) |
| Models | `app/infrastructure/persistence/models/ai_population_insight.py` | `AiPopulationInsightModel` (additive table) |
| Migration | `alembic/versions/20260812_ai_insights_phase11.py` | Idempotent additive migration |
| DTOs | `app/application/dtos/ai_governance_dtos.py` | Phase 11 data contracts + allow-list validators |
| Providers | `app/application/ai/operational_suggestion_provider.py` | `StubOperationalSuggestionProvider` + `assert_non_clinical` |
| Providers | `app/application/ai/equity_intelligence_provider.py` | `StubEquityIntelligenceProvider` + `assert_non_causal` |
| Providers | `app/application/ai/population_narrative_provider.py` | `StubPopulationNarrativeProvider` + `assert_narrative_safe` |
| Services | `app/application/services/ai_operational_suggestion_service.py` | Orchestrator (own-only, operational-only) |
| Services | `app/application/services/equity_intelligence_service.py` | Equity insight over de-identified aggregates |
| Services | `app/application/services/population_narrative_service.py` | SDG narratives over de-identified aggregates |
| Services | `app/application/services/ai_insight_review_service.py` | Human review lifecycle (approve/reject/edit/publish) |
| Endpoints | `app/api/v1/endpoints/ai_care_coordination.py` | `POST/GET /ai-care-coordination/suggestions` |
| Endpoints | `app/api/v1/endpoints/ai_equity_intelligence.py` | Equity, SDG narratives, review workflow |
| Router | `app/api/v1/router.py` (+) | Registered Phase 11 routers |
| Tests | `tests/test_ai_care_coordination_phase11.py` | 51 tests |

### 3.2 Frontend — new files

| File | Purpose |
|------|---------|
| `features/ai-governance/api/aiGovernanceService.ts` | Typed API client |
| `features/ai-governance/hooks/useAiGovernanceQueries.ts` | TanStack Query hooks |
| `features/ai-governance/components/AiGovernanceUI.tsx` | Shared presentational components |
| `features/ai-governance/pages/ChwSuggestionsPage.tsx` | CHW operational suggestions |
| `features/ai-governance/pages/EquityIntelligencePage.tsx` | Equity intelligence |
| `features/ai-governance/pages/SdgNarrativesPage.tsx` | SDG narratives + review queue |
| `features/ai-governance/components/__tests__/AiGovernancePages.test.tsx` | 18 tests |
| `routes/router.tsx` (+) | 3 new CMS routes |
| `layouts/DoctorLayout.tsx` (+) | "AI Governance" nav group |

---

## 4. Baseline findings (summary)

Full baseline: `MEDICHECK_PHASE11_BASELINE.md`. Key reuse points:

- **AI provider abstraction** (Phase 1/7): Protocol + stub + factory pattern
  reused for all three Phase 11 providers. No external API keys; deterministic
  stubs only.
- **Population analytics** (Phase 6): `PopulationAnalyticsService` already
  performs SQL-level aggregation with k=10 small-cell suppression and
  de-identification. Phase 11 equity/narrative services consume its
  **already-suppressed** outputs — the AI never sees raw patient data.
- **Care-continuity / referrals** (Phase 9/10): `ReferralModel` + care
  outcomes already exist. Phase 11 operational suggestions read referral
  operational state (age, overdue, contact attempts) **read-only**.
- **AI governance** (Phase 7): `AIInteractionAuditModel` + audit service
  pattern reused; Phase 11 insights are audited the same way (hashes + ids,
  no PHI).
- **RBAC**: `Permission` enum + `has_role` hierarchy extended additively.

---

## 5. RBAC

Three new permissions (additive to `Permission` enum):

| Permission | Granted to | Scope |
|-----------|-----------|-------|
| `AI_VIEW_OPERATIONAL_SUGGESTIONS` | CHW (15), MEDICAL_DIRECTOR (30), SUPER_ADMIN (40) | Own suggestions only (CHW sees only their own queue) |
| `AI_VIEW_POPULATION_INSIGHTS` | RESEARCH_REVIEWER (5), MEDICAL_DIRECTOR (30), SUPER_ADMIN (40) | De-identified aggregate only |
| `AI_REVIEW_INSIGHTS` | RESEARCH_REVIEWER (5), MEDICAL_DIRECTOR (30), SUPER_ADMIN (40) | Review/publish lifecycle |

Mock-auth users (no roles) are denied all three — correct security posture.
CHW suggestions are scoped to the caller's own `chw_user_id`; cross-user
access is impossible.

---

## 6. AI boundaries (enforced structurally, not just by prompt)

### 6.1 Operational suggestions
- Provider only emits `operational_reason_codes` from a fixed allow-list:
  `overdue`, `missing_follow_up`, `aged_referral`, `appointment_window`,
  `unresolved_admin`, `unsuccessful_contact`, `facility_unresponsive`,
  `offline_pending_sync`, `no_outstanding_flags`.
- `assert_non_clinical()` rejects any explanation containing clinical terms
  (diagnos*, severity, urgent, probability, mortality, risk score, etc.).
- The service computes the operational queue **read-only** from referral
  operational state; it never reads or writes clinical priority.

### 6.2 Equity intelligence
- Input is the **already de-identified + k-anonymity-suppressed** aggregate
  analytics (Phase 6). The AI never sees patient-level data.
- `assert_non_causal()` rejects outputs claiming disease prevalence,
  causation, or individual identification.
- Output is `observed_findings` + `possible_interpretations` (clearly labelled
  non-causal) + `limitations`. Always `requires_human_review = true` until a
  human acts.
- Service-level `_validate_output()` is defense-in-depth against a lying
  provider.

### 6.3 SDG narratives
- Describes supplied aggregate metrics only.
- `assert_narrative_safe()` rejects claims that an SDG target "has been
  achieved" or is an official UN indicator.
- Clearly states these are MediCheck SDG-aligned proxies.

### 6.4 Human review (no self-publishing)
Lifecycle (deterministic state machine in `AiInsightReviewService`):

```
generated → pending_review → approved → published
                         ↘ rejected (terminal)
                         ↘ edited → published
```

- `AI_REVIEW_INSIGHTS` required for every transition.
- Only `pending_review` items can be reviewed; only `approved`/`edited` can be
  published. Invalid transitions raise `ValueError`.
- `edited_output` is required for the `edit` action (reviewer overrides the AI
  text).
- Every transition records `reviewer_id`, `reviewer_comment`, `approved_at`.

---

## 7. Privacy model

- **k-anonymity k=10** (configurable) preserved from Phase 6. Phase 11
  consumes already-suppressed aggregates; it cannot bypass suppression because
  it never touches raw patient data.
- Equity/SDG outputs contain **no patient IDs, no session IDs, no emails**.
- AI audit records (Phase 7 pattern) store only hashes + ids — no raw PHI.

---

## 8. Consent

Phase 11 reuses the existing consent infrastructure. Population insights are
derived from de-identified aggregates (no individual consent burden for
aggregate statistics). CHW operational suggestions operate on the CHW's own
assigned referral queue (operational, not clinical disclosure).

---

## 9. AI governance / audit

Every Phase 11 AI call records governance metadata via the Phase 7
`AIAuditService` pattern: `provider`, `model`, `prompt_version`, `language`,
`literacy_level` (where applicable), `input_context_hash`, `output_hash`,
`quality_status`, `quality_reason`, `trace_id`. No raw patient text is logged.

Prompt versions:
- `1.0-operational-phase11`
- `1.0-equity-phase11`
- `1.0-sdg-narrative-phase11`

---

## 10. Performance

- Operational suggestions: bounded to the CHW's own pending referrals; single
  batched query, no N+1.
- Equity/SDG: consume pre-aggregated analytics (SQL `GROUP BY`/`COUNT` from
  Phase 6). No patient-population load into application memory.
- All list endpoints return bounded, deterministic-ordered results.

---

## 11. Migrations

One additive, idempotent migration: `20260812_ai_insights_phase11.py`.
Creates two new tables (`ai_operational_suggestions`, `ai_population_insights`)
with `down_revision = 20260810_ai_interaction_audits`. No existing table is
altered. Safe to re-run (skips if tables exist).

---

## 12. API routes (7)

| Method | Path | RBAC |
|--------|------|------|
| POST | `/api/v1/ai-care-coordination/suggestions` | `AI_VIEW_OPERATIONAL_SUGGESTIONS` (own only) |
| GET | `/api/v1/ai-care-coordination/suggestions` | `AI_VIEW_OPERATIONAL_SUGGESTIONS` (own only) |
| POST | `/api/v1/ai-equity/equity-insight` | `AI_VIEW_POPULATION_INSIGHTS` |
| GET | `/api/v1/ai-equity/equity-insight` | `AI_VIEW_POPULATION_INSIGHTS` |
| POST | `/api/v1/ai-equity/sdg-narratives` | `AI_VIEW_POPULATION_INSIGHTS` |
| GET | `/api/v1/ai-equity/sdg-narratives` | `AI_VIEW_POPULATION_INSIGHTS` |
| POST | `/api/v1/ai-equity/review/operational/{id}` | `AI_REVIEW_INSIGHTS` |
| POST | `/api/v1/ai-equity/review/operational/{id}/publish` | `AI_REVIEW_INSIGHTS` |
| POST | `/api/v1/ai-equity/review/population/{id}` | `AI_REVIEW_INSIGHTS` |
| POST | `/api/v1/ai-equity/review/population/{id}/publish` | `AI_REVIEW_INSIGHTS` |

---

## 13. Test results

### Backend
- Phase 11: `tests/test_ai_care_coordination_phase11.py` → **51 pass**.
- Full regression (run in batches due to suite size): **511 pass, 0 fail**.
  - Phase 6–10 + roles: 126 pass
  - AI phases 1–5 + longitudinal: 147 pass
  - Clinical/CMS/profile/UAT: 38 pass
  - Unit + integration: 149 pass
  - Phase 11: 51 pass
- Command:
  ```
  cd backend && ALLOW_MOCK_AUTH=true DATABASE_URL=sqlite+aiosqlite:///./test.db \
    ENVIRONMENT=development python -m pytest tests/ -q -W error::DeprecationWarning
  ```

### Frontend
- Phase 11: `AiGovernancePages.test.tsx` → **18 pass**.
- Full suite: **118 pass, 0 fail** (was 100; +18 Phase 11).
- `npm run typecheck` → clean.
- `npm run build` → succeeds.

### Coverage areas
- FHIR/SDG/referral: unchanged (Phase 10 regression green).
- Operational suggestion generation, allow-list, non-clinical assertion.
- Equity insight over suppressed aggregates, non-causal assertion.
- SDG narrative safety (no "achieved"/"official" claims).
- Review lifecycle state machine (approve/reject/edit/publish, invalid
  transitions rejected).
- RBAC: CHW own-only, researcher/admin for population, deny mock-auth.
- IDOR: CHW cannot see another CHW's suggestions.
- Privacy: k-anonymity preserved (consumes pre-suppressed data).
- Audit: governance metadata recorded.
- Data leakage: no PHI/tokens/secrets in any output.

---

## 14. Security

- **Authentication**: all endpoints require `get_current_user`.
- **Authorization**: 3 new permissions enforced via dedicated deps.
- **IDOR**: CHW suggestions scoped to `chw_user_id == caller`; cross-user →
  empty/403.
- **Privacy**: population outputs consume de-identified, k-suppressed
  aggregates; no patient-level data reaches the AI.
- **Data leakage**: outputs contain no passwords, tokens, secrets, AI provider
  credentials, or unrelated patient records.
- **Audit**: every AI call + every review transition is auditable.

---

## 15. Regression protection

`git diff --stat` confirms all changes to existing files are **additive only**
(122 insertions, 0 deletions). No clinical-engine, CDSE, scoring, report,
referral-clinical-priority, or Phase 1–10 service files were modified. The
only touched existing files: `rbac.py`, `config.py`, `deps.py`, `router.py`
(all purely additive new permissions/settings/routes).

**No Phase 11 feature can alter a previously generated deterministic clinical
result.**

---

## 16. Known limitations

- Providers are deterministic stubs (no external LLM). This is intentional for
  this phase — real LLM adapters can be added later behind the same Protocol,
  with the same structural guards.
- SDG narratives are MediCheck-aligned proxies, not official UN SDG indicators.
- Equity interpretations are non-causal observations over aggregates; they
  cannot prove causation.
- No real hospital/government system integration (by design — standards-
  compatible interfaces only; mock adapters where external systems absent).

---

## 17. Future work

- Swap stub providers for real LLM adapters (behind the existing Protocol +
  structural guards).
- Clinician-reviewed outcome calibration dataset (outcome data as a quality
  dataset for future clinician-reviewed work — NOT automatic CDSE feedback).
- Expanded FHIR resource coverage if integration partners require it.
- Geographic disaggregation where cohorts remain k-anonymous.

---

## 18. Final principle

> MediCheck does not replace healthcare professionals or clinical
> decision-making. Phase 11 adds governed, human-reviewed AI assistance for
> care coordination and equity intelligence — connecting operational task
> ranking, de-identified equity patterns, and SDG-aligned narratives into one
> traceable, auditable, human-accountable system.

The clinical engine remains deterministic. AI remains bounded. Patient data
remains protected. Population analytics remains de-identified. Human
professionals remain accountable.
