# Admin Guide

## Overview

The Admin module provides system administration capabilities including user management, body system configuration, clinical content management, and audit logging.

## Prerequisites

- Admin role required for system configuration
- Super Admin role required for user management and sensitive operations

## Features

### User Management

Manage users, roles, and permissions:

```
Admin → Users
```

- View all users
- Assign/change roles (Patient, Doctor, Specialist, Medical Director, Admin)
- Activate/deactivate accounts
- View login history

### Body Systems Management

Configure the 18 medical body systems:

```
Admin → Body Systems
```

| System | Code | Description |
|--------|------|-------------|
| Blood | BLOOD | Hematological system |
| Cancer Screening | CANCER | Oncology screening |
| Cardiovascular | CARDIO | Heart and circulatory |
| Digestive | DIGEST | Gastrointestinal |
| Endocrine | ENDO | Hormonal system |
| Eye | EYE | Ophthalmological |
| Female Health | FEMALE | Women's health |
| Immune | IMMUNE | Immunology |
| Kidney | KIDNEY | Renal system |
| Liver | LIVER | Hepatic system |
| Male Health | MALE | Men's health |
| Mental Health | MENTAL | Psychiatric |
| Musculoskeletal | MUSCLE | Bones and muscles |
| Neurological | NEURO | Nervous system |
| Respiratory | RESP | Pulmonary system |
| Sexual Health | SEXUAL | Sexual/reproductive |
| Skin | SKIN | Dermatological |

Each body system has configurable:
- Display name, icon, color
- Display order
- Active/inactive status
- Scoring weight

### Clinical Indicators

```
Admin → Indicators
```

Manage clinical indicators that detect conditions from questionnaire responses:
- Create/edit with key, name, severity, evidence strength
- Link to body systems
- Configure confidence levels and weights

### Evidence References

```
Admin → Evidence
```

Manage medical evidence references:
- Title, source, source type (journal, guideline, trial)
- Evidence level (A–D)
- Link to indicators

### Recommendations

```
Admin → Recommendations
```

Manage clinical recommendations:
- Title, text, priority (1–10)
- Urgency (routine, urgent, emergency)
- Evidence level
- Link to conditions via knowledge graph

### Audit Logging

All admin operations are logged to the audit trail:

```
Admin → Audit Logs
```

Each log entry captures:
- Actor (user ID + role)
- Entity type and ID
- Action (create, update, delete)
- Old and new values
- Timestamp

### Knowledge Graph Operations

Requires **Medical Director** role:

```
Admin → Knowledge Graph
```

- Create conditions with ICD-10 codes
- Create lab tests with LOINC codes and reference ranges
- Link indicators ↔ conditions
- Link conditions ↔ recommendations
- Link conditions ↔ lab tests
- Link indicators ↔ evidence
- Link questions → indicators
- Link question options → indicators

## Best Practices

1. **Always verify content** before publishing to production
2. **Use evidence levels** accurately — assign A only for strong RCT evidence
3. **Link thoroughly** — unlinked indicators/conditions won't appear in assessments
4. **Review audit logs** regularly for unauthorized changes
5. **Test changes** in staging before promoting to production
