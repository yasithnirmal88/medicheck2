# MEDICHECK — AI Integration Baseline Audit

**Status:** READ-ONLY architecture analysis. No application code, database schema,
migrations, CDSE logic, questionnaires, scoring, CMS, or RBAC were modified.
**Purpose:** Document exactly how the existing deterministic assessment engine works
so that a future AI-assisted adaptive layer can integrate safely.

---

## Core Product Principle (context)

> A patient may not recognize that an experience, symptom, behavior, or lifestyle
> factor is clinically relevant.

The future system should combine: patient-described concerns + AI-assisted discovery of
potentially relevant observations + the clinical knowledge graph + adaptive follow-up
questions + the existing deterministic CDSE. The AI must eventually help determine **what
should be explored**; the existing deterministic engine remains responsible for the
clinical assessment logic.

This document establishes the precise contract the deterministic engine exposes today,
so the AI layer can be grafted onto it without altering clinical behavior.

---

## 1. Current Patient Architecture

The complete patient flow, traced from UI to database. All paths verified against source.

### 1.1 Stage map

| Stage | Frontend route | Frontend component | Hook / API | API endpoint (backend) | Service | Repository | Database tables |
| ----- | -------------- | ------------------ | ---------- | ---------------------- | ------- | ---------- | --------------- |
| Registration | `/register` | `features/auth/pages/Register` | `useRegister` → `authApi` | `POST /api/v1/auth/register` | `AuthService` | `SQLUserRepository` | `users`, `user_roles` |
| Authentication | `/login` | `features/auth/pages/Login` | `useLogin` → `authApi` | `POST /api/v1/auth/login`, `GET /api/v1/auth/me` | `AuthService` (`firebase` provider) | `SQLUserRepository` | `users`, `user_roles` |
| Health Profile | `/profile`, `/profile/wizard` | `features/profile/pages/HealthProfilePage`, `ProfileWizard` | `useProfileQuery` → `profileApi`/`profileService` | `GET/POST /api/v1/profiles/me`, `/me/personal`, `/me/versions`, `/me/completion` | `ProfileService` | `SQLProfileRepository` | `health_profiles`, `personal_info`, `lifestyle`, `nutrition`, `medical_histories`, `medication_histories`, `surgical_histories`, `family_histories`, `allergies`, `immunizations`, `measurements`, `lab_reports`, `profile_versions` |
| Assessment Selection | `/assessments` | `features/questionnaire/pages/AssessmentSelectionPage` | `useTemplates` → `questionnaireApi.fetchTemplates` | `GET /api/v1/questionnaires` | `QuestionnaireService.get_available_templates` | `SQLQuestionnaireRepository` | `questionnaire_templates`, `questionnaire_versions` |
| Start Session | `/questionnaires/:id` | `QuestionnaireSessionPage` | `useStartSession` → `questionnaireApi.startSession` | `POST /api/v1/questionnaires/{id}/start` | `QuestionnaireService.start_session` | `SQLAssessmentSessionRepository`, `SQLQuestionRepository`, `SQLQuestionOptionRepository` | `assessment_sessions`, `questions`, `question_options`, `question_groups` |
| Question Retrieval | `/questionnaires/:id` | `QuestionRenderer` (dispatches `typeMap`) | `useSession` → `questionnaireApi.fetchSession` | `GET /api/v1/questionnaires/sessions/{id}` | `QuestionnaireService.get_session` → `QuestionnaireEngineImpl.load_questions` / `get_next_question` | `SQLQuestionRepository`, `SQLQuestionOptionRepository` | `questions`, `question_options`, `question_dependencies`, `question_groups` |
| Answer Submission | (in session) | `QuestionRenderer` + `useQuestionnaireFlow.submitAnswer` | `useSaveAnswer` → `questionnaireApi.saveAnswer` | `POST /api/v1/questionnaires/sessions/{id}/answer` | `QuestionnaireService.save_answer` → `ValidationEngine.validate`, `ScoringEngine.calculate_option_score` | (direct `AssessmentAnswerModel` insert), `SQLAssessmentSessionRepository` | `assessment_answers`, `assessment_sessions` |
| Branching | (server-driven, in session) | next question comes from `next_question` in save response | — (implicit in `save_answer` → `_evaluate_next`) | (same answer endpoint) | `QuestionnaireEngineImpl.get_next_question` / `evaluate_branching` → `BranchingEvaluator.evaluate_visibility` | `SQLQuestionRepository`, `_get_dependencies` (queries `question_dependencies`) | `question_dependencies` |
| Indicator Activation | — (backend, after completion) | — | — | `POST /api/v1/assessment/process` | `ClinicalDecisionService.process_assessment` | `SQLKnowledgeGraphRepository` (batch lookups) | `assessment_answers`, `question_indicator_links`, `question_option_indicator_links`, `clinical_indicators` |
| Condition Evaluation | — (backend) | — | — | (same process endpoint) | `ClinicalDecisionService.process_assessment` | `SQLKnowledgeGraphRepository.get_conditions_by_indicator_batch` | `indicator_condition_links`, `possible_conditions` |
| Recommendation Generation | — (backend) | — | — | (same process endpoint) | `ClinicalDecisionService.process_assessment` | `SQLKnowledgeGraphRepository.get_recommendations_by_condition_batch`, `get_laboratory_tests_by_condition_batch` | `condition_recommendation_links`, `recommendations`, `condition_laboratory_test_links`, `laboratory_tests` |
| Report | `/assessments/:id` (=ReportViewer), `/assessments/:id/results` | `features/dashboard/pages/ReportViewer`, `ResultsDashboard` | `useQuery(['report', id])` → `fetchReportBySession` | `POST /api/v1/report/generate`, `GET /api/v1/report/{session_id}`, `GET /api/v1/report/id/{report_id}` | `ReportService.generate_report` / `get_report_by_session` | `SQLReportRepository`, `SQLDecisionRepository`, `SQLKnowledgeGraphRepository`, `SQLProfileRepository` | `health_assessments`, `body_system_assessments`, `condition_assessments`, `lifestyle_assessments`, `generated_advices`, `assessment_results` (reads) |
| Timeline | `/timeline` | `features/health-timeline/pages/TimelinePage`; compare at `/timeline/compare` | `ComparePage` | `GET /api/v1/report/`, `GET /api/v1/report/compare/{id1}/{id2}` | `ReportService.list_reports`, `compare_reports` | `SQLReportRepository` | (reads report tables) |

