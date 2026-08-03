# Modules, Security, Deployment & Roadmap

*This document covers Deliverables 17-28: Dashboard, Doctor CMS, Research Portal, Notifications, Health Timeline, File Storage, Security, Deployment, Scalability, Mobile, AI Future, Development Roadmap.*

---

# 17. Dashboard Architecture

## 17.1 Dashboard Data Model

```
Dashboard is NOT a stored entity — it is a computed aggregate of:
  - Latest assessment (health_score, risk_level)
  - All body_system_scores from latest assessment
  - Last 12 months of health_scores (for trend chart)
  - Last 5 timeline events (for timeline preview)
  - Pending recommendations count
  - Unread notifications count
  - Latest lab report summary
  - Lifestyle data from user_profiles
  - Upcoming/suggested assessments
```

## 17.2 Dashboard API Design

```
GET /dashboard/overview
  Returns: {
    "overall_score": { "score": 78, "risk_level": "good", "trend": "improving" },
    "body_systems": [
      { "code": "cardiovascular", "name": "Cardiovascular", "score": 72,
        "risk_level": "fair", "trend": "stable" },
      ...
    ],
    "trends": {
      "labels": ["Jul","Aug","Sep",..."Jun"],
      "overall": [75, 73, 76, 78, ...],
      "systems": {
        "cardiovascular": [70, 68, 71, 72, ...],
        "kidney": [80, 81, 82, 83, ...]
      }
    },
    "lifestyle": {
      "smoking": "never",
      "exercise": "3x_week",
      "sleep": 7.5,
      "diet": "balanced",
      "bmi": 22.5
    },
    "lab_summary": {
      "recent": [{ "test": "Hemoglobin", "value": 14.2, "is_abnormal": false }],
      "abnormal_count": 0
    },
    "timeline_preview": [
      { "date": "2024-06-15", "type": "assessment", "title": "Health Assessment" },
      { "date": "2024-06-10", "type": "lab", "title": "Blood Work Results" }
    ],
    "pending_recommendations": 3,
    "unread_notifications": 2,
    "upcoming": ["Annual Health Assessment", "Eye Screening"]
  }

Caching:
  - Redis cache key: dashboard:{user_id}
  - TTL: 5 minutes (invalidated on assessment/lab/profile change)
  - TanStack Query: staleTime: 5min, cacheTime: 30min
```

## 17.3 Frontend Dashboard Components

```
DashboardPage
├── OverviewCards (row of stat cards)
│   ├── HealthScoreGauge          # Circular gauge 0-100
│   ├── RiskLevelBadge            # Color-coded risk level
│   ├── TrendIndicator            # Up/down/stable arrow
│   └── LastAssessmentDate
│
├── BodySystemGrid (2xN responsive grid)
│   └── BodySystemCard × 17       # Clickable → detail page
│       ├── SystemIcon
│       ├── SystemName
│       ├── ScoreBar
│       └── RiskLevelBadge
│
├── RiskTrendChart                # Recharts LineChart, 12-month
│
├── BottomGrid (2-column on desktop)
│   ├── Left Column
│   │   ├── LifestyleSummary      # Icons + values
│   │   └── LabSummaryTable       # Recent results, abnormal-highlighted
│   └── Right Column
│       ├── TimelinePreview        # 5 most recent events
│       └── RecommendationsPanel   # Top 3 pending, "View all" link
│
└── UpcomingAssessments            # Cards with "Start" button
```

---

# 18. Doctor CMS Architecture

## 18.1 CMS Purpose

Allow doctors (non-technical users) to manage all clinical content without writing code.

## 18.2 CMS Modules

```
┌────────────────────────────────────────────────────────────────┐
│                    DOCTOR CMS MODULES                           │
│                                                                │
│  1. Body System Manager                                        │
│     - View/edit body system metadata (name, icon, weight)     │
│     - Enable/disable systems                                  │
│     - Set scoring weights                                      │
│                                                                │
│  2. Question Manager                                           │
│     - CRUD questions (all types)                              │
│     - Multi-language text editor                              │
│     - Question preview (render as patient would see)          │
│     - Set scoring weights per question                         │
│     - Configure validation rules                              │
│     - Add/edit choices + choice weights                       │
│     - Add/edit dependencies (visual branching editor)         │
│     - Version history viewer                                  │
│     - Rollback to previous version                             │
│     - Activate/deactivate questions                           │
│                                                                │
│  3. Questionnaire Builder                                      │
│     - Compose questionnaires from available questions         │
│     - Drag-and-drop reordering                                │
│     - Section management                                      │
│     - Preview questionnaire as patient                        │
│     - Target audience settings                                │
│                                                                │
│  4. Risk Rule Manager                                          │
│     - Visual condition builder (field + operator + value)     │
│     - Score impact setting                                     │
│     - Risk level assignment                                    │
│     - Evidence reference attachment                            │
│     - Version history + rollback                              │
│     - A/B test rules (future)                                 │
│                                                                │
│  5. Recommendation Template Manager                            │
│     - Create/edit recommendation templates                    │
│     - Set trigger conditions                                   │
│     - Assign to body systems                                   │
│     - Multi-language content                                   │
│                                                                │
│  6. Content Locking                                            │
│     - Lock resource while editing (prevent conflicts)         │
│     - Auto-release on inactivity                              │
│     - View who is editing what                                 │
│                                                                │
│  7. Patient Finder                                             │
│     - Search patients by name/email                           │
│     - View patient health overview (read-only)                │
│     - View patient assessment history                         │
│     - Add doctor notes to patient record                      │
└────────────────────────────────────────────────────────────────┘
```

## 18.3 CMS Data Flow

```
CMS Frontend (Doctor):
  QuestionEditor.tsx
    ├── Fetches question via GET /cms/questions/{id}
    ├── User edits text, choices, dependencies
    ├── Auto-saves draft to local state (Zustand)
    ├── User clicks "Save" → PUT /cms/questions/{id}
    ├── Backend: version snapshot created automatically
    └── Backend: invalidates question cache

Branching Editor:
  ├── Visual tree view of dependencies
  ├── Drag from "source question" to "target question"
  ├── Select condition type + value
  └── Saves to question_dependencies table

Content Locking Flow:
  1. Doctor opens QuestionEditor → POST /cms/content/lock
  2. If locked by another → show "Being edited by Dr. Smith"
  3. On save → release lock automatically
  4. On close → POST /cms/content/unlock
  5. Heartbeat every 30s to keep lock alive
  6. Lock auto-expires after 15 minutes of inactivity
```

