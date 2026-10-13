# MediCheck SDG Indicator Mapping

Phase 10 — Interoperability, Health-System Integration & Outcome Feedback.

This document maps MediCheck analytics to SDG-aligned indicators for
research / public-health export. **Every metric below is a
MediCheck-aligned proxy, NOT an official UN SDG indicator**, unless
explicitly stated otherwise (none currently are).

## Export Endpoints

| Method | Path | Format | RBAC |
|--------|------|--------|------|
| GET | `/api/v1/interoperability/sdg` | JSON | `get_sdg_export_user` (RESEARCH_REVIEWER+) |
| GET | `/api/v1/interoperability/sdg/csv` | CSV | `get_sdg_export_user` |

## Row Schema

Each exported row has:

```
indicator          - stable metric key
sdg_target         - sdg-3-4 | sdg-3-8 | sdg-10
indicator_type     - "medicheck-aligned-proxy" (never claims "official")
period             - reporting period
geography          - null unless sufficiently aggregated
population_group   - null unless sufficiently aggregated
value              - metric value (null if suppressed)
numerator          - count (null if suppressed)
denominator        - count (null if suppressed)
suppression_status - "released" | "suppressed"
unit               - percent | days | count
methodology        - human-readable calculation method
limitations        - caveats
```

## K-Anonymity

- Minimum cohort threshold: `k = 10` (configurable via
  `settings.analytics_min_group_size`).
- Any cohort smaller than `k` is suppressed: `value`, `numerator`, and
  `denominator` are set to `null` and `suppression_status = "suppressed"`.
- Suppression is enforced at the service layer per-stage and per-metric.
- Users cannot bypass suppression by changing filters, querying narrow
  ranges, requesting individual dimensions, or combining endpoints.
- Exact patient counts are never exposed in a way that could reveal a small
  cohort.

## SDG 3.4 — NCDs + Mental Health

### sdg-3-4-assessment-coverage

| Field | Value |
|-------|-------|
| MediCheck metric | Completed MediCheck assessments in the period |
| Numerator | distinct completed sessions |
| Denominator | — (count) |
| Population | all patients with a completed assessment in period |
| Exclusion | abandoned / in-progress sessions |
| Privacy threshold | k ≥ 10 |
| Methodology | Count of completed MediCheck assessment sessions (distinct) in the period |
| Limitations | Platform activity proxy; not population prevalence |
| Interpretation | screening activity volume, not NCD prevalence |

### sdg-3-4-ncd-risk-distribution

| Field | Value |
|-------|-------|
| MediCheck metric | Worsening trajectory proportion |
| Numerator | patients with worsening Phase 4 trajectory |
| Denominator | patients with ≥2 assessments |
| Privacy threshold | k ≥ 10 |
| Methodology | Proportion of patients with a worsening MediCheck assessment trajectory (Phase 4 trend) |
| Limitations | Trajectory is an assessment trend, not disease progression |
| Unit | percent |

### sdg-3-4-screening-completion

| Field | Value |
|-------|-------|
| MediCheck metric | Assessment completion rate |
| Numerator | completed assessments |
| Denominator | started assessments |
| Privacy threshold | k ≥ 10 |
| Methodology | Completed / started assessments in the period |
| Limitations | Completion proxy; excludes abandoned sessions |
| Unit | percent |

### sdg-3-4-referral-rate

| Field | Value |
|-------|-------|
| MediCheck metric | Referral rate among screened |
| Numerator | distinct patients referred |
| Denominator | distinct patients screened |
| Privacy threshold | k ≥ 10 |
| Methodology | Distinct patients referred / distinct patients screened in the period |
| Limitations | Referral eligibility is CMS-controlled; not all flagged patients are referred |
| Unit | percent |

## SDG 3.8 — Universal Health Coverage

### sdg-3-8-screening-coverage

| Field | Value |
|-------|-------|
| MediCheck metric | Assessments initiated |
| Numerator | total assessments initiated |
| Denominator | — (count) |
| Privacy threshold | k ≥ 10 |
| Methodology | Total assessments initiated in the period |
| Limitations | Access proxy; not population coverage |

### sdg-3-8-referral-completion

| Field | Value |
|-------|-------|
| MediCheck metric | Referral completion rate |
| Numerator | patients with a `care_received` outcome |
| Denominator | patients referred |
| Privacy threshold | k ≥ 10 |
| Methodology | Distinct patients with a care_received outcome / distinct patients referred |
| Limitations | Outcome is operational; does not confirm diagnosis was treated |
| Unit | percent |

### sdg-3-8-time-to-care

| Field | Value |
|-------|-------|
| MediCheck metric | Median time-to-care |
| Numerator | — |
| Denominator | — |
| Privacy threshold | k ≥ 10 |
| Methodology | Median days from referral creation to first care_received outcome (per patient, earliest) |
| Limitations | Suppressed if cohort < k. Excludes negative/invalid deltas |
| Unit | days |

### sdg-3-8-care-funnel

| Field | Value |
|-------|-------|
| MediCheck metric | Care-continuity funnel |
| Methodology | screened → flagged → referred → referral_received → appointment_scheduled → care_received → followup_completed |
| Limitations | Each stage is k-anonymity-suppressed independently |

### sdg-3-8-language-accessibility

| Field | Value |
|-------|-------|
| MediCheck metric | Voice intake adoption |
| Numerator | voice intake sessions |
| Denominator | total sessions |
| Privacy threshold | k ≥ 10 |
| Methodology | Voice intake sessions / total sessions (Phase 5 accessibility) |
| Limitations | Language selection is an interaction metric; do not infer demographics |
| Unit | percent |

### sdg-3-8-chw-assisted-assessments

| Field | Value |
|-------|-------|
| MediCheck metric | CHW-assisted completion rate |
| Numerator | CHW-assisted referrals reaching care_received |
| Denominator | CHW-assisted referrals |
| Privacy threshold | k ≥ 10 |
| Methodology | CHW-assisted referrals reaching care_received / CHW-assisted referrals |
| Limitations | Operational completion; not clinical outcome |
| Unit | percent |

## SDG 10 — Reduced Inequalities

### sdg-10-completion-equity

| Field | Value |
|-------|-------|
| MediCheck metric | Languages with sufficient data |
| Numerator | intake languages with ≥ k data |
| Denominator | — (count) |
| Privacy threshold | k ≥ 10 |
| Methodology | Number of intake languages with sufficient data (equity proxy) |
| Limitations | Availability proxy; completion-rate differences require ≥ k per language cohort |

### sdg-10-modality-equity

| Field | Value |
|-------|-------|
| MediCheck metric | Voice vs text adoption |
| Numerator | voice sessions |
| Denominator | total sessions |
| Privacy threshold | k ≥ 10 |
| Methodology | Voice vs text modality adoption (accessibility equity proxy) |
| Limitations | Modality adoption is not demographic equity. Geographic equity requires aggregated geo data |
| Unit | percent |

## Official vs Proxy

All metrics above are **MediCheck-aligned proxies** (`indicator_type =
"medicheck-aligned-proxy"`). MediCheck does **not** claim any of these are
official UN SDG indicators. They are SDG-aligned operational proxies intended
to support health-system planning and research, with documented methodology
and limitations for every metric.

## Privacy Model

- All outputs are de-identified: no user_id, email, session_id, or patient
  identifier appears in any SDG row.
- Small-cell suppression (k ≥ 10) is applied per metric and per funnel stage.
- Suppressed cohorts return `null` values + `suppression_status = "suppressed"`.
- Suppression cannot be bypassed via filters, narrow ranges, individual
  dimensions, or endpoint combination.