### 1.2 Flow notes (verified behavior)

- The assessment is **one-question-at-a-time, server-driven**. `QuestionnaireSessionPage` keeps a
  local answer map (`useQuestionnaireFlow`) and autosaves with a 3 s debounce
  (`useQuestionnaireSession.triggerAutoSave`). The *next* question is whatever the backend
  returns in `SaveAnswerResponse.next_question`; the frontend does not compute branching.
- `QuestionnaireService.save_answer` (backend) computes the per-answer `score_value` by
  matching the chosen `value` against `QuestionOption.value` / `.code`, then calls
  `QuestionnaireEngineImpl.get_next_question`.
- **Important quirk (latent):** `SQLQuestionRepository.find_by_questionnaire(questionnaire_id)`
  ignores its argument and returns *all non-deleted questions ordered by `order_index`*
  (line: `_ = questionnaire_id`). So today the "template" selects all active questions
  regardless of template; grouping/visibility is what actually shapes the assessment.
  This is relevant to the AI layer: the question bank is effectively global, not per-template.
- Completion (`POST /sessions/{id}/complete`) sets status `completed` and runs an inline
  `_calculate_scores` (a *group/overall percentage* computation in `ScoringEngine`). The CDSE
  itself is invoked **separately** by `POST /assessment/process` (it is not auto-triggered by
  completion). Report generation is a third, explicit call (`POST /report/generate`) that
  requires the CDSE result to already exist.

---

## 2. Current CDSE Architecture

The deterministic Clinical Decision Support Engine entry point and its real
implementation. All symbols below are exact, taken from source.

### 2.1 Exact entry point

| Item | Value |
| ---- | ----- |
| API file | `backend/app/api/v1/endpoints/cdse.py` |
| API route | `POST /api/v1/assessment/process` (router prefix `/assessment`, tag `cdse`) |
| Endpoint function | `process_assessment(payload, current_user, session)` |
| Service file | `backend/app/application/services/clinical_decision_service.py` |
| Service class | `ClinicalDecisionService` |
| Service method | `async def process_assessment(self, session_id, user_id=None) -> dict[str, Any]` |
| Trace symbol | `trace_id = uuid.uuid4().hex[:16]` (generated per run) |

Supporting engines (the questionnaire-side deterministic logic invoked during the session,
distinct from the CDSE post-processing):

| Concern | File | Class | Function |
| ------- | ---- | ----- | -------- |
| Question loading / next / branching | `backend/app/modules/questionnaire/engine.py` | `QuestionnaireEngineImpl` (implements `domain/services/questionnaire_engine.QuestionnaireEngine`) | `load_questions`, `get_next_question`, `evaluate_branching`, `calculate_progress`, `validate_answer` |
| Scoring | `backend/app/modules/questionnaire/scoring.py` | `ScoringEngine` | `calculate_option_score`, `calculate_group_score`, `calculate_body_system_score`, `calculate_overall_score`, `_determine_severity` |
| Branching | `backend/app/modules/questionnaire/branching.py` | `BranchingEvaluator` | `evaluate_visibility`, `evaluate_branch_rules`, `_evaluate_group`, `_evaluate_condition_tree` |
| Dependency evaluation | `backend/app/modules/questionnaire/dependency_evaluator.py` | `DependencyEvaluator` | `evaluate` (static), `_evaluate_computed`, `_compare`, `_calculate_age` |
| Validation | `backend/app/modules/questionnaire/validation.py` | `ValidationEngine` | `validate`, `_validate_numeric/_decimal/_slider/_date/_time/_single_choice/_multiple_choice/_text/_file` |

### 2.2 CDSE pipeline (verified from `process_assessment`, lines referenced)

1. **Load session + answers** — `self.session.get(AssessmentSessionModel, session_id)`;
   answers come via the `selectin` relationship `sess.answers`. Ownership checked against
   `user_id`.
2. **Build answer map** — `answer_map: dict[question_id, list[answer]]`.
3. **Map answers → indicators (batch)** —
   `kg_repo.get_indicators_by_question_batch(question_ids)` (question-level links) and
   `kg_repo.get_indicators_by_option_batch(option_ids)` (option-level links). Option
   `score_value` is loaded as the option-level weight (default `1.0`).
4. **Aggregate indicator scores** — for each answer:
   - question-level indicator: `score += 1.0` (constant).
   - option-level indicator: `score += float(option.score_value)` (default `1.0`).
   Each accumulation records a `source` entry (`{question_id, type, value, weight}`) into
   `indicator_sources[indicator_id]`.
5. **Activate indicators** — `threshold = 1.0` (hardcoded in the method, comment says
   "configurable"). `activated_indicators = [(id, score) for ... if score >= threshold]`.
6. **Create result record** — `dec_repo.create_result({session_id, user_id, summary, confidence, created_at})`.
7. **Load evidence (batch)** — `kg_repo.get_evidence_by_indicator_batch(activated_ids)`.
8. **Persist activated indicators + explanations** — for each, `dec_repo.add_activated_indicator`
   and `dec_repo.add_explanation(result_id, "indicator", ind_id, text)` where
   `text = f"[trace:{trace_id}] Indicator {id}: score=..., evidence_count=..., sources=..."`.
9. **Map indicators → conditions (batch)** — `kg_repo.get_conditions_by_indicator_batch`.
10. **Aggregate condition scores** — `condition_scores[c.id] += score` for each contributing
    activated indicator; track `condition_indicator_map[c.id] = [indicator_ids]`.
11. **Activate conditions** — `activated_conditions = [(cid, sc) for ... if sc > 0]`.
12. **Normalize confidence** — `max_possible_condition_score = max(scores)`; per condition
    `confidence = clamp(sc / max_possible, 0, 1)`. **Note: this is *relative* normalization
    against the strongest condition in this run, not an absolute probability.** Persist via
    `dec_repo.add_activated_condition` + an `add_explanation("condition", cid, ...)`.
13. **Map conditions → recommendations + labs (batch)** —
    `get_recommendations_by_condition_batch`, `get_laboratory_tests_by_condition_batch`.
    Persist via `add_recommendation(source=f"condition:{cid}", notes=trace text)` and
    `add_laboratory_test(reason=trace text)`.
14. **Overall confidence** — mean of per-condition normalized confidences
    (`sum(confs)/len(confs)`, else `0.0`).
