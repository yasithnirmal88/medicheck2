# Entity-Relationship Diagrams — Medicheck

> All entities use UUID primary keys (`id: String(32)`) and inherit `created_at`, `updated_at`, `deleted_at` timestamps from `BaseModel`. Soft-delete is used throughout.

---

## 1. Core Clinical Entities

```mermaid
erDiagram
    body_systems {
        string id PK
        string code UK
        string name
        text description
        string icon
        string color_hex
        int display_order
        float scoring_weight
        bool is_active
        bool is_core
        json metadata
    }

    question_groups {
        string id PK
        string body_system_id FK
        string code UK
        string name
        text description
        int display_order
        bool is_active
        json metadata
    }

    questions {
        string id PK
        string body_system_id FK
        string question_group_id FK
        string code UK
        string question_type
        text text
        text description
        string tooltip
        text medical_notes
        int order_index
        int priority
        string difficulty
        string status
        bool is_required
        json validation_rules
        float scoring_weight
        int version
    }

    question_options {
        string id PK
        string question_id FK
        string code
        string text
        string value
        float score_value
        string severity
        string color_hex
        text recommendation_trigger
        text follow_up_trigger
        text medical_notes
        int display_order
        bool is_active
    }

    question_dependencies {
        string id PK
        string question_id FK
        string depends_on_question_id FK
        string condition_type
        json condition_value
        string logic_operator
        int group_id
    }

    assessment_sessions {
        string id PK
        string user_id FK
        string questionnaire_template_id
        string questionnaire_version_id
        string status
        string current_question_id
        string current_group_id
        int answers_count
        int total_questions
        int completed_questions
        datetime started_at
        datetime paused_at
        datetime completed_at
        datetime expires_at
        json metadata
    }

    assessment_answers {
        string id PK
        string session_id FK
        string question_id FK
        int question_version
        string question_code
        string option_id
        string value
        float numeric_value
        json response_value
        float score_value
        bool is_skipped
        int time_taken_seconds
        json branch_path
        datetime recorded_at
    }

    assessment_progress {
        string id PK
        string session_id FK
        string current_section
        int completed_questions
        int total_questions
        int answered_questions
        int skipped_questions
        int estimated_time_remaining
        float completion_percentage
    }

    body_systems ||--o{ question_groups : "has"
    body_systems ||--o{ questions : "groups"
    question_groups ||--o{ questions : "contains"
    questions ||--o{ question_options : "has options"
    questions ||--o{ question_dependencies : "depends on"
    questions ||--o{ assessment_answers : "answered by"
    assessment_sessions ||--o{ assessment_answers : "contains"
    assessment_sessions ||--o| assessment_progress : "tracks"
    users ||--o{ assessment_sessions : "completes"
```

---

## 2. Knowledge Graph Entities

```mermaid
erDiagram
    clinical_indicators {
        string id PK
        string body_system_id FK
        string key UK
        string name
        text description
        string severity
        string evidence_strength
        float confidence
        float positive_weight
        float negative_weight
        float neutral_weight
        json related_disease_ids
        json related_symptom_ids
        int order
        bool is_active
        int version
        string status
    }

    possible_conditions {
        string id PK
        string code
        string name
        text description
        string body_system_id
        string severity
        string status
        string icd10
        text notes
    }

    recommendations {
        string id PK
        string key UK
        string body_system_id
        string disease_id
        string category
        string title
        text text
        int order
        int priority
        string urgency
        string evidence_level
        bool is_active
        int version
        string status
    }

    laboratory_tests {
        string id PK
        string code UK
        string name
        text description
        string body_system_id
        string loinc_code
        string normal_range
        string unit
        float reference_range_min
        float reference_range_max
        float critical_low
        float critical_high
        bool is_active
        int version
        string status
    }

    evidence_references {
        string id PK
        string question_id
        string title
        string url
        string source
        string evidence_level
        text summary
    }

    knowledge_graphs {
        string id PK
        string name
        text description
        string body_system_id
        bool is_active
        int version
        string status
    }

    knowledge_graph_nodes {
        string id PK
        string graph_id FK
        string entity_type
        string entity_id
        string label
        float x_position
        float y_position
        string color
        json metadata
    }

    knowledge_graph_edges {
        string id PK
        string graph_id FK
        string source_node_id
        string target_node_id
        string relationship_type
        string label
        float weight
        json metadata
    }

    body_systems ||--o{ clinical_indicators : "categorizes"
    body_systems ||--o{ possible_conditions : "associated_with"
    body_systems ||--o{ recommendations : "targets"
    body_systems ||--o{ laboratory_tests : "belongs_to"
    body_systems ||--o{ knowledge_graphs : "visualizes"
    knowledge_graphs ||--o{ knowledge_graph_nodes : "contains"
    knowledge_graphs ||--o{ knowledge_graph_edges : "connects"
```

