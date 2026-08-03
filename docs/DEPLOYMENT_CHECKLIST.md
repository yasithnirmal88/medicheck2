# Deployment Checklist

**Version**: 1.0.0-RC1
**Date**: 2026-07-23

## Pre-Deployment

### Environment Configuration
- [ ] `.env.production` configured with production values
- [ ] `DATABASE_URL` points to production PostgreSQL
- [ ] `REDIS_URL` configured with password
- [ ] `SECRET_KEY` is a 64-char random string
- [ ] `ENVIRONMENT=production`
- [ ] Firebase service account JSON secured
- [ ] `CORS_ORIGINS` restricted to known domains
- [ ] `ALLOWED_HOSTS` configured

### Database
- [ ] PostgreSQL 16+ running and accessible
- [ ] Database created: `createdb medicheck`
- [ ] Migrations run: `alembic upgrade head`
- [ ] Seed data loaded: `python -m app.infrastructure.seed`
- [ ] Backup configured: daily pg_dump + WAL archiving
- [ ] Connection pooling configured (pgbouncer)

### Redis
- [ ] Redis 7+ running and accessible
- [ ] Password configured
- [ ] Persistence enabled (RDB/AOF)

### Infrastructure
- [ ] Docker images built and tagged
- [ ] Docker Compose file reviewed
- [ ] Nginx config verified (reverse proxy, SSL)
- [ ] SSL certificates obtained and configured
- [ ] Firewall rules applied (80, 443, 5432, 6379 restricted)

## Deployment

### Application
- [ ] Backend containers started
- [ ] Frontend containers started
- [ ] Nginx started
- [ ] Health check passes: `GET /api/v1/health`
- [ ] Auth endpoint works: `POST /api/v1/auth/register`
- [ ] Seed data verified in database

### Monitoring
- [ ] Prometheus configured and scraping
- [ ] Grafana dashboards imported
- [ ] Health check alerts configured
- [ ] Logging level set to WARNING

### Security
- [ ] Rate limiting enabled (100 req/60s)
- [ ] Security headers verified (CSP, HSTS, X-Frame-Options)
- [ ] CSRF protection enabled
- [ ] Firebase token verification working
- [ ] RBAC permissions verified for all roles

## Post-Deployment

### Verification
- [ ] Patient can complete questionnaire
- [ ] Doctor can view assessment and generate report
- [ ] CMS editor can create/edit content
- [ ] Publishing workflow works (change request → approve → snapshot)
- [ ] Admin can view audit logs
- [ ] Knowledge graph search works
- [ ] Report generation and comparison works

### Smoke Tests
- [ ] All 11 UAT workflows pass
- [ ] All 156 regression tests pass
- [ ] API endpoints respond correctly
- [ ] Error responses are structured (not stack traces)

### Documentation
- [ ] API reference available
- [ ] Administrator guide shared
- [ ] Doctor guide shared
- [ ] Developer guide shared
- [ ] Troubleshooting guide available
- [ ] Backup/recovery procedures documented

## Rollback Preparation
- [ ] Previous version Docker images tagged
- [ ] Database backup verified
- [ ] Rollback script reviewed
- [ ] Rollback checklist accessible
