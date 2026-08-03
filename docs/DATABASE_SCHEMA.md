# MediCheck Database Schema

**Database:** PostgreSQL (with asyncpg) / SQLite (dev)  
**ORM:** SQLAlchemy 2.0 (async)  
**Naming Convention:**

| Prefix | Pattern | Example |
|--------|---------|---------|
| PK | `pk_%(table_name)s` | `pk_users` |
| FK | `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s` | `fk_health_profiles_user_id_users` |
| IX | `ix_%(column_0_label)s` | `ix_users_email` |
| UQ | `uq_%(table_name)s_%(column_0_name)s` | `uq_users_email` |
| CK | `ck_%(table_name)s_%(constraint_name)s` | `ck_users_chk_1` |

**Default Table Name:** Class name lowercased + plural `s` (e.g. `UserModel` → `users`)

---

## Base Model Columns (inherited by ALL tables)

Every table inherits from `BaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin)`:

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `String(32)` | PK, default=`uuid.uuid4().hex` | 32-char hex UUID (no hyphens) |
| `created_at` | `DateTime(timezone=True)` | NOT NULL, server_default=func.now() | Auto-set on insert |
| `updated_at` | `DateTime(timezone=True)` | NOT NULL, server_default=func.now(), onupdate=func.now() | Auto-updated |
| `deleted_at` | `DateTime(timezone=True)` | NULLABLE, default=NULL | Soft delete marker |

---

## Conventions

- **IDs:** 32-char hex UUID strings (`uuid.uuid4().hex`)
- **Timestamps:** Timezone-aware `DateTime(timezone=True)`
- **Soft delete:** All tables have `deleted_at` column; queries filter `WHERE deleted_at IS NULL`
- **JSON columns:** Named `metadata` (aliased as `extra_metadata` or `profile_metadata` in models) or explicitly named
- **FK column naming:** `<target_table_singular>_id`, e.g. `user_id`, `profile_id`
- **Indexes:** FK columns and frequently-queried columns are indexed
- **Status fields:** Many content entities use `String(20)` status fields (`draft`, `active`, `inactive`, `archived`, `pending`, `published`)
- **Versioning:** Content entities include an `Integer` `version` column defaulting to 1
- **Audit fields:** Many tables include `created_by` and `updated_by` (`String(32)`, nullable)

---

## Functional Area 1: Users & Roles

### `users`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| (inherited base columns) | | | id, created_at, updated_at, deleted_at |
| `firebase_uid` | `String(128)` | UNIQUE, NOT NULL | Firebase Auth UID |
| `email` | `String(255)` | UNIQUE, NOT NULL | User email |
| `full_name` | `String(255)` | NOT NULL | Display name |
| `avatar_url` | `Text` | NULLABLE | Profile picture URL |
| `email_verified` | `Boolean` | NOT NULL, default=false | Email verification flag |
| `is_active` | `Boolean` | NOT NULL, default=true | Account active flag |
| `last_login_at` | `DateTime(tz)` | NULLABLE | Last login timestamp |

**Indexes:** `ix_users_firebase_uid`, `ix_users_email`, `ix_users_is_active`  
**Relationships:** `roles` M2M via `user_roles`

### `roles`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| (inherited base columns) | | | |
| `code` | `String(50)` | UNIQUE, NOT NULL, INDEX | `patient`, `doctor`, `researcher`, `administrator` |
| `name` | `JSON` | NOT NULL, default={} | Multi-language name dict |
| `description` | `Text` | NOT NULL, default="" | Role description |
| `is_system` | `Boolean` | NOT NULL, default=false | System-protected role |
| `priority` | `Integer` | NOT NULL, default=0 | Sorting priority |

**Relationships:** `users` M2M via `user_roles`

### `user_roles` (junction table)

| Column | Type | Constraints |
|--------|------|-------------|
| `user_id` | `String(32)` | PK, FK → `users.id` ON DELETE CASCADE |
| `role_id` | `String(32)` | PK, FK → `roles.id` ON DELETE CASCADE |

---

## Functional Area 2: Health Profile

### `health_profiles`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| (inherited base columns) | | | |
| `user_id` | `String(32)` | FK → `users.id`, NOT NULL | Owner |
| `draft` | `Boolean` | NOT NULL, default=true | Draft/published flag |
| `metadata` | `JSON` | NULLABLE | Profile metadata |

**Indexes:** `ix_health_profiles_user_id`  
**Relationships:** `personal_info` (1:1), `lifestyle` (1:1), `nutrition` (1:1), `medical_histories` (1:M), `medication_histories` (1:M), `surgical_histories` (1:M), `family_histories` (1:M), `allergies` (1:M), `immunizations` (1:M), `measurements` (1:M), `lab_reports` (1:M)

