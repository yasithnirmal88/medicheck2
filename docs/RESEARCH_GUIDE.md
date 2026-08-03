# Research Guide

## Overview

The Research module provides tools for exploring medical knowledge, analyzing assessment data, and understanding clinical relationships through the knowledge graph.

## Knowledge Graph

The knowledge graph maps the complete clinical ontology:

```
Questions → Indicators → Conditions → Recommendations
                              ↓
                         Lab Tests
Indicators → Evidence
```

### Graph Traversal

Search and navigate the knowledge graph:

```
Research → Knowledge Graph
```

**Search by**:
- Body system
- Indicator key or name
- Condition (ICD-10 code or name)
- Recommendation
- Lab test (LOINC code)
- Evidence reference

**Navigation**:

From any node, you can traverse to connected nodes:
- From an indicator: see linked conditions, evidence, and questions
- From a condition: see linked indicators, recommendations, and lab tests
- From a recommendation: see linked conditions and evidence levels

### Graph Statistics

```
Research → Knowledge Graph → Statistics
```

- Total indicators, conditions, recommendations, lab tests
- Link density (average connections per node)
- Body system coverage
- Evidence level distribution

## Data Analysis

### Assessment Trends

```
Research → Analytics → Assessments
```

- Assessment volume over time
- Severity distribution
- Common activated indicators
- Most frequent conditions

### Questionnaire Analytics

```
Research → Analytics → Questionnaires
```

- Completion rates
- Question response distributions
- Drop-off analysis
- Time-to-complete statistics

### Report Analysis

```
Research → Analytics → Reports
```

- Report generation volume
- Recommendation frequency
- Evidence level usage
- Body system score distributions

## Export Capabilities

- **Graph export**: Export knowledge graph subsets as JSON
- **Data export**: Export anonymized assessment data for research
- **Report export**: Export reports as JSON or PDF

## API Access

Research tools are also available via API:

```bash
# Search knowledge graph
GET /api/v1/graph/search?q=diabetes

# Get graph statistics
GET /api/v1/graph/stats

# List indicators by body system
GET /api/v1/cms/knowledge-graph/indicators?body_system_id=CARDIO

# Export graph data
GET /api/v1/graph/export?format=json
```

## FAQ

**Q: Can I export data for external research?**
A: Yes, anonymized assessment data can be exported. All PHI is removed automatically.

**Q: How current is the medical knowledge?**
A: The knowledge base is maintained by medical editors and reviewed before publication. Each update creates a version snapshot.

**Q: Can I trace a recommendation back to its source evidence?**
A: Yes. Every recommendation has a linked evidence chain: recommendation → condition → indicator → evidence.
