# Questionnaire Engine Documentation

## Overview

The Questionnaire Engine handles creation, validation, branching, and scoring of medical questionnaires. It supports 7 question types with configurable validation rules and conditional visibility.

## Question Types

| Type | Description | Value Format | Validation |
|------|-------------|-------------|------------|
| `yes_no` | Binary choice | `"yes"` / `"no"` | None |
| `multiple_choice` | Single or multiple selection | Array of option codes | Max selections |
| `scale` | Numeric scale (e.g., 1–10) | Integer | Min/max range |
| `numeric` | Numeric input | Number | Min/max bounds |
| `decimal` | Decimal number | Float | Min/max bounds, precision |
| `date` | Date selection | ISO date string | Past/future validation |
| `text` | Free text | String | Max length |

## Scoring System

### Score Calculation

Each answer contributes to the body system score:

```
score_percentage = (earned_score / max_possible) × 100
```

Where:
- `earned_score` = sum of answer option `score_value` × question weight
- `max_possible` = sum of all question weights in the system

### Weight Normalization

- `max_possible` adds the weight of every question unconditionally (regardless of score value)
- This ensures percentage accuracy — a question answered with score 0 still counts toward max possible

### Body System Scoring

Each body system has:
- `scoring_weight`: Multiplier for the system (default: 1.0)
- Questions assigned to the system contribute to its score

### Severity Thresholds

Thresholds are configured in the `severity_thresholds` database table:

| Level | Range |
|-------|-------|
| Low | < 30% |
| Moderate | 30% – 60% |
| High | 60% – 85% |
| Critical | > 85% |

## Branching Logic

Questions can have conditional visibility based on previous answers:

```python
{
  "question_id": "depression_q2",
  "condition": {
    "dependency_type": "equals",
    "target_question": "depression_q1",
    "target_value": "yes"
  }
}
```

### Dependency Evaluation

The `DependencyEvaluator` in `modules/questionnaire/dependency_evaluator.py`:

1. Loads all dependency definitions for the questionnaire
2. Checks each dependency against the user's answered values
3. Returns visibility status per question

### Dependency Types

| Type | Description |
|------|-------------|
| `equals` | Visible when target answer equals value |
| `not_equals` | Visible when target answer does not equal value |
| `greater_than` | Visible when target answer > value (numeric) |
| `less_than` | Visible when target answer < value (numeric) |
| `in` | Visible when target answer is in a list of values |

## Question Groups

Questions are organized into groups within each body system:

```
Body System
  └── Question Group
       ├── Question 1
       ├── Question 2
       └── ...
```

Groups control display order and section organization within the questionnaire UI.

## Validation Rules

Applied at question creation:

```python
"validation_rules": {
  "min_value": 0,
  "max_value": 150,
  "max_length": 500,
  "required": True
}
```

### Question Validation

The `QuestionValidator` in `modules/questionnaire/validation.py` checks:
- Required fields (code, question_type, text, body_system_id)
- Question type-specific requirements (options for multiple_choice, etc.)
- Validation rules consistency (min ≤ max)
- Unique question codes within body system

## API Endpoints

### Question Management

```http
GET    /api/v1/questions                    # List questions (filtered)
POST   /api/v1/questions                    # Create question
GET    /api/v1/questions/{id}               # Get question detail
PUT    /api/v1/questions/{id}               # Update question
DELETE /api/v1/questions/{id}               # Soft delete question
```

### Questionnaire Flow

```http
POST   /api/v1/questionnaire/start          # Create assessment session
POST   /api/v1/questionnaire/submit         # Submit answers
GET    /api/v1/questionnaire/progress/{id}  # Get completion progress
```

## Implementation Details

**Key files**:
- `backend/app/modules/questionnaire/engine.py` — Main engine implementation
- `backend/app/modules/questionnaire/scoring.py` — Score calculation
- `backend/app/modules/questionnaire/branching.py` — Conditional logic
- `backend/app/modules/questionnaire/dependency_evaluator.py` — Dependency resolution
- `backend/app/modules/questionnaire/validation.py` — Question validation