### `personal_infos`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `full_name` | `String(255)` | NOT NULL |
| `date_of_birth` | `Date` | NULLABLE |
| `sex` | `String(16)` | NULLABLE |
| `height_cm` | `Float` | NULLABLE |
| `weight_kg` | `Float` | NULLABLE |
| `blood_group` | `String(10)` | NULLABLE |
| `nationality` | `String(100)` | NULLABLE |
| `country` | `String(100)` | NULLABLE |
| `state` | `String(100)` | NULLABLE |
| `city` | `String(100)` | NULLABLE |
| `preferred_language` | `String(50)` | NULLABLE |
| `emergency_contact` | `Text` | NULLABLE |
| `occupation` | `String(150)` | NULLABLE |
| `industry` | `String(150)` | NULLABLE |
| `education_level` | `String(100)` | NULLABLE |
| `marital_status` | `String(50)` | NULLABLE |
| `children_count` | `Integer` | NULLABLE |

### `lifestyles`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `smoking` | `String(50)` | NULLABLE |
| `alcohol` | `String(50)` | NULLABLE |
| `water_intake_l_per_day` | `Integer` | NULLABLE |
| `daily_walking_minutes` | `Integer` | NULLABLE |
| `avg_daily_steps` | `Integer` | NULLABLE |
| `exercise_frequency` | `String(50)` | NULLABLE |
| `exercise_type` | `String(100)` | NULLABLE |
| `sleep_duration_hours` | `Integer` | NULLABLE |
| `sleep_quality` | `String(50)` | NULLABLE |
| `stress_level` | `String(50)` | NULLABLE |
| `working_hours` | `Integer` | NULLABLE |
| `working_style` | `String(50)` | NULLABLE |
| `remote_office` | `String(50)` | NULLABLE |
| `sitting_hours` | `Integer` | NULLABLE |
| `transportation_method` | `String(100)` | NULLABLE |
| `physical_activity_level` | `String(50)` | NULLABLE |

### `nutritions`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `meals_per_day` | `Integer` | NULLABLE |
| `fruit_intake_per_day` | `String(50)` | NULLABLE |
| `vegetable_intake_per_day` | `String(50)` | NULLABLE |
| `fast_food_frequency` | `String(50)` | NULLABLE |
| `sugary_drinks_frequency` | `String(50)` | NULLABLE |
| `salt_intake` | `String(50)` | NULLABLE |
| `red_meat_frequency` | `String(50)` | NULLABLE |
| `processed_meat_frequency` | `String(50)` | NULLABLE |
| `fish_frequency` | `String(50)` | NULLABLE |
| `dairy_frequency` | `String(50)` | NULLABLE |
| `snacks_frequency` | `String(50)` | NULLABLE |
| `coffee_cups_per_day` | `Integer` | NULLABLE |
| `tea_cups_per_day` | `Integer` | NULLABLE |
| `energy_drinks_per_day` | `Integer` | NULLABLE |
| `special_diet` | `String(100)` | NULLABLE |
| `food_allergies` | `String(255)` | NULLABLE |

### `medical_histories`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `condition` | `String(255)` | NOT NULL |
| `diagnosis_date` | `Date` | NULLABLE |
| `severity` | `String(50)` | NULLABLE |
| `status` | `String(50)` | NULLABLE |
| `treating_doctor` | `String(255)` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `medication_histories`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `medication` | `String(255)` | NOT NULL |
| `dosage` | `String(100)` | NULLABLE |
| `frequency` | `String(100)` | NULLABLE |
| `start_date` | `Date` | NULLABLE |
| `end_date` | `Date` | NULLABLE |
| `reason` | `String(255)` | NULLABLE |
| `current_status` | `String(50)` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `surgical_histories`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `procedure` | `String(255)` | NOT NULL |
| `date` | `Date` | NULLABLE |
| `hospital` | `String(255)` | NULLABLE |
| `reason` | `String(255)` | NULLABLE |
| `outcome` | `String(255)` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `family_histories`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `relative` | `String(50)` | NOT NULL |
| `disease` | `String(255)` | NOT NULL |
| `age_at_diagnosis` | `Integer` | NULLABLE |
| `current_status` | `String(50)` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `allergies`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `type` | `String(50)` | NOT NULL |
| `substance` | `String(255)` | NOT NULL |
| `severity` | `String(50)` | NULLABLE |
| `reaction` | `Text` | NULLABLE |

### `immunizations`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `vaccine` | `String(255)` | NOT NULL |
| `dose` | `String(50)` | NULLABLE |
| `provider` | `String(255)` | NULLABLE |
| `date` | `Date` | NULLABLE |
| `notes` | `String(500)` | NULLABLE |

### `measurements`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `type` | `String(100)` | NOT NULL |
| `value` | `Float` | NULLABLE |
| `unit` | `String(50)` | NULLABLE |
| `recorded_at` | `DateTime(tz)` | NULLABLE |
| `notes` | `String(500)` | NULLABLE |

### `lab_reports`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `test_name` | `String(255)` | NOT NULL |
| `value` | `Float` | NULLABLE |
| `unit` | `String(50)` | NULLABLE |
| `reference_range` | `String(100)` | NULLABLE |
| `laboratory` | `String(255)` | NULLABLE |
| `date` | `Date` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `profile_versions`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `profile_id` | `String(32)` | FK → `health_profiles.id`, NOT NULL, INDEX |
| `version` | `Integer` | NOT NULL, default=1 |
| `snapshot` | `JSON` | NOT NULL |
| `created_at` | `DateTime(tz)` | NOT NULL (overridden from base) |
| `created_by` | `String(32)` | FK → `users.id`, NULLABLE, INDEX |