---

## 3. Link Tables (Many-to-Many Relationships)

```mermaid
erDiagram
    question_indicator_links {
        string id PK
        string question_id FK
        string indicator_id FK
        bool active
    }

    question_option_indicator_links {
        string id PK
        string question_option_id FK
        string indicator_id FK
        bool active
    }

    indicator_condition_links {
        string id PK
        string indicator_id FK
        string condition_id FK
        bool active
    }

    indicator_evidence_links {
        string id PK
        string indicator_id FK
        string evidence_id FK
        bool active
    }

    indicator_recommendation_links {
        string id PK
        string indicator_id FK
        string recommendation_id FK
        bool active
    }

    condition_recommendation_links {
        string id PK
        string condition_id FK
        string recommendation_id FK
        bool active
    }

    condition_laboratory_test_links {
        string id PK
        string condition_id FK
        string laboratory_test_id FK
        bool active
    }

    body_system_condition_links {
        string id PK
        string body_system_id FK
        string condition_id FK
        bool active
    }

    questions }o--|| question_indicator_links : "links to"
    clinical_indicators }o--|| question_indicator_links : "linked from"
    questions }o--|| question_option_indicator_links : "via option"
    question_options }o--|| question_option_indicator_links : "links indicator"
    clinical_indicators }o--|| question_option_indicator_links : "linked from option"
    clinical_indicators }o--|| indicator_condition_links : "maps to"
    possible_conditions }o--|| indicator_condition_links : "mapped from"
    clinical_indicators }o--|| indicator_evidence_links : "supported by"
    evidence_references }o--|| indicator_evidence_links : "supports"
    clinical_indicators }o--|| indicator_recommendation_links : "suggests"
    recommendations }o--|| indicator_recommendation_links : "suggested for"
    possible_conditions }o--|| condition_recommendation_links : "triggers"
    recommendations }o--|| condition_recommendation_links : "triggered by"
    possible_conditions }o--|| condition_laboratory_test_links : "requires"
    laboratory_tests }o--|| condition_laboratory_test_links : "required for"
    body_systems }o--|| body_system_condition_links : "related to"
    possible_conditions }o--|| body_system_condition_links : "related from"
```

---

## 4. User / Profile Entities

```mermaid
erDiagram
    users {
        string id PK
        string firebase_uid UK
        string email UK
        string full_name
        text avatar_url
        bool email_verified
        bool is_active
        datetime last_login_at
    }

    roles {
        string id PK
        string code UK
        json name
        text description
        bool is_system
        int priority
    }

    user_roles {
        string user_id FK
        string role_id FK
    }

    health_profiles {
        string id PK
        string user_id FK
        bool draft
        json metadata
    }

    personal_info {
        string id PK
        string profile_id FK
    }

    medical_histories {
        string id PK
        string profile_id FK
        string condition
        date diagnosis_date
        string severity
        string status
        string treating_doctor
        text notes
    }

    medication_histories {
        string id PK
        string profile_id FK
    }

    surgical_histories {
        string id PK
        string profile_id FK
    }

    family_histories {
        string id PK
        string profile_id FK
    }

    allergies {
        string id PK
        string profile_id FK
    }

    immunizations {
        string id PK
        string profile_id FK
    }

    measurements {
        string id PK
        string profile_id FK
    }

    lab_reports {
        string id PK
        string profile_id FK
    }

    lifestyles {
        string id PK
        string profile_id FK
    }

    nutrition {
        string id PK
        string profile_id FK
    }

    users ||--o{ health_profiles : "has"
    health_profiles ||--o| personal_info : "contains"
    health_profiles ||--o| lifestyles : "contains"
    health_profiles ||--o| nutrition : "contains"
    health_profiles ||--o{ medical_histories : "contains"
    health_profiles ||--o{ medication_histories : "contains"
    health_profiles ||--o{ surgical_histories : "contains"
    health_profiles ||--o{ family_histories : "contains"
    health_profiles ||--o{ allergies : "contains"
    health_profiles ||--o{ immunizations : "contains"
    health_profiles ||--o{ measurements : "contains"
    health_profiles ||--o{ lab_reports : "contains"
    users }o--o{ roles : "assigned via"
    user_roles }o--|| users : "links"
    user_roles }o--|| roles : "links"
```

---

## 5. Scoring & Decision Entities

