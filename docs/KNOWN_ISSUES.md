# Known Issues Report

**Version**: 1.0.0-RC1
**Date**: 2026-07-23

## Open Issues

### P1 — Critical (0)

None.

### P2 — High (1)

| ID | Description | Component | Workaround | Target |
|----|-------------|-----------|------------|--------|
| KNW-001 | `datetime.utcnow()` deprecation warnings across multiple files (admin_service.py, knowledge_graph_service.py, test files) | Application/Infrastructure | Replace with `datetime.now(UTC)` | RC2 |

### P3 — Medium (2)

| ID | Description | Component | Workaround | Target |
|----|-------------|-----------|------------|--------|
| KNW-002 | Negative score percentages not clamped to 0 — a net-negative score produces a negative percentage in scoring engine | Questionnaire Engine | No clinical scenario currently produces negative scores; cosmetic only | RC2 |
| KNW-003 | Test database (SQLite) doesn't test PostgreSQL-specific features (JSONB, full-text search) | Testing | PostgreSQL-specific features not used in current release | v1.1 |

### P4 — Low (3)

| ID | Description | Component | Workaround | Target |
|----|-------------|-----------|------------|--------|
| KNW-004 | Seed data does not include all 29 clinical indicators in every test environment | Seed Data | Run `python -m app.infrastructure.seed` before testing | v1.1 |
| KNW-005 | API rate limit (100/60s) not configurable per-role | API/Security | Limit applies globally | v1.1 |
| KNW-006 | No automated UI/E2E tests for frontend | Testing | Manual testing required for frontend | v1.1 |

## Resolved Issues (This Release)

| ID | Description | Component | Fix |
|----|-------------|-----------|-----|
| MED-001 | `max_possible` only counted scores >0, inflating percentages | Scoring Engine | Changed to unconditional weight addition |
| MED-002 | Raw SQL in questionnaire_service.py (2 locations) | Questionnaire | Replaced with ORM `select()` / `update()` |
| MED-003 | Missing `create_body_system` in SQLAdminRepository | Admin | Added method |
| MED-004 | `changed_at` set to None in KnowledgeGraphService._audit() | Audit | Fixed to use `datetime.utcnow()` |
| MED-005 | Missing `datetime` import in knowledge_graph_service.py | Audit | Added import |
| MED-006 | RecommendationModel missing `key` in test data | Tests | Added `key` field |
| MED-007 | `list_audit` method missing from SQLAdminRepository | Admin | Added method |
| MED-008 | Recommendation CRUD missing from SQLAdminRepository | Admin | Added methods |
| MED-009 | Incorrect body system icons/codes in seed data | Seed | Fixed eye, mental, male, sexual systems |
| MED-010 | Missing validation rules on numeric/decimal questions | Seed | Added min/max bounds |
