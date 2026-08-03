# MediCheck API Reference

**Base URL:** `/api/v1`  
**Authentication:** Bearer JWT (Firebase ID token) — pass as `Authorization: Bearer <token>` header.  
**Content-Type:** `application/json`

---

## Error Response Format

All errors return:
```json
{
  "success": false,
  "error": {
    "code": "string",
    "message": "string",
    "details": ["string", "..."]
  }
}
```

HTTP status codes: `400` Bad Request, `401` Unauthorized, `403` Forbidden, `404` Not Found, `422` Validation Error, `500` Internal Server Error.

---

## Pagination Format

List endpoints support `skip` (offset) and `limit` query params:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_previous": false
}
```

---

## Health

### `GET /health`

| Field | Value |
|---|---|
| Auth | None |
| Role | None |
| Description | Check API, database, and Redis health |

**Response:** `HealthResponse`
```json
{
  "status": "healthy|degraded",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-01-01T00:00:00Z",
  "db_status": "healthy|unhealthy",
  "redis_status": "healthy|unhealthy"
}
```

---

## Authentication (`/auth`)

### `POST /auth/register`

| Field | Value |
|---|---|
| Auth | No |
| Role | None |
| Description | Register a new user with Firebase ID token |

**Request Body:** `RegisterRequest`
```json
{
  "firebase_token": "string (min 10 chars)",
  "full_name": "string (1-200 chars)",
  "email": "user@example.com (optional)"
}
```

**Response (201):** `UserResponse`
```json
{
  "id": "32-char-hex",
  "firebase_uid": "string",
  "email": "user@example.com",
  "full_name": "string",
  "avatar_url": "string|null",
  "email_verified": false,
  "is_active": true,
  "last_login_at": "datetime|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `POST /auth/login`

| Field | Value |
|---|---|
| Auth | No |
| Role | None |
| Description | Login / get-or-create user, returns access token + user profile |

**Request Body:** `LoginRequest`
```json
{
  "firebase_token": "string (min 10 chars)"
}
```

**Response:** `TokenResponse`
```json
{
  "access_token": "string",
  "refresh_token": "string|null",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { "...UserResponse..." }
}
```

### `GET /auth/me`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get current authenticated user's profile |

**Response:** `UserResponse`

### `DELETE /auth/me`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Soft-delete (deactivate) current user's account |

**Response:** `204 No Content`

---

## Users (`/users`)

### `GET /users/me`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get current user's profile (alias) |

**Response:** `UserResponse`

### `PATCH /users/me`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Update own profile (full_name, avatar_url) |

**Query Params:** `full_name` (1-200), `avatar_url` (optional)  
**Response:** `UserResponse`

### `GET /users`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | List all users (paginated) |

**Query Params:** `skip` (default 0), `limit` (default 100, max 500)  
**Response:** `list[UserResponse]`

### `GET /users/count`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Count total users |

**Response:** `{"total": 42}`

---

## Health Profiles (`/profiles`)

### `GET /profiles/me`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get or create the authenticated user's health profile |

**Response:** `HealthProfileDTO`
```json
{
  "id": "string",
  "user_id": "string",
  "draft": true,
  "metadata": {},
  "personal_info": { "...PersonalInfoDTO..." },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `POST /profiles/me/personal`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Update personal info section |

**Request Body:** `PersonalInfoDTO`
```json
{
  "full_name": "string",
  "date_of_birth": "2024-01-01|null",
  "sex": "male|female|null",
  "height_cm": 175.0,
  "weight_kg": 70.0,
  "blood_group": "A+",
  "nationality": "string",
  "country": "string",
  "state": "string",
  "city": "string",
  "preferred_language": "en",
  "emergency_contact": {},
  "occupation": "string",
  "industry": "string",
  "education_level": "string",
  "marital_status": "single|married|null",
  "children_count": 0
}
```

**Response:** `HealthProfileDTO`

### `GET /profiles/me/versions`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List historical snapshot versions of the profile |

**Response:** `list[dict]` (snapshot objects)

### `GET /profiles/me/completion`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Compute profile completion percentage |

**Response:** `dict`

### `GET /profiles/me/versions/{version}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Preview a specific profile version snapshot |

**Path Params:** `version` (int > 0)  
**Response:** snapshot dict or `404`

### `POST /profiles/me/versions/{version}/restore`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Restore profile to a previous version |

**Path Params:** `version` (int > 0)  
**Response:** updated profile dict

### `POST /profiles/me/lifestyle`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Save lifestyle section data |

**Request Body:** `dict` (smoking, alcohol, exercise, sleep, etc.)  
**Response:** updated profile dict

### `POST /profiles/me/nutrition`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Save nutrition section data |

**Request Body:** `dict` (meals, fruit, vegetables, diet info, etc.)  
**Response:** updated profile dict

### `POST /profiles/me/medical`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Add a medical history record |

**Request Body:** `dict` (condition, diagnosis_date, severity, status, etc.)  
**Response:** updated profile dict

### `GET /profiles/me/medical`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List medical history records |

**Response:** `list[dict]`

### `POST /profiles/me/medications`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Add a medication history record |

### `GET /profiles/me/medications`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List medication history records |

### `POST /profiles/me/surgeries`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Add a surgical history record |

### `GET /profiles/me/surgeries`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List surgical history records |

### `POST /profiles/me/family`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Add a family history record |

### `GET /profiles/me/family`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List family history records |

### `POST /profiles/me/allergies`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Add an allergy record |

### `GET /profiles/me/allergies`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List allergy records |

### `POST /profiles/me/immunizations`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Add an immunization record |

### `GET /profiles/me/immunizations`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List immunization records |

### `POST /profiles/me/measurements`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Add a body measurement record (weight, BP, heart rate, etc.) |

### `GET /profiles/me/measurements`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List measurement records |

### `POST /profiles/me/lab-reports`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Add a lab report record |

### `GET /profiles/me/lab-reports`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List lab report records |

---

## Questionnaire (`/questionnaire`)

### `POST /questionnaire/start`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Start a new questionnaire assessment session |

**Request Body:** `{ "template_id": "optional-string" }`  
**Response:** session object (id, status, current_question, message)

### `GET /questionnaire/resume/{session_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Resume a previously started session |

**Response:** session state or `404`

### `POST /questionnaire/answer`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Save an answer for the current session |

**Request Body:**
```json
{
  "session_id": "string",
  "question_id": "string",
  "value": "answer-value",
  "option_id": "optional",
  "time_taken_seconds": 5,
  "is_skipped": false
}
```

**Response:** saved answer + next question

### `GET /questionnaire/next/{session_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get the next question in the session |

**Response:** `{ "next": { "...question..." } }`

### `GET /questionnaire/progress/{session_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get session progress |

**Response:** `SessionProgressResponse`

### `GET /questionnaire/search`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Search questions by keyword |

**Query Params:** `q` (search string)  
**Response:** `list[QuestionResponse]`

---

## Questionnaires (`/questionnaires`)

### `GET /questionnaires`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List available questionnaire templates, optionally filtered by audience |

**Query Params:** `audience` (optional)  
**Response:** `list[QuestionnaireTemplateResponse]`

### `GET /questionnaires/{id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get questionnaire template detail |

**Response:** `QuestionnaireTemplateResponse` or `404`

### `POST /questionnaires/{id}/start`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Start a questionnaire session from a template |

**Response:** `StartSessionResponse`
```json
{
  "session_id": "string",
  "status": "active",
  "current_question": { "...QuestionResponse..." },
  "message": "Session started successfully"
}
```

### `GET /questionnaires/sessions`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List user's past questionnaire sessions |

**Response:** `list[AssessmentSessionResponse]`

### `GET /questionnaires/sessions/{id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get a specific session state and progress |

**Response:** `AssessmentSessionResponse`

### `POST /questionnaires/sessions/{id}/answer`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Save an answer in a session |

**Request Body:** `SaveAnswerRequest`
```json
{
  "question_id": "string",
  "response_value": {},
  "time_taken_seconds": 0,
  "is_skipped": false
}
```

**Response:** `SaveAnswerResponse`
```json
{
  "answer": { "...AnswerResponse..." },
  "next_question": { "...QuestionResponse..." }
}
```

### `POST /questionnaires/sessions/{id}/pause`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Pause an in-progress session |

**Response:** `SubmitSessionResponse`

### `POST /questionnaires/sessions/{id}/resume`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Resume a paused session |

**Response:** `SubmitSessionResponse`

### `POST /questionnaires/sessions/{id}/complete`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Complete a session and trigger downstream processing |

**Response:** `SubmitSessionResponse`

### `GET /questionnaires/sessions/{id}/progress`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get detailed session progress |

**Response:** `SessionProgressResponse`
```json
{
  "session_id": "string",
  "current_section": "string|null",
  "completed_questions": 0,
  "total_questions": 10,
  "answered_questions": 7,
  "skipped_questions": 0,
  "estimated_time_remaining": 120,
  "completion_percentage": 70.0
}
```

---

## Questions (`/questions`)

### `GET /questions`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List questions, optionally filtered by body_system or group |

**Query Params:** `body_system` (optional), `group` (optional)  
**Response:** `list[QuestionResponse]`

### `GET /questions/{id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get question detail with options |

**Response:** `QuestionResponse` or `404`

### `GET /questions/by-body-system/{code}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get questions by body system code |

**Response:** `list[QuestionResponse]`

### `GET /questions/search`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Search questions by text query |

**Query Params:** `q` (search string)  
**Response:** `list[QuestionResponse]`

---

## Assessments (`/assessments`)

### `GET /assessments/sessions/{id}/result`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get the full assessment session data (questions, answers, state) |

**Response:** session dict

---

## Clinical Decision Support Engine (`/assessment`)

### `POST /assessment/process`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Process a completed session through the CDSE (scoring, conditions, recommendations) |

**Request Body:** `{ "session_id": "string" }`  
**Response:** assessment result dict

### `GET /assessment/results/{session_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get CDSE result by session ID |

**Response:** assessment result or `404`

### `GET /assessment/result/{result_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get CDSE result by result ID |

**Response:** assessment result or `404`

### `GET /assessment/{session_id}/explanation`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get explanations for the assessment result |

**Response:** `list[ExplanationRecordModel]`

### `GET /assessment/{session_id}/recommendations`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get generated recommendations for the session |

**Response:** `list[GeneratedRecommendationModel]`

### `GET /assessment/{session_id}/laboratory-tests`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get generated laboratory test suggestions |

**Response:** `list[GeneratedLaboratoryTestModel]`

### `GET /assessment/{session_id}/screenings`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get generated screening suggestions |

**Response:** `list[GeneratedScreeningModel]`

---

## Reports (`/report`)

### `POST /report/generate`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Generate a health report from a completed assessment session |

**Request Body:** `{ "session_id": "string" }`  
**Response:** report dict

### `GET /report/{session_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get report by session ID |

**Response:** report dict or `404`

### `GET /report/id/{report_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get report by report ID |

**Response:** report dict or `404`

### `GET /report/`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | List reports for current user |

**Query Params:** `limit` (default 100), `offset` (default 0)  
**Response:** list of report dicts

### `GET /report/compare/{id1}/{id2}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Compare two reports side-by-side |

**Response:** comparison dict or `404`

---

## Knowledge Graph (`/graph`)

### `POST /graph/question-indicators`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Link a question to a clinical indicator |

**Request Body:** `{ "question_id": "string", "indicator_id": "string" }`

### `POST /graph/question-option-indicators`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Link a question option to a clinical indicator |

### `POST /graph/indicator-conditions`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Link an indicator to a condition |

### `POST /graph/indicator-evidence`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Link an indicator to medical evidence |

### `POST /graph/indicator-recommendations`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Link an indicator to a recommendation |

### `POST /graph/condition-recommendations`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Link a condition to a recommendation |

### `POST /graph/condition-laboratory-tests`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Link a condition to a laboratory test |

### `POST /graph/body-system-conditions`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Link a body system to a condition |

### `GET /graph/question/{question_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Build knowledge graph from a question |

### `GET /graph/indicator/{indicator_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get conditions and evidence for an indicator |

### `GET /graph/condition/{condition_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | Any authenticated |
| Description | Get recommendations and lab tests for a condition |

### `POST /graph/conditions`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Create a new condition in the knowledge graph |

### `POST /graph/laboratory-tests`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Create a new laboratory test entry |

---

## Admin (`/admin`)

### `POST /admin/body-systems`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Create a body system |

### `GET /admin/body-systems`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | List all body systems |

### `POST /admin/indicators`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Create a clinical indicator |

### `GET /admin/indicators`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | List clinical indicators, optionally filtered by body_system_id |

### `POST /admin/evidence`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Create a medical evidence entry |

### `GET /admin/evidence`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | List medical evidence (limit param) |

### `POST /admin/recommendations`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | Create a recommendation |

### `GET /admin/recommendations`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | List recommendations (limit param) |

### `GET /admin/audit`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` |
| Description | View audit logs, optionally filtered by entity_type |

---

## CMS Questions & Templates (`/cms`)

### `GET /cms/questions`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | List all active questions with options |

### `POST /cms/questions`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Create a new question |

**Request Body:**
```json
{
  "body_system_id": "string",
  "question_group_id": "string",
  "code": "string",
  "question_type": "free_text|single_choice|multiple_choice|scale|boolean",
  "text": "string",
  "description": "string",
  "tooltip": "string",
  "medical_notes": "string",
  "evidence_ref": "string",
  "order_index": 0,
  "priority": 3,
  "difficulty": "basic|intermediate|advanced",
  "status": "active|inactive|draft|archived",
  "is_required": false,
  "validation_rules": {},
  "scoring_weight": 1.0
}
```

### `PUT /cms/questions/{id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Update an existing question |

### `DELETE /cms/questions/{id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Soft-delete (deactivate) a question |

### `GET /cms/questions/{id}/versions`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | List version history for a question |

### `POST /cms/questions/{id}/versions`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Create a new version snapshot |

### `POST /cms/questions/{id}/options`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Add an option to a question |

**Request Body:**
```json
{
  "code": "string",
  "text": "string",
  "value": "string",
  "score_value": 0.0,
  "severity": "none|mild|moderate|severe",
  "color_hex": "#FF0000",
  "recommendation_trigger": "string",
  "follow_up_trigger": "string",
  "display_order": 0,
  "is_active": true
}
```

### `PUT /cms/questions/{id}/options/{opt_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Update a question option |

### `DELETE /cms/questions/{id}/options/{opt_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Deactivate a question option |

### `POST /cms/questions/{id}/dependencies`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Add a dependency rule to a question |

### `DELETE /cms/questions/{id}/dependencies/{dep_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Remove a dependency rule |

### `GET /cms/body-systems`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | List all active body systems |

### `PUT /cms/body-systems/{code}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Update a body system |

### `GET /cms/question-groups`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | List question groups, optionally filtered by body_system_id |

### `POST /cms/question-groups`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Create a question group |

### `PUT /cms/question-groups/{id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Update a question group |

### `GET /cms/templates`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | List all active questionnaire templates |

### `POST /cms/templates`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Create a questionnaire template |

### `PUT /cms/templates/{id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | `admin` / CMS user |
| Description | Update a questionnaire template |

---

## CMS Content Management (`/cms/content`)

### `GET /cms/content/{entity_type}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (RBAC) |
| Description | List entities of a given type with filtering/sorting/pagination |

**Path Params:** `entity_type` — one of: disease, clinical_indicator, symptom, laboratory_test, imaging_test, medical_evidence, recommendation, lifestyle_advice, exercise_program, nutrition_advice, clinical_guideline, medication_recommendation, approval, workflow, decision_rule, questionnaire_rule_set, scoring_profile, severity_threshold, risk_category, medical_specialty, medical_tag, reference_source, research_paper, clinical_trial, medical_organization, evidence_collection, disease_category, body_system_category, recommendation_category, question_category, question_tag, lab_panel, biomarker, rule_library, template_library, change_request, notification

**Query Params:** `body_system_id`, `status`, `search`, `skip`, `limit`

**Response:** `list[CMSEntityResponse]`

### `GET /cms/content/{entity_type}/{entity_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (RBAC) |
| Description | Get a single entity |

### `POST /cms/content/{entity_type}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (RBAC) |
| Description | Create a new entity |

### `PUT /cms/content/{entity_type}/{entity_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (RBAC) |
| Description | Update an entity |

### `DELETE /cms/content/{entity_type}/{entity_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (RBAC) |
| Description | Soft-delete an entity |

### `PUT /cms/content/{entity_type}/{entity_id}/status`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (CMS_WRITE_PUBLISH) |
| Description | Update the publication status of an entity |

### `GET /cms/content/{entity_type}/count`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Count entities of a given type, optionally by status |

### `POST /cms/content/{entity_type}/bulk/status`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (CMS_WRITE_PUBLISH) |
| Description | Bulk update status of multiple entities |

### `POST /cms/content/{entity_type}/bulk/delete`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (RBAC write) |
| Description | Bulk soft-delete entities |

---

## CMS Questionnaire Builder (`/cms/builder`)

### `PUT /cms/builder/groups/reorder`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (CMS_WRITE_QUESTION) |
| Description | Reorder question groups |

### `PUT /cms/builder/groups/{group_id}/move`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (CMS_WRITE_QUESTION) |
| Description | Move a group under a parent group |

### `POST /cms/builder/questions/{question_id}/clone`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (CMS_WRITE_QUESTION) |
| Description | Clone a question with all its options |

### `POST /cms/builder/dependencies`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (CMS_WRITE_QUESTION) |
| Description | Create a conditional dependency between questions |

### `DELETE /cms/builder/dependencies/{dependency_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (CMS_WRITE_QUESTION) |
| Description | Remove a dependency |

### `GET /cms/builder/questions/{question_id}/dependencies`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get all dependencies for a question |

### `POST /cms/builder/branch-rules/{body_system_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (CMS_WRITE_QUESTION) |
| Description | Set branch rules for a body system |

### `GET /cms/builder/branch-rules/{body_system_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get branch rules for a body system |

### `POST /cms/builder/simulate/{template_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Simulate a questionnaire with test answers |

### `POST /cms/builder/versions/{questionnaire_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (CMS_WRITE_QUESTION) |
| Description | Create a version snapshot of a questionnaire |

### `GET /cms/builder/versions/{questionnaire_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get version history for a questionnaire |

### `POST /cms/builder/versions/{questionnaire_id}/restore/{version}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user (CMS_WRITE_QUESTION) |
| Description | Restore a questionnaire to a previous version |

---

## CMS Rule Engine (`/cms/rules`)

### `POST /cms/rules/evaluate`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Evaluate a single rule against a context |

### `POST /cms/rules/evaluate/batch`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Evaluate a set of rules (ALL/ANY logic) |

### `POST /cms/rules/simulate`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Simulate rule evaluation with verbose output |

### `POST /cms/rules/validate`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Validate an expression syntactically and semantically |

### `POST /cms/rules/compute`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Compute a variable value from context |

### `POST /cms/rules/detect-conflicts`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Detect conflicts and circular dependencies in rules |

---

## CMS Knowledge Graph Editor (`/cms/knowledge-graph`)

### `GET /cms/knowledge-graph/graphs`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | List knowledge graphs, optionally filtered by body_system_id |

### `POST /cms/knowledge-graph/graphs`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Create a new knowledge graph |

### `GET /cms/knowledge-graph/graphs/{graph_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get a knowledge graph with nodes and edges |

### `PUT /cms/knowledge-graph/graphs/{graph_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Update a knowledge graph |

### `DELETE /cms/knowledge-graph/graphs/{graph_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Delete a knowledge graph |

### `POST /cms/knowledge-graph/graphs/{graph_id}/nodes`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Add a node to a graph |

### `PUT /cms/knowledge-graph/graphs/nodes/{node_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Update a graph node |

### `DELETE /cms/knowledge-graph/graphs/nodes/{node_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Remove a node from a graph |

### `POST /cms/knowledge-graph/graphs/{graph_id}/edges`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Add an edge (relationship) between two nodes |

### `DELETE /cms/knowledge-graph/graphs/edges/{edge_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Remove an edge |

### `POST /cms/knowledge-graph/graphs/{graph_id}/validate`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Validate the graph structure |

### `GET /cms/knowledge-graph/impact/{entity_type}/{entity_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Analyze the impact of changing an entity across the graph |

### `GET /cms/knowledge-graph/search`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Search entities across the knowledge graph |

### `POST /cms/knowledge-graph/bulk-link`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Bulk link entities with a relationship type |

---

## CMS Publishing Workflow (`/cms/publishing`)

### `GET /cms/publishing/workflows`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | List publishing workflows |

### `POST /cms/publishing/workflows`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Create a publishing workflow |

### `GET /cms/publishing/workflows/{workflow_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get a workflow |

### `PUT /cms/publishing/workflows/{workflow_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Update a workflow |

### `GET /cms/publishing/jobs`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | List publishing jobs, filterable by status and entity_type |

### `POST /cms/publishing/jobs`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Create a publishing job |

### `GET /cms/publishing/jobs/{job_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get a publishing job |

### `POST /cms/publishing/jobs/{job_id}/approve`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Approve a publishing job |

### `POST /cms/publishing/jobs/{job_id}/publish`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Execute publishing of a job |

### `POST /cms/publishing/jobs/{job_id}/fail`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Mark a job as failed |

### `POST /cms/publishing/jobs/{job_id}/rollback`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Rollback a published job to a previous version |

### `POST /cms/publishing/jobs/process-scheduled`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Process all scheduled publishing jobs |

### `GET /cms/publishing/approvals`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | List approval requests |

### `POST /cms/publishing/approvals`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Create an approval request |

### `POST /cms/publishing/approvals/{approval_id}/approve`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Approve an entity |

### `POST /cms/publishing/approvals/{approval_id}/reject`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Reject an approval request |

### `POST /cms/publishing/approvals/{approval_id}/comment`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Add a comment to an approval |

### `GET /cms/publishing/reviews`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | List reviews |

### `POST /cms/publishing/reviews`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Create a review |

### `POST /cms/publishing/reviews/{review_id}/complete`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Complete a review with decision and score |

### `GET /cms/publishing/change-requests`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | List change requests |

### `POST /cms/publishing/change-requests`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Create a change request |

### `POST /cms/publishing/change-requests/{cr_id}/approve`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Approve a change request |

### `POST /cms/publishing/change-requests/{cr_id}/reject`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Reject a change request |

### `GET /cms/publishing/change-requests/conflicts`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Detect conflicts for an entity |

### `GET /cms/publishing/snapshots`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | List version snapshots for an entity |

### `POST /cms/publishing/snapshots`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Create a version snapshot |

---

## CMS Clinical Evidence (`/cms/evidence`)

### `GET /cms/evidence`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | List all evidence references |

### `POST /cms/evidence`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Add an evidence reference |

**Request Body:**
```json
{
  "title": "string",
  "citation": "string",
  "pmid": "optional",
  "doi": "optional",
  "evidence_level": "Level I",
  "confidence_score": 0.90,
  "summary": "optional"
}
```

### `GET /cms/evidence/pubmed/lookup`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Fetch metadata from PubMed by PMID |

**Query Params:** `pmid` (required)

### `GET /cms/evidence/doi/lookup`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Fetch metadata from DOI |

**Query Params:** `doi` (required)

---

## CMS Audit & Compliance (`/cms/audit`)

### `GET /cms/audit/logs`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Search audit logs with filters |

**Query Params:** `actor_id`, `entity_type`, `entity_id`, `action`, `query`, `skip`, `limit`

### `GET /cms/audit/timeline/{entity_type}/{entity_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get an audit timeline for a specific entity |

### `GET /cms/audit/diffs/{entity_type}/{entity_id}`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get field-level diffs for all changes to an entity |

### `GET /cms/audit/export`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Export audit logs as JSON or CSV |

### `GET /cms/audit/stats`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get audit statistics for the last N days |

---

## CMS Dashboard (`/cms/dashboard`)

### `GET /cms/dashboard/overview`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get CMS overview statistics |

### `GET /cms/dashboard/recent-activity`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get recent CMS activity |

### `GET /cms/dashboard/workflow-summary`

| Field | Value |
|---|---|
| Auth | Yes |
| Role | CMS user |
| Description | Get workflow status summary |
