# Sequence Diagrams — Medicheck

---

## 1. Patient Completes Questionnaire

```mermaid
sequenceDiagram
    actor Patient as Patient
    participant FE as Frontend
    participant QS as QuestionnaireService
    participant QE as QuestionnaireEngine
    participant DB as Database

    Patient->>FE: Select template / start assessment
    FE->>QS: start_session(user, template_id)
    QS->>QS: Load template & questions
    QS->>QE: load_questions(session)
    QE->>DB: Query active questions
    DB-->>QE: questions[]
    QE-->>QS: questions
    QS->>QS: Determine first question & options
    QS-->>FE: { session_id, current_question, options }
    FE-->>Patient: Display first question

    loop For each question
        Patient->>FE: Submit answer (option selection)
        FE->>QS: save_answer(session_id, answer_data)
        QS->>QE: validate_answer(question, response)
        QE-->>QS: errors (or empty)
        QS->>QS: Compute score_value from option
        QS->>QS: Create AssessmentAnswer
        QS->>DB: INSERT assessment_answer
        QS->>QE: evaluate_branching(session, answer)
        QE->>QE: Check dependencies & branch rules
        QE-->>QS: branch_path[]
        QS->>QE: get_next_question(session, current)
        QE->>DB: Load dependencies
        QE->>QE: Evaluate visibility rules
        QE-->>QS: next_question (or null)
        QS-->>FE: { answer, next_question }
        FE-->>Patient: Next question (or completion)

        alt Dependency not met
            QE->>QE: Skip question (mark hidden)
        end
    end

    Patient->>FE: Submit final / complete
    FE->>QS: complete_session(session_id)
    QS->>QE: calculate_progress(session)
    QE-->>QS: progress
    QS->>QS: _calculate_scores()
    QS->>QE: calculate_overall_score()
    QE-->>QS: score_summary
    QS->>DB: UPDATE session status = completed
    QS-->>FE: { status, score_summary }
    FE-->>Patient: Assessment complete
```

---

## 2. Doctor Reviews Assessment & Generates Report

```mermaid
sequenceDiagram
    actor Doctor
    participant FE as Frontend
    participant RS as ReportService
    participant CDS as ClinicalDecisionService
    participant KG as KnowledgeGraphRepository
    participant DB as Database

    Doctor->>FE: Select patient assessment session
    FE->>RS: generate_report(session_id, user_id)
    RS->>CDS: process_assessment(session_id, user_id)
    
    CDS->>DB: Load AssessmentSession with answers
    DB-->>CDS: session + answers[]

    CDS->>KG: get_indicators_by_question_batch(all_qids)
    KG-->>CDS: question->indicators map
    CDS->>KG: get_indicators_by_option_batch(all_option_ids)
    KG-->>CDS: option->indicators map

    CDS->>CDS: Aggregate indicator scores (threshold >= 1.0)
    CDS->>CDS: Determine activated_indicators

    CDS->>KG: get_evidence_by_indicator_batch(activated_ids)
    KG-->>CDS: indicator->evidence map
    CDS->>KG: get_conditions_by_indicator_batch(activated_ids)
    KG-->>CDS: indicator->conditions map
    CDS->>CDS: Aggregate condition scores

    CDS->>KG: get_recommendations_by_condition_batch(condition_ids)
    KG-->>CDS: condition->recommendations map
    CDS->>KG: get_laboratory_tests_by_condition_batch(condition_ids)
    KG-->>CDS: condition->lab_tests map

    CDS->>DB: Persist AssessmentResult + activated_indicators + activated_conditions + recommendations + labs + explanations
    CDS-->>RS: { result_id, summary, confidence_score }

    RS->>DB: Load decision result
    DB-->>RS: result with all relations

    RS->>RS: Aggregate body system scores
    RS->>DB: Load SeverityThresholds
    DB-->>RS: thresholds

    RS->>DB: CREATE health_assessment
    RS->>DB: INSERT body_system_assessments
    RS->>DB: INSERT condition_assessments
    RS->>RS: Calculate confidence labels

    RS->>DB: Load profile & lifestyle
    DB-->>RS: lifestyle data
    RS->>DB: INSERT lifestyle_assessment
    RS->>RS: Map generated recommendations to advice text
    RS->>DB: INSERT generated_advices

    RS-->>FE: { report_id, summary }

    FE-->>Doctor: Display comprehensive report
    Doctor->>FE: Add clinical notes / finalize
```