---

## Functional Area 3: Body Systems & Question Groups

### `body_systems`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `code` | `String(100)` | UNIQUE, NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `icon` | `String(255)` | NULLABLE |
| `color_hex` | `String(7)` | NULLABLE |
| `display_order` | `Integer` | NOT NULL, default=0, INDEX |
| `module_version` | `String(20)` | NOT NULL, default="1.0.0" |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `is_core` | `Boolean` | NOT NULL, default=false |
| `scoring_weight` | `Float` | NOT NULL, default=1.0 |
| `metadata` | `JSON` | NULLABLE |

**Relationships:** `question_groups` (1:M)

### `question_groups`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | FK → `body_systems.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `display_order` | `Integer` | NOT NULL, default=0, INDEX |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `metadata` | `JSON` | NULLABLE, default={} |

**Relationships:** `body_system` → `body_systems`, `questions` (1:M)

---

## Functional Area 4: Questions & Options

### `questions`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| (inherited base columns) | | | |
| `body_system_id` | `String(32)` | FK → `body_systems.id` ON DELETE CASCADE, NOT NULL, INDEX | |
| `question_group_id` | `String(32)` | FK → `question_groups.id` ON DELETE CASCADE, NOT NULL, INDEX | |
| `code` | `String(100)` | NOT NULL, INDEX | Unique question code |
| `question_type` | `String(30)` | NOT NULL | free_text, single_choice, multiple_choice, scale, boolean |
| `text` | `Text` | NOT NULL | Question body text |
| `description` | `Text` | NULLABLE | Detailed description |
| `tooltip` | `String(500)` | NULLABLE | Help tooltip |
| `medical_notes` | `Text` | NULLABLE | Internal medical notes |
| `evidence_ref` | `String(255)` | NULLABLE | Reference to evidence |
| `order_index` | `Integer` | NOT NULL, default=0, INDEX | Display order |
| `priority` | `Integer` | NOT NULL, default=3 | Priority level |
| `difficulty` | `String(20)` | NOT NULL, default="basic" | basic, intermediate, advanced |
| `status` | `String(20)` | NOT NULL, default="active", INDEX | active, inactive, draft, archived |
| `is_required` | `Boolean` | NOT NULL, default=false | |
| `validation_rules` | `JSON` | NULLABLE, default={} | Validation configuration |
| `scoring_weight` | `Float` | NOT NULL, default=1.0 | |
| `version` | `Integer` | NOT NULL, default=1 | |
| `created_by` | `String(32)` | NULLABLE | |
| `updated_by` | `String(32)` | NULLABLE | |
| `activation_date` | `DateTime(tz)` | NULLABLE | |
| `expiration_date` | `DateTime(tz)` | NULLABLE | |

**Relationships:** `options` (1:M), `group` → `question_groups`, `dependencies` (1:M)

### `question_options`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `question_id` | `String(32)` | FK → `questions.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `text` | `String(1000)` | NOT NULL |
| `value` | `String(255)` | NOT NULL |
| `score_value` | `Float` | NOT NULL, default=0.0 |
| `severity` | `String(20)` | NOT NULL, default="none" |
| `color_hex` | `String(7)` | NULLABLE |
| `recommendation_trigger` | `Text` | NULLABLE |
| `follow_up_trigger` | `Text` | NULLABLE |
| `medical_notes` | `Text` | NULLABLE |
| `display_order` | `Integer` | NOT NULL, default=0, INDEX |
| `is_active` | `Boolean` | NOT NULL, default=true |

### `question_dependencies`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `question_id` | `String(32)` | FK → `questions.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `depends_on_question_id` | `String(32)` | FK → `questions.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `condition_type` | `String(30)` | NOT NULL, default="equals" |
| `condition_value` | `JSON` | NOT NULL, default={} |
| `logic_operator` | `String(10)` | NOT NULL, default="AND" |
| `group_id` | `Integer` | NOT NULL, default=0 |

### `questionnaire_templates`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `code` | `String(100)` | UNIQUE, NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `body_system_id` | `String(32)` | NULLABLE, INDEX |
| `target_audience` | `String(30)` | NOT NULL, default="all" |
| `estimated_time_minutes` | `Integer` | NOT NULL, default=10 |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `is_template` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `metadata` | `JSON` | NULLABLE, default={} |

### `questionnaire_versions`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `questionnaire_template_id` | `String(32)` | NOT NULL, INDEX |
| `version` | `Integer` | NOT NULL, default=1 |
| `snapshot` | `JSON` | NOT NULL |
| `change_notes` | `String(1000)` | NULLABLE |
| `created_by` | `String(32)` | NULLABLE |

---

## Functional Area 5: Assessment Sessions & Answers

