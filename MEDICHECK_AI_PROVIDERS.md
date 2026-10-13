# MediCheck AI Providers — Stubs vs Real Vendors

How the AI layer switches between deterministic stubs (local/dev/CI) and real
OpenAI-compatible LLM + STT vendors, how to verify the switch, and the safety
invariants that hold in both modes.

## 1. Architecture and switching

Five Protocols, one pattern: services depend on the Protocol, factories build
the implementation from settings. Interfaces are stable — adding a vendor
never changes the service layer.

| Consumer | Setting | Stub | Real (HTTP) |
|---|---|---|---|
| Report explanation (`AIExplanationService`) | `AI_PROVIDER` | `stub`, `personalized-stub` | `openai`, `openai-compatible` |
| Intake extraction (`AIIntakeService`) | `AI_PROVIDER` (same knob) | `stub` (+`personalized-stub` maps here) | `openai`, `openai-compatible` |
| Trajectory explanation (`LongitudinalExplanationService`) | `AI_PROVIDER` (same knob) | `stub` (+`personalized-stub` maps here) | `openai`, `openai-compatible` |
| Speech-to-text (`AIIntakeService.transcribe_audio`) | `STT_PROVIDER` | `stub` | `openai`, `whisper`, `openai-compatible` |
| CHW queue ranking | `CHW_QUEUE_PROVIDER` | `stub` (only option) | — none implemented |

Real implementations (no vendor SDK, plain `httpx`):

- `app/application/ai/http_chat_provider.py` — `OpenAICompatibleChatProvider`
  implements all three LLM Protocols. `POST {base}/chat/completions` with
  `temperature=0` + `response_format: json_object`. Reuses the versioned
  system prompts verbatim (Phase 1 v2.0 / intake 1.0 / longitudinal 1.0).
  Returns the raw JSON string; parsing + allow-list validation stay in the
  services. Failures raise the caller's own error type (`AIProviderError` /
  `AIIntakeProviderError` / longitudinal `AIProviderError`) so existing
  fallbacks + audit engage unchanged.
- `app/application/ai/http_stt_provider.py` — `OpenAICompatibleSTTProvider`
  implements `SpeechToTextProvider`. `POST {base}/audio/transcriptions`
  (multipart). Audio stays transient: validated, sent once, never stored or
  logged. Failures raise `SpeechToTextError` → the endpoint falls back to
  "type instead".

Fail-fast selection (`app/application/ai/provider_selection.py`): any
explicitly configured name that is not a known stub/real name — or a real
name without credentials — raises `AIConfigurationError` at factory time.
**Unknown names never silently fall back to a stub.** Stubs remain the safe
default; CI/dev are unaffected unless they opt into a real name.

## 2. Environment variables / settings

| Variable | Default | Required when | Notes |
|---|---|---|---|
| `AI_PROVIDER` | `stub` | — | `stub` \| `personalized-stub` \| `openai` \| `openai-compatible` |
| `AI_MODEL` | `""` | `AI_PROVIDER=openai*` | Explicit model, e.g. `gpt-4o-mini`. No silent default. |
| `AI_API_KEY` | `""` | `AI_PROVIDER=openai*` | Never logged; presence-only in health output. |
| `AI_BASE_URL` | `""` (= OpenAI default) | — | Any Bearer-auth OpenAI-compatible endpoint. Azure *native* shape unsupported — use a compatible gateway. |
| `AI_MAX_RETRIES` | `1` | — | Retries after first attempt; transient failures only (429/5xx/network). Auth errors never retry. |
| `AI_REQUEST_TIMEOUT_SECONDS` | `20.0` | — | Now actually enforced via `httpx.Timeout` (previously dead config). |
| `STT_PROVIDER` | `stub` | — | `stub` \| `openai` \| `whisper` \| `openai-compatible` |
| `STT_MODEL` | `""` (= `whisper-1`) | — | Defaults to `whisper-1` when unset. |
| `STT_API_KEY` | `""` | `STT_PROVIDER=openai*` | New setting (did not exist before). |
| `STT_BASE_URL` | `""` (= OpenAI default) | — | New setting. |
| `STT_REQUEST_TIMEOUT_SECONDS` | `20.0` | — | Now actually enforced (previously dead config). |
| `CHW_QUEUE_PROVIDER` | `stub` | — | Only `stub` implemented; anything else raises. |
| `AI_BUDGET_USER_HOURLY_REQUESTS` | `30` | — | Per-user hourly vendor-call budget (`0` = tier disabled). Stubs bypass. |
| `AI_BUDGET_USER_DAILY_REQUESTS` | `200` | — | Per-user daily vendor-call budget (`0` = tier disabled). |
| `AI_BUDGET_GLOBAL_DAILY_REQUESTS` | `20000` | — | Global daily circuit breaker (`0` = tier disabled). |