15. **Persist** — update `assessment_sessions.status='processed'` and
    `assessment_results.summary=str(summary), confidence_score=overall_confidence`.
16. **Return** — `{result_id, summary, confidence_score}`. The `summary` dict contains
    `trace_id`, counts, and the raw `indicator_scores` map.

### 2.3 Severity calculation (two separate mechanisms)

- **Questionnaire-side (`ScoringEngine._determine_severity`)** — applied to *body-system
  percentage scores* during `complete_session`/`_calculate_scores`. Bands:
  `>=80 critical`, `>=60 severe`, `>=40 moderate`, `>=20 mild`, else `none`.
- **Report-side (`ReportService.generate_report`)** — loads `severity_thresholds` rows
  (`is_active=True`, ordered by `min_score`) and buckets each body-system aggregate score
  into the first `min_score` band; falls back to hardcoded categories
  (`Normal / Monitor / Needs Attention / Recommend Screening / Urgent Medical Review`).
- The **CDSE itself does not compute severity**; it only computes indicator/condition
  scores and normalized confidence. Condition `confidence` is later mapped to a *label*
  (`Very Weak / Weak / Moderate / Strong`) in the report step.

### 2.4 What the CDSE does NOT do today (relevant to AI design)

- It does not consume any free-text/natural-language input — only structured
  `option_id`/`value` answers persisted in `assessment_answers`.
- It does not consult the `HealthProfile` (profile data is only used by `ReportService` for a
  lifestyle snapshot, not by the CDSE). The profile's `user_attributes` (BMI/age) are used by
  the *branching* dependency evaluator, not the CDSE.
- It has no concept of "candidate indicators" supplied externally; indicators are discovered
  purely by graph traversal from the answered questions/options.
- It does not auto-run on completion; it must be triggered explicitly.

---

## 3. Knowledge Graph

The graph is implemented as link/junction tables in
`backend/app/infrastructure/persistence/models/links.py`, with the core node tables
alongside. Every link has an `active` boolean (soft-delete / reactivation semantics in the
repository).

### 3.1 Relationship table

| Source (node table) | Relationship (link table) | Target (node table) | Implementation |
| ------------------- | ------------------------ | ------------------- | -------------- |
| `questions` | `question_indicator_links` | `clinical_indicators` | `QuestionIndicatorLinkModel(question_id, indicator_id, active)` |
| `question_options` | `question_option_indicator_links` | `clinical_indicators` | `QuestionOptionIndicatorLinkModel(question_option_id, indicator_id, active)` |
| `clinical_indicators` | `indicator_condition_links` | `possible_conditions` | `IndicatorConditionLinkModel(indicator_id, condition_id, active)` |
| `clinical_indicators` | `indicator_evidence_links` | `evidence_references` | `IndicatorEvidenceLinkModel(indicator_id, evidence_id, active)` |
| `clinical_indicators` | `indicator_recommendation_links` | `recommendations` | `IndicatorRecommendationLinkModel(indicator_id, recommendation_id, active)` |
| `possible_conditions` | `condition_recommendation_links` | `recommendations` | `ConditionRecommendationLinkModel(condition_id, recommendation_id, active)` |
| `possible_conditions` | `condition_laboratory_test_links` | `laboratory_tests` | `ConditionLaboratoryTestLinkModel(condition_id, laboratory_test_id, active)` |
| `body_systems` | `body_system_condition_links` | `possible_conditions` | `BodySystemConditionLinkModel(body_system_id, condition_id, active)` |

### 3.2 Other nodes and relationships discovered (not in the core spine)

| Node table | Notes / extra relationships |
| ---------- | -------------------------- |
| `body_systems` | Parent of `question_groups` (FK) and `questions` (FK). Has `scoring_weight`. `body_system_condition_links` ties it to conditions. |
| `question_groups` | Parent of `questions` (FK); belongs to a body system. Used for ordering/sections. |
| `question_options` | Children of `questions`; carry `score_value`, `severity`, `color_hex`, `recommendation_trigger`, `follow_up_trigger`, `medical_notes`. |
| `question_dependencies` | `question_id` depends on `depends_on_question_id` with `condition_type`, `condition_value`, `logic_operator`, `group_id` (the branching substrate). |
| `severity_thresholds` | Per body-system (+ optional `scoring_profile_id`) severity bands: `min_score/max_score/severity/label/color_hex/recommendation`. |
| `clinical_guidelines` | Standalone reference docs (per body system / disease), `evidence_level`, `source_organization`, `guideline_url`, `recommendations` JSON, `reviewed_at/published_at`. |
| `lifestyle_advice`, `exercise_programs`, `nutrition_advice`, `medication_recommendations` | Content nodes managed via CMS (`ENTITY_REGISTRY`), linked to body systems. Not yet wired into the CDSE pipeline. |
| `imaging_tests` | Like `laboratory_tests` but for imaging (`modality`, `is_contrast_required`, `preparation_notes`). No link table to conditions found in the CDSE path today. |
| `recommendations` | Has `priority`, `urgency`, `evidence_level`, `category`, `disease_id`. Reached via condition→recommendation and indicator→recommendation links. |
| `evidence_references` | `title/url/source/evidence_level/summary`; can also be directly attached to a `question_id` (loose coupling) plus the indicator→evidence link. |
| `diseases`, `symptoms`, `disease_categories`, `body_system_categories` | Taxonomy nodes; indicators carry `related_disease_ids`/`related_symptom_ids` (JSON arrays), not separate link tables. |

### 3.3 Graph traversal helpers (repository, exact)

`SQLKnowledgeGraphRepository` (`backend/app/infrastructure/persistence/repositories/sql_knowledge_graph_repository.py`)
exposes both single and **batch** retrieval (the CDSE uses the batch variants):

`get_indicators_by_question`, `get_indicators_by_question_option`,
`get_indicators_by_question_batch`, `get_indicators_by_option_batch`,
`get_conditions_by_indicator` / `_batch`, `get_recommendations_by_condition` / `_batch`,
`get_evidence_by_indicator` / `_batch`, `get_laboratory_tests_by_condition` / `_batch`,
`build_graph_from_question` (full question→indicator→condition→recommendation→evidence
subgraph), `link_*` creators (with duplicate/reactivate handling).

---

## 4. Question Engine

### 4.1 Question types (exact enum — `domain/entities/question.py: QuestionType`)

`single_choice`, `multiple_choice`, `yes_no`, `numeric`, `decimal`, `slider`, `date`,
`time`, `dropdown`, `multi_select`, **`free_text`**, `search`, `file_upload`.