### `assessment_sessions`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `user_id` | `String(32)` | FK → `users.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `questionnaire_template_id` | `String(32)` | NULLABLE, INDEX |
| `questionnaire_version_id` | `String(32)` | NULLABLE |
| `status` | `String(20)` | NOT NULL, default="active", INDEX |
| `current_question_id` | `String(32)` | NULLABLE |
| `current_group_id` | `String(32)` | NULLABLE |
| `answers_count` | `Integer` | NOT NULL, default=0 |
| `total_questions` | `Integer` | NOT NULL, default=0 |
| `completed_questions` | `Integer` | NOT NULL, default=0 |
| `started_at` | `DateTime(tz)` | NULLABLE |
| `paused_at` | `DateTime(tz)` | NULLABLE |
| `completed_at` | `DateTime(tz)` | NULLABLE |
| `expires_at` | `DateTime(tz)` | NULLABLE |
| `device_info` | `String(500)` | NULLABLE |
| `metadata` | `JSON` | NULLABLE, default={} |

**Relationships:** `answers` (1:M)

### `assessment_answers`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `session_id` | `String(32)` | FK → `assessment_sessions.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `question_id` | `String(32)` | FK → `questions.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `question_version` | `Integer` | NOT NULL, default=1 |
| `question_code` | `String(100)` | NOT NULL |
| `option_id` | `String(32)` | NULLABLE, INDEX |
| `value` | `String(500)` | NULLABLE |
| `numeric_value` | `Float` | NULLABLE |
| `response_value` | `JSON` | NOT NULL, default={} |
| `score_value` | `Float` | NOT NULL, default=0.0 |
| `is_skipped` | `Boolean` | NOT NULL, default=false |
| `time_taken_seconds` | `Integer` | NOT NULL, default=0 |
| `branch_path` | `JSON` | NULLABLE, default=[] |
| `recorded_at` | `DateTime` | NULLABLE |

### `assessment_progress`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `session_id` | `String(32)` | NOT NULL, INDEX |
| `current_section` | `String(100)` | NULLABLE |
| `completed_questions` | `Integer` | NOT NULL, default=0 |
| `total_questions` | `Integer` | NOT NULL, default=0 |
| `answered_questions` | `Integer` | NOT NULL, default=0 |
| `skipped_questions` | `Integer` | NOT NULL, default=0 |
| `estimated_time_remaining` | `Integer` | NOT NULL, default=0 |
| `completion_percentage` | `Float` | NOT NULL, default=0.0 |

---

## Functional Area 6: Clinical Decision & Assessment Results

### `assessment_results`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `session_id` | `String(32)` | NOT NULL, INDEX |
| `user_id` | `String(32)` | NOT NULL, INDEX |
| `summary` | `Text` | NULLABLE |
| `confidence_score` | `Float` | NULLABLE |
| `created_at` | `DateTime(tz)` | NULLABLE |

**Relationships:** `activated_indicators`, `activated_conditions`, `generated_recommendations`, `generated_laboratory_tests`, `generated_screenings`, `explanations`

### `activated_indicators`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `result_id` | `String(32)` | FK → `assessment_results.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `indicator_id` | `String(32)` | NOT NULL, INDEX |
| `score` | `Float` | NULLABLE |
| `evidence_count` | `Integer` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `activated_conditions`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `result_id` | `String(32)` | FK → `assessment_results.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `condition_id` | `String(32)` | NOT NULL, INDEX |
| `score` | `Float` | NULLABLE |
| `confidence` | `Float` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `generated_recommendations`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `result_id` | `String(32)` | FK → `assessment_results.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `recommendation_id` | `String(32)` | NOT NULL, INDEX |
| `source` | `String(100)` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `generated_laboratory_tests`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `result_id` | `String(32)` | FK → `assessment_results.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `laboratory_test_id` | `String(32)` | NOT NULL, INDEX |
| `reason` | `Text` | NULLABLE |

### `generated_screenings`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `result_id` | `String(32)` | FK → `assessment_results.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `reason` | `Text` | NULLABLE |

### `explanation_records`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `result_id` | `String(32)` | FK → `assessment_results.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `source_type` | `String(50)` | NOT NULL |
| `source_id` | `String(32)` | NULLABLE |
| `text` | `Text` | NULLABLE |

---

## Functional Area 7: Health Assessments (Reports)

### `health_assessments`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `session_id` | `String(32)` | NOT NULL, INDEX |
| `user_id` | `String(32)` | NOT NULL, INDEX |
| `summary` | `Text` | NULLABLE |
| `created_at` | `DateTime(tz)` | NULLABLE |

**Relationships:** `body_systems` (1:M), `conditions` (1:M), `lifestyle` (1:M), `advices` (1:M)

### `body_system_assessments`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `assessment_id` | `String(32)` | FK → `health_assessments.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `body_system_id` | `String(32)` | NULLABLE, INDEX |
| `category` | `String(50)` | NULLABLE |
| `score` | `String(50)` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `condition_assessments`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `assessment_id` | `String(32)` | FK → `health_assessments.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `condition_id` | `String(32)` | NOT NULL, INDEX |
| `score` | `String(50)` | NULLABLE |
| `confidence` | `String(50)` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `lifestyle_assessments`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `assessment_id` | `String(32)` | FK → `health_assessments.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `data` | `Text` | NULLABLE |

### `generated_advices`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `assessment_id` | `String(32)` | FK → `health_assessments.id` ON DELETE CASCADE, NOT NULL, INDEX |
| `recommendation_id` | `String(32)` | NULLABLE, INDEX |
| `category` | `String(50)` | NULLABLE |
| `text` | `Text` | NULLABLE |

