# Rollback Checklist

**Version**: 1.0.0-RC1

## When to Rollback

Rollback is triggered when:
1. Critical bug found in production (P1 severity)
2. Security vulnerability discovered
3. Data corruption detected
4. Performance regression beyond acceptable threshold
5. Failed deployment (health check fails, critical endpoints down)

## Immediate Actions (First 5 Minutes)

### 1. Stop Deployment
- [ ] Stop incoming traffic: Remove backend from load balancer
- [ ] Verify rollback trigger: Confirm severity and scope
- [ ] Notify team: Post in incident channel

### 2. Assess Impact
- [ ] How long has the bad version been deployed?
- [ ] How many users affected?
- [ ] Is data corrupted or just user experience?
- [ ] Can we fix forward or must roll back?

## Rollback Execution

### Database Rollback

```bash
# Option A: Alembic downgrade (if schema changed)
cd backend
alembic downgrade -1   # downgrade one revision

# Option B: Full database restore (if data corrupted)
pg_restore -U postgres -d medicheck -F custom /backups/medicheck_latest.dump
alembic upgrade head   # bring migrations back to current state
```

### Application Rollback

```bash
# Docker Compose (tagged images)
docker-compose stop api ui
docker-compose -f docker-compose.yml -f docker-compose.rollback.yml up -d

# Docker Swarm
docker service update --image medicheck-api:<previous-tag> medicheck_api
docker service update --image medicheck-ui:<previous-tag> medicheck_ui

# Manual
# 1. Revert backend to previous version
git checkout <previous-tag> -- backend/
# 2. Rebuild and deploy
docker build -f backend/Dockerfile -t medicheck-api:<previous-tag> .
docker-compose up -d api
# 3. Revert frontend
git checkout <previous-tag> -- frontend/
docker build -f frontend/Dockerfile -t medicheck-ui:<previous-tag> .
docker-compose up -d ui
```

### Redis Rollback

```bash
# Option A: Flush all (cache only, no persistent data)
redis-cli FLUSHALL

# Option B: Restore from RDB
systemctl stop redis
cp /backups/redis_<pre-deploy-date>.rdb /var/lib/redis/dump.rdb
systemctl start redis
```

## Verification (After Rollback)

### Critical Checks
- [ ] `GET /api/v1/health` returns 200 with all services green
- [ ] Patient questionnaire flow works end-to-end
- [ ] Doctor can generate report
- [ ] Auth endpoints work (register, login, token verification)
- [ ] No error rate spike in monitoring

### Secondary Checks
- [ ] Knowledge graph search works
- [ ] CMS create/edit content works
- [ ] Admin audit logs accessible
- [ ] Publishing workflow functional

## Post-Rollback

### Communication
- [ ] Notify affected users (if any)
- [ ] Document incident in post-mortem
- [ ] Update status page

### Investigation
- [ ] Determine root cause
- [ ] Create fix with tests
- [ ] Run full regression suite
- [ ] Deploy fix through normal CI/CD pipeline

### Cleanup
- [ ] Remove rollback images if disk space concern
- [ ] Update Known Issues if applicable
- [ ] Update rollback procedure if gaps found

## Rollback History

| Date | Version Rolled Back | Version Rolled To | Reason | Duration |
|------|--------------------|-------------------|--------|----------|
| | | | | |

## Key Contacts

- **Primary On-Call**: [Contact]
- **Database Admin**: [Contact]
- **Security Lead**: [Contact]
- **Medical Director**: [Contact]