---

# 19. Research Portal Architecture

## 19.1 Purpose

Provide researchers with anonymized population health data for analysis while maintaining strict privacy controls.

## 19.2 Research Data Access

```
┌────────────────────────────────────────────────────────────────┐
│                    RESEARCH DATA PIPELINE                       │
│                                                                │
│  Step 1: Anonymization                                         │
│    - All PII stripped (name, email, phone, exact DOB → age)   │
│    - User IDs replaced with random research IDs                │
│    - Free-text fields excluded (notes, comments)               │
│    - Date fields shifted by random offset (date shifting)      │
│    - Audit log of all anonymized data access                   │
│                                                                │
│  Step 2: Aggregation                                           │
│    - Population-level statistics: mean, median, distribution   │
│    - Minimum cell size: 10 (hide small groups)                 │
│    - No individual-level data export without ethics approval   │
│                                                                │
│  Step 3: Export                                                │
│    - CSV, JSON, or Parquet formats                             │
│    - Asynchronous processing for large datasets                │
│    - Download link expires after 7 days                        │
│    - All exports logged with researcher ID                     │
└────────────────────────────────────────────────────────────────┘
```

## 19.3 Research Portal Features

```
Dashboard:
  - Total population count
  - Demographics distribution (age, gender, region)
  - Risk score distribution chart
  - Most common risk factors (word cloud / bar chart)
  - Body system health distribution

Cohort Builder:
  - Filter by: age range, gender, body system, risk level, lab values
  - Save cohorts for repeated access
  - Cohort size always shown (but not individual data)

Data Export:
  - Select data types: assessments, lab values, timeline events
  - Select time range
  - Select cohort (or all anonymized)
  - Submit → async processing → email when ready → download

Visualization:
  - Risk score distributions (histogram)
  - Trend analysis (population averages over time)
  - Correlation explorer (risk factors vs outcomes)
  - Geographic heat map (future)
```

---

# 20. Notification Architecture

## 20.1 Notification Types

| Type | Trigger | Channel | Priority |
|---|---|---|---|
| `assessment_ready` | Assessment calculation complete | In-app, Email | High |
| `lab_abnormal` | Abnormal lab value detected | In-app, Email | High |
| `abnormal_vital` | Abnormal vital sign reported | In-app, Email | High |
| `recommendation_due` | Upcoming recommendation deadline | In-app | Medium |
| `questionnaire_reminder` | Questionnaire incomplete > 48h | In-app, Email | Medium |
| `health_score_change` | Significant score change | In-app | Low |
| `weekly_summary` | Weekly health summary | Email | Low |
| `account_activity` | Login from new device | Email | High |
| `cms_content_update` | Content updated by doctor | In-app | Low |
| `system_announcement` | Platform announcements | In-app, Email | Medium |

## 20.2 Notification Backend Design

```
┌────────────────────────────────────────────────────────────────┐
│                   NOTIFICATION PIPELINE                         │
│                                                                │
│  Trigger Event:                                                │
│    Domain Event (e.g., AssessmentCompleted)                    │
│         │                                                       │
│         ▼                                                       │
│  Notification Service:                                         │
│    1. Check user preferences (which channels?)                 │
│    2. Create notification record in DB                        │
│    3. Enqueue delivery tasks:                                  │
│       - in_app: store in notifications table (polled by FE)   │
│       - email: enqueue to Celery → email worker               │
│       - push: enqueue to Celery → Firebase Cloud Messaging    │
│         (future PWA push)                                     │
│                                                                │
│  Delivery:                                                     │
│    In-App: Frontend polls GET /notifications every 60s        │
│            TanStack Query refetchIntervals: 60000             │
│            WebSocket for real-time (future)                   │
│                                                                │
│    Email: SendGrid / Resend transactional email API           │
│           Templates stored externally (SendGrid)              │
│           Batch: max 50 emails per batch                       │
│                                                                │
│    Push: Firebase Cloud Messaging (future PWA + mobile)       │
│           Requires FCM token from client                       │
└────────────────────────────────────────────────────────────────┘
```

## 20.3 Notification Preferences

```json
{
  "userId": "uuid",
  "channels": {
    "email": true,
    "in_app": true,
    "push": false
  },
  "subscriptions": {
    "assessment_ready": { "email": true, "in_app": true },
    "lab_abnormal": { "email": true, "in_app": true },
    "questionnaire_reminder": { "email": false, "in_app": true },
    "weekly_summary": { "email": true, "in_app": false },
    "marketing": false
  },
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00",
    "timezone": "America/New_York"
  }
}
```

---

# 21. Health Timeline Architecture

## 21.1 Timeline Design

```
The health timeline is an event-sourced chronological view of the user's health journey.

Event Sources:
  ┌────────────────────────────────────────────────────────────────┐
  │  Source                  │  Event Type        │  Data           │
  ├──────────────────────────┼────────────────────┼─────────────────┤
  │ Questionnaire completed  │ assessment         │ Score, summary  │
  │ Lab report added         │ lab                │ Test, value     │
  │ Medication added         │ medication          │ Drug, dosage    │
  │ Medication changed       │ medication_change   │ Old → new       │
  │ Symptom reported         │ symptom            │ Description     │
  │ Surgery recorded         │ surgery            │ Procedure       │
  │ Vaccination recorded     │ vaccination        │ Vaccine type    │
  │ Vital sign recorded      │ measurement        │ BP, HR, weight   │
  │ Manual entry             │ manual             │ User-defined     │
  │ Weight updated           │ measurement        │ Value           │
  │ Profile field changed    │ lifestyle_change   │ Old → new       │
  └────────────────────────────────────────────────────────────────┘
```

## 21.2 Timeline Storage

