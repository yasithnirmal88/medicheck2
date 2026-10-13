# MediCheck AI — Phase 5: Multilingual + Voice AI Clinical Intake

## 1. Executive Summary

Phase 5 extends the existing Phase 3 AI clinical-intake pipeline with
**multilingual support (English, Sinhala, Tamil)** and **voice input**,
directly serving **SDG 3.8 (Universal Health Coverage)** and **SDG 10
(Reduced Inequalities)** by lowering language, literacy, and digital-access
barriers.

The implementation is **strictly additive**. No clinical decision logic, no
database schema, no CDSE code, and no Phase 1–4 functionality was modified. The
deterministic Clinical Decision Support Engine remains the single clinical
source of truth. The AI continues to be an **input-interpretation layer only**.

**Key result:** A patient who cannot read medical English, who cannot type, or
who speaks Sinhala/Tamil can now describe what they are experiencing in their
own words — by typing or speaking — and the system maps that description to
the *same* existing clinical indicators the English questionnaire uses.

---

## 2. Existing Phase 3 Architecture Reused

Phase 5 does **not** create a second intake architecture. It extends the
existing Phase 3 pipeline:

| Phase 3 component | Phase 5 extension |
|---|---|
| `IntakeRequestContext` DTO | Added `language`, `input_type`, `detected_language` fields |
| `IntakeResponse` DTO | Added language/input_type traceability metadata |
| `AIClinicalIntakeProvider` Protocol | Unchanged contract; stub extended with multilingual synonyms |
| `StubClinicalIntakeProvider` | Added Sinhala/Tamil patient-term synonyms + multilingual negation/uncertainty/temporality cues + localized clarification |
| `CandidateValidationService` | Unchanged — allow-list validation is language-agnostic (rejects hallucinated IDs regardless of input language) |
| `AIIntakeQuestionService` | Unchanged — question discovery works on indicator IDs, not language |
| `AIIntakeService.extract()` | Extended to accept `language` + `input_type`; passes them through to context + response |
| `POST /api/v1/ai/intake/extract` | Extended request body with optional `language` + `input_type` |
| `IntakePage.tsx` | Extended with language selector + mic button + transcript review |

The flow remains:
```
Patient (text/voice, en/si/ta)
  → language detection/normalization
  → AI provider (multilingual extraction)
  → parse + validate against knowledge graph (reject unknown IDs)
  → discover existing questions/groups
  → existing branching engine
  → deterministic CDSE
  → health report
```

---

## 3. Multilingual Architecture

### Principle: language is an INTERFACE layer, not a clinical layer

Sinhala/Tamil/English descriptions of the same clinical concept resolve to
the **SAME canonical indicator ID**. The knowledge graph is never fragmented
by language.

```
"මට හුස්ම ගන්න අමාරුයි"  (Sinhala: "I have difficulty breathing")
"மூச்சு வாங்குறது"        (Tamil: "breathlessness")
"I'm short of breath"     (English)
            │
            ▼
   localized interpretation (interface layer)
            │
            ▼
   canonical MediCheck indicator ID: "ind_exertional_dyspnea"
            │
            ▼
   existing questions → existing CDSE → existing report
```

### Language module (`app/application/ai/language.py`)

- **Supported languages:** `en`, `si`, `ta` (bounded vocabulary; extensible).
- **Normalization:** accepts aliases (`en-US`, `sin`, `si-LK`, `Tamil`...) → canonical codes.
- **Detection:** deterministic Unicode-script-based (Sinhala U+0D80–0DFF, Tamil U+0B80–0BFF). Requires ≥25% of non-whitespace characters to be in the target script to avoid false detection.
- **Resolution:** confident detection → detected language; uncertain → user-selected → default (English).
- **Safety:** English is never "detected" (it is the default fallback), so a low-signal guess never overrides an explicit user selection.

### Multilingual prompt (`app/application/ai/multilingual_prompts.py`)

Version `1.1-multilingual`. Extends the Phase 3 prompt with:
- instruction to understand any supported language;
- instruction to normalize concepts to canonical (English) indicator names;
- instruction to localize clarifications when possible;
- the same hard safety constraints (no diagnosis, no scoring, no severity, no invented IDs).

### Multilingual stub provider

The deterministic stub provider (`StubClinicalIntakeProvider`) was extended
with:
- Sinhala/Tamil patient-term synonyms mapping to the same canonical keywords;
- multilingual negation cues (`නැත`, `இல்லை`...);
- multilingual uncertainty cues;
- multilingual temporality cues (historical/recent/recurring);
- localized informational clarifications (non-diagnostic, asking when/how-long/how-often).