## 3. Health-check mechanism

`GET /api/v1/ai/health` (`app/api/v1/endpoints/ai_health.py`), RBAC-gated
with the existing `get_ai_governance_user` dep (RESEARCH_REVIEWER+).

- Default (`probe=false`): zero network I/O. Reports per consumer —
  `explanation`, `intake`, `longitudinal`, `stt`, `queue` — the configured
  name, resolved implementation class, credential *presence* (never values),
  model, base-URL host, and any misconfiguration error. Misconfiguration is
  reported in the body (HTTP 200), never raised.
- `?probe=true`: one lightweight `GET {base}/models` per configured vendor
  (reachability + auth, no inference tokens, no PHI) → `healthy` /
  `auth_failed` / `unreachable`. Probe timeout is a short fixed 5 s.

## 4. Test coverage (`tests/test_ai_providers_http.py`, 53 tests, + `tests/test_ai_budget.py`, 13 tests)

- **Selection/fail-fast (14):** stub defaults, `personalized-stub` mapping,
  unknown names raise in all five factories, missing key/model raise without
  leaking secrets, base-URL override, STT default model.
- **Chat provider over `httpx.MockTransport` (10):** request shape
  (path/auth/temperature/response_format), prompt binding sent, retry-then-
  success, persistent-500/auth/timeout mapping, fence stripping, empty/non-
  JSON rejection, per-Protocol error mapping, key-never-logged.
- **STT provider (6):** multipart success, empty/oversize rejected pre-
  flight, 401/500/timeout/empty-transcript paths.
- **Diagnostic screen (2 + 7 multilingual):** explicit EN claims rejected;
  negated + standard stub/fallback phrasing passes; SI/TA claim rejection,
  SI/TA negation hatch, bare existentials pass, romanized gap documented as
  a passing test, shipped-stub corpus sweep passes.
- **End-to-end (8):** valid HTTP explanation through `AIExplanationService`
  (RAG allow-lists, provider/model propagation, audit row with hashes-only);
  hallucinated-id rejection; diagnostic-claim rejection
  (`validation_failed`); vendor-down fallback (`provider_unavailable`);
  intake extraction citing a real indicator; intake failure fallback; STT
  transcription + STT failure through `AIIntakeService`.
- **Health (6):** auth required, stub report, misconfiguration reported with
  no secret leakage, probe healthy/auth_failed/unreachable.
- **Budgets (`tests/test_ai_budget.py`, 13):** stub bypass (zero I/O),
  hourly/daily/global enforcement, independent operation buckets, disabled
  tiers, Redis-outage local fallback, no-secret errors, `metered` flags,
  explain-report rejection + audit, intake user-id passthrough, transcribe
  propagation, endpoint 429s for extract + transcribe.

Regression: Phase 1 (explanation), Phase 2 (RAG), Phase 3 (intake), Phase 4
(longitudinal), Phase 5 (multilingual/voice), Phase 7 — all pass unchanged.

## 5. Running with stubs vs real providers

**Stubs (local/dev/CI — default):** set nothing. `AI_PROVIDER=stub`,
`STT_PROVIDER=stub`. No keys, no network. All tests run this way.

**Real providers:**

```bash
export AI_PROVIDER=openai-compatible
export AI_MODEL=gpt-4o-mini
export AI_API_KEY=sk-...
export AI_BASE_URL=https://api.openai.com/v1   # optional; this is the default
export STT_PROVIDER=openai-compatible
export STT_API_KEY=sk-...
# STT_MODEL defaults to whisper-1; set explicitly to pin it.
```

**Verify:**

1. Start the backend, authenticate as a RESEARCH_REVIEWER+ user.
2. `GET /api/v1/ai/health` → implementations should read
   `OpenAICompatibleChatProvider` / `OpenAICompatibleSTTProvider`.
3. `GET /api/v1/ai/health?probe=true` → `healthy` for both vendors.
4. Run a report explanation and confirm `provider`/`model` in the response
   and a new `AIInteractionAuditModel` row (hashes only).

Missing keys fail fast: the first factory call raises `AIConfigurationError`
(`ai_provider_misconfigured`), and `/ai/health` reports `misconfigured`.

## 6. Safety invariants (hold in both modes)

- The LLM **explains/extracts only** — it never diagnoses, scores, sets
  severity, creates recommendations/evidence, or modifies the deterministic
  assessment (CDSE). Enforced structurally: output validators reject unknown
  ids/citations; the output-side diagnostic screen
  (`screen_diagnostic_claims` in `ai_dtos.py`, negation-aware, now
  English + Sinhala + Tamil) rejects explicit diagnostic claims
  (`validation_failed` → safe fallback).