```
Two storage layers:

Layer 1: Raw Events (timeline_events table)
  - Append-only log of all health events
  - Partitioned by month
  - Indexed on (user_id, event_date DESC)

Layer 2: Aggregated View (for dashboard)
  - Materialized view or in-memory aggregation
  - Computed at query time via SQL aggregation
  - Cached in Redis for 5 minutes

Query Patterns:
  - Full timeline (paginated): SELECT * WHERE user_id = ? ORDER BY event_date DESC
  - By type: WHERE user_id = ? AND event_type_code = ?
  - By date range: WHERE user_id = ? AND event_date BETWEEN ? AND ?
  - Latest N: SELECT * WHERE user_id = ? ORDER BY event_date DESC LIMIT 5
  - Count by type: SELECT event_type_code, COUNT(*) GROUP BY event_type_code
```

## 21.3 Frontend Timeline Component

```
TimelinePage
├── TimelineFilter
│   ├── DateRangePicker
│   ├── EventTypeSelect (checkboxes: all | assessment | lab | medication | ...)
│   └── SearchInput (full-text search on titles)
│
└── TimelineView (vertical timeline layout)
    └── TimelineEvent × N
        ├── EventDateBadge (left column)
        ├── EventDot (connector line)
        └── EventCard (right column)
            ├── EventIcon (type-based)
            ├── EventTitle
            ├── EventDescription
            ├── EventValue (if numeric: "BP: 120/80")
            └── EventActions (view detail, delete if manual)

Infinite Scroll:
  - TanStack Query useInfiniteQuery with cursor-based pagination
  - Load 20 events per page
  - "Show more" button or auto-load on scroll
```

---

# 22. File Storage Architecture

## 22.1 Storage Structure

```
Supabase Storage (S3-compatible):

Buckets:
  medicheck-uploads/
    ├── avatars/
    │   └── {user_id}/
    │       └── profile.{ext}
    ├── lab-reports/
    │   └── {user_id}/
    │       └── {report_id}/
    │           ├── report.{ext}
    │           └── ocr-results.json (future)
    ├── medical-docs/
    │   └── {user_id}/
    │       └── {doc_id}.{ext}
    ├── exports/
    │   └── {user_id}/
    │       └── {export_id}.{ext}
    └── temp/
        └── {session_id}/
            └── {file}.{ext}  (auto-delete after 24h)

Access Control:
  - All buckets are private by default
  - Signed URLs generated by backend (expire in 1 hour)
  - URLs restricted to authenticated user or admin
  - Supabase RLS policies match application RBAC
```

## 22.2 Upload Flow

```
Client                        Backend                       Supabase Storage
  │                             │                             │
  │ 1. POST /files/upload       │                             │
  │   {filename, mime, size}    │                             │
  ├────────────────────────────▶│                             │
  │                             │ 2. Validate file            │
  │                             │    - MIME type whitelist    │
  │                             │    - Max size (10MB docs,   │
  │                             │      5MB images)            │
  │                             │    - Virus scan (ClamAV)    │
  │                             │                             │
  │                             │ 3. Generate signed URL      │
  │                             │    (POST with policy)       │
  │                             │                             │
  │   { signed_url, file_id }   │                             │
  │◀────────────────────────────┤                             │
  │                             │                             │
  │ 4. PUT file to signed URL   │                             │
  ├──────────────────────────────────────────────────────────▶│
  │                             │                             │
  │   File stored + checksum    │                             │
  │◀──────────────────────────────────────────────────────────┤
  │                             │                             │
  │ 5. POST /files/{id}/confirm │                             │
  ├────────────────────────────▶│                             │
  │                             │ 6. Verify checksum          │
  │                             │ 7. Create file_metadata row │
  │                             │ 8. If lab report → queue    │
  │                             │    OCR processing (future)  │
  │   File confirmed            │                             │
  │◀────────────────────────────┤                             │
```

## 22.3 File Processing Pipeline (Future)

```
Upload → Virus Scan (ClamAV) → Validate → [Conditional steps]:
                                         │
                              ┌──────────┴──────────┐
                              │                      │
                         Image File            Document File
                              │                      │
                              ▼                      ▼
                      ┌──────────────┐      ┌──────────────┐
                      │ Optimize     │      │ OCR Extract   │
                      │ - Resize     │      │ (Tesseract/  │
                      │ - WebP conv  │      │  AWS Textract)│
                      │ - Strip EXIF │      │ - Extract     │
                      └──────────────┘      │   values      │
                                            │ - Parse with  │
                                            │   LLM (future)│
                                            │ - Populate    │
                                            │   lab_report_ │
                                            │   values      │
                                            └──────────────┘
```

---

# 23. Security Architecture

## 23.1 Security Layers

```
┌────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS (Defense in Depth)           │
│                                                                │
│  Layer 1: Network Security                                     │
│  ├── All traffic via HTTPS (TLS 1.3, forced redirect)         │
│  ├── Vercel WAF (Web Application Firewall)                    │
│  ├── DDoS protection (Cloudflare or Vercel Firewall)          │
│  ├── CORS: whitelist of allowed origins                       │
│  └── Security headers: HSTS, CSP, X-Frame-Options, XSS-Protect│
│                                                                │
│  Layer 2: API Security                                         │
│  ├── Rate limiting: per-user, per-IP, per-endpoint            │
│  ├── Request validation: Pydantic models (all inputs)         │
│  ├── Idempotency keys: prevent duplicate mutations            │
│  ├── Body size limits: 1MB requests, 10MB file uploads        │
│  └── API keys: for future third-party integrations            │
│                                                                │
│  Layer 3: Authentication & Authorization                      │
│  ├── Firebase Auth: email/password + Google + Apple           │
│  ├── JWT token verification on every request (Firebase Admin) │
│  ├── Role-based access control (4 roles)                      │
│  ├── Resource-level permission checks                         │
│  └── Supabase RLS as defense-in-depth at DB level             │
│                                                                │
│  Layer 4: Data Security                                        │
│  ├── Encryption in transit: TLS 1.3                           │
│  ├── Encryption at rest: Supabase AES-256, server-side        │
│  ├── Field-level encryption: PII columns encrypted via pgcrypto│
│  ├── File encryption: Supabase Storage server-side encryption │
│  ├── Backup encryption: all backups encrypted                 │
│  └── Key management: Supabase managed keys (future: Vault)    │
│                                                                │
│  Layer 5: Application Security                                 │
│  ├── Input sanitization: XSS prevention in all user text      │
│  ├── SQL injection prevention: ORM (parameterized queries)    │
│  ├── CSRF: SameSite cookies, custom headers                   │
│  ├── Secure file upload: type validation, size limits, virus  │
│  ├── Dependency scanning: Dependabot + Snyk (CI/CD)           │
│  └── No secrets in code: all via environment variables        │
│                                                                │
│  Layer 6: Audit & Compliance                                   │
│  ├── Immutable audit logs: all PHI access logged              │
│  ├── Audit hash chain: SHA-256 verification                   │
│  ├── GDPR: right to access, right to erasure, data portability│
│  ├── HIPAA readiness: BAAs, access controls, audit controls   │
│  └── Incident response: documented runbooks                   │
└────────────────────────────────────────────────────────────────┘
```

