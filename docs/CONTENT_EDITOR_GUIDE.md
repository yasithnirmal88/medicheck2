# Content Editor Guide

## Overview

The Content Management System (CMS) allows medical editors to manage all clinical content including questions, body systems, indicators, conditions, and recommendations.

## Roles

| Role | Permissions |
|------|-------------|
| CMS Medical Editor | Create/edit clinical content |
| CMS Publisher | Manage change requests and publishing |
| CMS Approver | Review and approve content changes |
| CMS Admin | Full CMS access including audit logs |

## Content Types

### Questions

Create and manage questionnaire questions:

```
CMS → Questions
```

- **Type**: yes_no, multiple_choice, scale, numeric, decimal, date, text
- **Body System**: Assign to one of 18 medical systems
- **Validation**: Min/max bounds for numeric types
- **Branching**: Conditional visibility based on previous answers
- **Dependencies**: Link questions for dependent evaluation
- **Options**: Define answer options with score values

### Body Systems

```
CMS → Body Systems
```

Manage the medical body system hierarchy:
- Display order for questionnaire organization
- Icon selection (droplet, brain, heartbeat, etc.)
- Color coding
- Active/inactive status
- Scoring weight per system

### Clinical Indicators

```
CMS → Indicators
```

- Link to body system
- Set severity (mild, moderate, severe, critical)
- Assign evidence strength (A, B, C, D)
- Configure confidence (0–1)
- Set positive/negative/neutral weights

### Medical Evidence

```
CMS → Evidence
```

Attach evidence references to indicators:
- Source type: journal, clinical_trial, guideline, textbook, expert_opinion
- Evidence level: A (strong) through D (expert opinion)
- URL or citation for source

## Publishing Workflow

```
Content Editor creates/edits
        ↓
Change Request created
        ↓
Approver reviews
        ↓
Approved → Snapshot created → Published
Rejected → Returned to editor
```

### Change Requests

All content changes go through a change request workflow:
1. Editor makes changes in draft mode
2. Publisher creates a change request with description and reason
3. Approver reviews and approves/rejects
4. Approved changes create a version snapshot
5. Snapshot is published to production

## Best Practices

1. **Key naming**: Use uppercase snake_case with body system prefix (e.g., `CARDIO_CHEST_PAIN`)
2. **ICD-10 codes**: Always include ICD-10 codes for conditions
3. **LOINC codes**: Include LOINC codes for lab tests
4. **Reference ranges**: Specify normal ranges for numeric/decimal questions
5. **Evidence linking**: Every indicator should link to at least one evidence reference
6. **Condition linking**: Every condition should link to at least one recommendation
7. **Question coverage**: Ensure each question maps to at least one indicator
8. **Version control**: Always use the publishing workflow for production changes