---

## Functional Area 8: Knowledge Graph & Link Tables

### `knowledge_graphs`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `name` | `String(500)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `knowledge_graph_nodes`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `graph_id` | `String(32)` | NOT NULL, INDEX |
| `entity_type` | `String(50)` | NOT NULL, INDEX |
| `entity_id` | `String(32)` | NOT NULL |
| `label` | `String(500)` | NOT NULL |
| `x_position` | `Float` | NOT NULL, default=0.0 |
| `y_position` | `Float` | NOT NULL, default=0.0 |
| `color` | `String(20)` | NULLABLE |
| `metadata` | `JSON` | NULLABLE, default={} |

### `knowledge_graph_edges`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `graph_id` | `String(32)` | NOT NULL, INDEX |
| `source_node_id` | `String(32)` | NOT NULL |
| `target_node_id` | `String(32)` | NOT NULL |
| `relationship_type` | `String(50)` | NOT NULL, INDEX |
| `label` | `String(255)` | NULLABLE |
| `weight` | `Float` | NOT NULL, default=1.0 |
| `metadata` | `JSON` | NULLABLE, default={} |

### Knowledge Graph Link/Junction Tables

All link tables follow the same pattern (inherited base columns + two entity IDs + `active` flag):

| Table | Columns | Notes |
|-------|---------|-------|
| `question_indicator_links` | `question_id` (INDEX), `indicator_id` (INDEX), `active` (default=true) | Links questions to clinical indicators |
| `question_option_indicator_links` | `question_option_id` (INDEX), `indicator_id` (INDEX), `active` | Links options to indicators |
| `indicator_condition_links` | `indicator_id` (INDEX), `condition_id` (INDEX), `active` | Links indicators to conditions |
| `indicator_evidence_links` | `indicator_id` (INDEX), `evidence_id` (INDEX), `active` | Links indicators to evidence |
| `indicator_recommendation_links` | `indicator_id` (INDEX), `recommendation_id` (INDEX), `active` | Links indicators to recommendations |
| `condition_recommendation_links` | `condition_id` (INDEX), `recommendation_id` (INDEX), `active` | Links conditions to recommendations |
| `condition_laboratory_test_links` | `condition_id` (INDEX), `laboratory_test_id` (INDEX), `active` | Links conditions to lab tests |
| `body_system_condition_links` | `body_system_id` (INDEX), `condition_id` (INDEX), `active` | Links body systems to conditions |

---

## Functional Area 9: Clinical Reference Data