---

## 4. Voice Architecture

### Principle: voice is another INPUT channel only

Voice does **not** create a second clinical interpretation system. Audio is
transcribed to text, the patient reviews/edits the transcript, and the
*reviewed text* enters the same Phase 3 intake pipeline.

```
Microphone
  → SpeechToTextProvider.transcribe(audio, language) → transcript
  → patient reviews + edits transcript
  → existing AI intake pipeline (text)
  → observation extraction
  → candidate indicators
  → existing question groups
  → deterministic questionnaire
  → CDSE
```

### Audio is NOT sent to the LLM

```
Audio → STT → Text → existing AI intake provider
```
(not Audio → LLM directly). This gives easier auditing, testing, language
control, and provider replacement.

### Audio privacy

- Audio is processed **transiently in memory** and discarded immediately.
- Audio is **never** permanently stored, logged, or exposed via URLs.
- The STT provider receives only audio bytes + a language hint.
- The transcript is returned to the patient for review before clinical
  interpretation — an incorrect transcript is never silently sent into the
  pipeline.

---

## 5. Provider Abstractions

### AI intake provider (Phase 3, reused)

`AIClinicalIntakeProvider` Protocol: `extract_candidates(context) → JSON string`.
Default: `StubClinicalIntakeProvider` (deterministic, no network). Selectable
via `settings.ai_provider`. No third-party AI packages installed.

### Speech-to-text provider (Phase 5, new)

`SpeechToTextProvider` Protocol:
```python
async def transcribe(audio_bytes, *, language, content_type) → TranscriptResult
```
Default: `StubSpeechToTextProvider` (deterministic, no network). Selectable
via `settings.stt_provider`. No third-party STT packages installed. The stub
returns a deterministic English placeholder transcript so the full
voice→intake→questionnaire flow can be exercised end-to-end in tests/CI.

Both providers raise typed errors (`AIIntakeProviderError` /
`SpeechToTextError`) so the service/endpoint can map any failure to a single
safe fallback.

---

## 6. AI Contract

### Input (to the provider)
Only the minimum necessary:
- patient message (text)
- language + input_type (interface metadata)
- bounded indicator catalog (active, non-deleted)
- prompt version

**No** auth tokens, passwords, emergency contacts, unrelated patient history,
or internal DB objects are sent to the AI.

### Output (from the provider, validated)
```json
{
  "observations": [...],      // structured, with polarity/temporality/certainty
  "candidates": [...],        // indicator_id MUST be in the supplied catalog
  "clarifications": [...]     // informational only, never diagnostic
}
```

### Confidence definition
`extraction_confidence ∈ [0,1]` = how confident the model is that the
patient's words match the indicator. It is **NOT** a clinical probability and
**NOT** a disease likelihood. The AI never outputs clinical disease
probability.

---

## 7. Knowledge Graph Validation

The existing allow-list philosophy is **unchanged and language-agnostic**:

- Every candidate `indicator_id` is re-validated against the bounded catalog
  (built from active, non-deleted indicators).
- Unknown / hallucinated / inactive / deleted indicator IDs are **rejected**
  (silently dropped, never created, never inserted).
- Orphan observation references are dropped.
- Out-of-range confidence is rejected.

This guard works identically for English, Sinhala, and Tamil input — the
validation operates on indicator IDs, not language. A hallucinated ID is
rejected regardless of the input language.

The AI **cannot** modify CMS content: no creating/editing indicators,
diseases, questions, or recommendations. Any future AI-generated CMS
suggestion must go through draft → medical review → approval → publication.

---

## 8. Patient Flow

1. Patient navigates to `/assessments/intake`.
2. Selects a language (English / සිංහල / தமிழ்) — or the system auto-detects.
3. Types their description **or** presses the mic button and speaks.
4. If voice: audio is transcribed; the transcript appears in the textarea for
   review. A banner prompts: *"Please review your transcript. Edit it if
   anything is incorrect, then continue."*
5. Patient edits the transcript (if needed) and presses **Continue**.
6. The AI extracts observations + candidate indicators (validated against the
   knowledge graph).
7. The results section shows:
   - "What I understood" — observations (patient can reject any).
   - Clarifying questions (informational, non-diagnostic).
   - Recommended assessments (existing question groups).
