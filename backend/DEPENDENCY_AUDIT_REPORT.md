# Backend Dependency Audit Report

**Date:** 2026-08-04  
**Purpose:** Fix Render deployment failure due to missing runtime dependencies

---

## Missing Production Dependencies

### 🔴 CRITICAL - Missing from requirements.txt

| Package | Required By | Import Usage | Status |
|---------|-------------|--------------|--------|
| **email-validator** | Pydantic | `from pydantic import EmailStr` | ✅ ADDED |

### Implicit Dependencies (automatically installed)

| Package | Required By | Status |
|---------|-------------|--------|
| dnspython | email-validator | ✅ Auto-installed |
| idna | email-validator | ✅ Auto-installed |

---

## Dependency Analysis by Framework

### Pydantic
```
Used: BaseModel, Field, ConfigDict, field_validator, EmailStr
Required extras: None (email-validator for EmailStr)
Status: ✅ Complete
```

### SQLAlchemy
```
Used: ORM, AsyncSession, select, update, etc.
Required extras: [asyncio] (already included)
Status: ✅ Complete
```

### Alembic
```
Used: command, context, op, Config
Required extras: None
Status: ✅ Complete
```

### FastAPI
```
Used: APIRouter, Depends, FastAPI, Body, Query, etc.
Required extras: None (starlette auto-installed)
Status: ✅ Complete
```

### Uvicorn
```
Used: ASGI server
Required extras: [standard] (already included)
Status: ✅ Complete
```

### Firebase Admin
```
Used: auth, credentials, initialize_app
Required extras: google-auth (auto-installed with firebase-admin)
Status: ✅ Complete
```

### Celery
```
Used: Celery, shared_task
Required extras: [redis] (already included)
Status: ✅ Complete
```

### Redis
```
Used: Redis, ConnectionPool
Required extras: None
Status: ✅ Complete
```

---

## Verified Non-Required Packages

The following packages are NOT used in the codebase and do NOT need to be added:

| Package | Reason |
|---------|--------|
| passlib | Not used (Firebase handles auth) |
| bcrypt | Not used (Firebase handles auth) |
| Pillow | Not used (no image processing) |
| reportlab | Not used (no PDF generation) |
| fpdf | Not used (no PDF generation) |
| pytesseract | Not used (no OCR) |
| easyocr | Not used (no OCR) |

---

## Dockerfile Analysis

### System Packages
```
build-essential - ✅ Required for compiling Python packages
libpq-dev - ✅ Required for asyncpg (PostgreSQL driver)
curl - ✅ Required for healthcheck
postgresql-client - ✅ Useful for debugging
```

### Python Packages in Dockerfile
```
requirements.txt - ✅ Installed with --user flag
uvicorn[standard] - ✅ Explicitly installed
gunicorn - ✅ Explicitly installed
```

---

## Updated requirements.txt

The following changes were made:

```diff
# Core dependencies
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy[asyncio]>=2.0.30
asyncpg>=0.29.0
alembic>=1.13.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
firebase-admin>=6.5.0
python-jose[cryptography]>=3.3.0
celery[redis]>=5.4.0
redis>=5.0.0
httpx>=0.27.0
python-multipart>=0.0.9
aiofiles>=24.1.0
python-dotenv>=1.0.1
+email-validator>=2.1.0

# Development dependencies
pytest>=8.3.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
ruff>=0.5.0
mypy>=1.10.0
```

---

## Verification Steps

1. ✅ All imports scanned across 100+ Python files
2. ✅ Compared against requirements.txt
3. ✅ Framework dependencies verified
4. ✅ Dockerfile system packages verified
5. ✅ Non-required packages identified
6. ✅ Missing dependencies added

---

## Next Steps for Deployment

1. Update requirements.txt (done ✅)
2. Push changes to GitHub
3. Trigger new Render deployment
4. Verify deployment succeeds