### `clinical_indicators`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `key` | `String(100)` | UNIQUE, NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `severity` | `String(20)` | NOT NULL, default="moderate" |
| `evidence_strength` | `String(5)` | NOT NULL, default="C" |
| `confidence` | `Float` | NOT NULL, default=0.5 |
| `positive_weight` | `Float` | NOT NULL, default=1.0 |
| `negative_weight` | `Float` | NOT NULL, default=0.0 |
| `neutral_weight` | `Float` | NOT NULL, default=0.0 |
| `related_disease_ids` | `JSON` | NULLABLE, default=[] |
| `related_symptom_ids` | `JSON` | NULLABLE, default=[] |
| `order` | `Integer` | NOT NULL, default=0 |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `diseases`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `icd10_code` | `String(20)` | UNIQUE, NOT NULL, INDEX |
| `name` | `String(500)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `risk_factors` | `JSON` | NULLABLE, default=[] |
| `early_indicators` | `JSON` | NULLABLE, default=[] |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `symptoms`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `severity` | `String(20)` | NOT NULL, default="moderate" |
| `duration_rule` | `String(100)` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `possible_conditions`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `code` | `String(64)` | NULLABLE, INDEX |
| `name` | `String(255)` | NOT NULL, INDEX |
| `description` | `Text` | NULLABLE |
| `body_system_id` | `String(32)` | NULLABLE, INDEX |
| `severity` | `String(50)` | NULLABLE |
| `status` | `String(50)` | NULLABLE |
| `icd10` | `String(64)` | NULLABLE |
| `notes` | `Text` | NULLABLE |

### `recommendations`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `key` | `String(100)` | UNIQUE, NOT NULL, INDEX |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `disease_id` | `String(32)` | NULLABLE, INDEX |
| `category` | `String(100)` | NOT NULL, default="general" |
| `title` | `String(500)` | NOT NULL |
| `text` | `Text` | NOT NULL |
| `order` | `Integer` | NOT NULL, default=0 |
| `priority` | `Integer` | NOT NULL, default=5, INDEX |
| `urgency` | `String(20)` | NOT NULL, default="routine" |
| `evidence_level` | `String(5)` | NOT NULL, default="C" |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `laboratory_tests`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `code` | `String(100)` | UNIQUE, NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `loinc_code` | `String(20)` | NULLABLE, INDEX |
| `normal_range` | `String(255)` | NULLABLE |
| `unit` | `String(50)` | NULLABLE |
| `reference_range_min` | `Float` | NULLABLE |
| `reference_range_max` | `Float` | NULLABLE |
| `critical_low` | `Float` | NULLABLE |
| `critical_high` | `Float` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `imaging_tests`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `code` | `String(100)` | UNIQUE, NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `modality` | `String(50)` | NOT NULL, default="X-ray" |
| `is_contrast_required` | `Boolean` | NOT NULL, default=false |
| `preparation_notes` | `Text` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `medical_evidence`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `title` | `String(500)` | NOT NULL |
| `source` | `String(255)` | NOT NULL |
| `source_type` | `String(50)` | NOT NULL, default="journal" |
| `doi` | `String(100)` | NULLABLE, INDEX |
| `pmid` | `String(20)` | NULLABLE, INDEX |
| `url` | `String(2000)` | NULLABLE |
| `authors` | `JSON` | NULLABLE, default=[] |
| `publication_year` | `Integer` | NULLABLE |
| `evidence_level` | `String(5)` | NOT NULL, default="C" |
| `summary` | `Text` | NULLABLE |
| `body_system_id` | `String(32)` | NULLABLE, INDEX |
| `disease_ids` | `JSON` | NULLABLE, default=[] |
| `indicator_ids` | `JSON` | NULLABLE, default=[] |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `clinical_guidelines`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `disease_id` | `String(32)` | NULLABLE, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `title` | `String(500)` | NOT NULL |
| `summary` | `Text` | NULLABLE |
| `recommendations` | `JSON` | NULLABLE, default=[] |
| `evidence_level` | `String(5)` | NOT NULL, default="C" |
| `source_organization` | `String(255)` | NULLABLE |
| `guideline_url` | `String(2000)` | NULLABLE |
| `publication_year` | `Integer` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |
| `reviewed_at` | `DateTime(tz)` | NULLABLE |
| `published_at` | `DateTime(tz)` | NULLABLE |
| `archived_at` | `DateTime(tz)` | NULLABLE |

### `medication_recommendations`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `disease_id` | `String(32)` | NULLABLE, INDEX |
| `drug_name` | `String(255)` | NOT NULL |
| `generic_name` | `String(255)` | NULLABLE |
| `drug_class` | `String(100)` | NULLABLE |
| `dosage` | `String(100)` | NULLABLE |
| `frequency` | `String(100)` | NULLABLE |
| `route` | `String(50)` | NULLABLE |
| `duration` | `String(100)` | NULLABLE |
| `contraindications` | `JSON` | NULLABLE, default=[] |
| `side_effects` | `JSON` | NULLABLE, default=[] |
| `interactions` | `JSON` | NULLABLE, default=[] |
| `evidence_level` | `String(5)` | NOT NULL, default="C" |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### Advice Tables

**`lifestyle_advice`**, **`nutrition_advice`**, **`exercise_programs`** — all share a similar structure:

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `title` / `name` | `String(500)` | NOT NULL |
| `description` / `summary` / `details` | `Text` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `decision_rules`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `rule_type` | `String(50)` | NOT NULL, default="decision" |
| `condition_expression` | `JSON` | NULLABLE |
| `action_expression` | `JSON` | NULLABLE |
| `priority` | `Integer` | NOT NULL, default=5 |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `branch_rules`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `code` | `String(100)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `condition_operator` | `String(10)` | NOT NULL, default="AND" |
| `conditions` | `JSON` | NOT NULL, default={} |
| `target_question_id` | `String(32)` | NOT NULL |
| `priority` | `Integer` | NOT NULL, default=0 |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |

### `evidence_references`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `question_id` | `String(32)` | NULLABLE, INDEX |
| `title` | `String(255)` | NOT NULL |
| `url` | `String(1000)` | NULLABLE |
| `source` | `String(255)` | NULLABLE |
| `evidence_level` | `String(5)` | NOT NULL, default="C" |
| `summary` | `Text` | NULLABLE |

---

## Functional Area 10: Scoring & Risk

### `scoring_profiles`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `weights` | `JSON` | NULLABLE, default={} |
| `thresholds` | `JSON` | NULLABLE, default=[] |
| `formula` | `String(500)` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `severity_thresholds`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `scoring_profile_id` | `String(32)` | NULLABLE, INDEX |
| `name` | `String(255)` | NOT NULL |
| `severity` | `String(20)` | NOT NULL |
| `min_score` | `Float` | NOT NULL, default=0.0 |
| `max_score` | `Float` | NOT NULL, default=100.0 |
| `color_hex` | `String(7)` | NULLABLE |
| `label` | `String(100)` | NULLABLE |
| `recommendation` | `Text` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `risk_categories`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `min_probability` | `Float` | NOT NULL, default=0.0 |
| `max_probability` | `Float` | NOT NULL, default=1.0 |
| `color_hex` | `String(7)` | NULLABLE |
| `action_required` | `Text` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

---

## Functional Area 11: CMS Publishing Workflow

