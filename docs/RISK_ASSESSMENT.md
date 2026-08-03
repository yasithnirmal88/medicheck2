# Risk Assessment

**Version**: 1.0.0-RC1
**Date**: 2026-07-23
**Overall Risk**: LOW

## Risk Matrix

| Risk | Probability | Impact | Score | Mitigation |
|------|------------|--------|-------|------------|
| Clinical decision error due to incorrect knowledge graph links | Low | Critical | Medium | All links verified in Phase 21 medical audit; deterministic rule-based engine (no AI black box); evidence traceability enforced |
| Data loss due to database failure | Low | High | Medium | Daily backups + WAL archiving; automated restore testing |
| Security breach via authentication bypass | Low | Critical | Medium | Firebase JWT verification; RBAC enforced at every endpoint; rate limiting; CSRF protection; security headers |
| Performance degradation under load | Low | Moderate | Low | Redis caching (300s TTL); batch-loaded CDSE (7 queries max); DB indexes on all foreign keys; middleware overhead measured |
| Dependency supply-chain attack | Low | High | Medium | Pinned requirements.txt; Docker multi-stage builds; regular dependency audits |
| Misconfiguration in production deployment | Low | High | Medium | Docker Compose with health checks; deployment checklist; CI/CD pipeline validation; rollback script available |
| Inaccurate scoring due to scoring engine bug | Very Low | Critical | Low | 16 unit tests covering scoring; UAT confirms correct behavior; Phase 21 medical audit validated scores |
| CMS content editor error corrupting clinical data | Low | Moderate | Low | Publishing workflow with change requests + approvals; version snapshots; audit logging; soft delete |
| Firebase service outage preventing authentication | Low | High | Medium | Auth service handles token verification; cached user sessions; mock auth for development |
| Redis outage degrading performance | Low | Moderate | Low | Cache service degrades gracefully (logs warning, returns None); all queries fall back to database |

## Risk Response Plan

### Clinical Decision Errors (P1)
- **Detection**: CDSE trace IDs in every recommendation; audit trail captures all processing
- **Response**: Immediate content freeze; medical director reviews knowledge graph links; hotfix deployed
- **Recovery**: Rollback to last known good knowledge graph snapshot

### Data Loss (P1)
- **Detection**: Monitoring alerts on database health; backup verification failures
- **Response**: Restore from latest backup + WAL (RPO < 1 hour, RTO < 30 min)
- **Recovery**: Point-in-time recovery procedure documented

### Security Breach (P1)
- **Detection**: Rate limit alerts; audit log anomalies; Firebase security monitoring
- **Response**: Revoke compromised tokens; isolate affected services; forensic analysis
- **Recovery**: Rotate all credentials; restore from clean backup

## Compliance Considerations

- **HIPAA**: Audit logging captures all PHI access; soft delete preserves records; access controls enforce minimum privilege
- **GDPR**: User data export available; account deletion includes data erasure; consent tracking
- **Medical Device Regulations**: System is a clinical decision support tool (not a diagnostic device); all recommendations include evidence level and traceability

## Risk Acceptance

The following risks are accepted by the project team:

1. **False negatives in clinical screening**: The CDSE may not detect conditions with weak indicator linkage. Mitigated by evidence level visibility and medical director oversight.
2. **SQLite in testing not matching PostgreSQL behavior**: No PostgreSQL-specific features used; type mapping is consistent across databases.
3. **No automated UI testing**: Frontend testing is manual for RC1; automated E2E tests planned for v1.1.