## 23.2 Sensitive Data Handling

```
PII Fields requiring special handling:

Users table:
  - email: Deterministic encryption (for lookup) + hashed display
  - full_name: AES-256 encryption
  - phone: Deterministic encryption + partial mask in UI (*6789)

Health data:
  - date_of_birth: Store age (int) after user reaches 18, destroy exact DOB
  - medical_history.notes: AES-256 encryption at column level
  - user_responses.response_value: AES-256 encryption for free-text

Files:
  - All uploaded files encrypted at rest (S3 SSE-S3 or SSE-KMS)
  - File metadata in separate encrypted table
  - Signed URLs with 1-hour expiration

Logging:
  - Audit logs contain resource IDs but NOT PII values
  - Application logs scrub sensitive fields automatically
  - Error logs never include request bodies
```

## 23.3 Audit Log Chain

```
┌────────────────────────────────────────────────────────────────┐
│                 IMMUTABLE AUDIT LOG CHAIN                       │
│                                                                │
│  Each audit_log entry contains:                                │
│  - All event data (action, resource, user, timestamp)          │
│  - previous_hash: SHA-256 of the previous log entry            │
│  - immutable_hash: SHA-256(previous_hash || event_data)        │
│                                                                │
│  [Entry 1]                                                     │
│  previous_hash: null                                           │
│  immutable_hash: H(null || data1) → "abc123"                  │
│                                                                │
│  [Entry 2]                                                     │
│  previous_hash: "abc123"                                       │
│  immutable_hash: H("abc123" || data2) → "def456"              │
│                                                                │
│  [Entry 3]                                                     │
│  previous_hash: "def456"                                       │
│  immutable_hash: H("def456" || data3) → "ghi789"              │
│                                                                │
│  Verification: Re-compute chain from genesis.                  │
│  Mismatch = tampering detected.                                │
└────────────────────────────────────────────────────────────────┘
```

---

# 24. Deployment Architecture

## 24.1 Environment Strategy

```
┌────────────────────────────────────────────────────────────────┐
│                    ENVIRONMENTS                                 │
│                                                                │
│  Local (Developer Machine):                                    │
│  ├── Docker Compose: backend + worker + db + redis            │
│  ├── Supabase local (via CLI: supabase start)                 │
│  ├── Firebase Emulator Suite                                  │
│  ├── Vite dev server (HMR)                                    │
│  └── .env.local with local credentials                        │
│                                                                │
│  Development (shared):                                         │
│  ├── Vercel preview deployment (auto on PR)                   │
│  ├── Render web service (backend dev branch)                  │
│  ├── Supabase project (dev tier)                              │
│  ├── Firebase project (dev)                                   │
│  └── Seeded test data                                         │
│                                                                │
│  Staging (pre-production):                                     │
│  ├── Vercel production deployment (staging branch)            │
│  ├── Render web service (staging branch)                      │
│  ├── Supabase project (pro tier)                              │
│  ├── Firebase project (staging)                               │
│  ├── Load test environment                                    │
│  └── E2E tests run here                                        │
│                                                                │
│  Production:                                                    │
│  ├── Vercel production (main branch)                          │
│  ├── Render web service (main branch, auto-scale)             │
│  ├── Render worker (main branch, 2+ instances)                │
│  ├── Supabase project (pro tier, point-in-time recovery)      │
│  ├── Firebase project (production, MFA enabled)               │
│  ├── Custom domain: medicheck.com                             │
│  ├── CDN: Vercel Edge Network (global)                        │
│  └── Monitoring: Sentry + Render dashboard                    │
└────────────────────────────────────────────────────────────────┘
```

