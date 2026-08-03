# Troubleshooting Guide

## Common Issues

### Backend Won't Start

| Symptom | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError` | Missing dependencies | `pip install -r requirements.txt` |
| `Address already in use` | Port conflict | Change port or kill existing process: `netstat -ano | findstr :8000` |
| `Connection refused` to DB | Database not running | Start PostgreSQL: `pg_ctl start` |
| `FIREBASE_CREDENTIALS_PATH` error | Firebase config missing | Set env var or copy service account JSON |
| Alembic migration errors | Migration state mismatch | `alembic stamp head` then `alembic upgrade head` |

### Database Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| `NOT NULL constraint failed` | Missing required field | Check model schema for required columns |
| `UNIQUE constraint failed` | Duplicate key/code | Use unique values for key/code fields |
| `FOREIGN KEY constraint failed` | Referenced entity doesn't exist | Create referenced entity first |
| SQLite `database is locked` | Concurrent writes | Use PostgreSQL in production; SQLite for dev only |
| Migration conflicts | Branch merge issues | `alembic merge heads` to resolve |

### Authentication Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| 401 Unauthorized | Invalid or expired token | Refresh Firebase token |
| 403 Forbidden | Insufficient role/permissions | Check RBAC assignments |
| Firebase token verification fails | Wrong project ID | Verify `FIREBASE_PROJECT_ID` in `.env` |
| Mock auth mode issues | Wrong mock behavior | Check `ENVIRONMENT` is set to `development` |

### CDSE / Clinical Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| No indicators activated | Questions not linked to indicators | Check `question_indicators` and `option_indicators` links |
| No conditions found | Indicators not linked to conditions | Check `indicator_conditions` links |
| Empty recommendations | Conditions not linked to recommendations | Check `condition_recommendations` links |
| Score = 0 | Questions not scored | Check scoring weights and answer score values |
| Abnormal severity | Incorrect thresholds | Check `severity_thresholds` table |

### CMS / Admin Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Audit log not created | `changed_at` is None | Use `datetime.utcnow()` in `_audit()` |
| Body system creation fails | Missing `create_body_system` in repo | Add method to `SQLAdminRepository` |
| Recommendation save fails | Missing `key` field | Include unique `key` in recommendation data |
| Entity expects dict not object | Service uses dict interface | Pass dict, not entity (`.to_dict()`) |

### Redis Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| `ConnectionError` to Redis | Redis not running | Start Redis server: `redis-server` |
| Cache miss on every request | Redis unresponsive | Check `REDIS_URL`; system degrades gracefully |
| Stale cached data | TTL too long | Reduce `CACHE_TTL` in settings |

## Debugging Tips

### Enable Debug Logging

```python
# In .env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### Check Health Endpoint

```bash
curl http://localhost:8000/api/v1/health
```

Response includes DB, Redis, and Firebase status.

### Inspect Database

```bash
# SQLite
sqlite3 backend/test.db
.tables
SELECT * FROM clinical_indicators LIMIT 5;

# PostgreSQL
psql -U postgres -d medicheck
\dt
SELECT * FROM clinical_indicators LIMIT 5;
```

### Test Seed Data

```bash
cd backend
python -m app.infrastructure.seed
```

### Run Specific Tests

```bash
cd backend
py -3 -m pytest tests/test_uat.py -k "cms" -v
```

## Performance Issues

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| Slow endpoint responses | N+1 queries | Check for missing eager loading |
| High CPU usage | Missing indexes | Add database indexes for frequently queried columns |
| Memory growth | Unclosed sessions | Ensure `AsyncSession` is properly closed via context manager |
| Slow CDSE processing | Large number of links | Batch loading should keep it at O(7) queries |

## Getting Help

- Check existing documentation in `/docs/`
- Review code comments in the relevant module
- Check the test suite for usage examples
- Verify seed data is loaded correctly