`free_text` is a first-class question type with a full frontend renderer
(`features/questionnaire/components/question-types/FreeTextInput.tsx`) and backend
validation (`ValidationEngine._validate_text`). It supports `min_length`/`max_length`/
`pattern` validation rules. **However**, free-text answers do not flow into the CDSE: the
CDSE only consumes `option_id`-bearing answers (option-level links) and question-level links;
a `free_text` answer has no `option_id`, so unless its question is linked at the
question→indicator level it contributes nothing to indicator activation.

### 4.2 Question selection contract (Input → Output)

```
Input:  session = AssessmentSession(questionnaire_template_id, current_question_id,
                                     metadata.user_attributes)
        │
        ▼
QuestionnaireEngineImpl.load_questions(session)
   ├─ if session.questionnaire_template_id:
   │     SQLQuestionRepository.find_by_questionnaire(template_id)
   │       ⚠ ignores template_id → returns ALL non-deleted questions ordered by order_index
   └─ else:
         SQLQuestionRepository.find_active()  (status=='active', not deleted, by order_index)
        │
        ▼
QuestionnaireEngineImpl.get_next_question(session, current_question)
   answers = _get_answers_map(session.id)          (AssessmentAnswerModel rows → value)
   user_attrs = session.metadata["user_attributes"]
   1. if current_question: within same group, return first unanswered+visible successor
   2. else: first unanswered question whose deps evaluate visible
        │
        ▼ visibility filter
BranchingEvaluator.evaluate_visibility(deps, answers, user_attrs)
   group deps by group_id → evaluate each group (AND default, OR if logic_operator)
   → all groups must pass → question visible
        │
        ▼ per-condition
DependencyEvaluator.evaluate(condition_type, condition_value, answer_value, user_attrs)
        │
        ▼
Output: next Question (with options fetched separately) or None (session complete)
```

**Filtering dimensions available today:** `body_system_id`, `question_group_id`,
`status` (active/inactive/draft/archived), `order_index`, `priority`, `difficulty`,
`activation_date`/`expiration_date` (columns exist; not filtered in `find_active`).
**Ordering:** `order_index` ascending. **Branching:** dependency-table driven (see §5).

### 4.3 The "candidate indicator" insertion question (§7 of the brief)

> If we wanted to provide an additional candidate clinical indicator to the current
> assessment system, what existing API/service would we eventually need to call?

There is **no existing endpoint that accepts an externally-suggested indicator into a
running assessment**. The CDSE discovers indicators exclusively by graph traversal
(`get_indicators_by_question_batch` / `get_indicators_by_option_batch`). To inject a
candidate indicator today, the only existing mechanisms are:

1. **Create a question→indicator or option→indicator link** via the CMS/admin graph router
   `POST /api/v1/graph/question-indicators` or `/question-option-indicators`
   (`KnowledgeGraphService.link_question_indicator`) — **but this mutates the global
   knowledge graph for everyone**, requires `get_current_admin`, and is not assessment-scoped.
2. **Create an indicator itself** via `POST /api/v1/cms/...` (admin/content) or the
   dedicated indicator CRUD in `admin.py`.

**Conclusion:** a future AI layer that wants to surface *candidate* indicators for a
*specific session* without mutating shared clinical content will need a **new,
session-scoped intake contract** (proposed in §11). No existing API satisfies this
safely. (Not implementing it here.)

---

## 5. Branching Engine

### 5.1 Current deterministic adaptation (already implemented)

The system **already supports adaptive questioning** deterministically via
`question_dependencies`. This must not be reimplemented by the AI layer.

- **Substrate:** `question_dependencies(question_id, depends_on_question_id, condition_type,
  condition_value, logic_operator, group_id)`.
- **Condition types (`DependencyEvaluator.evaluate`):** `equals`, `not_equals`, `in`,
  `not_in`, `greater_than`/`gt`, `less_than`/`lt`, `gte`, `lte`, `range`, `has_any`,
  `has_all`, `is_empty`, `is_not_empty`, `computed` (BMI from `user_attributes`, age from
  `date_of_birth`).
- **Logical composition (`BranchingEvaluator`):**
  - Within a dependency *group* (`group_id`): operator is the group's `logic_operator`
    (`AND` default; `OR` supported).
  - Across groups: groups are **AND-ed** (`all(results)`).
  - `evaluate_branch_rules` supports a nested condition tree with explicit
    `operator ∈ {AND, OR, NOT}` nodes (`_evaluate_condition_tree`), recursive `clauses`.
- **Inputs to visibility:** (a) `answers_map` (previous answers in the session), (b)
  `user_attributes` from `session.metadata["user_attributes"]` (used by `computed` for
  BMI/age).
- **Question ordering:** within a group, by `order_index`; the next-question algorithm
  prefers the next unanswered visible question in the *current group*, then falls back to
  the first unanswered visible question overall.
- **`evaluate_branching`** also records a `branch_path` list (`[answered_qid, "hidden:<qid>", ...]`),
  persisted on the answer's `branch_path` JSON column.

### 5.2 Future AI-assisted adaptation (distinct from the above)

The deterministic engine decides visibility/ordering from fixed dependencies. The future AI
layer should **augment** this, not replace it: AI proposes *candidate question groups* or
*additional indicators* that the deterministic engine then validates/expands into concrete
questions through the existing branching substrate. The boundary: AI may suggest what to
explore; the dependency table + `BranchingEvaluator` remain the arbiter of what is actually
shown.

---

## 6. Indicator Engine

### 6.1 Question → indicator relationships (verified)

1. **Can one question map to multiple indicators?** Yes. `get_indicators_by_question_batch`
   returns `dict[question_id, list[Indicator]]`; the CDSE iterates all of them
   (`for ind in q_indicators`), each accumulating `+1.0`.
2. **Can one option activate multiple indicators?** Yes. Same shape via
   `get_indicators_by_option_batch`; each option→indicator pair contributes
   `+option.score_value`.
3. **Can indicators have different weights?** The `clinical_indicators` table has
   `positive_weight`/`negative_weight`/`neutral_weight`/`confidence` columns, **but the CDSE
   does not currently use them** — question-level contribution is a flat `+1.0` and
   option-level uses the *option's* `score_value`, not the indicator's weights. These columns
   are seed metadata for future/expected behavior, not active in the scoring loop.