## 24.2 CI/CD Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE (GitHub Actions)              │
│                                                                │
│  On PR to main:                                                │
│  ───────────────                                               │
│  Job 1: Lint & Type Check                                     │
│    - backend: ruff, mypy                                      │
│    - frontend: eslint, tsc --noEmit                           │
│                                                                │
│  Job 2: Test                                                  │
│    - backend: pytest (unit + integration)                     │
│    - frontend: vitest (unit + component)                      │
│    - coverage report                                          │
│                                                                │
│  Job 3: Build & Preview                                       │
│    - Build Docker images                                      │
│    - Deploy to Vercel preview                                 │
│    - Run Playwright E2E tests on preview                      │
│    - Comment preview URL on PR                                │
│                                                                │
│  On merge to main:                                             │
│  ──────────────────                                            │
│  Job 4: Deploy to Staging                                     │
│    - Build & push Docker images to registry                   │
│    - Deploy backend to Render (staging)                       │
│    - Deploy frontend to Vercel (staging)                      │
│    - Run integration tests against staging                    │
│    - Run load tests (k6)                                       │
│                                                                │
│  Job 5: Deploy to Production                                  │
│    - Manual approval gate                                      │
│    - Deploy backend to Render (production, blue/green)        │
│    - Deploy frontend to Vercel (production)                   │
│    - Run smoke tests                                          │
│    - Monitor error rates for 15 minutes                       │
│    - Rollback if error rate > 1%                              │
└────────────────────────────────────────────────────────────────┘
```

## 24.3 Docker Compose (Local Dev)

```yaml
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db, redis]
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/medicheck
      - REDIS_URL=redis://redis:6379/0
      - FIREBASE_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json
      - SUPABASE_URL=http://supabase:8000
      - SUPABASE_SERVICE_KEY=...
    volumes:
      - ./backend:/app
      - ~/.firebase-service-account.json:/app/firebase-service-account.json:ro

  worker:
    build: ./backend
    command: celery -A workers.celery_app worker -Q assessments,recommendations,notifications --loglevel=info
    depends_on: [db, redis]
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/medicheck
      - REDIS_URL=redis://redis:6379/0

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on: [api]
    environment:
      - VITE_API_URL=http://localhost:8000/api/v1
      - VITE_FIREBASE_CONFIG=...
    volumes:
      - ./frontend:/app

  db:
    image: postgres:16-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: medicheck
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  pgdata:
```

---

# 25. Scalability Strategy

## 25.1 Vertical Scaling (Initial)

| Component | Spec | Users Supported |
|---|---|---|
| API (Render) | 2 CPU, 4GB RAM | 5,000 concurrent |
| Worker (Render) | 2 CPU, 4GB RAM | 10,000 assessments/day |
| PostgreSQL (Supabase) | 4 CPU, 8GB RAM | 100,000 users |
| Redis (Upstash) | 256MB | 100,000 users (cache only) |

## 25.2 Horizontal Scaling (Growth)

```
┌────────────────────────────────────────────────────────────────┐
│                    HORIZONTAL SCALING                           │
│                                                                │
│  API Layer (Render):                                           │
│  ├── Render auto-scaling: 2-10 instances based on CPU         │
│  ├── Stateless: any instance handles any request              │
│  ├── Session data in Redis (not in-memory)                    │
│  └── Target: 500 req/s per instance                           │
│                                                                │
│  Worker Layer (Render):                                        │
│  ├── Scale workers independently per queue                    │
│  ├── assessments queue: high priority, 2-5 workers            │
│  ├── recommendations queue: medium, 2-3 workers               │
│  ├── notifications queue: low, 1-2 workers                    │
│  └── exports queue: low, 1 worker (elastic)                   │
│                                                                │
│  Database Layer (Supabase):                                    │
│  ├── Connection pooling: PgBouncer (Supabase managed)         │
│  ├── Read replicas: 1-3 replicas for dashboard/analytics     │
│  ├── Partitioning: time-based for timeline, audit, scores     │
│  └── Future: Citus (sharding) for 10M+ users                  │
│                                                                │
│  Cache Layer (Redis/Upstash):                                  │
│  ├── Read-through cache for frequently accessed data          │
│  ├── Cache dashboard results (5min TTL)                       │
│  ├── Cache questionnaire definitions (1hr TTL)                │
│  ├── Cache reference ranges (1hr TTL)                         │
│  ├── Invalidate on mutation (event-driven)                    │
│  └── Target: 95% cache hit rate                               │
│                                                                │
│  CDN Layer (Vercel Edge):                                      │
│  ├── Static assets: immutable, 1yr cache                      │
│  ├── API responses: cacheable GET endpoints (5min)            │
│  ├── Questionnaires: cache per body system                    │
│  └── Files: served via CDN with signed URLs                   │
└────────────────────────────────────────────────────────────────┘
```

## 25.3 Database Performance Targets

```
Query Performance:
  - p95 query time: < 50ms for indexed queries
  - p95 query time: < 200ms for complex dashboard aggregation
  - Write throughput: 500 writes/second (single PG instance)
  - Read throughput: 2000 reads/second (with replicas)

Optimization strategies:
  1. Index all foreign keys (already done in schema)
  2. Composite indexes for common query patterns (user_id + timestamp)
  3. Partial indexes for active-only queries (WHERE is_active)
  4. Materialized views for dashboard aggregation (refresh every 5min)
  5. JSONB GIN indexes for rule condition queries
  6. Connection pooling via PgBouncer (managed by Supabase)
  7. Query timeout: 30s (any query exceeding is killed and logged)
  8. Statement timeout: 15s for API queries, 120s for background workers
```

## 25.4 Caching Strategy

```
┌──────────────┬───────────────────────────────┬──────────┬──────────┐
│ Cache         │ Key Pattern                   │ TTL      │ Inval on │
├──────────────┼───────────────────────────────┼──────────┼──────────┤
│ Browser       │ Static assets (fingerprinted)│ 1 year   │ Build    │
│ CDN           │ API responses (GET)          │ 5 min    │ TTL exp  │
│ Redis (API)   │ questionnaire:{id}           │ 1 hour   │ CMS save │
│ Redis (API)   │ questions:body_system:{code} │ 1 hour   │ CMS save │
│ Redis (API)   │ body_system:list             │ 1 hour   │ CMS save │
│ Redis (API)   │ lab_tests:all                │ 1 hour   │ Admin    │
│ Redis (API)   │ ref_ranges:{test_id}         │ 1 hour   │ Admin    │
│ Redis (Dash)  │ dashboard:{user_id}          │ 5 min    │ Mutation │
│ Redis (Auth)  │ rate_limit:{key}             │ Window   │ TTL exp  │
│ Redis (Queue) │ celery:*                     │ Instant  │ Consumed │
│ App (RQ)      │ Query data (TanStack)        │ 5-30 min │ Manual   │
└──────────────┴───────────────────────────────┴──────────┴──────────┘
```

---

# 26. Future Mobile Integration

## 26.1 Mobile Strategy Phases

```
Phase 1: PWA (MVP - Month 1)
  ├── Full PWA via Vite PWA plugin + Workbox
  ├── Install prompt on mobile
  ├── Offline questionnaire support (IndexedDB)
  ├── Push notifications (Firebase Cloud Messaging)
  ├── Camera access for document upload
  └── Responsive design (mobile-first from day one)

Phase 2: React Native (Month 6-9)
  ├── Shared TypeScript types with web
  ├── Shared Zod validation schemas
  ├── Native navigation (React Navigation)
  ├── Biometric auth (Face ID / Fingerprint via expo-local-auth)
  ├── Apple HealthKit integration (steps, HR, sleep)
  ├── Google Fit integration
  ├── Push notifications (FCM native)
  └── Offline-first architecture (WatermelonDB)

Phase 3: Native SDK (Year 2+)
  ├── White-label SDK for hospital partners
  ├── EHR integration modules
  ├── Wearable device data ingestion
  └── IoT integration (BP monitors, glucometers)
