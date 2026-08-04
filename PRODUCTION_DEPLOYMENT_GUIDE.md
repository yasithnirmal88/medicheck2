# Medicheck Production Deployment Guide

## Overview

This guide provides a complete production deployment workflow for the Medicheck Healthcare Platform.

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MEDICHECK PLATFORM                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐   │
│  │   VERCEL    │         │   RENDER    │         │   RENDER    │   │
│  │  Frontend   │ ──────▶ │ Backend API │ ──────▶ │ PostgreSQL  │   │
│  │  (Static)   │  HTTPS  │  (FastAPI)  │         │  Database   │   │
│  └─────────────┘         └─────────────┘         └─────────────┘   │
│                                │                                    │
│                                │                                    │
│                                ▼                                    │
│                          ┌─────────────┐                            │
│                          │   RENDER    │                            │
│                          │    Redis    │                            │
│                          │   (Cache)   │                            │
│                          └─────────────┘                            │
│                                │                                    │
│                                ▼                                    │
│                          ┌─────────────┐                            │
│                          │  FIREBASE   │                            │
│                          │   Auth      │                            │
│                          └─────────────┘                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Order

### Phase 1: Infrastructure Setup

1. **Render PostgreSQL** - Create database
2. **Render Redis** - Create cache service
3. **Verify connections** - Test infrastructure

### Phase 2: Backend Deployment

4. **Deploy Backend to Render**
5. **Run migrations** - Alembic setup
6. **Verify health endpoint** - `/api/v1/health`
7. **Configure environment variables** - Firebase, secrets

### Phase 3: Frontend Deployment

8. **Update API URL** - Point to Render backend
9. **Deploy Frontend to Vercel**
10. **Configure environment variables** - Firebase, API URL

### Phase 4: Integration Testing

11. **Test authentication flow**
12. **Test API endpoints**
13. **Test CORS configuration**
14. **Test end-to-end workflows**

---

## Part 1: Render Backend Setup

### Step 1.1: Create Render Account & Blueprint

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Create a new Blueprint or connect your Git repository
3. Import `backend/render.yaml`

### Step 1.2: Configure Environment Variables

Set these in Render Dashboard → Your Service → Environment:

| Variable | Value | Notes |
|----------|-------|-------|
| `ENVIRONMENT` | `production` | |
| `SECRET_KEY` | Generate strong key | Use `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `FIREBASE_PROJECT_ID` | Your Firebase project ID | |
| `FIREBASE_CLIENT_EMAIL` | Firebase service account email | |
| `FIREBASE_PRIVATE_KEY` | Firebase private key | Include newlines as `\n` |
| `CORS_ORIGINS` | See below | |
| `ALLOWED_HOSTS` | See below | |

### CORS Origins (Update for your deployment)

```bash
CORS_ORIGINS=https://your-app.vercel.app,https://*.vercel.app,http://localhost:3000,http://localhost:5173
```

### Allowed Hosts

```bash
ALLOWED_HOSTS=your-backend.onrender.com,.onrender.com
```

### Step 1.3: Create PostgreSQL Database

1. In Render Dashboard → Create New → PostgreSQL
2. Configure:
   - Name: `medicheck-db`
   - Plan: Starter (Free) or Standard
   - Region: Oregon (or closest to your users)
3. Copy the Internal Connection URL
4. In your backend service, add environment variable:
   - Key: `DATABASE_URL`
   - Value: (paste the connection string)

### Step 1.4: Create Redis Cache

1. In Render Dashboard → Create New → Redis
2. Configure:
   - Name: `medicheck-redis`
   - Plan: Starter (Free) or Standard
3. Copy the Connection String
4. In your backend service, add environment variable:
   - Key: `REDIS_URL`
   - Value: (paste the connection string)

### Step 1.5: Deploy Backend

1. Trigger manual deploy or push to main branch
2. Monitor deployment logs
3. Verify health endpoint: `https://your-backend.onrender.com/api/v1/health`

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production",
  "db_status": "healthy",
  "redis_status": "healthy"
}
```

---

## Part 2: Vercel Frontend Setup

### Step 2.1: Create Vercel Account & Import Project

1. Go to [Vercel Dashboard](https://vercel.com)
2. Import your Git repository
3. Select the `frontend` directory as root

### Step 2.2: Configure Framework

Vercel should auto-detect Vite. Verify settings:
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

### Step 2.3: Configure Environment Variables

Add these in Vercel Dashboard → Project → Settings → Environment Variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `VITE_FIREBASE_API_KEY` | Your Firebase API key | |
| `VITE_FIREBASE_AUTH_DOMAIN` | `your-project.firebaseapp.com` | |
| `VITE_FIREBASE_PROJECT_ID` | Your Firebase project ID | |
| `VITE_API_BASE_URL` | `https://your-backend.onrender.com/api/v1` | Your Render backend URL |

### Step 2.4: Deploy Frontend