4. **How is the score calculated?** Summation: question-level `+1.0` per linked indicator per
   answered question; option-level `+float(option.score_value)` per linked indicator per
   option-bearing answer. No normalization at indicator stage.
5. **When is an indicator "activated"?** When its aggregated `score >= threshold`, where
   `threshold = 1.0` is hardcoded inside `process_assessment` (commented as "configurable").
   A single yes/option answer (weight 1.0) is enough to activate.
6. **Can an indicator be activated by multiple questions?** Yes — scores accumulate across
   all contributing questions/options; `indicator_sources` records every contributing source.
7. **Conflicting answers:** there is no explicit conflict resolution. Each answer is scored
   independently and summed. There is no notion of "negative evidence" in the active loop
   even though `negative_weight` exists on the indicator.

### 6.2 Indicator → condition → recommendation (verified)

- Condition score = sum of contributing activated-indicator scores (`if sc > 0`).
- Confidence = `score / max_condition_score_in_run` (relative), clamped `[0,1]`.
- Recommendations are attached 1:1 via `condition_recommendation_links` (and a parallel
  `indicator_recommendation_links` path exists but the CDSE uses the condition path).
- Lab tests attached via `condition_laboratory_test_links`.

---

## 7. Clinical Indicator Semantics

`clinical_indicators` columns (`backend/app/infrastructure/persistence/models/clinical_indicator.py`):

| Field | Meaning |
| ----- | ------- |
| `key` | Stable human-readable code, e.g. `CV_CHEST_PAIN`, `KD_PROTEINURIA` (unique). |
| `name` | Display name, e.g. "Chest Pain / Angina Equivalent". |
| `description` | Free-text clinical meaning (Text). |
| `body_system_id` | Owning body system. |
| `severity` | `mild` / `moderate` / `high` (seed values). |
| `evidence_strength` | A–C evidence grade. |
| `confidence` | 0–1 prior confidence (seeded, e.g. 0.85 for chest pain). |
| `positive_weight` / `negative_weight` / `neutral_weight` | Weights (metadata; not used by active CDSE loop). |
| `related_disease_ids` / `related_symptom_ids` | JSON arrays (loose links, no junction tables). |
| `order`, `is_active`, `version`, `status` (`draft`/`medical_review`/`approved`/`published`/`archived`), `created_by`/`updated_by` | Lifecycle + governance fields. |