```

## 26.2 API Compatibility

```
Mobile API Requirements:
  - Same REST API endpoints (no separate mobile API)
  - Smaller payloads via field selection (?fields=id,name,score)
  - Response compression (gzip/brotli)
  - Offline queue: POST/PATCH requests queued when offline
  - Conflict resolution: last-write-wins with timestamp comparison
  - Reduced image sizes: ?width=320 parameter on file URLs

React Native Shared Module:
  frontend/src/shared/  ← shared with React Native app
    ├── types/
    │   ├── api.ts              # API response types
    │   ├── user.ts             # User + profile types
    │   ├── questionnaire.ts    # Question, answer types
    │   ├── assessment.ts       # Score, risk types
    │   └── lab.ts              # Lab report types
    ├── validation/
    │   ├── auth.ts             # Zod schemas for auth forms
    │   ├── profile.ts          # Zod schemas for health profile
    │   └── questionnaire.ts    # Dynamic schema builder
    └── utils/
        ├── formatters.ts       # Date, number, health metric formatters
        └── constants.ts        # Body system codes, risk levels
```

---

# 27. Future AI Integration

## 27.1 AI/ML Roadmap

```
Phase 1 (Launch): Rule-Based
  ├── Configurable risk rules (Doctor CMS)
  ├── Transparent scoring with explanations
  ├── No ML training data required
  └── Immediate value

Phase 2 (Month 6-9): ML-Assisted Rules
  ├── Collect training data: all assessments + outcomes
  ├── Train XGBoost models per body system
  ├── ML suggests rule weights and thresholds
  ├── A/B test ML vs rule-based recommendations
  └── Doctor validates ML suggestions before deployment

Phase 3 (Month 12-18): Hybrid Engine
  ├── ML primary inference, rules as fallback
  ├── Per-body-system: Random Forest + Gradient Boosting
  ├── SHAP explanations for all predictions
  ├── Automated feature engineering pipeline
  └── Continuous model retraining (weekly)

Phase 4 (Month 18-24): Deep Learning
  ├── Transformer-based health trajectory prediction
  ├── LSTM models for time-series trend analysis
  ├── Autoencoder-based anomaly detection on lab values
  ├── Clustering for population health segmentation
  └── Personalized risk trajectories with confidence intervals

Phase 5 (Month 24+): LLM Integration
  ├── Natural language health insights generation
  ├── Conversational questionnaire (LLM-driven)
  ├── Automated answer consistency validation
  ├── Personalized recommendation generation
  ├── Doctor-facing clinical decision support
  └── AI-assisted question drafting (for CMS)
```

## 27.2 LLM Integration Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    LLM ORCHESTRATOR                             │
│                                                                │
│  Provider Abstraction:                                         │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  interface LLMProvider {                               │   │
│  │    complete(prompt: str, options: Options) → str      │   │
│  │  }                                                      │   │
│  │                                                         │   │
│  │  Implementations:                                       │   │
│  │  ├── OpenAIProvider (GPT-4 Turbo)                      │   │
│  │  ├── AnthropicProvider (Claude 3 Opus)                 │   │
│  │  ├── LocalProvider (Llama 3, for sensitive data)       │   │
│  │  └── MockProvider (deterministic responses for testing)│   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Prompt Management:                                            │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Templates stored in DB (prompt_templates table)       │   │
│  │  Versioned with content versions                       │   │
│  │  Variables: {{risk_scores}}, {{user_name}}, etc.       │   │
│  │  PII stripping: automated before sending               │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Safety:                                                       │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  ✓ All prompts reviewed & approved by clinical team    │   │
│  │  ✓ Output validation regex: no diagnostic claims       │   │
│  │  ✓ Rate limited: 100 LLM calls/user/day                │   │
│  │  ✓ Response caching: hash(input) → Redis               │   │
│  │  ✓ Audit log: every LLM call logged                    │   │
│  │  ✓ Fallback: rule-based when LLM unavailable           │   │
│  │  ✓ PII stripping: regex + NER before API call         │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

## 27.3 Feature Store Design (for ML)

```
┌────────────────────────────────────────────────────────────────┐
│                    FEATURE PIPELINE                              │
│                                                                │
│  Feature extraction (triggered on assessment completion):      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  For each body system:                                 │   │
│  │    - All question scores (numerical features)          │   │
│  │    - Derived metrics (BMI, BP category, etc.)          │   │
│  │    - Demographics (age, gender)                        │   │
│  │    - Temporal features (days since last assessment)    │   │
│  │    - Historical trends (score delta from last)         │   │
│  │    - Lab values (closest to assessment date)           │   │
│  │                                                         │   │
│  │  Features stored in: feature_store table                │   │
│  │    { assessment_id, user_id, features: JSONB }          │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Model Training:                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Labels: Actual health outcomes (collected over time)  │   │
│  │  Target: "Did user develop condition X within 1 year?" │   │
│  │  Model: XGBoost binary classifier per condition        │   │
│  │  Eval: AUC-ROC, Precision@K, calibration curve        │   │
│  │  Explain: SHAP values for each prediction              │   │
│  │  Deploy: ONNX format, served via FastAPI endpoint      │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

# 28. Development Roadmap

## 28.1 Phase Breakdown