8. Patient explicitly starts a suggested assessment → existing questionnaire
   → deterministic CDSE → health report.

The AI **never** silently launches clinical assessments. The patient is always
in control.

---

## 9. Security & Privacy

- **Authentication:** existing `get_current_user` dependency (RBAC preserved).
- **Patient ownership:** session_id (if supplied) is verified to belong to the
  caller. Cross-patient attempts → 404 (no ownership leak).
- **No PHI to AI:** only the patient message + language + catalog are sent.
- **No provider keys exposed:** API keys are server-side only.
- **Rate limiting / input validation:** preserved from existing API security.

---

## 10. PHI Handling

| Data | Stored? | Logged? |
|---|---|---|
| Raw audio | No (transient in-memory) | No |
| Transcript | No (returned to patient only) | No |
| Patient narrative | No (session-scoped, not persisted) | No |
| Trace metadata (trace_id, language, counts) | No | Yes (safe structured logging) |
| API keys | Server-side | No |

Structured logging records only safe metrics: `trace_id`, `provider`,
`language`, `input_type`, `detected_language`, `latency`, `success/failure`,
`candidate_count`, `question_group_count`. **No** raw audio, raw patient
narrative, full transcripts, or sensitive health details are logged.

---

## 11. Accessibility

- **Keyboard navigation:** all controls are keyboard-accessible.
- **Screen readers:** `aria-label`, `aria-describedby`, `aria-hidden` on icons.
- **Visible focus states:** `focus:ring-2 focus:ring-indigo-300`.
- **Accessible mic controls:** mic button has clear label; recording state is
  visually distinct (red Stop button).
- **Sufficient contrast:** Tailwind color classes meet WCAG AA.
- **Large touch targets:** buttons are `px-4 py-2` minimum.
- **Voice is additional, not the only method:** typing is always available.
  If the browser lacks MediaRecorder support, the mic button is hidden and
  only typing is offered.

---

## 12. Error/Fallback Behaviour

| Failure | Behaviour |
|---|---|
| Speech recognition unavailable | "Voice input isn't available right now. You can type instead." (mic hidden if unsupported) |
| AI intake unavailable | `available=false` + "AI-assisted intake is currently unavailable. You can continue with the standard questionnaire." |
| Unsupported language | 422 + "This language isn't currently supported. Please select English, Sinhala, or Tamil." |
| Network failure | Standard questionnaire remains accessible |
| Empty audio | 422 + "No audio was captured. Please try again." |
| Oversized audio | 413 + "Audio recording is too long." |
| Unsupported audio format | 422 + "Unsupported audio format." |

**Mandatory:** AI intake failure → standard assessment catalog (never
application failure).

---

## 13. SDG 3.8 / SDG 10 Alignment

### SDG 3.8 — Universal Health Coverage
Multilingual + voice intake lowers the activation barrier for people who face
language barriers, literacy barriers, or difficulty typing/navigating complex
questionnaires. A patient who speaks only Sinhala or Tamil, or who cannot
type, can now access the assessment.

### SDG 10 — Reduced Inequalities
Language and accessibility support reduces health-access inequality along
language and disability axes.

### SDG 3.4 — Prevention / Early Detection (indirect)
By making intake accessible to more people, more assessments are initiated,
enabling earlier detection of NCD risk patterns (the longitudinal trajectory
from Phase 4).

### SDG measurement foundation
The implementation records safe, de-identified metrics (language, input_type,
candidate/question_group counts, completion/fallback) so future SDG analytics
(Phase 6) can measure: assessments initiated through AI intake, English vs
Sinhala vs Tamil usage, voice vs text usage, fallback rate, discovery rate.
**No** unnecessary demographic data is collected for analytics.

---

## 14. Testing

### Backend (`tests/test_intake_phase5.py`)

50 tests covering:
- **Language (12):** normalize/detect/resolve for en/si/ta, unsupported fallback,
  mismatch (detection wins), uncertain fallback.
- **Extraction (6):** Sinhala/Tamil map to same indicator IDs, negation,
  hallucinated-ID rejection (multilingual path), no-candidates, multiple.
- **Voice (7):** stub transcription, empty/oversized audio, language
  normalization, service transcribe, provider default.
- **Endpoint (7):** extract with language, Sinhala extract, unsupported
  language 422, /languages, /transcribe success/empty/unsupported-type.
- **Security (5):** unauthorized extract/transcribe/languages, wrong-patient
  session 404, missing session 404.