---

## 3. Clinical Decision Support Engine (CDSE) Processing Pipeline

```mermaid
sequenceDiagram
    participant CDS as ClinicalDecisionService
    participant KG as KnowledgeGraphRepo
    participant DEC as DecisionRepo
    participant DB as Database

    Note over CDS: process_assessment(session_id)

    CDS->>DB: Load session + answers (selectin)
    DB-->>CDS: session, answers[]

    CDS->>CDS: Build answer_map { question_id -> [answers] }

    par Batch Load 1
        CDS->>KG: get_indicators_by_question_batch(qids)
        KG-->>CDS: q_indicators_map
    and Batch Load 2
        CDS->>KG: get_indicators_by_option_batch(option_ids)
        KG-->>CDS: opt_indicators_map
    and Batch Load 3
        CDS->>DB: Load QuestionOption models by ids
        DB-->>CDS: opt_models (with score_values)
    end

    CDS->>CDS: Generate trace_id (uuid hex 16)
    CDS->>CDS: Aggregate indicator_scores from questions & options
    CDS->>CDS: Filter activated_indicators (score >= 1.0)

    CDS->>DEC: create_result({ session_id, user_id, ... })
    DEC-->>CDS: result (AssessmentResult)

    par Batch Load 4
        CDS->>KG: get_evidence_by_indicator_batch(activated_ids)
        KG-->>CDS: evidence_map
    and Batch Load 5
        CDS->>KG: get_conditions_by_indicator_batch(activated_ids)
        KG-->>CDS: conditions_map
    end

    loop For each activated indicator
        CDS->>DEC: add_activated_indicator(result.id, ind_id, score, evidence_count)
        CDS->>DEC: add_explanation(result.id, "indicator", ind_id, text)
    end

    CDS->>CDS: Aggregate condition_scores from indicators
    CDS->>CDS: Filter activated_conditions (score > 0)
    CDS->>CDS: Compute max_possible_condition_score

    par Batch Load 6
        CDS->>KG: get_recommendations_by_condition_batch(condition_ids)
        KG-->>CDS: recs_map
    and Batch Load 7
        CDS->>KG: get_laboratory_tests_by_condition_batch(condition_ids)
        KG-->>CDS: labs_map
    end

    loop For each activated condition
        CDS->>CDS: Normalize confidence (score / max_score, clamp 0-1)
        CDS->>DEC: add_activated_condition(result.id, cond_id, score, confidence)
        CDS->>DEC: add_explanation(result.id, "condition", cond_id, text)
        loop For each recommendation
            CDS->>DEC: add_recommendation(result.id, rec_id, source, notes)
        end
        loop For each lab test
            CDS->>DEC: add_laboratory_test(result.id, lab_id, reason)
        end
    end

    CDS->>CDS: Compute overall_confidence (mean of condition confidences)
    CDS->>DB: UPDATE assessment_session status = "processed"
    CDS->>DB: UPDATE assessment_result summary + confidence_score
    CDS-->>CDS: Return { result_id, summary, confidence_score }
```

---

## 4. Knowledge Graph Search & Navigation