### `workflows`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `entity_type` | `String(50)` | NOT NULL, INDEX |
| `steps` | `JSON` | NULLABLE, default=[] |
| `current_step` | `Integer` | NOT NULL, default=0 |
| `status` | `String(20)` | NOT NULL, default="active", INDEX |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `publishing_jobs`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `entity_type` | `String(50)` | NOT NULL, INDEX |
| `entity_id` | `String(32)` | NOT NULL, INDEX |
| `version` | `Integer` | NOT NULL |
| `requested_by` | `String(32)` | NOT NULL |
| `approved_by` | `String(32)` | NULLABLE |
| `status` | `String(20)` | NOT NULL, default="pending", INDEX |
| `schedule_at` | `DateTime(tz)` | NULLABLE |
| `published_at` | `DateTime(tz)` | NULLABLE |
| `rollback_version` | `Integer` | NULLABLE |
| `notes` | `Text` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `approvals`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `entity_type` | `String(50)` | NOT NULL, INDEX |
| `entity_id` | `String(32)` | NOT NULL, INDEX |
| `requested_by` | `String(32)` | NOT NULL |
| `assigned_to` | `String(32)` | NULLABLE |
| `role_required` | `String(50)` | NULLABLE |
| `status` | `String(20)` | NOT NULL, default="pending", INDEX |
| `comments` | `JSON` | NULLABLE, default=[] |
| `decided_at` | `DateTime(tz)` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `reviews`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `entity_type` | `String(50)` | NOT NULL, INDEX |
| `entity_id` | `String(32)` | NOT NULL, INDEX |
| `reviewer_id` | `String(32)` | NOT NULL |
| `review_type` | `String(50)` | NOT NULL, default="medical" |
| `status` | `String(20)` | NOT NULL, default="pending", INDEX |
| `decision` | `String(20)` | NULLABLE |
| `comments` | `Text` | NULLABLE |
| `score` | `Integer` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |
| `completed_at` | `DateTime(tz)` | NULLABLE |

### `review_comments`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `review_id` | `String(32)` | NOT NULL, INDEX |
| `user_id` | `String(32)` | NOT NULL |
| `comment` | `Text` | NOT NULL |
| `parent_id` | `String(32)` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `created_by` | `String(32)` | NULLABLE |

### `change_requests`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `entity_type` | `String(50)` | NOT NULL, INDEX |
| `entity_id` | `String(32)` | NOT NULL, INDEX |
| `requested_by` | `String(32)` | NOT NULL |
| `title` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `changes` | `JSON` | NOT NULL |
| `reason` | `Text` | NULLABLE |
| `status` | `String(20)` | NOT NULL, default="pending", INDEX |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |
| `resolved_at` | `DateTime(tz)` | NULLABLE |
| `resolved_by` | `String(32)` | NULLABLE |

### `version_snapshots`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `entity_type` | `String(50)` | NOT NULL, INDEX |
| `entity_id` | `String(32)` | NOT NULL, INDEX |
| `version` | `Integer` | NOT NULL |
| `snapshot` | `JSON` | NOT NULL |
| `snapshot_type` | `String(20)` | NOT NULL, default="auto" |
| `reason` | `Text` | NULLABLE |
| `created_by` | `String(32)` | NULLABLE |

### `notifications`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `user_id` | `String(32)` | NOT NULL, INDEX |
| `title` | `String(255)` | NOT NULL |
| `body` | `Text` | NULLABLE |
| `notification_type` | `String(50)` | NOT NULL, default="info" |
| `entity_type` | `String(50)` | NULLABLE |
| `entity_id` | `String(32)` | NULLABLE |
| `is_read` | `Boolean` | NOT NULL, default=false |
| `read_at` | `DateTime(tz)` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `created_by` | `String(32)` | NULLABLE |

---

## Functional Area 12: Audit

### `audit_logs`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `actor_id` | `String(32)` | NULLABLE, INDEX |
| `actor_role` | `String(100)` | NULLABLE |
| `entity_type` | `String(100)` | NOT NULL, INDEX |
| `entity_id` | `String(32)` | NULLABLE |
| `action` | `String(50)` | NOT NULL, INDEX |
| `changed_at` | `DateTime(tz)` | NOT NULL, INDEX |
| `old_value` | `Text` | NULLABLE |
| `new_value` | `Text` | NULLABLE |
| `reason` | `Text` | NULLABLE |
| `ip_address` | `String(45)` | NULLABLE |
| `user_agent` | `String(500)` | NULLABLE |
| `session_id` | `String(32)` | NULLABLE |
| `request_id` | `String(32)` | NULLABLE |
| `status_code` | `Integer` | NULLABLE |
| `method` | `String(10)` | NULLABLE |
| `path` | `String(500)` | NULLABLE |

---

## Functional Area 13: Categories & Tags

These tables follow an identical hierarchical pattern:

| Table | Unique Field | Parent FK | Description |
|-------|-------------|-----------|-------------|
| `disease_categories` | `code` (UNIQUE, INDEX) | `parent_id` NULLABLE INDEX | Disease classification hierarchy |
| `body_system_categories` | `code` (UNIQUE, INDEX) | `parent_id` NULLABLE INDEX | Body system classification |
| `recommendation_categories` | `code` (UNIQUE, INDEX) | `parent_id` NULLABLE INDEX | Recommendation grouping |
| `question_categories` | `code` (UNIQUE, INDEX) | `parent_id` NULLABLE INDEX | Question categorization |
| `medical_specialties` | `code` (UNIQUE, INDEX) | — | Medical specialties |
| `medical_tags` | `code` (UNIQUE, INDEX) | — | Medical tagging (with `category`, `color_hex`) |
| `question_tags` | `code` (UNIQUE, INDEX) | — | Question tagging (with `category`, `color_hex`) |
| `medical_organizations` | `code` (UNIQUE, INDEX) | — | Organizations (with `org_type`, `country`, `website`) |