```
PHASE 0: Foundation (Weeks 1-4)
  ┌────────────────────────────────────────────────────────────┐
  │  Week 1: Project Setup                                    │
  │    ├── Initialize monorepo (pnpm workspace)               │
  │    ├── Backend: FastAPI app factory, config, DI container │
  │    ├── Frontend: Vite + React + Tailwind + Shadcn setup   │
  │    ├── Supabase project setup + initial migration         │
  │    ├── Firebase project setup + SDK integration           │
  │    └── Docker Compose for local development               │
  │                                                           │
  │  Week 2: Core Auth + User Module                          │
  │    ├── Firebase Auth integration (email + Google)         │
  │    ├── User registration flow (Firebase → DB sync)       │
  │    ├── JWT verification middleware                        │
  │    ├── RBAC: roles, permissions, user_roles tables        │
  │    ├── Frontend: LoginPage, RegisterPage, AuthProvider    │
  │    └── Frontend: ProtectedRoute, RoleRoute                │
  │                                                           │
  │  Week 3: Database Schema + First Migration                │
  │    ├── Complete all table definitions                     │
  │    ├── Alembic initial migration                          │
  │    ├── Seed data: body systems, roles, permissions        │
  │    ├── Audit log infrastructure                           │
  │    └── File metadata table + Supabase Storage setup       │
  │                                                           │
  │  Week 4: Health Profile Module                            │
  │    ├── User profiles CRUD                                 │
  │    ├── Medical history CRUD                               │
  │    ├── Family history CRUD                                │
  │    ├── Medication history CRUD                            │
  │    ├── Frontend: ProfilePage, HealthProfileForm           │
  │    └── Frontend: React Hook Form + Zod validation         │
  └────────────────────────────────────────────────────────────┘

PHASE 1: Core Questionnaire Engine (Weeks 5-8)
  ┌────────────────────────────────────────────────────────────┐
  │  Week 5: Question & Questionnaire API                     │
  │    ├── Body system CRUD endpoints                         │
  │    ├── Question CRUD endpoints (with choices)             │
  │    ├── Question dependency CRUD                           │
  │    ├── Questionnaire + section CRUD                       │
  │    ├── Questionnaire-Question mapping                    │
  │    └── Question versioning logic                          │
  │                                                           │
  │  Week 6: Questionnaire Engine                             │
  │    ├── Session creation + state machine                   │
  │    ├── Branching evaluation (question_dependencies)       │
  │    ├── Answer validation                                  │
  │    ├── Auto-save logic                                    │
  │    ├── Session pause/resume                               │
  │    └── Question rendering order                           │
  │                                                           │
  │  Week 7: Frontend Questionnaire                           │
  │    ├── QuestionnaireListPage + QuestionnaireCard          │
  │    ├── QuestionnaireSessionPage                           │
  │    ├── QuestionRenderer + all question type components    │
  │    ├── ProgressBar, SectionHeader                         │
  │    ├── AutoSaveIndicator, SaveAndResumeBanner             │
  │    ├── Adaptive flow (branching-based)                    │
  │    └── TanStack Query integration (optimistic updates)    │
  │                                                           │
  │  Week 8: Body System Seed Data                            │
  │    ├── Implement 5 core body system modules               │
  │    ├── Each module: questions, choices, dependencies       │
  │    ├── Question seed data for cardiovascular, kidney,     │
  │        liver, respiratory, digestive                      │
  │    └── Frontend: BodySystemCard, BodySystemDetailPage     │
  └────────────────────────────────────────────────────────────┘

PHASE 2: Risk Engine + Assessment (Weeks 9-12)
  ┌────────────────────────────────────────────────────────────┐
  │  Week 9: Rule Engine                                       │
  │    ├── Risk rule CRUD endpoints                            │
  │    ├── JSONB condition parser                              │
  │    ├── Rule evaluation engine                              │
  │    ├── Score aggregation logic                             │
  │    ├── Scoring weights configuration                       │
  │    └── Rule versioning                                     │
  │                                                           │
  │  Week 10: Assessment Pipeline                             │
  │    ├── Assessment creation + storage                      │
  │    ├── Body system scores table                           │
  │    ├── Celery worker: calculate_assessment                 │
  │    ├── Async status polling endpoint                      │
  │    ├── Explainability engine (structured JSON)            │
  │    └── Health score history                                │
  │                                                           │
  │  Week 11: Frontend Assessment Results                     │
  │    ├── HealthScoreGauge component                         │
  │    ├── BodySystemScoreCard component                      │
  │    ├── Risk explanation panel                             │
  │    ├── RiskTrendChart (Recharts)                          │
  │    └── Assessment history page                            │
  │                                                           │
  │  Week 12: Seed Risk Rules                                │
  │    ├── Risk rules for cardiovascular system               │
  │    ├── Risk rules for kidney system                       │
  │    ├── Risk rules for liver system                        │
  │    ├── Risk rules for respiratory system                  │
  │    ├── Risk rules for digestive system                    │
  │    └── Unit tests for all rule evaluations                │
  └────────────────────────────────────────────────────────────┘

PHASE 3: Lab Reports + Timeline (Weeks 13-14)
  ┌────────────────────────────────────────────────────────────┐
  │  Week 13: Lab Reports                                     │
  │    ├── Lab test catalog CRUD                              │
  │    ├── Reference ranges CRUD                              │
  │    ├── Lab report manual entry                            │
  │    ├── Abnormal value detection                           │
  │    ├── File upload integration                            │
  │    ├── Frontend: LabReportForm, LabReportList             │
  │    └── ReferenceRangeIndicator component                  │
  │                                                           │
  │  Week 14: Health Timeline                                │
  │    ├── Timeline event creation (auto + manual)            │
  │    ├── Event type catalog                                 │
  │    ├── Timeline aggregation query                         │
  │    ├── Frontend: TimelineView, TimelineFilter             │
  │    ├── Infinite scroll with TanStack Query               │
  │    └── Integration: assessment, lab, profile → timeline  │
  └────────────────────────────────────────────────────────────┘

PHASE 4: Recommendations + Dashboard (Weeks 15-16)
  ┌────────────────────────────────────────────────────────────┐
  │  Week 15: Recommendations                                  │
  │    ├── Recommendation template CRUD                       │
  │    ├── Trigger condition evaluation                       │
  │    ├── Recommendation generation worker                   │
  │    ├── Status management (pending→acknowledged→completed) │
  │    └── Frontend: RecommendationCard, CategoryFilter       │
  │                                                           │
  │  Week 16: Dashboard                                       │
  │    ├── Dashboard aggregation endpoint                     │
  │    ├── Health score calculation + trends                   │
  │    ├── Redis caching for dashboard                        │
  │    └── Frontend: DashboardPage with all components        │
  └────────────────────────────────────────────────────────────┘

PHASE 5: Doctor CMS (Weeks 17-19)
  ┌────────────────────────────────────────────────────────────┐
  │  Week 17: CMS Foundation                                  │
  │    ├── Doctor role middleware                              │
  │    ├── Content locking system                             │
  │    ├── Version history viewer + diff                       │
  │    └── Frontend: CMSDashboardLayout, CMSSidebar           │
  │                                                           │
  │  Week 18: Question + Branching Editor                     │
  │    ├── Visual question editor                             │
  │    ├── Choice editor with scoring                         │
  │    ├── Visual dependency editor (tree view)               │
  │    ├── Multi-language text editor                         │
  │    └── Question preview                                   │
  │                                                           │
  │  Week 19: Rule + Recommendation Editor                    │
  │    ├── Visual rule condition builder                      │
  │    ├── Recommendation template editor                     │
  │    ├── Body system configuration                          │
  │    └── Patient search + overview                          │
  └────────────────────────────────────────────────────────────┘

PHASE 6: Admin + Notifications + Polish (Weeks 20-21)
  ┌────────────────────────────────────────────────────────────┐
  │  Week 20: Admin Portal                                    │
  │    ├── User management table                              │
  │    ├── Role & permission editor                           │
  │    ├── Audit log viewer                                   │
  │    ├── System health dashboard                            │
  │    └── Frontend: AdminDashboard, user/role management     │
  │                                                           │
  │  Week 21: Notifications + Remaining Body Systems          │
  │    ├── Notification infrastructure                        │
  │    ├── Email integration (SendGrid/Resend)                │
  │    ├── In-app notification polling                        │
  │    ├── Notification preferences                           │
  │    ├── Seed remaining 12 body systems                     │
  │    └── Frontend: NotificationBell, NotificationList       │
  └────────────────────────────────────────────────────────────┘

PHASE 7: Testing + Hardening (Weeks 22-24)
  ┌────────────────────────────────────────────────────────────┐
  │  Week 22: Testing                                         │
  │    ├── Unit tests: all domain entities + services          │
  │    ├── Integration tests: all API endpoints                │
  │    ├── E2E tests: critical flows (Playwright)              │
  │    ├── Load tests (k6): questionnaire + assessment         │
  │    ├── Security audit: dependency scan, penetration test   │
  │    └── Coverage target: 85%+                              │
  │                                                           │
  │  Week 23: Staging Deployment + Performance                │
  │    ├── Deploy to staging environment                      │
  │    ├── Performance profiling and optimization              │
  │    ├── Database query optimization                        │
  │    ├── Caching strategy implementation                    │
  │    └── Monitoring setup (Sentry, Render dashboard)        │
  │                                                           │
  │  Week 24: Production Launch                               │
  │    ├── Production environment setup                       │
  │    ├── CI/CD pipeline finalization                        │
  │    ├── Documentation (API docs, runbooks)                 │
  │    ├── Security review + compliance check                  │
  │    ├── Production deployment                              │
  │    ├── Monitoring + alerting active                       │
  │    └── Post-launch: bug fixes + performance tuning        │
  └────────────────────────────────────────────────────────────┘

PHASE 8: Post-Launch (Month 7+)
  ┌────────────────────────────────────────────────────────────┐
  │  Research Portal (Weeks 25-26)                            │
  │    ├── Anonymization pipeline                             │
  │    ├── Population analytics endpoints                     │
  │    ├── Cohort builder + export                            │
  │    └── Frontend: ResearchDashboardPage                    │
  │                                                           │
  │  PWA + Offline (Weeks 27-28)                             │
  │    ├── Service worker (Workbox)                           │
  │    ├── Offline questionnaire (IndexedDB)                  │
  │    ├── Push notifications (FCM)                           │
  │    └── App manifest + install prompt                      │
  │                                                           │
  │  ML Pipeline (Months 9-12)                                │
  │    ├── Feature store implementation                       │
  │    ├── Model training pipeline (GitHub Actions)           │
  │    ├── ML inference endpoint                              │
  │    ├── A/B testing framework                              │
  │    └── SHAP explainability                                │
  │                                                           │
  │  React Native (Months 9-14)                              │
  │    ├── Shared types + validation package                  │
  │    ├── React Native app scaffold                          │
  │    ├── HealthKit + Google Fit integration                │
  │    ├── Biometric auth                                    │
  │    └── Offline-first sync engine                          │
  └────────────────────────────────────────────────────────────┘
```