```mermaid
sequenceDiagram
    actor Editor as Medical Editor
    participant FE as Frontend
    participant KGS as KnowledgeGraphService
    participant KGR as KnowledgeGraphRepo
    participant DB as Database

    Editor->>FE: Search knowledge graph
    FE->>KGS: search_graph(query)
    KGS->>KGS: Search across names & descriptions
    KGS->>DB: List indicators (admin_repo)
    DB-->>KGS: indicators[]
    KGS-->>FE: { questions, indicators, conditions, recommendations, evidence }

    Editor->>FE: View question-indicator relationships
    FE->>KGS: build_graph_from_question(question_id)
    KGS->>KGR: Traverse from question
    KGR->>DB: Get question
    KGR->>DB: Get linked indicators (question_indicator_links)
    DB-->>KGR: indicators[]
    loop For each indicator
        KGR->>DB: Get linked conditions (indicator_condition_links)
        KGR->>DB: Get linked evidence (indicator_evidence_links)
        DB-->>KGR: conditions[], evidence[]
        loop For each condition
            KGR->>DB: Get linked recommendations (condition_recommendation_links)
            KGR->>DB: Get linked lab tests (condition_laboratory_test_links)
            DB-->>KGR: recommendations[], labs[]
        end
    end
    KGR-->>KGS: Full graph structure
    KGS-->>FE: Visual graph data
    FE-->>Editor: Display interactive graph

    Editor->>FE: Follow node (e.g., condition)
    FE->>KGS: get_conditions_by_indicator(indicator_id)
    KGS->>KGR: Query link table
    KGR-->>KGS: linked conditions
    KGS-->>FE: condition details
```

---

## 5. CMS Content Lifecycle (Create → Update → Publish)

```mermaid
sequenceDiagram
    actor Editor as Medical Editor
    participant CMS as CMSContentService
    participant REPO as GenericCMSRepository
    participant DB as Database

    Note over Editor,DB: CREATE
    Editor->>CMS: create_entity(entity_type, data, user_id)
    CMS->>CMS: Lookup ENTITY_REGISTRY[entity_type]
    CMS->>CMS: domain_entity.create(**data, created_by)
    CMS->>REPO: create(model)
    REPO->>DB: INSERT
    DB-->>REPO: created model
    REPO-->>CMS: created
    CMS-->>Editor: Created entity (default status: "draft")

    Note over Editor,DB: UPDATE
    Editor->>CMS: update_entity(entity_type, entity_id, updates, user_id)
    CMS->>REPO: find_by_id(entity_id)
    REPO->>DB: SELECT
    DB-->>REPO: existing model
    REPO-->>CMS: model
    CMS->>CMS: Set fields from updates
    CMS->>CMS: Increment version
    CMS->>REPO: update(model)
    REPO->>DB: UPDATE
    DB-->>REPO: updated model
    REPO-->>CMS: updated
    CMS-->>Editor: Updated entity

    Note over Editor,DB: STATUS TRANSITION
    Editor->>CMS: update_status(entity_type, entity_id, new_status, user_id)
    CMS->>CMS: VALID_TRANSITIONS[current] contains new_status?
    alt Invalid transition
        CMS-->>Editor: Error: invalid transition
    else Valid transition
        CMS->>REPO: update(status, updated_by)
        REPO->>DB: UPDATE
        DB-->>REPO: updated model
        REPO-->>CMS: result
        CMS-->>Editor: Entity with new status
    end

    Note over Editor,DB: DELETE (soft)
    Editor->>CMS: delete_entity(entity_type, entity_id, user_id)
    CMS->>REPO: soft_delete(entity_id)
    REPO->>DB: SET deleted_at = now
    DB-->>REPO: success
    REPO-->>CMS: done
    CMS-->>Editor: Deleted

    Note over Editor,DB: RESTORE
    Editor->>CMS: restore_entity(entity_type, entity_id)
    CMS->>REPO: restore(entity_id)
    REPO->>DB: SET deleted_at = NULL
    DB-->>REPO: restored model
    REPO-->>CMS: restored
    CMS-->>Editor: Restored entity
```

---

## 6. Publishing Workflow (Change Request → Approval → Snapshot)