- Deterministic trajectory/RAG retrieval never consult the LLM for
  relevance — the LLM only verbalizes supplied context.
- Audit (`AIInteractionAuditModel`) stores hashes + ids + statuses only.
  Column-level test asserts no free-text PHI columns exist. Budget
  rejections are audited too (`budget_exceeded`, input hash only).
- Timeouts always enforced; retries only on transient failures with a small
  backoff; vendor 429 ultimately degrades to the safe fallback, never to a
  broken report.

## 6b. Multilingual diagnostic screening

`screen_diagnostic_claims()` runs three rule sets over every screened field
(summary, finding explanations, severity explanation):

- **English** (legacy, prefix-only window): `you have`, `diagnosed with`,
  `confirmed diagnosis`, disease progression/prediction forms.
- **Sinhala**: subject `ඔබට` + have/exists verbs
  (`තියෙනවා|තියෙයි|ඇත|ඇති`) within 40 chars, or `තහවුරු` (confirmed)
  forms. Negation hatch: `නෑ|නැහැ|නොමැත|නැති|නැත|නොව|නොහැක|නොකිය`
  (the last covers the disclaimer form `…බව නොකියයි` = "does not say").
- **Tamil**: subject `உங்களுக்கு` + have/exists verbs
  (`உள்ளது|இருக்கிறது|…`) within 40 chars, `நோய்…உறுதி`
  ("disease confirmed"), or `உறுதிப்படுத்தப்பட்ட`. Negation hatch:
  `இல்லை`-family, `அல்ல`, and `-ஆது` verb negations (`சொல்லாது` =
  "does not say").

Sinhala/Tamil check an 80+80-char bidirectional window because SOV
negators typically follow the claim (sometimes across a subordinate
clause); English keeps its exact legacy prefix-only behaviour. A corpus
sweep test runs the screen over every patient-facing SI/TA/EN string in
the AI phrase tables — the repo's own "does not mean/say you have a
disease" disclaimers must (and do) pass.

## 6c. Vendor spend / abuse guardrails

`app/application/ai/ai_budget.py` — request-count budgets for metered
(real-vendor) calls only; stubs bypass with zero I/O:

| Tier | Key scope | Default | Setting (`0` = disabled) |
|---|---|---|---|
| Per-user hourly | user + operation + UTC hour | 30 | `AI_BUDGET_USER_HOURLY_REQUESTS` |
| Per-user daily | user + operation + UTC day | 200 | `AI_BUDGET_USER_DAILY_REQUESTS` |
| Global daily (circuit breaker) | operation + UTC day | 20000 | `AI_BUDGET_GLOBAL_DAILY_REQUESTS` |

Counters: Redis `INCR`+`EXPIRE` (`medicheck:ai:budget:v1:…`); unreachable
Redis → process-local fallback keeps enforcing approximately (never blocks
care, never silently unprotected). Exceeding any tier raises
`AIBudgetExceededError` → HTTP **429** `ai_budget_exceeded` — enforced in
all four vendor paths (report/intake/trajectory/STT) after ownership+cache
and before the provider call; it is never converted to a stub fallback
(transcribe/extract endpoints explicitly re-raise past their defensive
handlers). Budget rejections are audit-logged; `/ai/health` is unaffected
(no vendor calls). `GET /api/v1/ai-governance/summary` shows them under
`by_status.budget_exceeded`.

## 7. Remaining risks / follow-ups

- The diagnostic screen covers **explicit** claims in EN/SI/TA; subtly
  implied diagnoses are still caught only by prompt binding + human review.
  Consider clinician spot-checks on real-vendor output before patient-facing
  rollout. SI/TA patterns are narrow and curated — native-speaker review
  recommended before relying on them beyond the tested forms.
- Romanized (Latin-script) Sinhala/Tamil evades the native-script patterns
  (encoded as an explicit passing test); relies on prompt binding +
  allow-lists.
- Budgets are request-count, not token-count (predictable, but a single
  huge-output call costs the same as a tiny one). Token-based accounting
  from vendor `usage` fields is a follow-up (no audit-schema change needed
  if recorded as hashed aggregates — currently not recorded at all).
- No per-tenant / per-deployment budget dimensions (single global breaker).
- Azure native endpoint shape (header + path scheme) is not supported —
  only Bearer-auth OpenAI-compatible endpoints.
- `temperature=0` reduces variance but vendors don't guarantee
  determinism; the validators (not the prompt) are the guarantee.
- Real-vendor latency at p99 under clinical load is unmeasured — run a
  load probe against `?probe=true`-style traffic before rollout.