## 28.2 Development Team Structure

```
Recommended Team:
  ┌────────────────────────────────────────────────────────────┐
  │  Phase 0-2 (Foundation): 3-4 engineers                    │
  │  ├── 1 Senior Backend (FastAPI, PostgreSQL, architecture) │
  │  ├── 1 Senior Frontend (React, TypeScript, design)        │
  │  ├── 1 Full-Stack Engineer (both sides, integrations)     │
  │  └── 1 DevOps/Infrastructure (CI/CD, Docker, cloud)       │
  │                                                           │
  │  Phase 3-6 (Features): 5-7 engineers                      │
  │  ├── 2 Backend Engineers                                  │
  │  ├── 2 Frontend Engineers                                 │
  │  ├── 1 Full-Stack Engineer                                │
  │  ├── 1 DevOps Engineer                                    │
  │  └── 1 Product Manager + 1 Clinical Advisor (part-time)   │
  │                                                           │
  │  Phase 7+ (Scale): 8-12 engineers                         │
  │  ├── 3 Backend Engineers                                  │
  │  ├── 3 Frontend Engineers                                 │
  │  ├── 1 ML Engineer (Phase 2 starts)                       │
  │  ├── 2 Mobile Engineers (Phase 2 starts)                  │
  │  ├── 1 DevOps/SRE                                         │
  │  ├── 1 Product Manager                                    │
  │  └── 1 Clinical Advisor (part-time)                       │
  └────────────────────────────────────────────────────────────┘
```

## 28.3 Key Milestones

```
M1 (Week 4):   Auth + User Profile working end-to-end
M2 (Week 8):   Questionnaire engine complete — user can answer dynamic questions
M3 (Week 12):  Risk assessment engine complete — user receives health scores
M4 (Week 14):  Lab reports + health timeline functional
M5 (Week 16):  Recommendations + dashboard operational
M6 (Week 19):  Doctor CMS allows content management without code
M7 (Week 21):  Admin portal + notifications complete
M8 (Week 24):  PRODUCTION LAUNCH
M9 (Week 28):  Research portal + PWA offline mode
M10 (Month 12): ML pipeline + first predictive models
M11 (Month 14): React Native mobile app
M12 (Month 18): LLM integration + conversational features
```