```mermaid
sequenceDiagram
    actor Editor as Medical Editor
    actor Approver
    participant PWS as PublishingWorkflowService
    participant DB as Database

    Note over Editor,DB: Step 1: Create Change Request
    Editor->>PWS: create_change_request(entity_type, entity_id, user, title, changes)
    PWS->>DB: INSERT change_requests
    DB-->>PWS: created
    PWS-->>Editor: { id, status: "pending", changes, ... }

    Note over Editor,DB: Step 2: Create Approval
    Editor->>PWS: create_approval(entity_type, entity_id, requested_by, assigned_to)
    PWS->>DB: INSERT approvals
    DB-->>PWS: created
    PWS-->>Editor: { id, status: "pending", ... }

    Note over Editor,DB: Step 3: Review
    Editor->>PWS: create_review(entity_type, entity_id, reviewer_id)
    PWS->>DB: INSERT reviews
    DB-->>PWS: created
    PWS-->>Editor: { id, status: "pending" }

    Approver->>PWS: complete_review(review_id, decision, comments, score)
    PWS->>PWS: domain Review.complete()
    PWS->>DB: UPDATE reviews (status, decision, completed_at)
    DB-->>PWS: updated
    PWS-->>Approver: Completed review

    Note over Editor,DB: Step 4: Approve Change Request
    Approver->>PWS: approve_change_request(cr_id, user_id)
    PWS->>PWS: domain ChangeRequest.approve()
    PWS->>DB: UPDATE change_requests (status = approved, resolved_by)
    DB-->>PWS: updated
    PWS-->>Approver: Approved

    alt Conflict Detection
        Editor->>PWS: detect_conflicts(entity_type, entity_id)
        PWS->>DB: SELECT pending change_requests
        PWS->>PWS: Compare overlapping fields
        PWS-->>Editor: [ { request_a, request_b, overlapping_fields } ]
    end

    Note over Editor,DB: Step 5: Approve the Approval
    Approver->>PWS: approve_entity(approval_id, user_id, comment)
    PWS->>PWS: domain Approval.approve()
    PWS->>DB: UPDATE approvals (status = approved, decided_at)
    DB-->>PWS: updated
    PWS-->>Approver: Approved

    Note over Editor,DB: Step 6: Create & Execute Publishing Job
    Editor->>PWS: create_job(entity_type, entity_id, version, requested_by)
    PWS->>DB: INSERT publishing_jobs
    DB-->>PWS: created
    PWS-->>Editor: { id, status: "pending" }

    Approver->>PWS: approve_job(job_id, user_id)
    PWS->>DB: UPDATE publishing_jobs (status = "approved", approved_by)
    DB-->>PWS: updated
    PWS-->>Approver: Job approved

    Editor->>PWS: execute_publish(job_id)
    PWS->>PWS: Validate job status = "approved"
    PWS->>DB: INSERT version_snapshot (snapshot_type = "publish")
    PWS->>DB: UPDATE publishing_jobs (status = "published", published_at)
    DB-->>PWS: updated
    PWS-->>Editor: { status: "published" }

    Note over Editor,DB: Rollback
    Editor->>PWS: rollback_job(job_id, rollback_version)
    PWS->>DB: GET snapshot at rollback_version
    DB-->>PWS: snapshot
    PWS->>DB: INSERT new version_snapshot (snapshot_type = "rollback")
    PWS->>DB: UPDATE publishing_jobs (status = "rolled_back")
    DB-->>PWS: updated
    PWS-->>Editor: Rolled back
```

---

## 7. Admin CRUD Operations