1. Deploy to Preview (for testing)
2. Verify all features work
3. Deploy to Production

---

## Part 3: Firebase Configuration

### Step 3.1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create new project or select existing
3. Note your Project ID

### Step 3.2: Enable Authentication

1. In Firebase Console → Authentication → Sign-in method
2. Enable:
   - Email/Password
   - Google (optional)

### Step 3.3: Get Firebase Config for Frontend

1. Go to Project Settings → General
2. Scroll to "Your apps"
3. Click "Add app" → Web
4. Copy the configuration values:
   - `apiKey`
   - `authDomain`
   - `projectId`

### Step 3.4: Get Firebase Admin SDK for Backend

1. Go to Project Settings → Service accounts
2. Click "Generate new private key"
3. Copy the JSON content

Backend environment variables:
```
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n
```

---

## Part 4: CORS Configuration

### Backend CORS Settings

In your Render backend, set `CORS_ORIGINS`:

```bash
CORS_ORIGINS=https://your-frontend.vercel.app,https://*.vercel.app,http://localhost:3000,http://localhost:5173
```

### Allowed Origins Explained

| Origin | Purpose |
|--------|---------|
| `https://your-frontend.vercel.app` | Your production Vercel domain |
| `https://*.vercel.app` | All Vercel preview deployments |
| `http://localhost:3000` | Local frontend development |
| `http://localhost:5173` | Local Vite dev server |

### Update for Your Domains

Replace `your-frontend.vercel.app` with your actual Vercel deployment URL.

---

## Part 5: Security Checklist

### Environment Variables

- [ ] `SECRET_KEY` - Strong random key (64+ characters)
- [ ] `FIREBASE_PRIVATE_KEY` - Service account key
- [ ] Database password - Strong password
- [ ] Redis password - Strong password

### Security Headers

- [ ] `ENABLE_SECURITY_HEADERS=true`
- [ ] `HSTS_MAX_AGE=31536000` (1 year)
- [ ] CORS configured with specific origins

### Authentication

- [ ] `ALLOW_MOCK_AUTH=false`
- [ ] Firebase credentials configured
- [ ] Firebase Admin SDK verified

### Rate Limiting

- [ ] `RATE_LIMIT_MAX_REQUESTS=100`
- [ ] `RATE_LIMIT_WINDOW_SECONDS=60`

---

## Part 6: Production Verification

### Backend Health Check

```bash
curl https://your-backend.onrender.com/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production",
  "db_status": "healthy",
  "redis_status": "healthy"
}
```

### API Documentation

Access Swagger UI:
```
https://your-backend.onrender.com/api/v1/docs
```

### Test Authentication

```bash
curl -X POST https://your-backend.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"firebase_token": "test-token"}'
```

### Frontend Verification

1. Open your Vercel deployment URL
2. Test login with Firebase
3. Verify API calls succeed
4. Check browser console for errors

---

## Troubleshooting

### Backend Issues

#### 502 Bad Gateway
- Check if the service is running
- Verify environment variables are set
- Check deployment logs

#### Database Connection Failed
- Verify `DATABASE_URL` is set
- Check PostgreSQL is accessible
- Verify connection string format

#### Firebase Not Working
- Check `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY`
- Verify Firebase Admin SDK initializes
- Check service account permissions

### Frontend Issues

#### API Calls Failing
- Verify `VITE_API_BASE_URL` points to correct backend
- Check CORS headers in response
- Verify backend is accessible

#### Authentication Not Working
- Verify Firebase config matches frontend
- Check Firebase console for errors
- Verify CORS allows frontend origin

#### 404 on Page Refresh
- This should not happen with Vercel's SPA handling
- Verify `vercel.json` has `framework: "vite"`

---

## Rollback Procedures

### Backend Rollback

1. In Render Dashboard → Your Service → Deployments
2. Find the last working deployment
3. Click "Download" → "Redeploy"

### Frontend Rollback

1. In Vercel Dashboard → Deployments
2. Find the last working deployment
3. Click "..." → "Promote to Production"

### Database Rollback

1. Use Alembic to downgrade:
   ```bash
   alembic downgrade -1
   ```

---

## Monitoring

### Backend Logs

In Render Dashboard → Your Service → Logs

### Metrics

- Response times
- Error rates
- Database connections
- Redis cache hit rates

### Alerts

Set up alerts for:
- High error rates (>5%)
- Slow response times (>2s)
- Database connection failures

---

## Performance Optimization

### Backend

- Connection pooling: 20 connections
- Redis caching enabled
- GZip compression enabled
- Async SQLAlchemy

### Frontend

- Code splitting enabled
- Vendor chunks separated
- Minification enabled
- No source maps in production

---

## Support

For issues, check:
1. Backend deployment logs
2. Vercel deployment logs
3. Browser console
4. Network tab for failed requests

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-08-04 | 1.0.0 | Initial production deployment guide |