```mermaid
erDiagram
    scoring_profiles {
        string id PK
        string body_system_id FK
        string code UK
        string name
        text description
        json weights
        json thresholds
        string formula
        bool is_active
        int version
        string status
    }

    decision_rules {
        string id PK
        string body_system_id FK
        string code UK
        string name
        text description
        string rule_type
        json condition_expression
        json action_expression
        int priority
        bool is_active
        int version
        string status
    }

    risk_categories {
        string id PK
        string body_system_id FK
        string code UK
        string name
        text description
        float min_probability
        float max_probability
        string color_hex
        text action_required
        bool is_active
        int version
        string status
    }

    severity_thresholds {
        string id PK
        string body_system_id FK
        string scoring_profile_id FK
        string name
        string severity
        float min_score
        float max_score
        string color_hex
        string label
        text recommendation
        bool is_active
        int version
        string status
    }

    assessment_results {
        string id PK
        string session_id FK
        string user_id FK
        text summary
        float confidence_score
        datetime created_at
    }

    activated_indicators {
        string id PK
        string result_id FK
        string indicator_id FK
        float score
        int evidence_count
        text notes
    }

    activated_conditions {
        string id PK
        string result_id FK
        string condition_id FK
        float score
        float confidence
        text notes
    }

    generated_recommendations {
        string id PK
        string result_id FK
        string recommendation_id FK
        string source
        text notes
    }

    generated_laboratory_tests {
        string id PK
        string result_id FK
        string laboratory_test_id FK
        text reason
    }

    generated_screenings {
        string id PK
        string result_id FK
        string name
        text reason
    }

    explanation_records {
        string id PK
        string result_id FK
        string source_type
        string source_id
        text text
    }

    assessment_results ||--o{ activated_indicators : "contains"
    assessment_results ||--o{ activated_conditions : "contains"
    assessment_results ||--o{ generated_recommendations : "contains"
    assessment_results ||--o{ generated_laboratory_tests : "contains"
    assessment_results ||--o{ generated_screenings : "contains"
    assessment_results ||--o{ explanation_records : "traces"
    body_systems ||--o{ scoring_profiles : "scored by"
    body_systems ||--o{ decision_rules : "evaluated by"
    body_systems ||--o{ risk_categories : "classified by"
    body_systems ||--o{ severity_thresholds : "thresholds for"
    assessment_sessions ||--o| assessment_results : "produces"
```

---

## 6. CMS / Admin Entities

```mermaid
erDiagram
    change_requests {
        string id PK
        string entity_type
        string entity_id
        string requested_by
        string title
        text description
        json changes
        text reason
        string status
        bool is_active
        int version
        datetime resolved_at
        string resolved_by
    }

    approvals {
        string id PK
        string entity_type
        string entity_id
        string requested_by
        string assigned_to
        string role_required
        string status
        json comments
        datetime decided_at
        bool is_active
        int version
    }

    reviews {
        string id PK
        string entity_type
        string entity_id
        string reviewer_id
        string review_type
        string status
        string decision
        text comments
        int score
        bool is_active
        int version
        datetime completed_at
    }

    version_snapshots {
        string id PK
        string entity_type
        string entity_id
        int version
        json snapshot
        string snapshot_type
        text reason
        string created_by
    }

    publishing_jobs {
        string id PK
        string entity_type
        string entity_id
        int version
        string requested_by
        string approved_by
        string status
        datetime schedule_at
        datetime published_at
        int rollback_version
        text notes
        bool is_active
    }

    workflows {
        string id PK
        string name
        text description
        string entity_type
        json steps
        int current_step
        string status
        bool is_active
        int version
    }

    audit_logs {
        string id PK
        string actor_id
        string actor_role
        string entity_type
        string entity_id
        string action
        datetime changed_at
        text old_value
        text new_value
        text reason
        string ip_address
        string user_agent
        string session_id
        string request_id
        int status_code
        string method
        string path
    }

    questionnaire_templates {
        string id PK
        string code UK
        string name
        text description
        string body_system_id
        string target_audience
        int estimated_time_minutes
        bool is_active
        bool is_template
        int version
        json metadata
    }

    questionnaire_versions {
        string id PK
        string questionnaire_template_id FK
        int version
        json snapshot
        string change_notes
        string created_by
    }

    change_requests }o--|| approvals : "requires"
    approvals }o--|| reviews : "may include"
    approvals }o--|| publishing_jobs : "triggers"
    publishing_jobs }o--|| version_snapshots : "creates"
    questionnaires ||--o{ questionnaire_versions : "versioned as"
```