- **Safety (3):** no diagnosis in output, confidence is not clinical
  probability, no graph mutation.
- **Handoff (2):** Sinhala candidate→question group, duplicate removal.
- **Regression (2):** Phase 3 backward compat (no language kwarg), CDSE
  tables unchanged.
- **Provider (2):** localized clarification (Sinhala/English).

**Result: 50 passed.**

### Full backend suite
**336 passed** (286 existing + 50 new). Zero regressions.

### Frontend
- `IntakePage.test.tsx`: 13 tests (10 existing + 3 new Phase 5: language
  selector renders en/si/ta, language sent to API, non-diagnostic disclaimer
  regardless of language).
- Full suite: **62 passed** (was 59 in Phase 4). Zero regressions.
- Typecheck: **clean**.
- Production build: **clean**.

---

## 15. Performance

- **One intake request → one validated extraction → one deterministic discovery
  query.** No repeated AI calls.
- The STT call is a single request; the transcript is then reviewed and
  submitted once via the existing extract endpoint.
- No global caching of patient-sensitive results.
- Catalog is bounded (`CATALOG_LIMIT = 60`) so prompts stay bounded.

---

## 16. Known Limitations

1. **Stub STT provider** returns a deterministic English placeholder
   transcript, not a real transcription. A real vendor STT provider must be
   implemented and selected via `STT_PROVIDER` for production voice support.
2. **Stub AI provider** uses deterministic keyword/synonym matching, not a
   real LLM. A real vendor provider must be implemented for production
   multilingual NLP. The abstraction is in place; only the concrete vendor
   implementation is pending.
3. **Language detection** is script-based (Unicode ranges). Mixed-language
   text (e.g., "I feel හුස්ම ගන්න අමාරුයි") will detect based on the
   dominant script proportion. This is a safe heuristic, not a full NLP
   language detector.
4. **Sinhala/Tamil synonym coverage** is bounded. The map covers common
   cardiovascular/respiratory symptoms; additional synonyms can be added as
   the knowledge graph grows.
5. **No audio persistence** by design. If a future requirement needs audio
   retention (e.g., for clinician review), it must be explicitly designed with
   retention limits, cleanup, and access control.
6. **No population analytics yet** (deferred to Phase 6 per the roadmap). The
   measurement foundation (safe metrics in structured logs) is in place.

---

## 17. Future Extensions

- **Phase 6:** Population-health / SDG analytics dashboard using the
  de-identified intake/trajectory metrics now being recorded.
- Real vendor STT provider (e.g., a cloud speech API via the existing
  `SpeechToTextProvider` abstraction).
- Real vendor multilingual LLM provider (via the existing
  `AIClinicalIntakeProvider` abstraction).
- Additional languages (the `SUPPORTED_INTAKE_LANGUAGES` vocabulary is
  extensible without touching the pipeline).
- FHIR / HL7 interoperability for integration into national health systems.
- Automated referral decisions (future phase, not this one).

---

## Final Verification

### Backend
- All previous tests pass: **286/286**
- All Phase 5 tests pass: **50/50**
- Total: **336/336**

### Frontend
- All previous tests pass: **59/59** (from Phase 4)
- Phase 5 tests: **3 new** (13 total in IntakePage)
- Total: **62/62**
- Typecheck: **clean**
- Production build: **clean**

### Safety
- AI cannot diagnose ✓ (diagnostic-language guard preserved + extended)
- AI cannot score ✓ (no score fields in output)
- AI cannot set severity ✓ (no severity in intake output)
- AI cannot modify graph ✓ (no graph mutation; verified by test)
- AI cannot create CMS content ✓ (read-only; no write paths)
- AI cannot bypass questionnaire validation ✓ (allow-list unchanged)
- AI cannot bypass CDSE ✓ (intake converges on existing pipeline)

### Accessibility
- English works ✓
- Sinhala works ✓
- Tamil works ✓
- Text fallback works ✓
- Voice fallback works ✓ (mic hidden if unsupported; 422 → typing)
- Transcript can be edited ✓
- Keyboard navigation works ✓

### Clinical integrity
```
AI intake → existing concepts → existing questions → existing branching → existing CDSE
```
No alternate clinical decision path has been introduced. ✓

### Database
- Migrations created: **none**
- Existing tables changed: **none**
- Data modified: **none**
- Seed data modified: **none**

### Git
- Branch: `feat/multilingual-voice-intake-phase5`
- CDSE / domain / ORM models / migrations: **unchanged** (verified by diff)
