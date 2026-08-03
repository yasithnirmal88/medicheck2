# Doctor Guide

## Overview

Medicheck is a clinical decision support tool that helps doctors assess patients through structured questionnaires. The system generates evidence-based recommendations and risk assessments to support clinical decision-making.

## Key Features

- **Patient Assessment**: Review patient-completed questionnaires
- **Clinical Decision Support**: Automated analysis with indicator → condition → recommendation mapping
- **Report Generation**: Comprehensive health assessment reports with severity grading
- **Knowledge Graph**: Explore medical relationships between symptoms, conditions, and treatments

## Workflow

### 1. Patient Submits Questionnaire

Patients answer questions organized by body system. The system evaluates responses against clinical indicators.

### 2. Review Assessment

Access patient assessments from the dashboard:

```
Dashboard → Patients → Select Patient → Assessment
```

The assessment shows:
- **Activated Indicators**: Clinical signs detected from responses
- **Possible Conditions**: Conditions matching the activated indicators
- **Severity Level**: Low / Moderate / High / Critical
- **Confidence Score**: 0–1 normalized confidence in the assessment

### 3. Generate Report

Generate a structured clinical report:

```json
{
  "report_id": "abc123",
  "summary": {
    "severity": "moderate",
    "activated_indicators": 5,
    "possible_conditions": 3,
    "confidence": 0.78
  },
  "recommendations": [
    {
      "title": "Cardiology Referral",
      "priority": 8,
      "urgency": "urgent",
      "evidence_level": "A",
      "text": "Refer to cardiologist for ECG and stress test"
    }
  ],
  "body_system_scores": {
    "cardiovascular": { "score": 0.85, "max": 1.0 }
  }
}
```

### 4. Compare Reports

Compare reports from different dates to track patient progress:

```
Reports → Select Two Reports → Compare
```

## Clinical Decision Engine

The CDSE processes responses through 7 batch-load steps:

1. Load session answers
2. Map answers to indicators (via question → indicator and option → indicator links)
3. Aggregate indicator scores (weighted by answer values)
4. Map indicators to conditions (via indicator → condition links)
5. Calculate condition probabilities
6. Map conditions to recommendations (via condition → recommendation links)
7. Generate evidence-based explanations

## Evidence Levels

| Level | Meaning |
|-------|---------|
| A | Strong evidence from multiple RCTs or meta-analyses |
| B | Moderate evidence from well-designed studies |
| C | Limited evidence from observational studies |
| D | Expert opinion or case reports |

## Severity Thresholds

Scores are mapped to severity levels based on database-configured thresholds:
- **Low**: < 0.3
- **Moderate**: 0.3 – 0.6
- **High**: 0.6 – 0.85
- **Critical**: > 0.85

## FAQ

**Q: Is this a diagnosis tool?**
A: No. Medicheck is a decision support tool. All assessments should be reviewed by a qualified healthcare professional.

**Q: How are recommendations generated?**
A: Recommendations are rule-based, mapped via indicator → condition → recommendation links. Each recommendation includes an evidence level.

**Q: Can I export reports?**
A: Yes. Reports can be exported as PDF or shared via secure link.