```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin Frontend
    participant AS as AdminService
    participant DB as Database

    Note over Admin,DB: BODY SYSTEMS
    Admin->>AS: create_body_system(user_id, data)
    AS->>DB: INSERT body_systems
    AS->>DB: INSERT audit_logs (action="create")
    DB-->>AS: created
    AS-->>Admin: BodySystem

    Admin->>AS: update_body_system(user_id, bs_id, data)
    AS->>DB: GET old body_system
    AS->>DB: UPDATE body_systems
    AS->>DB: INSERT audit_logs (action="update", old_value, new_value)
    DB-->>AS: updated
    AS-->>Admin: Updated BodySystem

    Note over Admin,DB: INDICATORS
    Admin->>AS: create_indicator(user_id, data)
    AS->>DB: INSERT clinical_indicators
    AS->>DB: INSERT audit_logs
    DB-->>AS: created
    AS-->>Admin: ClinicalIndicator

    Admin->>AS: update_indicator(user_id, ind_id, data)
    AS->>DB: GET old indicator
    AS->>DB: UPDATE clinical_indicators
    AS->>DB: INSERT audit_logs
    DB-->>AS: updated
    AS-->>Admin: Updated Indicator

    Admin->>AS: list_indicators(body_system_id?)
    AS->>DB: SELECT clinical_indicators
    DB-->>AS: indicators[]
    AS-->>Admin: indicators list

    Note over Admin,DB: EVIDENCE
    Admin->>AS: create_evidence(user_id, data)
    AS->>DB: INSERT evidence_references
    AS->>DB: INSERT audit_logs
    DB-->>AS: created
    AS-->>Admin: EvidenceReference

    Note over Admin,DB: RECOMMENDATIONS
    Admin->>AS: create_recommendation(user_id, data)
    AS->>DB: INSERT recommendations
    AS->>DB: INSERT audit_logs
    DB-->>AS: created
    AS-->>Admin: Recommendation

    Admin->>AS: update_recommendation(user_id, rec_id, data)
    AS->>DB: GET old recommendation
    AS->>DB: UPDATE recommendations
    AS->>DB: INSERT audit_logs
    DB-->>AS: updated
    AS-->>Admin: Updated Recommendation

    Note over Admin,DB: AUDIT LOGS
    Admin->>AS: list_audit_logs(entity_type?, limit=100)
    AS->>DB: SELECT audit_logs (filtered + ordered)
    DB-->>AS: logs[]
    AS-->>Admin: audit trail entries
```

---

## 8. Full Scoring & Recommendation Pipeline

```mermaid
sequenceDiagram
    participant QE as QuestionnaireEngine
    participant SE as ScoringEngine
    participant CDS as ClinicalDecisionService
    participant RS as ReportService
    participant DB as Database

    Note over QE,RS: Score calculation during questionnaire

    QE->>SE: register_weight(code, value, label, severity)
    SE-->>QE: weight registered

    QE->>SE: calculate_group_score(answers[], scoring_weights)
    SE->>SE: For each answer: weighted_score = score * weight
    SE->>SE: total_score = sum(weighted_scores)
    SE->>SE: max_possible = sum(weights)
    SE->>SE: percentage = total / max * 100
    SE-->>QE: { total_score, max_possible, percentage, answer_details }

    QE->>SE: calculate_body_system_score(group_scores, system_weight)
    SE->>SE: total = sum(group_scores * system_weight)
    SE->>SE: Determine severity (critical/severe/moderate/mild/none)
    SE-->>QE: { total_score, max_possible, percentage, severity, group_scores }

    QE->>SE: calculate_overall_score(system_scores)
    SE->>SE: Aggregate all system scores
    SE->>SE: Determine overall severity
    SE-->>QE: { overall_score, overall_percentage, overall_severity, system_details }

    Note over QE,RS: Clinical decision processing

    CDS->>CDS: Process assessment answers
    CDS->>CDS: Aggregate indicator_scores from question & option indicators
    CDS->>CDS: Filter activated (score >= 1.0)
    CDS->>CDS: Aggregate condition_scores from indicator mapping
    CDS->>CDS: Normalize confidence per condition (0-1)
    CDS->>CDS: Compute overall_confidence (mean of condition confidences)
    CDS->>DB: Persist AssessmentResult + trace explanations

    Note over QE,RS: Report generation

    RS->>RS: Aggregate body_system scores from activated_indicators
    RS->>RS: Map scores to severity thresholds
    RS->>RS: Assign category labels (Normal / Monitor / Needs Attention / etc.)
    RS->>RS: Build condition assessments with confidence labels
    RS->>RS: Map recommendations to advice text
    RS-->>RS: { report_id, summary with counts }
```