**Seed data** (`backend/app/infrastructure/seed_medical.py`) defines ~29 indicators across
Cardiovascular (`CV_*`) and Kidney (`KD_*`) body systems, each with `severity`,
`evidence_strength`, and `confidence`. This is the concrete bridge candidate: an indicator
like `CV_CHEST_PAIN` has a stable `key`, a body system, linked conditions, and linked
evidence — so an AI-extracted observation ("I feel pressure in my chest when walking
uphill") can be mapped to the `CV_CHEST_PAIN` indicator id, after which the **existing**
deterministic engine takes over (indicator → condition → recommendation → report).

**Associations available per indicator (via the graph):** conditions
(`indicator_condition_links`), evidence (`indicator_evidence_links`), recommendations
(`indicator_recommendation_links`), questions (`question_indicator_links`), options
(`question_option_indicator_links`), body system (direct column), related
diseases/symptoms (JSON columns). This is sufficient for an AI layer to use the indicator as
the **bridge entity** between free-text observation and the deterministic CDSE.

---

## 8. Report Engine

`ReportService` (`backend/app/application/services/report_service.py`), entry
`generate_report(session_id, user_id)`; endpoint `POST /api/v1/report/generate`.

### 8.1 Inputs & steps

- Requires a CDSE result to already exist (`dec_repo.get_result_by_session`; raises if absent).
- Loads activated indicators, resolves their `body_system_id`, aggregates a per-body-system
  score (sum of indicator scores).
- Loads `severity_thresholds` (active, by `min_score`) to bucket each body-system score;
  falls back to hardcoded categories.
- Creates a `health_assessments` record, then `body_system_assessments`,
  `condition_assessments` (with `Very Weak/Weak/Moderate/Strong` confidence label),
  `lifestyle_assessments` (JSON snapshot from profile), and `generated_advices` (mapped from
  the CDSE's `generated_recommendations`).
- Computes a small `summary` dict (counts).
- `compare_reports(id1, id2)` does a set-diff on body-system / condition / advice ids.

### 8.2 What is persisted for reproducibility

- `assessment_results`: `session_id`, `user_id`, `summary` (stringified dict incl. `trace_id`
  and raw `indicator_scores`), `confidence_score`.
- `activated_indicators`: `indicator_id`, `score`, `evidence_count`, `notes`.
- `activated_conditions`: `condition_id`, `score`, `confidence`, `notes`.
- `generated_recommendations`: `recommendation_id`, `source` (`condition:<cid>`),
  `notes` (trace text).
- `generated_laboratory_tests`: `laboratory_test_id`, `reason` (trace text).
- `generated_screenings`: `name`, `reason`.
- `explanation_records`: `source_type` (`answer`/`indicator`/`condition`),
  `source_id`, `text` (the `[trace:...]` strings).
- `health_assessments` + child assessment tables (the report view).
- `assessment_answers`: each answer keeps `question_version`, `question_code`, `option_id`,
  `value`, `numeric_value`, `response_value` (JSON), `score_value`, `branch_path`, `recorded_at`.

---

## 9. Current Traceability

**Yes — the system can already answer "why" questions**, via `explanation_records` +
`indicator_sources`/`condition_indicator_map`, all stamped with a run-scoped `trace_id`.

| Question | Mechanism (exact) |
| -------- | ------------------ |
| "Why was this indicator activated?" | `explanation_records` row with `source_type='indicator'`, `source_id=<indicator_id>`, `text="[trace:{trace_id}] Indicator {id}: score={score}, evidence_count={n}, sources={...}"`. `sources` lists each contributing `{question_id, type, option_id, weight, value}`. |
| "Why was this condition considered?" | `explanation_records` row `source_type='condition'`, `text="[trace:...] Condition {id}: score={sc}, contributing_indicators=[...], confidence={...}"`. |
| "Why was this recommendation generated?" | `generated_recommendations.source = "condition:<cid>"` and `notes = "[trace:...] Score {sc} triggered recommendation {rid}"`. |

**Trace id:** `trace_id = uuid.uuid4().hex[:16]` generated once per `process_assessment` run,
embedded in every explanation string and in `assessment_results.summary`. This is the
foundation for future AI explainability: an AI explanation layer must **reference** these
trace records rather than invent rationale.

---

## 10. Current Free-Text Capabilities

There are **two distinct** kinds of free text today; neither feeds the CDSE.

1. **`free_text` question type (assessment-scoped).** A first-class `QuestionType.FREE_TEXT`
   with frontend `FreeTextInput.tsx`, backend `ValidationEngine._validate_text`
   (`min_length`/`max_length`/`pattern`). Path:
   `Frontend (FreeTextInput) → POST /questionnaires/sessions/{id}/answer (response_value={value:<str>}) → AssessmentAnswerModel.response_value (JSON) + value (String(500))`.
   **CDSE impact: none**, unless the question is question-level-linked to an indicator
   (option-level links are impossible — there is no option). So a free-text answer can at
   best activate a question-level indicator with a flat `+1.0`, independent of the textual
   content. The text itself is never interpreted.

2. **Profile notes (profile-scoped, not assessment).** `medical_histories.notes`,
   `family_histories.notes`, profile wizard "General Notes", etc. Stored in profile tables
   via `ProfileService`; not consumed by the CDSE or report engine (only
   `lifestyle` is stringified into `lifestyle_assessments`).

**Conclusion for AI design:** There is **no dedicated patient-observation / natural-language
intake layer that produces structured observations or candidate indicators**. Free text is
captured but inert. This is the single biggest gap the future AI intake must fill, and it
must be a **new** layer — the existing `free_text` question type is a display/storage
mechanism, not an extraction pipeline.

---

## 11. AI Integration Opportunities

Four candidates evaluated. None implemented. For each: location, existing API, required new
component, risks, data required, reusability of existing entities.

### Candidate A — Patient free text → AI → structured observations → CDSE

- **Location:** a new pre-assessment intake step *before* `/questionnaires/{id}/start`,
  producing structured observations that map to candidate indicators.
- **Existing API to reuse:** `KnowledgeGraphService` /
  `SQLKnowledgeGraphRepository.get_indicators_by_question*` (read-only) to resolve candidate
  indicator ids; the indicator `key`/`name`/`description` as the AI's target vocabulary.
- **Required new component:** an `AIObservationService` (extraction → candidate indicators),
  a session-scoped intake store, and a contract that the CDSE can read candidate indicators
  from (today it only reads from graph links — see §4.3).
- **Risks:** hallucinated indicator mappings; mapping text to the wrong indicator;
  over-triggering; PHI leaving the system via an external LLM.
- **Data required:** patient free text; the indicator catalog (read-only); body-system
  context from the selected template.
- **Reuses existing entities:** `clinical_indicators` (as the target vocabulary), `body_systems`,
  `question_groups`, the future session. **Highest value, highest risk.** Recommended first.

### Candidate B — Question selection → AI-assisted candidate question groups → deterministic validation

- **Location:** between template selection and `QuestionnaireEngineImpl.load_questions`.
- **Existing API to reuse:** `SQLQuestionGroupRepository.find_by_body_system`,
  `SQLQuestionRepository.find_by_group`, the branching substrate.
- **Required new component:** a recommender that, given observations + profile, proposes
  *which question groups* to present; the deterministic `BranchingEvaluator` still gates
  visibility.
- **Risks:** skipping clinically required groups; bias toward "interesting" branches.
- **Data required:** observations (from A), profile `user_attributes`, group metadata.
- **Reuses existing entities:** `question_groups`, `questions`, `question_dependencies`.
- **Note:** because `find_by_questionnaire` ignores the template id (§1.2), a per-session
  group *allowlist* would be the natural hook and would also fix that latent quirk.

### Candidate C — Report → RAG → AI explanation

- **Location:** after `ReportService.generate_report`, on the report viewer.
- **Existing API to reuse:** `GET /api/v1/report/{session_id}`,
  `GET /api/v1/assessment/{session_id}/explanation`, `GET /api/v1/assessment/{session_id}/recommendations`.
- **Required new component:** a RAG summarizer over the report + `explanation_records` +
  `evidence_references`; output is a plain-language narrative **anchored to trace ids**.
- **Risks:** narrative drift beyond what the deterministic engine concluded; inventing
  evidence not in `evidence_references`.
- **Data required:** the report, its explanations, its evidence refs.
- **Reuses existing entities:** `health_assessments`, `explanation_records`,
  `evidence_references`, `recommendations`. **Lowest risk.** Good early win.

### Candidate D — Evidence → RAG → patient explanation

- **Location:** per-recommendation or per-indicator explanation view.
- **Existing API to reuse:** `GET /api/v1/graph/indicator/{id}` (conditions + evidence),
  `evidence_references` table.
- **Required new component:** RAG over `evidence_references` (`title/url/source/summary`)
  scoped to the activated indicators; output a cited, patient-readable rationale.
- **Risks:** mis-citing; summarizing beyond the cited source; readability vs. accuracy.
- **Data required:** the indicator's `evidence_references`.
- **Reuses existing entities:** `evidence_references`, `clinical_indicators`. Low–medium
  risk; depends on evidence data quality.

---

## 12. Recommended AI Architecture (contract only — not implemented)

Conceptual target flow (matches the brief):

```
Patient text
      ↓
AI extraction                          [FUTURE AI]
      ↓
Structured observation                 [FUTURE AI]
      ↓
Candidate clinical indicators          [FUTURE AI] → Clinical Knowledge Graph [EXISTING]
      ↓
Question groups (candidate)           [FUTURE AI] → existing question bank [EXISTING]
      ↓
Existing adaptive questionnaire        [EXISTING]
      ↓
Existing deterministic CDSE            [EXISTING]
      ↓
Evidence-traceable Report              [EXISTING]
      ↓
Future RAG explanation                 [FUTURE AI]
```

### Proposed AI output contract (what the AI is allowed to emit)

```json
{
  "observations": [
    {
      "text": "patient-authored original phrase",
      "category": "symptom|behavior|lifestyle|history|concern",
      "confidence": 0.0,
      "source_span": { "start": 0, "end": 0 }
    }
  ],
  "candidate_indicator_ids": ["<existing clinical_indicators.id>"],
  "candidate_question_group_ids": ["<existing question_groups.id>"],
  "clarifying_questions": [
    { "text": "...", "target_indicator_id": "<id>", "rationale": "..." }
  ],
  "evidence": [
    { "evidence_reference_id": "<existing id>", "relevance": 0.0 }
  ]
}
```

**Rules for the contract:**

- `candidate_indicator_ids` MUST reference existing rows in `clinical_indicators` (validated
  server-side). The AI cannot invent indicator ids.
- `candidate_question_group_ids` MUST reference existing `question_groups`. The deterministic
  `BranchingEvaluator` + dependency table decide actual visibility — candidates are a *hint*,
  not a *command*.
- `clarifying_questions` are *suggestions* for the adaptive layer; they do not bypass the
  question bank and must be reviewed/linked by a content editor before they can carry
  indicator links (otherwise they are informational only).
- `evidence` MUST reference existing `evidence_references`; relevance is the AI's ranking only.
- `confidence` fields are the AI's *self-reported* extraction confidence, **never** a clinical
  probability. The deterministic CDSE produces the only clinical confidence.

### What the AI must NOT directly determine (boundary)

`diagnosis`, `severity`, `final probability`, `final recommendation`. These are outputs of
the deterministic CDSE and `ReportService` only. The AI may *summarize* them (Candidates C/D)
but not *produce* them.

---

## 13. AI Safety Boundary

### AI MAY

- Interpret patient natural language (extract observations, normalize phrasing).
- Identify *candidate* clinical concepts by mapping text to existing `clinical_indicators`.
- Suggest relevant `question_groups` to explore (subject to deterministic validation).
- Translate questionnaire/report text and simplify language (accessibility).
- Retrieve and rank existing `evidence_references` (RAG).
- Summarize deterministic reports and explanations **anchored to existing trace ids**.

### AI MAY NOT

- Diagnose or name a final condition.
- Override deterministic scoring, thresholds, or severity bands.
- Modify clinical rules, dependencies, or the knowledge graph directly.
- Create new medical content (indicators, conditions, recommendations, evidence)
  autonomously.
- Publish CMS content or bypass the publishing workflow / approvals.
- Change severity thresholds or `confidence_score`.
- Invent evidence or cite sources not in `evidence_references`.
- Bypass RBAC (`get_current_user` / `get_cms_user` / `get_current_admin`).
- Bypass the knowledge graph (no direct text→recommendation shortcut).
- Compute or alter the clinical `confidence_score` (relative-normalized by the CDSE).
- Mutate shared content for an individual session (graph links are global — see §4.3).

### Governance reuse (existing, already built)

The future AI governance can reuse the existing CMS publishing pipeline:
`PublishingWorkflowService` (workflows, change requests, approvals, reviews, version
snapshots), `VALID_TRANSITIONS` (`draft → medical_review → approved → published → archived`),
the `audit_log` middleware, and RBAC roles (`medical_director`, `content_editor`,
`read_only_reviewer`). Any AI-proposed *content* (e.g. a new indicator→condition link it
suggests) must enter the same `draft → review → approval` funnel; the AI never publishes.

---

## 14. Doctor CMS Integration

### 14.1 What the CMS can already manage (verified)

| Capability | Status | Where |
| ---------- | ------ | ----- |
| Clinical indicators (CRUD, status, version, governance fields) | ✅ | `cms/content.py` (`ENTITY_REGISTRY["clinical_indicator"]`), `admin.py` |
| Questions (CRUD, types incl. `free_text`, validation rules, status) | ✅ | `cms/questions.py` (`cms_create_question`), `SQLQuestionRepository` |
| Options (CRUD, `score_value`, `severity`, triggers) | ✅ | `cms/questions.py`, `SQLQuestionOptionRepository` |
| Conditions (`possible_conditions`) | ✅ | graph router `create_condition`, CMS content |
| Recommendations (CRUD, priority/urgency/evidence_level) | ✅ | `ENTITY_REGISTRY["recommendation"]` |
| Evidence references | ✅ | `cms/evidence.py`, `evidence_references` |
| Question groups | ✅ | `SQLQuestionGroupRepository`, CMS |
| Branching / dependencies | ✅ | `question_dependencies` managed via CMS question authoring; `BranchingEvaluator` consumes them |
| Publishing (workflows, change requests, approvals, reviews) | ✅ | `PublishingWorkflowService`, `cms/publishing.py` |
| Versioning (snapshots, questionnaire versions) | ✅ | `version_snapshots`, `questionnaire_versions`, `VersionHistoryPage` |
| Audit logs | ✅ | `audit_log` model + `audit.py` middleware + `cms/audit.py` viewer |
| Rule sets (create/simulate/validate) | ✅ | `cms/rules.py`, `RuleEngineService` |
| Knowledge graph editor | ✅ | `cms/knowledge_graph.py`, `KnowledgeGraphEditorService` |
| Users / roles | ✅ | `admin.py` (`GET/PUT /admin/users/{id}/roles`, toggle-active) |

### 14.2 Future AI governance functionality that can reuse the CMS

- **Change requests for AI-suggested links:** an AI suggestion of a new
  `question_indicator`/`indicator_condition` link can be written as a `ChangeRequest` and
  routed through the existing `medical_review → approved → published` workflow.
- **Version snapshots** can capture the knowledge graph state before/after an AI-assisted
  batch import for rollback.
- **Audit log** can record "proposed by AI, approved by <medical_director>" provenance.
- **Users/roles** already separates who may *propose* vs *approve* (RBAC hierarchy via
  `has_role` + `_ROLE_HIERARCHY`).

**No CMS modification is required or proposed.** The AI governance layer would sit *on top*
of these existing primitives.

---

## 15. Future Database Requirements (conceptual only — no migrations)

The existing schema **can support** AI integration with **additive tables only**; no existing
table needs structural change. Candidate new tables (conceptual, not created):

| Conceptual table | Purpose | Key fields (conceptual) | Reuse |
| ---------------- | ------- | ----------------------- | ----- |
| `patient_observations` | Store AI-extracted structured observations per session | `id`, `session_id`→`assessment_sessions`, `text`, `category`, `ai_confidence`, `source_span` | reuses `assessment_sessions` |
| `ai_extractions` | Provenance of an extraction run (model, prompt hash, input hash, timestamps) | `id`, `observation_batch_id`, `model_id`, `input_hash`, `created_at`, `created_by` | new |
| `ai_candidate_indicators` | AI-proposed indicator mapping for a session (not global) | `id`, `extraction_id`, `indicator_id`→`clinical_indicators`, `ai_confidence`, `status` | reuses `clinical_indicators` |
| `ai_traces` | Link an AI extraction to the deterministic `trace_id` for end-to-end audit | `id`, `extraction_id`, `trace_id` (matches `assessment_results.summary.trace_id`), `result_id`→`assessment_results` | reuses `assessment_results`, `explanation_records` |
| `ai_evidence_retrievals` | RAG retrieval log (which `evidence_references` were fetched, ranking, for which report) | `id`, `report_id`→`health_assessments`, `evidence_id`→`evidence_references`, `relevance`, `prompt_hash` | reuses `evidence_references`, `health_assessments` |
| `ai_explanations` | AI-generated narrative anchored to a deterministic report/trace | `id`, `report_id`, `trace_id`, `narrative`, `model_id`, `citation_ids[]` | reuses `health_assessments`, `evidence_references` |

**Why additive is enough:** every AI concept references *existing* entities (sessions,
indicators, results, reports, evidence). The deterministic tables
(`assessment_answers`, `assessment_results`, `activated_indicators`, `explanation_records`,
`clinical_indicators`, `question_indicator_links`, …) are **untouched**. The CDSE would gain
a *read-only* view of `ai_candidate_indicators` (one new input source alongside the graph
links) — but per the boundary, the CDSE's logic does not change; only an adapter would feed it
extra candidate ids (still a future implementation decision, not done here).

---

## 16. Final Architecture Diagram

```
                         ┌─────────────────────────────────────────────┐
                         │                  PATIENT                      │
                         └─────────────────────────────────────────────┘
                                   │
                                   ▼
   ╔═══════════════════════════════╗   FUTURE AI: intake / extraction
   ║   Future AI Intake            ║   (free text → structured observations)
   ║   (observations, candidate    ║
   ║    indicators, candidate      ║
   ║    question groups)           ║
   ╚═══════════════════════════════╝
                                   │  (contract: §12 — references existing ids only)
                                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  EXISTING: Clinical Knowledge Graph                                    │
   │  questions ──question_indicator_links──► clinical_indicators           │
   │  question_options ──option_indicator_links──► clinical_indicators       │
   │  clinical_indicators ──indicator_condition_links──► possible_conditions │
   │  clinical_indicators ──indicator_evidence_links──► evidence_references  │
   │  possible_conditions ──condition_recommendation_links──► recommendations│
   │  possible_conditions ──condition_lab_links──► laboratory_tests         │
   │  body_systems ──body_system_condition_links──► possible_conditions      │
   └──────────────────────────────────────────────────────────────────────┘
                                   │  (candidate groups feed selection)
                                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  EXISTING: Adaptive Questionnaire                                      │
   │  QuestionnaireEngineImpl.load_questions / get_next_question             │
   │  → BranchingEvaluator (question_dependencies: AND/OR/NOT, computed)    │
   │  → ValidationEngine (incl. free_text)                                   │
   │  one question at a time, server-driven; answers → assessment_answers    │
   └──────────────────────────────────────────────────────────────────────┘
                                   │  (on completion: POST /assessment/process)
                                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  EXISTING: Deterministic CDSE  (ClinicalDecisionService.process_assessment)│
   │  answers → indicators (graph traversal) → activate (score ≥ 1.0)       │
   │  → conditions (relative-normalized confidence) → recommendations + labs │
   │  trace_id per run; explanations persisted in explanation_records       │
   └──────────────────────────────────────────────────────────────────────┘
                                   │  (POST /report/generate)
                                   ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  EXISTING: Evidence-traceable Report  (ReportService.generate_report) │
   │  body-system scores + severity_thresholds → health_assessments + children│
   │  explanations + trace_id preserved                                      │
   └──────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
   ╔═══════════════════════════════╗   FUTURE AI: RAG explanation
   ║   Future RAG Explanation      ║   (narrative anchored to trace_id +
   ║   (patient + clinician view,  ║    existing evidence_references)
   ║    cited, trace-anchored)     ║
   ╚═══════════════════════════════╝

   Governance (EXISTING, reused): CMS publishing (change requests → medical_review →
   approved → published), version snapshots, audit_log, RBAC roles. Any AI-proposed
   content enters the SAME funnel; AI never publishes directly.
```

**Legend:** `EXISTING` boxes are unchanged deterministic components verified in this audit.
`FUTURE AI` boxes are proposed additions only. The AI layer connects at two seams —
*before* the adaptive questionnaire (intake/observations/candidates) and *after* the report
(RAG explanation) — plus an optional governance reuse of the CMS publishing funnel.

---

## 17. Recommended Implementation Order

(Sequencing only — nothing implemented in this audit.)

1. **Candidate C — RAG report explanation (lowest risk, high value).** Pure read-only over
   `health_assessments` + `explanation_records` + `evidence_references`. No clinical
   behavior change; validates the traceability-anchoring pattern.
2. **Candidate D — Evidence RAG per indicator/recommendation.** Builds on C; depends on
   evidence data quality.
3. **Candidate A — Patient free-text → structured observations → candidate indicators.**
   The core differentiator. Requires the new session-scoped intake store (§15) and the
   output contract (§12). Must validate `candidate_indicator_ids` against existing rows.
4. **Candidate B — AI-assisted candidate question groups.** Builds on A; uses
   observations + profile to propose groups, gated by the existing `BranchingEvaluator`.
   Also the natural place to fix the `find_by_questionnaire`-ignores-template quirk via a
   per-session group allowlist.
5. **AI governance wiring.** Route AI-suggested *content* through the existing
   `ChangeRequest → medical_review → approved → published` workflow; record provenance in
   `audit_log`. Reuses CMS, no CMS changes.

Each stage keeps the deterministic CDSE, scoring, branching, report, and CMS untouched,
consistent with the safety boundary in §13.

---

## 18. Verification

This audit was performed read-only. Per the task instructions, `git status` was run after
the work:

- Working tree was clean before this report.
- The only artifact created by this task is **this file** (`MEDICHECK_AI_BASELINE.md`).
- No application code, database schema, migration, CDSE logic, questionnaire, scoring, CMS,
  or RBAC was modified.
- No AI/LLM packages were installed (none exist in the codebase today — verified by
  searching `requirements.txt`, `requirements/`, and `app/` for openai/anthropic/langchain/
  llm/gemini/transformers/spacy/sklearn; the only matches were the unrelated word
  "enrollment").

(See the `git status` output captured at the end of the audit run confirming a clean tree
prior to this file's creation. This report is intentionally the sole change.)