All include: `name`, `description` (nullable), `is_active`, `version`, `status`, `created_by`, `updated_by`.

### `evidence_collections`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `disease_id` | `String(32)` | NULLABLE, INDEX |
| `title` | `String(500)` | NOT NULL |
| `methodology` | `String(255)` | NULLABLE |
| `evidence_ids` | `JSON` | NULLABLE, default=[] |
| `conclusion` | `Text` | NULLABLE |
| `overall_grade` | `String(5)` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

---

## Functional Area 14: Reference & Research

### `reference_sources`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `title` | `String(500)` | NOT NULL |
| `authors` | `JSON` | NULLABLE, default=[] |
| `source_type` | `String(50)` | NOT NULL, default="journal" |
| `journal` | `String(255)` | NULLABLE |
| `volume` | `String(50)` | NULLABLE |
| `issue` | `String(50)` | NULLABLE |
| `pages` | `String(50)` | NULLABLE |
| `doi` | `String(100)` | NULLABLE, INDEX |
| `pmid` | `String(20)` | NULLABLE, INDEX |
| `isbn` | `String(20)` | NULLABLE |
| `url` | `String(2000)` | NULLABLE |
| `publication_year` | `Integer` | NULLABLE |
| `publisher` | `String(255)` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `research_papers`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `title` | `String(500)` | NOT NULL |
| `abstract` | `Text` | NULLABLE |
| `authors` | `JSON` | NULLABLE, default=[] |
| `journal` | `String(255)` | NULLABLE |
| `doi` | `String(100)` | NULLABLE, INDEX |
| `pmid` | `String(20)` | NULLABLE, INDEX |
| `publication_year` | `Integer` | NULLABLE |
| `keywords` | `JSON` | NULLABLE, default=[] |
| `mesh_terms` | `JSON` | NULLABLE, default=[] |
| `evidence_level` | `String(5)` | NULLABLE |
| `sample_size` | `Integer` | NULLABLE |
| `methodology` | `String(255)` | NULLABLE |
| `findings` | `Text` | NULLABLE |
| `limitations` | `Text` | NULLABLE |
| `conflict_of_interest` | `Text` | NULLABLE |
| `url` | `String(2000)` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `clinical_trials`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `title` | `String(500)` | NOT NULL |
| `nct_id` | `String(20)` | NULLABLE, INDEX |
| `phase` | `String(50)` | NULLABLE |
| `status` | `String(50)` | NOT NULL, default="registered" |
| `conditions` | `JSON` | NULLABLE, default=[] |
| `interventions` | `JSON` | NULLABLE, default=[] |
| `sponsor` | `String(255)` | NULLABLE |
| `enrollment` | `Integer` | NULLABLE |
| `start_date` | `DateTime(tz)` | NULLABLE |
| `completion_date` | `DateTime(tz)` | NULLABLE |
| `results` | `Text` | NULLABLE |
| `url` | `String(2000)` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

---

## Functional Area 15: Rule Libraries & Templates

### `rule_libraries`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `rules` | `JSON` | NULLABLE, default=[] |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `template_libraries`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `template_type` | `String(50)` | NOT NULL, default="questionnaire" |
| `content` | `JSON` | NOT NULL, default={} |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `questionnaire_rule_sets`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `questionnaire_id` | `String(32)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `rules` | `JSON` | NULLABLE, default=[] |
| `logic` | `String(10)` | NOT NULL, default="ALL" |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `biomarkers`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `unit` | `String(50)` | NULLABLE |
| `reference_range_min` | `Float` | NULLABLE |
| `reference_range_max` | `Float` | NULLABLE |
| `critical_low` | `Float` | NULLABLE |
| `critical_high` | `Float` | NULLABLE |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

### `lab_panels`

| Column | Type | Constraints |
|--------|------|-------------|
| (inherited base columns) | | |
| `body_system_id` | `String(32)` | NOT NULL, INDEX |
| `code` | `String(100)` | NOT NULL, INDEX |
| `name` | `String(255)` | NOT NULL |
| `description` | `Text` | NULLABLE |
| `lab_test_ids` | `JSON` | NULLABLE, default=[] |
| `is_active` | `Boolean` | NOT NULL, default=true |
| `version` | `Integer` | NOT NULL, default=1 |
| `status` | `String(20)` | NOT NULL, default="draft", INDEX |
| `created_by` | `String(32)` | NULLABLE |
| `updated_by` | `String(32)` | NULLABLE |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total tables | ~75 |
| Junction/link tables | 10 (user_roles + 9 knowledge graph link tables) |
| Tables with soft delete | All (inherited from BaseModel) |
| Tables with versioning | ~30+ |
| Tables with status field | ~35+ |
