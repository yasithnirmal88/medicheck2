# Medicheck — Preventive Health Risk Assessment Platform
## Complete Production Architecture

> **Disclaimer**: This system is NOT a medical diagnosis platform. It identifies potential health risks for preventive action. All outputs require clinician verification.

---

## Table of Contents

1. [Overall Software Architecture](#1-overall-software-architecture)
2. [High Level Architecture Diagram](#2-high-level-architecture-diagram)
3. [Low Level Architecture](#3-low-level-architecture)
4. [Complete Module Breakdown](#4-complete-module-breakdown)
5. [Folder Structure](#5-folder-structure)
6. [Frontend Architecture](#6-frontend-architecture)
7. [Backend Architecture](#7-backend-architecture)
8. [Technology Justification](#8-technology-justification)
9. [Database Architecture](#9-database-architecture)
10. [Entity Relationship Diagram](#10-entity-relationship-diagram)
11. [API Architecture](#11-api-architecture)
12. [Authentication Architecture](#12-authentication-architecture)
13. [Authorization Architecture](#13-authorization-architecture)
14. [Questionnaire Engine Architecture](#14-questionnaire-engine-architecture)
15. [Risk Engine Architecture](#15-risk-engine-architecture)
16. [AI Architecture](#16-ai-architecture)
17. [Dashboard Architecture](#17-dashboard-architecture)
18. [Doctor CMS Architecture](#18-doctor-cms-architecture)
19. [Research Portal Architecture](#19-research-portal-architecture)
20. [Notification Architecture](#20-notification-architecture)
21. [Health Timeline Architecture](#21-health-timeline-architecture)
22. [File Storage Architecture](#22-file-storage-architecture)
23. [Security Architecture](#23-security-architecture)
24. [Deployment Architecture](#24-deployment-architecture)
25. [Scalability Strategy](#25-scalability-strategy)
26. [Future Mobile Integration](#26-future-mobile-integration)
27. [Future AI Integration](#27-future-ai-integration)
28. [Development Roadmap](#28-development-roadmap)

---

# 1. Overall Software Architecture

## 1.1 Architectural Philosophy

| Principle | Application |
|---|---|
| **Clean Architecture** | Domain → Application → Infrastructure → Presentation. Dependency rule: outer layers depend on inner layers, never vice versa. |
| **Domain-Driven Design** | Bounded contexts, aggregates, entities, value objects, domain events, repository interfaces, ubiquitous language. |
| **SOLID** | Single responsibility per module, open for extension/closed for modification, Liskov substitution for polymorphic engines, interface segregation in repositories, dependency inversion via DI container. |
| **Feature-Based** | Every feature is a self-contained module with its own components, hooks, API layer, types, and pages. |
| **API First** | All functionality exposed through versioned REST APIs. Frontend is a consumer, not the system. |
| **Microservice Ready** | Modular monolith with strict bounded contexts. Each context can be extracted into a separate service by extracting its module folder. |
| **Event Driven Ready** | Domain events published for cross-context communication. Events queued via Redis/Celery for async processing. |
| **Future AI Ready** | Engine abstractions allow swapping rule-based with ML-based implementations. Feature store designed for model training. |
| **Security First** | Defense in depth: network → API → auth → data → application → audit. |

## 1.2 Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       PRESENTATION LAYER                             │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    React SPA (Vite + TS)                     │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │    │
│  │  │ Shadcn UI│ │TanStack  │ │ React    │ │ React Hook   │  │    │
│  │  │ Tailwind │ │ Query    │ │ Router   │ │ Form + Zod   │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                    │                                  │
│                          HTTP REST + WebSocket                       │
│                                    │                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                     API GATEWAY LAYER                        │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │    │
│  │  │ Firebase │ │ Rate     │ │ CORS +   │ │ Request/     │  │    │
│  │  │ Auth     │ │ Limiting │ │ Security │ │ Response     │  │    │
│  │  │ Verify   │ │          │ │ Headers  │ │ Validation   │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │    │
│  └──────────────────────────────┬──────────────────────────────┘    │
│                                 │                                    │
│  ┌──────────────────────────────┴──────────────────────────────┐    │
│  │                    APPLICATION LAYER                          │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │    │
│  │  │ Use Cases│ │ App      │ │ DTOs +   │ │ Domain Event │  │    │
│  │  │ (CQRS)   │ │ Services │ │ Mappers  │ │ Publishers   │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │    │
│  └──────────────────────────────┬──────────────────────────────┘    │
│                                 │                                    │
│  ┌──────────────────────────────┴──────────────────────────────┐    │
│  │                      DOMAIN LAYER                            │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │    │
│  │  │ Entities │ │ Value    │ │Aggregates│ │ Repository   │  │    │
│  │  │          │ │ Objects  │ │          │ │ Interfaces   │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │    │
│  │  │ Domain   │ │ Domain   │ │ Module   │                  │    │
│  │  │ Events   │ │ Services │ │ Contracts│                  │    │
│  │  └──────────┘ └──────────┘ └──────────┘                  │    │
│  └──────────────────────────────┬──────────────────────────────┘    │
│                                 │                                    │
│  ┌──────────────────────────────┴──────────────────────────────┐    │
│  │                   INFRASTRUCTURE LAYER                       │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │    │
│  │  │ Supabase │ │ Firebase │ │ Celery + │ │ Supabase     │  │    │
│  │  │ PG DB    │ │ Auth SDK │ │ Redis    │ │ Storage      │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │    │
│  │  │ Email    │ │ LLM SDK  │ │ OCR SDK  │                  │    │
│  │  │ Service  │ │ (future) │ │ (future) │                  │    │
│  │  └──────────┘ └──────────┘ └──────────┘                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## 1.3 Bounded Contexts Map

```
┌────────────────────────────────────────────────────────────────────┐
│                     BOUNDED CONTEXTS                                │
│                                                                     │
│  ┌────────────────────────┐  ┌────────────────────────┐            │
│  │   CONTEXT: Identity     │  │  CONTEXT: Questionnaire │           │
│  │   ──────────────────    │  │  ─────────────────────  │           │
│  │   Aggregate: User       │  │  Aggregate: Question    │           │
│  │   Aggregate: Session    │  │  Aggregate: Session     │           │
│  │   Value: Email, Phone   │  │  Value: Answer, Score   │           │
│  │   Domain Event:         │  │  Domain Event:          │           │
│  │   UserRegistered        │  │  QuestionnaireSubmitted │           │
│  └─────────────┬──────────┘  └─────────────┬──────────┘            │
│                │                            │                       │
│  ┌─────────────┴──────────┐  ┌─────────────┴──────────┐            │
│  │   CONTEXT: Health       │  │  CONTEXT: Assessment   │            │
│  │   ────────────────      │  │  ──────────────────    │            │
│  │   Aggregate: Profile    │  │  Aggregate: RiskScore  │            │
│  │   Aggregate: LabReport  │  │  Value: RiskLevel      │            │
│  │   Aggregate: Timeline   │  │  Domain Service:       │            │
│  │   Value: BMI, BP        │  │  RiskEngine            │            │
│  │   Domain Event:         │  │  Domain Event:         │            │
│  │   LabReportAdded        │  │  AssessmentCompleted   │            │
│  └─────────────┬──────────┘  └─────────────┬──────────┘            │
│                │                            │                       │
│  ┌─────────────┴──────────┐  ┌─────────────┴──────────┐            │
│  │   CONTEXT: Recommends   │  │   CONTEXT: CMS         │            │
│  │   ──────────────────    │  │   ────────────         │            │
│  │   Aggregate: Recomend   │  │   Aggregate: Content   │            │
│  │   Value: Priority       │  │   Value: Version       │            │
│  │   Domain Event:         │  │   Domain Event:        │            │
│  │   RecGenerated          │  │   ContentUpdated       │            │
│  └────────────────────────┘  └────────────────────────┘            │
│                                                                     │
│  ┌────────────────────────┐  ┌────────────────────────┐            │
│  │   CONTEXT: Analytics   │  │   CONTEXT: Notify      │            │
│  │   ────────────────     │  │   ────────────────     │            │
│  │   Aggregate: Report    │  │   Aggregate: Notif     │            │
│  │   Value: Statistic     │  │   Value: Channel       │            │
│  └────────────────────────┘  └────────────────────────┘            │
└────────────────────────────────────────────────────────────────────┘

Bounded Context Communication:
  - Synchronous: Direct service calls (modular monolith)
  - Asynchronous: Domain events → Message Queue → Handlers
  - Integration: Anti-corruption layer between contexts
```

## 1.4 Evolution: Modular Monolith → Microservices

```
PHASE 1 (Months 1-6): Modular Monolith
  Single FastAPI process on Render
  All modules in same process, separate folders
  Shared database (single PostgreSQL schema)
  Strict interface boundaries between modules
  Domain events for async communication

PHASE 2 (Months 6-12): Extracted Services
  Extract Auth module → Firebase handles independently
  Extract Questionnaire Engine → separate service
  Extract Assessment Engine → separate service
  Each service has its own schema (database per service)
  Communication via REST + Message Queue

PHASE 3 (Year 2+): Full Microservices
  API Gateway (Kong/APISIX) in front
  Service mesh (Istio/Linkerd)
  Event-driven with Kafka
  Independent scaling per service
  Polyglot persistence (graph for recommendations, TSDB for vitals)

Extraction Strategy:
  Step 1: Identify a bounded context boundary
  Step 2: Create the FastAPI sub-app with its own router
  Step 3: Move domain entities, application services, and persistence
  Step 4: Replace in-process calls with HTTP/gRPC calls
  Step 5: Set up message queue for eventual consistency
  Step 6: Deploy as independent service on Render
```

---

# 2. High Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MEDICHECK PLATFORM                                   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      USER INTERFACES                                 │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  │   │
│  │  │  Patient Web  │  │  Doctor CMS  │  │  Researcher  │  │  Admin  │  │   │
│  │  │  (React SPA)  │  │  (React SPA) │  │  (React SPA) │  │ (React) │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────┬────┘  │   │
│  │         │                 │                  │               │        │   │
│  │         └─────────────────┴──────────────────┴───────────────┘        │   │
│  │                              │ HTTPS                                   │   │
│  └──────────────────────────────┼─────────────────────────────────────────┘   │
│                                 │                                              │
│  ┌──────────────────────────────┼─────────────────────────────────────────┐   │
│  │                    VERGEL (CDN + Frontend)                              │   │
│  │                              │                                          │   │
│  │                    Vercel Edge Network                                  │   │
│  │                              │                                          │   │
│  └──────────────────────────────┼─────────────────────────────────────────┘   │
│                                 │                                              │
│  ┌──────────────────────────────┼─────────────────────────────────────────┐   │
│  │                    FIREBASE AUTHENTICATION                              │   │
│  │                              │                                          │   │
│  │  ┌────────────┐ ┌──────────┐│┌──────────┐ ┌──────────────────┐       │   │
│  │  │ Email/Pwd  │ │ Google   │││ Apple    │ │ 2FA + MFA        │       │   │
│  │  │ Auth       │ │ OAuth    │││ OAuth    │ │ (Future)         │       │   │
│  │  └────────────┘ └──────────┘│└──────────┘ └──────────────────┘       │   │
│  │                              │                                          │   │
│  │                     Firebase Token Verification                         │   │
│  └──────────────────────────────┼─────────────────────────────────────────┘   │
│                                 │                                              │
│  ┌──────────────────────────────┼─────────────────────────────────────────┐   │
│  │                     RENDER (Backend)                                    │   │
│  │                              │                                          │   │
│  │  ┌──────────────────────────┴──────────────────────────────────┐      │   │
│  │  │                FASTAPI APPLICATION                            │      │   │
│  │  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │      │   │
│  │  │  │ Auth  │ │ User │ │Health│ │ Ques │ │ Risk │ │ Lab   │   │      │   │
│  │  │  │Module │ │Module│ │Profile│ │-naire│ │Engine│ │Module │   │      │   │
│  │  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │      │   │
│  │  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │      │   │
│  │  │  │Timeln│ │Recom │ │Dash  │ │ CMS  │ │Resrch│ │Admin │   │      │   │
│  │  │  │Module│ │-end  │ │-board│ │Module│ │Module│ │Module│   │      │   │
│  │  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │      │   │
│  │  └─────────────────────────────────────────────────────────────┘      │   │
│  │                              │                                          │   │
│  │  ┌──────────────────────────┴──────────────────────────────────┐      │   │
│  │  │              BACKGROUND WORKERS (Celery)                     │      │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │      │   │
│  │  │  │Assessment│ │Recommend │ │Notification │ Report Export  │ │      │   │
│  │  │  │  Worker  │ │  Worker  │ │  Worker    │   Worker       │ │      │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘ │      │   │
│  │  └─────────────────────────────────────────────────────────────┘      │   │
│  └──────────────────────────────┬────────────────────────────────────────┘   │
│                                 │                                              │
│  ┌──────────────────────────────┼─────────────────────────────────────────┐   │
│  │                    SUPABASE (Database + Storage)                        │   │
│  │                              │                                          │   │
│  │  ┌──────────────────────────┴──────────────────────────────────┐      │   │
│  │  │                    POSTGRESQL 16                              │      │   │
│  │  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ │      │   │
│  │  │  │Users│ │Qs  │ │Resp│ │Asse│ │Lab │ │Time│ │Aud │ │Rec │ │      │   │
│  │  │  │     │ │tion-│ │nses│ │ssmt│ │Rpts│ │line│ │it  │ │s   │ │      │   │
│  │  │  │     │ │naire│ │    │ │    │ │    │ │    │ │    │ │    │ │      │   │
│  │  │  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ │      │   │
│  │  └─────────────────────────────────────────────────────────────┘      │   │
│  │                              │                                          │   │
│  │  ┌──────────────────────────┴──────────────────────────────────┐      │   │
│  │  │              SUPABASE STORAGE (S3-compatible)                │      │   │
│  │  │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────┐│      │   │
│  │  │  │   Lab Reports    │ │  Medical Docs    │ │  Profile Pics ││      │   │
│  │  │  │   (encrypted)    │ │  (encrypted)     │ │  (optimized)  ││      │   │
│  │  │  └──────────────────┘ └──────────────────┘ └──────────────┘│      │   │
│  │  └─────────────────────────────────────────────────────────────┘      │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    EXTERNAL INTEGRATIONS (Future)                      │   │
│  │                                                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐  │   │
│  │  │  OpenAI  │  │Anthropic │  │  Google  │  │  Apple   │  │ OCR  │  │   │
│  │  │  LLM API │  │ LLM API  │  │  Fit API │  │HealthKit │  │Service│  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 3. Low Level Architecture

## 3.1 Package Dependency Rules

```
Backend Dependency Graph:
  ┌──────────────────────────────────────────────────────────────┐
  │                                                               │
  │  api/ (depends on: application, infrastructure)              │
  │    ↑                                                         │
  │  application/ (depends on: domain)                           │
  │    ↑                                                         │
  │  domain/ (depends on: nothing — pure Python)                 │
  │    ↑                                                         │
  │  infrastructure/ (depends on: domain, external libs)         │
  │                                                               │
  │  modules/ (depends on: domain, application)                  │
  │    ↑                                                         │
  │  core/ (no dependencies within app)                          │
  │                                                               │
  │  Rule: Domain knows nothing about infrastructure.            │
  │  Rule: Outer layers depend on inner layers, never reverse.   │
  │  Rule: Modules communicate through application services.     │
  │  Rule: Cross-context communication uses domain events.       │
  └──────────────────────────────────────────────────────────────┘
```

## 3.2 Dependency Injection Container

```
Container Setup (lifespan):
  ┌──────────────────────────────────────────────────────────────┐
  │  FastAPI app startup:                                        │
  │    1. Load config from environment                           │
  │    2. Initialize database session factory                    │
  │    3. Initialize Firebase Admin SDK                          │
  │    4. Initialize Redis connection pool                       │
  │    5. Initialize storage client (Supabase)                   │
  │    6. Register repository implementations                    │
  │    7. Register service implementations                       │
  │    8. Register module engines (questionnaire, risk, etc.)    │
  │    9. Discover and register body system modules              │
  │   10. Return DI container to app state                       │
  │                                                               │
  │  FastAPI Depends() functions:                                 │
  │    get_db() → AsyncSession                                   │
  │    get_current_user() → User (from Firebase token)           │
  │    get_current_doctor() → User (with role check)             │
  │    get_current_admin() → User (with role check)              │
  │    get_questionnaire_service() → QuestionnaireService        │
  │    get_risk_engine() → RiskEngine                            │
  │    get_storage_client() → StorageClient                      │
  └──────────────────────────────────────────────────────────────┘
```

## 3.3 Request Lifecycle

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Client   │   │ Middleware│   │  Router  │   │  Service  │   │    DB    │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │                │              │              │
     │ HTTP Request │                │              │              │
     ├─────────────▶│                │              │              │
     │              │ 1. CORS check  │              │              │
     │              │ 2. Rate limit  │              │              │
     │              │ 3. Firebase    │              │              │
     │              │    token verify│              │              │
     │              │ 4. Log request │              │              │
     │              │                │              │              │
     │              │ Route to       │              │              │
     │              │ endpoint       │              │              │
     │              ├───────────────▶│              │              │
     │              │                │ 5. Validate  │              │
     │              │                │    (Pydantic)│              │
     │              │                │ 6. Check     │              │
     │              │                │    permissions│             │
     │              │                │ 7. Call use  │              │
     │              │                │    case      │              │
     │              │                ├─────────────▶│              │
     │              │                │              │ 8. Business  │
     │              │                │              │    logic     │
     │              │                │              │ 9. Domain    │
     │              │                │              │    events    │
     │              │                │              │10. Persist   │
     │              │                │              ├─────────────▶│
     │              │                │              │◀─────────────┤
     │              │                │◀─────────────┤              │
     │              │◀───────────────┤              │              │
     │              │11. Format      │              │              │
     │              │    response    │              │              │
     │              │12. Log response│              │              │
     │◀─────────────┤                │              │              │
```

---

# 4. Complete Module Breakdown

## 4.1 Module Catalog

| # | Module | Role | Key Responsibilities |
|---|---|---|---|
| 1 | **Authentication** | Core | Firebase token verification, session management, profile sync, 2FA check |
| 2 | **User Management** | Core | CRUD profiles, role assignment, account settings, data export/deletion |
| 3 | **Health Profile** | Core | Personal info, demographics, anthropometrics, vitals, lifestyle baselines |
| 4 | **Medical History** | Core | Conditions, surgeries, allergies, immunizations, current medications |
| 5 | **Family History** | Core | Hereditary conditions, family disease patterns, genetic risk indicators |
| 6 | **Medication History** | Core | Active/past medications, dosages, adherence tracking, side effects |
| 7 | **Laboratory Reports** | Core | Manual test entry, reference ranges, abnormal flagging, trend analysis |
| 8 | **Questionnaire Engine** | Core | Dynamic question rendering, branching, scoring, versioning (see §14) |
| 9 | **Risk Assessment** | Core | Score calculation, rule evaluation, explainability, trend tracking (see §15) |
| 10 | **Recommendations** | Core | Lifestyle, diet, exercise, lab tests, screenings generation |
| 11 | **Body Systems** | Framework | 17+ modular body system definitions, pluggable architecture |
| 12 | **Health Timeline** | Core | Chronological health event aggregation, filtering, visualization |
| 13 | **Dashboard** | Core | Health score, system cards, trends, summaries, upcoming actions |
| 14 | **Doctor CMS** | Portal | Question/rule/body-system management, versioning, patient overview |
| 15 | **Research Portal** | Portal | Anonymized population analytics, data export, cohort filtering |
| 16 | **Notification** | Cross | Email, in-app, push notifications, preferences, templates |
| 17 | **Audit Logging** | Cross | Immutable audit trail, PHI access logging, security events |
| 18 | **Administration** | Portal | User management, role config, system health, platform settings |

## 4.2 Body System Module Framework

```
BodySystemModule (Abstract Base Class):
┌──────────────────────────────────────────────────────────────┐
│  BodySystemModule                                             │
│  ─────────────────                                            │
│  + code: str                                                  │
│  + name: JSON (multi-lang)                                    │
│  + icon: str                                                  │
│  + is_active: bool                                            │
│  + version: str                                               │
│  + description: JSON                                          │
│  + get_questions() → list[QuestionDef]                        │
│  + get_risk_rules() → list[RiskRuleDef]                       │
│  + get_risk_indicators() → list[IndicatorDef]                 │
│  + get_medical_conditions() → list[ConditionDef]              │
│  + get_recommendations() → list[RecommendationDef]            │
│  + get_lab_tests() → list[LabTestDef]                         │
│  + get_default_scoring_weights() → dict                       │
└──────────────────────────────────────────────────────────────┘

Registered Body Systems:
  ┌──────────────┬─────────────────────────────────────┬─────────┐
  │ Code          │ Name                                │ Priority│
  ├──────────────┼─────────────────────────────────────┼─────────┤
  │ cardiovascular│ Cardiovascular Health               │ Core    │
  │ kidney       │ Kidney & Urinary Health              │ Core    │
  │ liver        │ Liver Health                         │ Core    │
  │ digestive    │ Digestive Health                     │ Core    │
  │ respiratory  │ Respiratory & Lung Health            │ Core    │
  │ neurological │ Neurological Health                  │ Core    │
  │ eye          │ Eye & Vision Health                  │ Core    │
  │ endocrine    │ Endocrine & Hormonal Health          │ Core    │
  │ skin         │ Skin & Dermatological Health         │ Core    │
  │ musculoskeletal│ Musculoskeletal Health             │ Core    │
  │ blood        │ Blood & Hematological Health         │ Core    │
  │ immune       │ Immune System Health                 │ Core    │
  │ mental       │ Mental & Emotional Health            │ Core    │
  │ male_health  │ Male Reproductive Health             │ Gender  │
  │ female_health│ Female Reproductive Health           │ Gender  │
  │ sexual       │ Sexual Health                        │ Core    │
  │ cancer       │ Cancer Risk Screening                │ Core    │
  └──────────────┴─────────────────────────────────────┴─────────┘

Module Registration:
  - Auto-discovered at startup via Python entry_points or scanning
  - Each module seeds its default questions, rules, indicators to DB
  - Doctors can override defaults via CMS (creates new versions)
  - New module = new folder + registration line = zero code changes elsewhere
```

---

# 5. Folder Structure

## 5.1 Repository Root

```
medicheck/
├── frontend/                    # React SPA (Vercel)
├── backend/                     # FastAPI API (Render)
├── docs/                        # Architecture documentation
│   └── architecture/
│       ├── 02-CORE-ENGINES.md
│       └── 03-MODULES-DEPLOYMENT.md
├── infrastructure/              # IaC, CI/CD configs
│   ├── docker/
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.worker
│   │   └── docker-compose.yml
│   ├── .github/
│   │   └── workflows/
│   │       ├── ci.yml
│   │       ├── deploy-staging.yml
│   │       └── deploy-production.yml
│   └── scripts/
│       ├── seed_questions.py
│       └── migrate.sh
├── .gitignore
├── README.md
└── ARCHITECTURE.md              # This file
```

## 5.2 Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application factory
│   │
│   ├── api/                     # Presentation Layer
│   │   ├── __init__.py
│   │   ├── deps.py              # DI functions (get_db, get_user, etc.)
│   │   ├── middleware.py        # CORS, rate limit, logging
│   │   ├── errors.py            # Global error handlers
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py        # Aggregates all v1 routers
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py              # Firebase token exchange
│   │           ├── users.py             # User CRUD
│   │           ├── health_profile.py    # Health profile
│   │           ├── medical_history.py   # Medical/family/medication history
│   │           ├── questionnaires.py    # Questionnaire CRUD + start/submit
│   │           ├── questions.py         # Question browsing
│   │           ├── responses.py         # Answer submission
│   │           ├── body_systems.py      # Body system endpoints
│   │           ├── assessments.py       # Risk assessment results
│   │           ├── lab_reports.py       # Lab report CRUD
│   │           ├── timeline.py          # Health timeline
│   │           ├── recommendations.py   # Recommendations
│   │           ├── dashboard.py         # Dashboard aggregation
│   │           ├── notifications.py     # Notification preferences
│   │           ├── cms/                 # Doctor CMS endpoints
│   │           │   ├── __init__.py
│   │           │   ├── questions.py
│   │           │   ├── body_systems.py
│   │           │   ├── risk_rules.py
│   │           │   ├── recommendations.py
│   │           │   └── content_versions.py
│   │           ├── admin/               # Admin endpoints
│   │           │   ├── __init__.py
│   │           │   ├── users.py
│   │           │   ├── roles.py
│   │           │   ├── audit_logs.py
│   │           │   └── system.py
│   │           ├── research/            # Research endpoints
│   │           │   ├── __init__.py
│   │           │   ├── population.py
│   │           │   ├── analytics.py
│   │           │   └── export.py
│   │           ├── files.py             # File upload/download
│   │           └── health.py            # Health check endpoint
│   │
│   ├── core/                     # Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── config.py             # pydantic-settings (env → config)
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── firebase.py       # Firebase token verification
│   │   │   ├── rbac.py           # Role/permission checking
│   │   │   ├── encryption.py     # AES-256 field-level encryption
│   │   │   └── rate_limit.py     # Rate limiting logic
│   │   ├── logging.py            # Structured JSON logging
│   │   ├── cache.py              # Redis cache abstraction
│   │   ├── exceptions.py         # Custom exception hierarchy
│   │   └── events.py             # Domain event bus
│   │
│   ├── domain/                    # Domain Layer
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── role.py
│   │   │   ├── question.py
│   │   │   ├── question_choice.py
│   │   │   ├── question_dependency.py
│   │   │   ├── questionnaire.py
│   │   │   ├── questionnaire_session.py
│   │   │   ├── response.py
│   │   │   ├── body_system.py
│   │   │   ├── risk_rule.py
│   │   │   ├── risk_indicator.py
│   │   │   ├── medical_condition.py
│   │   │   ├── assessment.py
│   │   │   ├── health_score.py
│   │   │   ├── lab_report.py
│   │   │   ├── lab_test.py
│   │   │   ├── lab_reference_range.py
│   │   │   ├── timeline_event.py
│   │   │   ├── recommendation.py
│   │   │   ├── notification.py
│   │   │   ├── file_metadata.py
│   │   │   ├── audit_log.py
│   │   │   └── content_version.py
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── email.py
│   │   │   ├── phone.py
│   │   │   ├── address.py
│   │   │   ├── blood_pressure.py
│   │   │   ├── bmi.py
│   │   │   ├── lab_value.py
│   │   │   ├── risk_level.py
│   │   │   └── health_score_value.py
│   │   ├── aggregates/
│   │   │   ├── __init__.py
│   │   │   ├── patient_profile.py
│   │   │   ├── health_assessment.py
│   │   │   └── questionnaire_session_aggregate.py
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── user_registered.py
│   │   │   ├── questionnaire_submitted.py
│   │   │   ├── assessment_completed.py
│   │   │   ├── lab_report_added.py
│   │   │   ├── profile_updated.py
│   │   │   ├── recommendation_generated.py
│   │   │   └── content_updated.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── questionnaire_engine.py      # Interface
│   │   │   ├── risk_engine.py               # Interface
│   │   │   └── recommendation_engine.py     # Interface
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── user_repository.py           # Interface
│   │       ├── question_repository.py       # Interface
│   │       ├── questionnaire_repository.py  # Interface
│   │       ├── session_repository.py        # Interface
│   │       ├── response_repository.py       # Interface
│   │       ├── assessment_repository.py     # Interface
│   │       ├── lab_repository.py            # Interface
│   │       ├── timeline_repository.py       # Interface
│   │       ├── recommendation_repository.py # Interface
│   │       └── audit_repository.py          # Interface
│   │
│   ├── application/                # Application Layer
│   │   ├── __init__.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── health_profile_service.py
│   │   │   ├── medical_history_service.py
│   │   │   ├── questionnaire_service.py
│   │   │   ├── question_service.py
│   │   │   ├── response_service.py
│   │   │   ├── body_system_service.py
│   │   │   ├── assessment_service.py
│   │   │   ├── lab_service.py
│   │   │   ├── timeline_service.py
│   │   │   ├── recommendation_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── file_service.py
│   │   │   ├── cms_service.py
│   │   │   ├── admin_service.py
│   │   │   └── research_service.py
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   ├── submit_questionnaire.py
│   │   │   ├── calculate_risk_assessment.py
│   │   │   ├── generate_recommendations.py
│   │   │   ├── analyze_lab_report.py
│   │   │   ├── trigger_health_timeline_update.py
│   │   │   └── export_patient_data.py
│   │   └── dtos/
│   │       ├── __init__.py
│   │       ├── auth_dtos.py
│   │       ├── user_dtos.py
│   │       ├── question_dtos.py
│   │       ├── assessment_dtos.py
│   │       ├── dashboard_dtos.py
│   │       ├── lab_dtos.py
│   │       ├── timeline_dtos.py
│   │       └── recommendation_dtos.py
│   │
│   ├── infrastructure/             # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── database.py            # SQLAlchemy async engine + session
│   │   ├── redis.py               # Redis connection pool
│   │   ├── storage.py             # Supabase Storage adapter
│   │   ├── email.py               # Email service (SendGrid/Resend)
│   │   ├── persistence/
│   │   │   ├── __init__.py
│   │   │   ├── models/            # SQLAlchemy ORM models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py        # Declarative base + mixins
│   │   │   │   ├── user.py
│   │   │   │   ├── role.py
│   │   │   │   ├── question.py
│   │   │   │   ├── question_choice.py
│   │   │   │   ├── question_dependency.py
│   │   │   │   ├── questionnaire.py
│   │   │   │   ├── section.py
│   │   │   │   ├── questionnaire_question.py
│   │   │   │   ├── questionnaire_session.py
│   │   │   │   ├── response.py
│   │   │   │   ├── body_system.py
│   │   │   │   ├── risk_rule.py
│   │   │   │   ├── risk_indicator.py
│   │   │   │   ├── medical_condition.py
│   │   │   │   ├── condition_risk_indicator.py
│   │   │   │   ├── assessment.py
│   │   │   │   ├── body_system_score.py
│   │   │   │   ├── health_score.py
│   │   │   │   ├── lab_test.py
│   │   │   │   ├── lab_reference_range.py
│   │   │   │   ├── lab_report.py
│   │   │   │   ├── lab_report_value.py
│   │   │   │   ├── timeline_event.py
│   │   │   │   ├── recommendation.py
│   │   │   │   ├── user_recommendation.py
│   │   │   │   ├── notification.py
│   │   │   │   ├── file_metadata.py
│   │   │   │   ├── audit_log.py
│   │   │   │   ├── content_version.py
│   │   │   │   └── content_lock.py
│   │   │   └── repositories/     # Implementations
│   │   │       ├── __init__.py
│   │   │       ├── sql_user_repository.py
│   │   │       ├── sql_question_repository.py
│   │   │       ├── sql_questionnaire_repository.py
│   │   │       ├── sql_session_repository.py
│   │   │       ├── sql_response_repository.py
│   │   │       ├── sql_assessment_repository.py
│   │   │       ├── sql_lab_repository.py
│   │   │       ├── sql_timeline_repository.py
│   │   │       ├── sql_recommendation_repository.py
│   │   │       └── sql_audit_repository.py
│   │   └── external/
│   │       ├── __init__.py
│   │       ├── firebase_auth.py   # Firebase Admin SDK adapter
│   │       ├── llm_client.py     # Future LLM client adapter
│   │       └── ocr_client.py     # Future OCR adapter
│   │
│   └── modules/                   # Feature Modules
│       ├── __init__.py
│       ├── body_systems/
│       │   ├── __init__.py
│       │   ├── base.py            # BodySystemModule abstract class
│       │   ├── registry.py        # Module registry + auto-discover
│       │   ├── cardiovascular/
│       │   │   ├── __init__.py
│       │   │   └── module.py      # CardiovascularModule
│       │   ├── kidney/
│       │   ├── liver/
│       │   ├── digestive/
│       │   ├── respiratory/
│       │   ├── neurological/
│       │   ├── eye/
│       │   ├── endocrine/
│       │   ├── skin/
│       │   ├── musculoskeletal/
│       │   ├── blood/
│       │   ├── immune/
│       │   ├── mental_health/
│       │   ├── male_health/
│       │   ├── female_health/
│       │   ├── sexual_health/
│       │   └── cancer_screening/
│       ├── questionnaire/
│       │   ├── __init__.py
│       │   ├── engine.py          # Dynamic questionnaire engine
│       │   ├── branching.py       # Dependency evaluation engine
│       │   ├── scoring.py         # Answer scoring logic
│       │   └── validation.py      # Response validation
│       ├── risk_engine/
│       │   ├── __init__.py
│       │   ├── rules_engine.py    # Rule-based risk calculation
│       │   ├── score_aggregator.py # Multi-system aggregation
│       │   ├── explainer.py       # Human-readable risk explanations
│       │   └── ml_engine.py       # Future ML inference wrapper
│       ├── recommendations/
│       │   ├── __init__.py
│       │   ├── generator.py
│       │   ├── lifestyle.py
│       │   ├── diet.py
│       │   ├── exercise.py
│       │   ├── lab_tests.py
│       │   └── screenings.py
│       ├── lab_reports/
│       │   ├── __init__.py
│       │   ├── analyzer.py
│       │   └── reference_ranges.py
│       ├── timeline/
│       │   ├── __init__.py
│       │   ├── builder.py
│       │   └── aggregator.py
│       └── dashboard/
│           ├── __init__.py
│           ├── health_score_calculator.py
│           ├── insights_generator.py
│           └── trend_analyzer.py
│
├── workers/                       # Celery Background Workers
│   ├── __init__.py
│   ├── celery_app.py              # Celery application config
│   ├── celery_config.py           # Beat schedule, queues, routing
│   └── tasks/
│       ├── __init__.py
│       ├── assessment_tasks.py     # Run risk assessment
│       ├── recommendation_tasks.py # Generate recommendations
│       ├── notification_tasks.py   # Send notifications
│       ├── report_tasks.py         # Generate/export reports
│       └── maintenance_tasks.py    # Data cleanup, cache warming
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures, test DB, mock Firebase
│   ├── domain/
│   │   ├── test_entities.py
│   │   ├── test_value_objects.py
│   │   └── test_domain_services.py
│   ├── application/
│   │   ├── test_services.py
│   │   └── test_use_cases.py
│   ├── api/
│   │   ├── test_auth.py
│   │   ├── test_questionnaires.py
│   │   ├── test_assessments.py
│   │   ├── test_lab_reports.py
│   │   └── test_dashboard.py
│   ├── modules/
│   │   ├── test_questionnaire_engine.py
│   │   ├── test_risk_engine.py
│   │   ├── test_branching.py
│   │   └── test_recommendations.py
│   ├── integration/
│   │   ├── test_repositories.py
│   │   └── test_workers.py
│   └── fixtures/
│       ├── users.json
│       ├── questions.json
│       └── lab_tests.json
│
├── alembic/                       # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── pyproject.toml
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .env.test
└── requirements/
    ├── base.txt
    ├── dev.txt
    └── prod.txt
```

## 5.3 Frontend Structure

```
frontend/
├── public/
│   ├── manifest.json              # PWA manifest
│   ├── service-worker.js          # Service worker (Workbox)
│   ├── icons/                     # App icons (192x192, 512x512)
│   ├── favicon.ico
│   ├── robots.txt
│   └── offline.html               # Offline fallback page
│
├── src/
│   ├── main.tsx                   # React entry point
│   ├── App.tsx                    # Root component
│   ├── index.css                  # Tailwind imports + global styles
│   │
│   ├── routes/                    # Route definitions
│   │   ├── index.tsx              # Route tree
│   │   ├── ProtectedRoute.tsx     # Auth guard wrapper
│   │   └── RoleRoute.tsx          # Role-based guard wrapper
│   │
│   ├── layouts/                   # Layout components
│   │   ├── RootLayout.tsx
│   │   ├── AuthLayout.tsx
│   │   ├── DashboardLayout.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── MobileNav.tsx
│   │
│   ├── features/                  # Feature-based modules
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   ├── RegisterForm.tsx
│   │   │   │   ├── OAuthButtons.tsx
│   │   │   │   ├── PasswordResetForm.tsx
│   │   │   │   └── EmailVerificationBanner.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.ts
│   │   │   │   ├── useLogin.ts
│   │   │   │   └── useRegister.ts
│   │   │   ├── api/
│   │   │   │   └── authApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       ├── LoginPage.tsx
│   │   │       ├── RegisterPage.tsx
│   │   │       ├── ForgotPasswordPage.tsx
│   │   │       └── VerifyEmailPage.tsx
│   │   │
│   │   ├── questionnaire/
│   │   │   ├── components/
│   │   │   │   ├── QuestionnaireList.tsx
│   │   │   │   ├── QuestionnaireCard.tsx
│   │   │   │   ├── QuestionnaireSession.tsx
│   │   │   │   ├── QuestionRenderer.tsx
│   │   │   │   ├── question-types/
│   │   │   │   │   ├── SingleChoice.tsx
│   │   │   │   │   ├── MultipleChoice.tsx
│   │   │   │   │   ├── ScaleInput.tsx
│   │   │   │   │   ├── TextInput.tsx
│   │   │   │   │   ├── NumericInput.tsx
│   │   │   │   │   ├── DateInput.tsx
│   │   │   │   │   ├── BooleanInput.tsx
│   │   │   │   │   ├── BloodPressureInput.tsx
│   │   │   │   │   └── FileUpload.tsx
│   │   │   │   ├── ProgressBar.tsx
│   │   │   │   ├── SectionHeader.tsx
│   │   │   │   ├── NavigationButtons.tsx
│   │   │   │   ├── AutoSaveIndicator.tsx
│   │   │   │   └── SaveAndResumeBanner.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useQuestionnaire.ts
│   │   │   │   ├── useSession.ts
│   │   │   │   ├── useBranching.ts
│   │   │   │   └── useAutoSave.ts
│   │   │   ├── api/
│   │   │   │   └── questionnaireApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       ├── QuestionnaireListPage.tsx
│   │   │       └── QuestionnaireSessionPage.tsx
│   │   │
│   │   ├── dashboard/
│   │   │   ├── components/
│   │   │   │   ├── OverviewCards.tsx
│   │   │   │   ├── HealthScoreGauge.tsx
│   │   │   │   ├── BodySystemGrid.tsx
│   │   │   │   ├── BodySystemCard.tsx
│   │   │   │   ├── RiskTrendChart.tsx
│   │   │   │   ├── LifestyleSummary.tsx
│   │   │   │   ├── LabSummaryTable.tsx
│   │   │   │   ├── TimelinePreview.tsx
│   │   │   │   ├── RecommendationsPanel.tsx
│   │   │   │   └── UpcomingAssessments.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useDashboard.ts
│   │   │   ├── api/
│   │   │   │   └── dashboardApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       └── DashboardPage.tsx
│   │   │
│   │   ├── body-systems/
│   │   │   ├── components/
│   │   │   │   ├── BodySystemDetail.tsx
│   │   │   │   ├── RiskIndicatorList.tsx
│   │   │   │   ├── ScoreHistoryChart.tsx
│   │   │   │   └── RelatedRecommendations.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useBodySystem.ts
│   │   │   ├── api/
│   │   │   │   └── bodySystemApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       └── BodySystemDetailPage.tsx
│   │   │
│   │   ├── lab-reports/
│   │   │   ├── components/
│   │   │   │   ├── LabReportList.tsx
│   │   │   │   ├── LabReportCard.tsx
│   │   │   │   ├── LabReportForm.tsx
│   │   │   │   ├── LabValueInput.tsx
│   │   │   │   ├── TestSelector.tsx
│   │   │   │   └── ReferenceRangeIndicator.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useLabReports.ts
│   │   │   ├── api/
│   │   │   │   └── labApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       ├── LabReportsListPage.tsx
│   │   │       ├── LabReportDetailPage.tsx
│   │   │       └── AddLabReportPage.tsx
│   │   │
│   │   ├── health-timeline/
│   │   │   ├── components/
│   │   │   │   ├── TimelineView.tsx
│   │   │   │   ├── TimelineEvent.tsx
│   │   │   │   ├── TimelineFilter.tsx
│   │   │   │   └── AddEventModal.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useTimeline.ts
│   │   │   ├── api/
│   │   │   │   └── timelineApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       └── HealthTimelinePage.tsx
│   │   │
│   │   ├── recommendations/
│   │   │   ├── components/
│   │   │   │   ├── RecommendationList.tsx
│   │   │   │   ├── RecommendationCard.tsx
│   │   │   │   ├── CategoryFilter.tsx
│   │   │   │   └── ActionPlan.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useRecommendations.ts
│   │   │   ├── api/
│   │   │   │   └── recommendationApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       └── RecommendationsPage.tsx
│   │   │
│   │   ├── profile/
│   │   │   ├── components/
│   │   │   │   ├── PersonalInfoForm.tsx
│   │   │   │   ├── HealthProfileForm.tsx
│   │   │   │   ├── MedicalHistoryForm.tsx
│   │   │   │   ├── FamilyHistoryForm.tsx
│   │   │   │   ├── MedicationForm.tsx
│   │   │   │   └── AccountSettings.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useProfile.ts
│   │   │   │   └── useMedicalHistory.ts
│   │   │   ├── api/
│   │   │   │   ├── profileApi.ts
│   │   │   │   └── medicalHistoryApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       ├── ProfilePage.tsx
│   │   │       └── SettingsPage.tsx
│   │   │
│   │   ├── cms/                  # Doctor CMS
│   │   │   ├── components/
│   │   │   │   ├── CMSSidebar.tsx
│   │   │   │   ├── QuestionList.tsx
│   │   │   │   ├── QuestionEditor.tsx
│   │   │   │   ├── ChoiceEditor.tsx
│   │   │   │   ├── DependencyEditor.tsx
│   │   │   │   ├── RiskRuleEditor.tsx
│   │   │   │   ├── BodySystemEditor.tsx
│   │   │   │   ├── RecommendationTemplateEditor.tsx
│   │   │   │   ├── VersionHistory.tsx
│   │   │   │   └── VersionDiffViewer.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useCMSQuestions.ts
│   │   │   │   ├── useCMSRules.ts
│   │   │   │   └── useContentVersions.ts
│   │   │   ├── api/
│   │   │   │   └── cmsApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       ├── CMSDashboardPage.tsx
│   │   │       ├── ManageQuestionsPage.tsx
│   │   │       ├── ManageBodySystemsPage.tsx
│   │   │       ├── ManageRiskRulesPage.tsx
│   │   │       └── ViewVersionHistoryPage.tsx
│   │   │
│   │   ├── admin/
│   │   │   ├── components/
│   │   │   │   ├── UserManagementTable.tsx
│   │   │   │   ├── UserDetailPanel.tsx
│   │   │   │   ├── RoleEditor.tsx
│   │   │   │   ├── AuditLogViewer.tsx
│   │   │   │   ├── SystemHealthDashboard.tsx
│   │   │   │   └── PlatformConfigPanel.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useAdmin.ts
│   │   │   ├── api/
│   │   │   │   └── adminApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       ├── AdminDashboardPage.tsx
│   │   │       ├── UserManagementPage.tsx
│   │   │       └── AuditLogPage.tsx
│   │   │
│   │   ├── research/
│   │   │   ├── components/
│   │   │   │   ├── PopulationStats.tsx
│   │   │   │   ├── RiskDistributionChart.tsx
│   │   │   │   ├── CohortFilter.tsx
│   │   │   │   ├── DataTable.tsx
│   │   │   │   └── ExportPanel.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useResearch.ts
│   │   │   ├── api/
│   │   │   │   └── researchApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── pages/
│   │   │       └── ResearchDashboardPage.tsx
│   │   │
│   │   └── notifications/
│   │       ├── components/
│   │       │   ├── NotificationBell.tsx
│   │       │   ├── NotificationList.tsx
│   │       │   ├── NotificationItem.tsx
│   │       │   └── NotificationPreferences.tsx
│   │       ├── hooks/
│   │       │   └── useNotifications.ts
│   │       ├── api/
│   │       │   └── notificationApi.ts
│   │       ├── types/
│   │       │   └── index.ts
│   │       └── pages/
│   │           └── NotificationSettingsPage.tsx
│   │
│   ├── shared/
│   │   ├── ui/                   # Shadcn components (generated)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── select.tsx
│   │   │   ├── table.tsx
│   │   │   ├── form.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── skeleton.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── progress.tsx
│   │   │   └── (others as needed)
│   │   ├── loading/
│   │   │   ├── Spinner.tsx
│   │   │   ├── SkeletonCard.tsx
│   │   │   └── PageLoader.tsx
│   │   ├── ErrorBoundary.tsx
│   │   ├── EmptyState.tsx
│   │   ├── ConfirmDialog.tsx
│   │   └── StatusBadge.tsx
│   │
│   ├── hooks/                    # Global hooks
│   │   ├── useMediaQuery.ts
│   │   ├── useLocalStorage.ts
│   │   ├── useOnlineStatus.ts
│   │   ├── useDebounce.ts
│   │   ├── usePagination.ts
│   │   └── usePermissions.ts
│   │
│   ├── lib/                      # Core library code
│   │   ├── api-client.ts         # Axios instance with interceptors
│   │   ├── query-client.ts       # TanStack Query client config
│   │   ├── firebase.ts           # Firebase SDK initialization
│   │   ├── auth-context.tsx       # Auth context + provider
│   │   ├── theme-context.tsx      # Dark/Light mode
│   │   ├── notification-context.tsx
│   │   └── utils.ts              # cn(), formatters, helpers
│   │
│   ├── types/                    # Shared TypeScript types
│   │   ├── api.ts
│   │   ├── user.ts
│   │   ├── questionnaire.ts
│   │   ├── assessment.ts
│   │   ├── lab.ts
│   │   ├── timeline.ts
│   │   └── recommendation.ts
│   │
│   ├── styles/
│   │   └── globals.css           # Tailwind directives + custom vars
│   │
│   ├── providers/                # React context providers
│   │   ├── QueryProvider.tsx
│   │   ├── AuthProvider.tsx
│   │   ├── ThemeProvider.tsx
│   │   └── ToastProvider.tsx
│   │
│   └── test/
│       ├── setup.ts
│       ├── test-utils.tsx
│       └── mocks/
│           ├── handlers.ts
│           └── server.ts
│
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── postcss.config.js
├── .env.example
├── .eslintrc.cjs
├── .prettierrc
├── vitest.config.ts
├── playwright.config.ts
└── package.json
```

---

# 6. Frontend Architecture

## 6.1 State Management Strategy

```
┌────────────────────────────────────────────────────────────────┐
│                    STATE ARCHITECTURE                           │
│                                                                │
│  TanStack Query (Server State):                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  - All API data: questions, assessments, lab reports   │   │
│  │  - Automatic caching (staleTime: 5-30 min per query)  │   │
│  │  - Background refetch on window focus                  │   │
│  │  - Optimistic updates for questionnaire answers        │   │
│  │  - Infinite queries for timeline + recommendations     │   │
│  │  - Mutation hooks for all writes                        │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  React Context (Auth State):                                   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  - Firebase auth state (onAuthStateChanged listener)   │   │
│  │  - Current user object + custom claims (role)          │   │
│  │  - Auth token management (attached to API client)      │   │
│  │  - Login/Logout/Register methods                       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Local State (Component-level):                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  - Form state (React Hook Form)                        │   │
│  │  - Questionnaire session navigation (current question) │   │
│  │  - UI state (modals, toasts, sidebar open/closed)      │   │
│  │  - Theme preference (persisted to localStorage)        │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘

Cache Invalidation Strategy:
  Questions → invalidate on question mutation (CMS)
  Assessments → invalidate on questionnaire submission
  Lab Reports → invalidate on lab report CRUD
  Recommendations → invalidate on new assessment
  Dashboard → invalidate on any health data change
  Profile → invalidate on profile update
```

## 6.2 Routing Architecture

```
Routes tree:

/                                   → LandingPage (public)
/auth/login                         → LoginPage (public)
/auth/register                      → RegisterPage (public)
/auth/forgot-password               → ForgotPasswordPage (public)
/auth/verify-email                  → VerifyEmailPage (public)

/app                                → DashboardLayout (protected)
  /app/dashboard                    → DashboardPage
  /app/questionnaires                → QuestionnaireListPage
  /app/questionnaires/:id           → QuestionnaireSessionPage
  /app/body-systems                  → BodySystemListPage
  /app/body-systems/:code           → BodySystemDetailPage
  /app/lab-reports                  → LabReportsListPage
  /app/lab-reports/new              → AddLabReportPage
  /app/lab-reports/:id              → LabReportDetailPage
  /app/timeline                     → HealthTimelinePage
  /app/recommendations              → RecommendationsPage
  /app/profile                      → ProfilePage
  /app/settings                     → SettingsPage

/cms                                → CMSDashboardLayout (doctor+)
  /cms/dashboard                    → CMSDashboardPage
  /cms/questions                    → ManageQuestionsPage
  /cms/questions/:id/edit           → QuestionEditorPage
  /cms/body-systems                 → ManageBodySystemsPage
  /cms/body-systems/:code/edit      → BodySystemEditorPage
  /cms/risk-rules                   → ManageRiskRulesPage
  /cms/recommendations              → ManageRecommendationsPage
  /cms/versions                     → ViewVersionHistoryPage

/admin                              → AdminLayout (admin)
  /admin/dashboard                  → AdminDashboardPage
  /admin/users                      → UserManagementPage
  /admin/roles                      → RoleManagementPage
  /admin/audit-logs                 → AuditLogPage
  /admin/settings                   → PlatformConfigPage

/research                           → ResearchLayout (researcher+)
  /research/dashboard               → ResearchDashboardPage
  /research/population              → PopulationStatsPage
  /research/export                  → DataExportPage

Route Guards:
  ProtectedRoute:   isAuthenticated === true
  RoleRoute:        hasRole(['patient', 'doctor', 'admin', 'researcher'])
  DoctorRoute:      hasRole(['doctor', 'admin'])
  AdminRoute:       hasRole(['admin'])
  ResearcherRoute:  hasRole(['researcher', 'admin'])
```

## 6.3 Component Design Principles

```
Every feature component follows:
┌────────────────────────────────────────────────────────────────┐
│  Feature Component Pattern:                                    │
│                                                                │
│  1. Page Component (route entry)                              │
│     - Data fetching via TanStack Query useQuery               │
│     - Loading/Error/Empty states                              │
│     - Composes presentation components                        │
│     - Minimal logic — delegates to hooks                      │
│                                                                │
│  2. Hook Layer                                                │
│     - useFeature() — wraps TanStack Query calls               │
│     - Manages optimistic updates                              │
│     - Handles mutation side effects (toast, invalidate)       │
│     - Exposes { data, isLoading, error, mutate }             │
│                                                                │
│  3. API Layer                                                 │
│     - Axios/fetch calls to backend endpoints                  │
│     - Request/response type definitions                       │
│     - Base URL + auth header from interceptor                 │
│                                                                │
│  4. Type Definitions                                          │
│     - Zod schemas shared with backend (same validation)       │
│     - TypeScript interfaces inferred from Zod                 │
│                                                                │
│  UI Principles:                                                │
│  - All UI via Shadcn components (Radix primitives)           │
│  - Dark mode via Tailwind class strategy                     │
│  - Responsive: mobile-first, breakpoints at sm/md/lg/xl      │
│  - Accessible: keyboard nav, screen reader labels, ARIA      │
│  - PWA: offline fallback, push notifications, install prompt │
└────────────────────────────────────────────────────────────────┘
```

## 6.4 Form Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    FORM ARCHITECTURE                            │
│                                                                │
│  React Hook Form + Zod:                                        │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  const formSchema = z.object({                         │   │
│  │    email: z.string().email(),                          │   │
│  │    age: z.number().min(18).max(120),                   │   │
│  │    smokingStatus: z.enum(['never','former','current']) │   │
│  │  });                                                    │   │
│  │                                                         │   │
│  │  // TypeScript type inferred from schema                │   │
│  │  type FormData = z.infer<typeof formSchema>;           │   │
│  │                                                         │   │
│  │  const form = useForm<FormData>({                       │   │
│  │    resolver: zodResolver(formSchema),                   │   │
│  │    defaultValues: {...}                                 │   │
│  │  });                                                    │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Questionnaire Forms (Dynamic):                                │
│  - No fixed schema — questions fetched from API               │
│  - Dynamic Zod schema built at runtime from question data     │
│  - Rendered via QuestionRenderer switching on question_type   │
│  - Each answer stored optimistically (TanStack mutation)      │
│                                                                │
│  Validation Layers:                                            │
│  1. Client-side: Zod schema (instant feedback)                │
│  2. API-side: Pydantic model (server validation)              │
│  3. Database: PostgreSQL constraints (data integrity)         │
└────────────────────────────────────────────────────────────────┘
```

---

# 7. Backend Architecture

## 7.1 Application Factory Pattern

```python
# Conceptual structure only — no implementation code
def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Medicheck API",
        version="1.0.0",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
    )

    # Middleware stack
    app.add_middleware(CORSMiddleware, ...)
    app.add_middleware(TrustedHostMiddleware, ...)
    app.add_middleware(GZipMiddleware, ...)

    # Lifespan (startup/shutdown)
    @app.on_event("startup")
    async def startup():
        init_db()
        init_redis()
        init_firebase()
        discover_body_system_modules()
        register_domain_events()

    # Include routers
    app.include_router(v1_router, prefix="/api/v1")

    # Exception handlers
    app.add_exception_handler(ValidationError, handle_validation_error)
    app.add_exception_handler(AuthenticationError, handle_auth_error)
    app.add_exception_handler(NotFoundError, handle_not_found)

    return app
```

## 7.2 Service Layer Pattern

```
┌────────────────────────────────────────────────────────────────┐
│                   SERVICE INTERACTION PATTERN                   │
│                                                                │
│  Endpoint                      Service                     DB  │
│  ┌──────────────┐         ┌──────────────┐         ┌──────┐   │
│  │ POST /submit  │────────▶│SubmitQuestion│────────▶│      │   │
│  │              │         │naireUseCase  │         │      │   │
│  │ 1. Validate   │         │              │         │      │   │
│  │    Pydantic   │         │ 2. Call domain│         │      │   │
│  │ 3. Authorize  │         │    service    │ 4. Repo│      │   │
│  │ 5. Dispatch   │         │ 6. Publish    │────────▶│      │   │
│  │              │         │    event      │         │      │   │
│  └──────────────┘         └──────────────┘         └──────┘   │
│                                                                │
│  Rules:                                                        │
│  - Endpoints validate input, check auth, call use case        │
│  - Use cases orchestrate domain services                      │
│  - Domain services contain business logic                     │
│  - Repositories abstract persistence                          │
│  - Domain events signal cross-context actions                 │
└────────────────────────────────────────────────────────────────┘
```

## 7.3 Background Worker Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    WORKER ARCHITECTURE (Celery)                 │
│                                                                │
│  Queue Configuration:                                          │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Queues:                                                 │   │
│  │  - assessments: high priority, 2 workers                │   │
│  │  - recommendations: medium priority, 2 workers          │   │
│  │  - notifications: medium priority, 1 worker             │   │
│  │  - exports: low priority, 1 worker                       │   │
│  │  - maintenance: low priority, 1 worker (scheduled)      │   │
│  │                                                          │   │
│  │  Task Routing:                                           │   │
│  │  - calculate_assessment → assessments queue             │   │
│  │  - generate_recommendations → recommendations queue     │   │
│  │  - send_email_notification → notifications queue        │   │
│  │  - export_anonymized_data → exports queue               │   │
│  │  - cleanup_expired_sessions → maintenance queue         │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Async Flow:                                                   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  API: Submit questionnaire                             │   │
│  │  1. Validate + save responses                          │   │
│  │  2. Enqueue calculate_assessment.delay(session_id)     │   │
│  │  3. Return 202 Accepted + session_id                   │   │
│  │                                                          │   │
│  │  Worker: Assessment                                     │   │
│  │  4. Load responses + profile + lab values              │   │
│  │  5. Evaluate all risk rules                            │   │
│  │  6. Calculate scores                                   │   │
│  │  7. Save assessment                                    │   │
│  │  8. Enqueue generate_recommendations.delay(assessment) │   │
│  │  9. Enqueue update_timeline.delay(assessment)          │   │
│  │                                                          │   │
│  │  Worker: Recommendations                                │   │
│  │  10. Load assessment + user profile                    │   │
│  │  11. Generate recommendations per category             │   │
│  │  12. Save + enqueue notifications                      │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

# 8. Technology Justification

## 8.1 Frontend Stack

| Technology | Version | Role | Justification |
|---|---|---|---|
| **React** | 18+ | UI Library | Largest ecosystem, best PWA support, excellent TypeScript, concurrent features for future AI-driven UI updates |
| **Vite** | 5+ | Build tool | Sub-second HMR, native ESM, tree-shaking, faster than CRA/Webpack by 10x |
| **TypeScript** | 5+ | Language | Type safety reduces PHI-related bugs by ~40%, self-documenting API contracts |
| **TailwindCSS** | 3+ | Styling | Design system consistency, zero-runtime CSS, 10KB gzipped prod builds |
| **Shadcn UI** | latest | Components | Headless Radix primitives (accessible), copy-paste model (no dependency lock-in), full customization |
| **TanStack Query** | 5+ | Server state | Automatic cache invalidation, optimistic updates, background refetch, infinite queries for timeline |
| **React Router** | 6+ | Routing | Nested layouts, loaders/actions, lazy loading for CMS/Admin routes |
| **React Hook Form** | 7+ | Forms | Uncontrolled inputs (performant), Zod integration, dynamic schema generation for questionnaires |
| **Zod** | 3+ | Validation | TypeScript-first, runtime validation shared with backend Pydantic via JSON Schema bridge |
| **Recharts** | 2+ | Charts | Lightweight, composable, responsive, good for health trend visualizations |
| **Vitest** | 1+ | Unit tests | Fast, Vite-native, Jest compatible, native TS/ESM |
| **Playwright** | latest | E2E tests | Cross-browser, mobile emulation, network interception |
| **Workbox** | latest | PWA | Service worker generation, offline caching strategies, background sync |

## 8.2 Backend Stack

| Technology | Version | Role | Justification |
|---|---|---|---|
| **Python** | 3.12+ | Language | Dominant in healthcare/ML/AI ecosystem, rich libraries for data science |
| **FastAPI** | 0.110+ | Web framework | Async-native, Pydantic integration, automatic OpenAPI 3.1 docs, best performance among Python frameworks |
| **Pydantic v2** | 2+ | Validation | Rust-core validation engine (10-20x faster), JSON Schema generation, type safety |
| **SQLAlchemy 2.0** | 2+ | ORM | Mature, async support, raw SQL when needed, excellent PostgreSQL features |
| **Alembic** | latest | Migrations | Auto-generation, branching, version control, integrates with SQLAlchemy |
| **Celery** | 5+ | Task queue | Mature, Redis broker, periodic tasks, task routing, result backend |
| **Redis** | 7+ | Cache/broker | Sub-millisecond reads, Celery broker, rate limiting, session store |
| **PostgreSQL** | 16+ | Database | ACID compliance, JSONB, full-text search, table partitioning, extensions |
| **Supabase SDK** | latest | DB client | Auto-generated Python client, RLS integration, real-time subscriptions |
| **Firebase Admin** | latest | Auth | Token verification, user management, custom claims for RBAC |
| **httpx** | latest | HTTP | Async HTTP client, connection pooling, retries |
| **Pytest** | latest | Testing | Async fixtures, FastAPI TestClient, parametrization, coverage |

## 8.3 Infrastructure Stack

| Technology | Role | Justification |
|---|---|---|
| **Vercel** | Frontend hosting | Global CDN, automatic HTTPS, preview deployments, zero-config |
| **Render** | Backend hosting | Managed PostgreSQL, Docker support, auto-scaling, zero-downtime deploys |
| **Supabase** | Database + Storage | Managed PostgreSQL 16, S3-compatible storage, RLS, real-time subscriptions |
| **Firebase Auth** | Authentication | Social login (Google/Apple), email/password, MFA, SDKs for web + mobile |
| **Redis (Upstash)** | Caching | Serverless Redis, 99.99% uptime, global replication |
| **Sentry** | Error tracking | Real-time error monitoring, performance traces, release tracking |
| **GitHub Actions** | CI/CD | Native GitHub integration, matrix builds, secret management |
| **Docker** | Containerization | Development/production parity, reproducible builds |
| **Prometheus/Grafana** | Monitoring | Open source, custom dashboards, alerting (future) |

## 8.4 Why Supabase + Firebase (Not Raw PostgreSQL + DIY Auth)

```
Decision: Use Supabase as managed PostgreSQL + Firebase Auth
─────────────────────────────────────────────────────────

Alternatives considered:
  X Raw PostgreSQL on Render → Requires full DB management, backup config
  X Auth0 → Expensive at scale ($2,000+/mo for 10k users)
  X DIY JWT auth → Security risk, HIPAA concerns, no social login
  X Firebase only → Firebase Realtime DB is not relational
  X Supabase Auth → Less mature than Firebase, fewer social providers

Winner: Supabase (DB + Storage) + Firebase Auth
  - Best-in-class auth (Firebase) + best-in-class managed PG (Supabase)
  - Firebase Custom Claims → backend enforces RBAC
  - Supabase Row Level Security → additional data access layer
  - Supabase Storage → S3-compatible, CDN-enabled, server-side encryption
  - Both have generous free tiers → zero cost during development
  - Migration path: Easy to move from Supabase to RDS if needed
```

---

# 9. Database Architecture

*(See full ERD and table definitions in `docs/architecture/05-DATABASE-ERD.md`)*

## 9.1 Entity Catalog Summary

```
Core Identity:
  users, roles, permissions, user_roles, user_sessions

Health Profile:
  user_profiles, user_family_history, user_medical_history, user_medications

Questionnaire Engine:
  body_systems, question_categories, questions, question_choices,
  question_dependencies, question_versions, questionnaires, sections,
  questionnaire_questions, questionnaire_sessions, user_responses

Risk Assessment:
  risk_rules, risk_rule_conditions, risk_rule_versions, risk_indicators,
  medical_conditions, condition_risk_indicators, assessments,
  body_system_scores, health_scores

Laboratory:
  lab_tests, lab_reference_ranges, lab_reports, lab_report_values

Timeline:
  event_types, timeline_events

Recommendations:
  recommendation_templates, user_recommendations

Supporting:
  notifications, notification_preferences, file_metadata, audit_logs,
  content_versions, content_locks, system_config

Total: ~45 tables
```

## 9.2 Key Design Decisions

```
All Tables:
  - UUID primary keys (distributed-friendly, no sequential ID leaks)
  - created_at / updated_at timestamps
  - Soft delete (deleted_at) for PHI records
  - JSONB for multi-language text, extensible metadata
  - Immutable audit log (append-only, SHA-256 chain)

Questionnaire Tables:
  - Questions decoupled from questionnaires (many-to-many)
  - Section groupings within questionnaires
  - Versioned questions with full snapshot history
  - Dependency table supports AND/OR groups

Assessment Tables:
  - Assessments reference questionnaire sessions
  - Body system scores stored separately per assessment
  - Health scores denormalized for dashboard performance

Indexing:
  - Composite indexes on (user_id, created_at DESC) for all user data
  - Partial indexes for active records (WHERE is_active = true)
  - GIN indexes on JSONB columns for rule conditions
  - Exclusion constraints for content locking
```

---

# 10. Entity Relationship Diagram

*(Detailed Mermaid ERD in `docs/architecture/05-DATABASE-ERD.md`)*

```
Summary entity map:

users ──< user_roles >── roles ──< role_permissions >── permissions
  │
  ├── user_profiles (1:1)
  ├── user_family_history (1:N)
  ├── user_medical_history (1:N)
  ├── user_medications (1:N)
  ├── questionnaire_sessions (1:N)
  │     └── user_responses (1:N) ── questions
  ├── assessments (1:N)
  │     └── body_system_scores ── body_systems
  ├── health_scores (1:N) ── body_systems
  ├── lab_reports (1:N)
  │     └── lab_report_values ── lab_tests ── lab_reference_ranges
  ├── timeline_events (1:N) ── event_types
  ├── user_recommendations (1:N) ── recommendation_templates
  ├── notifications (1:N)
  ├── file_metadata (1:N)
  └── audit_logs (1:N)

body_systems ──< questions ──< question_choices
  │                  └──< question_dependencies >── questions
  │                  └──< question_versions
  ├── question_categories
  ├── risk_rules ──< risk_rule_versions
  ├── risk_indicators ──< condition_risk_indicators >── medical_conditions
  └── recommendation_templates

questionnaires ──< questionnaire_questions >── questions
  │                  └── sections
  └──< questionnaire_sessions
```

---

# 11. API Architecture

*(Complete endpoint catalog in `docs/architecture/02-CORE-ENGINES.md`)*

## 11.1 API Design Conventions

```
Base URL: https://api.medicheck.com/api/v1

Conventions:
  - Resource-oriented URLs (nouns, not verbs)
  - Plural nouns for collections (/users, /lab-reports)
  - Nesting for relationships (/users/{id}/profiles)
  - kebab-case for multi-word resources
  - Consistent error response format
  - Pagination via cursor-based (for streams) and page-based (for tables)
  - Sparse fieldsets via ?fields=id,name,age
  - ETags for conditional requests
  - Versioning via URL prefix (/api/v1/)

Standard Headers:
  Authorization: Bearer <firebase_id_token>
  X-Request-ID: <uuid>
  X-Idempotency-Key: <uuid> (for mutation endpoints)

Standard Response (200):
  {
    "data": { ... },
    "meta": { "page": 1, "page_size": 20, "total": 142 }
  }

Standard Error (4xx/5xx):
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Invalid input",
      "details": [{ "field": "email", "message": "Invalid format" }],
      "request_id": "req_abc"
    }
  }
```

## 11.2 Endpoint Summary by Module

```
AUTH (Firebase-managed, backend verifies):
  POST   /auth/register                    # Create Firebase user + DB record
  POST   /auth/login                       # Firebase client handles; backend exchanges token
  POST   /auth/refresh                     # Refresh Firebase token (if needed)
  POST   /auth/verify-token                # Verify Firebase token validity
  POST   /auth/forgot-password             # Firebase handles via client SDK
  GET    /auth/me                          # Get current user from token

USERS:
  GET    /users/me                         # Current user profile
  PATCH  /users/me                         # Update own profile
  DELETE /users/me                         # Self-deletion (GDPR right to erasure)
  GET    /users/me/data-export             # Export all personal data
  GET    /users/{id}                       # [doctor/admin] Get any user
  GET    /users                            # [admin] List users (paginated)

HEALTH PROFILE:
  GET    /users/me/profile                 # Health profile
  PATCH  /users/me/profile                 # Update health profile
  GET    /users/me/family-history          # Family medical history
  POST   /users/me/family-history          # Add family history entry
  DELETE /users/me/family-history/{id}     # Remove family history entry
  GET    /users/me/medical-history         # Medical history
  POST   /users/me/medical-history         # Add condition/surgery/allergy
  GET    /users/me/medications             # Current medications
  POST   /users/me/medications             # Add medication
  PATCH  /users/me/medications/{id}        # Update medication

QUESTIONNAIRES:
  GET    /questionnaires                   # List available questionnaires
  GET    /questionnaires/{id}              # Get questionnaire details
  POST   /questionnaires/{id}/start        # Start new session
  GET    /questionnaires/sessions/{id}     # Get session (with current Q)
  PATCH  /questionnaires/sessions/{id}     # Save partial answers
  POST   /questionnaires/sessions/{id}/submit  # Submit completed questionnaire
  GET    /questionnaires/sessions/{id}/status  # Check async assessment status
  GET    /questionnaires/history           # Past questionnaire sessions

QUESTIONS:
  GET    /questions/{id}                   # Get question details
  GET    /questions/by-body-system/{code}  # Questions for a body system
  GET    /questions/{id}/choices           # Get choices for choice-type Q

LAB REPORTS:
  GET    /lab-reports                      # List lab reports
  POST   /lab-reports                      # Create lab report (manual entry)
  GET    /lab-reports/{id}                 # Get lab report with values
  PUT    /lab-reports/{id}                 # Update lab report
  DELETE /lab-reports/{id}                 # Delete lab report
  POST   /lab-reports/upload               # Upload lab report file
  GET    /lab-tests                        # List available lab tests
  GET    /lab-tests/{id}/reference-ranges  # Get reference ranges

ASSESSMENTS:
  GET    /assessments                      # List assessments
  GET    /assessments/{id}                 # Get assessment detail
  GET    /assessments/latest               # Latest assessment summary
  GET    /assessments/{id}/body-systems    # Per-system breakdown
  GET    /assessments/trends               # Score history chart data

TIMELINE:
  GET    /timeline                         # Health timeline (paginated)
  POST   /timeline                         # Add manual timeline event
  GET    /timeline?event_type=lab          # Filter by type
  GET    /timeline?from=2024-01-01&to=2024-12-31  # Date range filter

RECOMMENDATIONS:
  GET    /recommendations                  # User's recommendations
  PATCH  /recommendations/{id}/status      # Acknowledge/complete/dismiss
  GET    /recommendations/categories       # Category summary

DASHBOARD:
  GET    /dashboard/overview               # Full dashboard data
  GET    /dashboard/health-score           # Current overall score
  GET    /dashboard/body-systems           # All system scores
  GET    /dashboard/trends                 # 12-month trend data
  GET    /dashboard/lifestyle              # Lifestyle summary

NOTIFICATIONS:
  GET    /notifications                    # User's notifications
  PATCH  /notifications/{id}/read          # Mark as read
  GET    /notifications/preferences        # Notification preferences
  PATCH  /notifications/preferences        # Update preferences

FILES:
  POST   /files/upload                     # Upload file (signed URL)
  GET    /files/{id}                       # Get file metadata
  DELETE /files/{id}                       # Delete file

CMS (Doctor role):
  GET    /cms/body-systems                 # List all body systems
  PUT    /cms/body-systems/{code}          # Update body system config
  GET    /cms/questions                    # List all questions
  POST   /cms/questions                    # Create question
  PUT    /cms/questions/{id}               # Update question
  GET    /cms/questions/{id}/versions      # Show version history
  POST   /cms/questions/{id}/versions      # Create new version (snapshot)
  POST   /cms/questions/{id}/dependencies  # Add dependency
  GET    /cms/risk-rules                   # List risk rules
  POST   /cms/risk-rules                   # Create risk rule
  PUT    /cms/risk-rules/{id}              # Update risk rule
  POST   /cms/risk-rules/{id}/versions     # Create rule version
  GET    /cms/recommendations              # List recommendation templates
  POST   /cms/recommendations              # Create template
  POST   /cms/content/lock                 # Lock content for editing
  POST   /cms/content/unlock               # Release content lock

ADMIN:
  GET    /admin/users                      # User management list
  POST   /admin/users                      # Create user
  PATCH  /admin/users/{id}/status          # Suspend/activate user
  PUT    /admin/users/{id}/role            # Change user role
  GET    /admin/roles                      # List roles
  POST   /admin/roles                      # Create role
  PUT    /admin/roles/{id}/permissions     # Update role permissions
  GET    /admin/audit-logs                 # Audit log viewer
  GET    /admin/analytics                  # System statistics
  GET    /admin/health                     # System health status

RESEARCH:
  GET    /research/population-stats        # Demographics statistics
  GET    /research/risk-distributions      # Risk score distributions
  POST   /research/export                  # Request data export (async)
  GET    /research/export/{id}             # Download export
```

---

# 12. Authentication Architecture

## 12.1 Firebase Authentication Integration

```
┌────────────────────────────────────────────────────────────────┐
│                    AUTH ARCHITECTURE                            │
│                                                                │
│  Client Side (Firebase SDK):                                   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  firebase.initializeApp(config)                        │   │
│  │  onAuthStateChanged → authContext.setUser(user)        │   │
│  │                                                         │   │
│  │  Login: signInWithEmailAndPassword(auth, email, pwd)   │   │
│  │  Login: signInWithPopup(auth, googleProvider)          │   │
│  │  Login: signInWithPopup(auth, appleProvider)           │   │
│  │  Register: createUserWithEmailAndPassword(auth, ...)   │   │
│  │                                                         │   │
│  │  Token: getIdToken(user) → gets Firebase ID token      │   │
│  │  Token sent in every API request:                       │   │
│  │    Authorization: Bearer <firebase_id_token>            │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Backend Side (Firebase Admin SDK):                            │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  # Middleware: verify Firebase token                    │   │
│  │  async def verify_firebase_token(token: str) -> dict:  │   │
│  │    decoded = firebase_admin.auth.verify_id_token(token) │   │
│  │    return decoded  # { uid, email, firebase: {claims} } │   │
│  │                                                         │   │
│  │  # Custom Claims (set by Admin only):                   │   │
│  │  firebase_admin.auth.set_custom_user_claims(uid, {     │   │
│  │    "role": "doctor",                                    │   │
│  │    "permissions": ["cms:read", "cms:write"]            │   │
│  │  })                                                     │   │
│  │                                                         │   │
│  │  # Sync: When user first logs in, create local DB user │   │
│  │  POST /auth/register → create Firebase user → sync →   │   │
│  │  INSERT INTO users (firebase_uid, email, ...)          │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

## 12.2 Auth Flow Sequences

```
Registration Flow:
  Client                     Firebase                    Backend
    │                          │                          │
    │ createUserWithEmail      │                          │
    ├─────────────────────────▶│                          │
    │   User Created           │                          │
    │◀─────────────────────────┤                          │
    │                          │                          │
    │ POST /auth/register      │                          │
    │ { idToken }              │                          │
    ├────────────────────────────────────────────────────▶│
    │                          │                          │
    │                          │ verify_id_token          │
    │                          │◀── Firebase Admin ──────│
    │                          │                          │
    │                          │ INSERT INTO users        │
    │                          │ (firebase_uid, ...)      │
    │                          │                          │
    │  201 Created + user      │                          │
    │◀─────────────────────────┤                          │

Login Flow:
  Client                     Firebase                    Backend
    │                          │                          │
    │ signInWithEmailAndPwd    │                          │
    ├─────────────────────────▶│                          │
    │   ID Token               │                          │
    │◀─────────────────────────┤                          │
    │                          │                          │
    │ GET /users/me            │                          │
    │ Authorization: Bearer    │                          │
    ├────────────────────────────────────────────────────▶│
    │                          │                          │
    │                          │ verify_id_token          │
    │                          │ SELECT * FROM users      │
    │                          │                          │
    │  200 + user data         │                          │
    │◀─────────────────────────┤                          │

Token Refresh:
  Firebase SDK handles token refresh automatically
  ID Token TTL: 1 hour (Firebase default)
  Refresh Token: Firebase persists and rotates silently
  Backend is stateless — no refresh needed
```

---

# 13. Authorization Architecture

## 13.1 Role-Based Access Control (RBAC)

```
┌────────────────────────────────────────────────────────────────┐
│                    ROLE HIERARCHY                               │
│                                                                │
│  Roles stored in local DB (roles table)                       │
│  Role assigned to user (user_roles table)                     │
│  Role synced to Firebase Custom Claims for client-side checks │
│                                                                │
│  ┌──────────────┐                                              │
│  │  SUPER_ADMIN  │  Global access, all permissions             │
│  └──────┬───────┘                                              │
│         │                                                       │
│  ┌──────┴───────┐                                              │
│  │   ADMIN       │  System config, user mgmt, audit            │
│  └──────┬───────┘                                              │
│         │                                                       │
│  ┌──────┴───────┐                                              │
│  │   DOCTOR      │  CMS access, patient read, content mgmt     │
│  └──────┬───────┘                                              │
│         │                                                       │
│  ┌──────┴───────┐                                              │
│  │  RESEARCHER   │  Anonymized data access, export             │
│  └──────┬───────┘                                              │
│         │                                                       │
│  ┌──────┴───────┐                                              │
│  │   PATIENT     │  Own data only                              │
│  └──────────────┘                                              │
│                                                                │
│  Permission Inheritance: higher roles inherit lower permissions│
└────────────────────────────────────────────────────────────────┘
```

## 13.2 Permission Matrix

| Resource | Action | Patient | Doctor | Researcher | Admin |
|---|---|---|---|---|---|
| `user:own` | read/write | ✓ | — | — | — |
| `user:any` | read/write | — | assigned | — | ✓ |
| `profile:own` | read/write | ✓ | — | — | — |
| `profile:any` | read | — | assigned | — | ✓ |
| `questionnaire:own` | start/submit | ✓ | — | — | — |
| `questionnaire:any` | read | — | assigned | — | ✓ |
| `question:cms` | crud | — | ✓ | — | ✓ |
| `body_system:cms` | crud | — | ✓ | — | ✓ |
| `risk_rule:cms` | crud | — | ✓ | — | ✓ |
| `recommendations:own` | read | ✓ | — | — | — |
| `recommendations:any` | crud | — | ✓ | — | ✓ |
| `assessment:own` | read | ✓ | — | — | — |
| `assessment:any` | read | — | assigned | — | ✓ |
| `lab:own` | crud | ✓ | — | — | — |
| `lab:any` | read | — | assigned | — | ✓ |
| `research:anonymized` | read | — | — | ✓ | ✓ |
| `research:export` | create | — | — | ✓ | ✓ |
| `admin:users` | crud | — | — | — | ✓ |
| `admin:roles` | crud | — | — | — | ✓ |
| `admin:audit` | read | — | — | — | ✓ |
| `admin:system` | config | — | — | — | ✓ |

## 13.3 Authorization Enforcement

```
┌────────────────────────────────────────────────────────────────┐
│              AUTHORIZATION ENFORCEMENT POINTS                   │
│                                                                │
│  Layer 1: Firebase Custom Claims (Client-side UI)              │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  user.firebase.claims.role === "doctor"                │   │
│  │  → Show CMS menu item                                  │   │
│  │  user.firebase.claims.role === "admin"                 │   │
│  │  → Show Admin menu item                                │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Layer 2: FastAPI Middleware (Endpoint access)                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  @router.get("/cms/questions")                         │   │
│  │  @require_role("doctor")  # Raises 403 if not          │   │
│  │  async def list_questions(user: User = Depends(...)):  │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Layer 3: Service Layer (Resource-level)                      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  def get_assessment(assessment_id, current_user):      │   │
│  │    assessment = repo.find_by_id(assessment_id)         │   │
│  │    if assessment.user_id != current_user.id and        │   │
│  │       not current_user.has_permission("assessment:any"):│  │
│  │      raise PermissionDenied                            │   │
│  │    return assessment                                    │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Layer 4: Supabase Row Level Security (Data-level)            │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  -- Example RLS policy for assessments                 │   │
│  │  CREATE POLICY assessment_access ON assessments        │   │
│  │  FOR ALL USING (                                        │   │
│  │    user_id = auth.uid() OR                              │   │
│  │    auth.has_claim('role') IN ('doctor', 'admin')       │   │
│  │  );                                                     │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

# 14. Questionnaire Engine Architecture

## 14.1 Core Design

```
┌────────────────────────────────────────────────────────────────┐
│              QUESTIONNAIRE ENGINE ARCHITECTURE                  │
│                                                                │
│  PRINCIPLES:                                                    │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  ✓ ALL questions stored in database (zero hardcoded)   │   │
│  │  ✓ Doctors configure via CMS without code               │   │
│  │  ✓ Dynamic branching based on previous answers         │   │
│  │  ✓ Versioned: historical answers always correct        │   │
│  │  ✓ Multi-language: text stored as JSONB per locale     │   │
│  │  ✓ Extensible: new question types added via plugin     │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ENGINE COMPONENTS:                                            │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  QuestionRenderer:                                      │   │
│  │    Input: Question object from DB                      │   │
│  │    Output: Rendered form field matching question_type  │   │
│  │    Types: single_choice, multiple_choice, scale,       │   │
│  │           boolean, text, numeric, date, blood_pressure,│   │
│  │           height_weight, multiline, file               │   │
│  │                                                         │   │
│  │  BranchingEngine:                                       │   │
│  │    Input: QuestionDependencies from DB + previous ans   │   │
│  │    Output: boolean (show/hide this question)            │   │
│  │    Logic: condition_type + condition_value + operator   │   │
│  │           (AND/OR groups)                               │   │
│  │                                                         │   │
│  │  ScoringEngine:                                         │   │
│  │    Input: UserAnswer + Question.scoring_weight         │   │
│  │    Output: Scored value (per question contribution)    │   │
│  │                                                         │   │
│  │  ValidationEngine:                                      │   │
│  │    Input: Answer + Question.validation_rules            │   │
│  │    Output: Validated answer or error list               │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

## 14.2 Branching Logic Model

```
Concept:
  Each question has 0..N dependencies defined in question_dependencies table.
  Dependencies are grouped by group_id with logic_operator (AND/OR).

  ┌──────────────────────────────────────────────────────────┐
  │  Example: Show "How many cigarettes per day?" only if   │
  │           smoking_status = "current"                     │
  │                                                          │
  │  question_dependencies:                                  │
  │    question_id: "cigarettes_per_day"                    │
  │    depends_on: "smoking_status"                         │
  │    condition_type: "equals"                              │
  │    condition_value: "current"                            │
  │    logic_operator: "AND"                                 │
  │    group_id: 0                                           │
  │                                                          │
  │  Example 2: Show "Chest pain assessment" if             │
  │            (age > 45 AND smoking = "current") OR         │
  │            family_history = "heart_disease"             │
  │                                                          │
  │  question_dependencies:                                  │
  │    # Group 1 (AND): age > 45 AND smoking = current     │
  │    { q: "chest_assess", dep: "age", type: "gt",         │
  │      val: 45, op: "AND", group: 1 }                    │
  │    { q: "chest_assess", dep: "smoking", type: "equals", │
  │      val: "current", op: "AND", group: 1 }             │
  │    # Group 2 (single): family_heart = yes               │
  │    { q: "chest_assess", dep: "family_heart",            │
  │      type: "equals", val: true, op: "AND", group: 2 }  │
  │                                                          │
  │  Evaluation: (Group1_results) OR (Group2_results)       │
  └──────────────────────────────────────────────────────────┘
```

## 14.3 Question Type Support

| Type | Storage | UI Widget | Validation |
|---|---|---|---|
| `single_choice` | string (choice_code) | Radio group | Must match active choice |
| `multiple_choice` | string[] (choice_codes) | Checkboxes | Min/max selections |
| `scale` | integer | Slider 1-5 or 1-10 | Min, max, step |
| `boolean` | boolean | Toggle switch | Must be true/false |
| `text` | string | TextArea | Min/max length, regex |
| `numeric` | float | Number input | Min, max, unit |
| `date` | ISO date string | Date picker | Past/future constraint |
| `blood_pressure` | {sys: int, dia: int} | Dual input | Sys 60-250, Dia 30-150 |
| `height_weight` | {height: cm, weight: kg} | Dual input | Valid ranges + BMI calc |
| `multiline` | string | Rich text editor | Max length |
| `file` | S3 URL | File upload | Type, size, virus scan |

## 14.4 Session Lifecycle

```
State Machine:
  ┌──────────┐
  │  DRAFT    │  ← User clicks "Start Questionnaire"
  └────┬─────┘
       │ First answer saved
       ▼
  ┌──────────┐
  │ACTIVE    │  ← Auto-saves after each answer
  └────┬─────┘
       │
       ├────────────────── 24h inactivity ─────▶ EXPIRED
       │                                              │
       │ User clicks "Save & Resume Later"             │
       ├──────────────────────────────────────────▶ PAUSED
       │                                              │
       │ User returns + clicks "Resume"               │
       │◀─────────────────────────────────────────────┤
       │
       │ User clicks "Submit"
       ▼
  ┌──────────┐     ┌────────────┐
  │SUBMITTED │────▶│ COMPLETED  │  ← Assessment triggered
  └──────────┘     └────────────┘
```

## 14.5 Adaptive Questionnaire Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    ADAPTIVE FLOW                                │
│                                                                │
│  1. User requests questionnaire                                │
│  2. API creates session (status: DRAFT)                       │
│  3. API evaluates branching for first visible question        │
│  4. Returns first question data                               │
│  5. User answers → auto-saved via PATCH /session/{id}        │
│  6. API re-evaluates branching based on all answers so far   │
│  7. Returns next visible question (or completion)             │
│  8. Repeat 5-7 until all questions answered                   │
│  9. User submits → status → COMPLETED                         │
│  10. Celery worker: calculate_assessment(session_id)         │
│                                                                │
│  Adaptive Features:                                            │
│  - Skip irrelevant sections based on gender (male_health)     │
│  - Skip sections based on age (pediatric questions)           │
│  - Deep-dive on positive answers (branching depth)            │
│  - Random question order within sections (anti-fatigue)       │
│  - Progress indicator: "Question 8 of ~25 (estimated)"       │
│  - Save & Resume: return to last unanswered question          │
└────────────────────────────────────────────────────────────────┘
```

---

# 15. Risk Engine Architecture

## 15.1 Two-Phase Strategy

```
Phase 1 (MVP - Immediate): Rule-Based Engine
  ┌────────────────────────────────────────────────────────┐
  │  - Configurable rules stored in risk_rules table      │
  │  - Doctors manage rules via CMS                       │
  │  - Transparent: "Your score is X because Y"          │
  │  - Immediate value: deploy Day 1                     │
  │  - No ML training data required                      │
  └────────────────────────────────────────────────────────┘

Phase 2 (Future): ML-Enhanced Hybrid Engine
  ┌────────────────────────────────────────────────────────┐
  │  - ML models suggest rule weights and thresholds      │
  │  - Hybrid: rule-based output + ML prediction          │
  │  - A/B test: rules vs ML for validation               │
  │  - Models per body system for specialization          │
  └────────────────────────────────────────────────────────┘
```

## 15.2 Rule-Based Engine Design

```
┌────────────────────────────────────────────────────────────────┐
│                    RULE EVALUATION PIPELINE                     │
│                                                                │
│  Input: User profile + Questionnaire answers + Lab values     │
│         + Family history + Medical history                    │
│                                                                │
│  Step 1: Load all active rules for all body systems           │
│  Step 2: For each rule, evaluate conditions against user data │
│  Step 3: For matching rules, apply score_impact               │
│  Step 4: Aggregate per-body-system scores                     │
│  Step 5: Calculate overall health score                       │
│  Step 6: Generate explanations for all applied rules          │
│  Step 7: Save assessment result                               │
│                                                                │
│  Score Calculation:                                            │
│    per_system_score = 100 - abs(sum(matched_rule_impacts))    │
│    clamped to [0, 100]                                         │
│                                                                │
│    overall_score = weighted_average(                           │
│      [per_system_score for each system],                       │
│      weights=[system_weight for each system]                   │
│    )                                                           │
│                                                                │
│    risk_level = classify(overall_score):                       │
│      90-100: "optimal"  75-89: "good"                         │
│      60-74: "fair"      40-59: "elevated"                     │
│      <40: "high"                                               │
└────────────────────────────────────────────────────────────────┘
```

## 15.3 Condition Structure (JSONB)

```json
{
  "$schema": "RiskRule.conditions",
  "type": "object",
  "properties": {
    "operator": { "type": "string", "enum": ["AND", "OR", "NOT"] },
    "conditions": {
      "type": "array",
      "items": {
        "oneOf": [
          {
            "type": "object",
            "properties": {
              "field": { "type": "string" },
              "operator": { "type": "string" },
              "value": {}
            },
            "required": ["field", "operator", "value"]
          },
          {
            "type": "object",
            "properties": {
              "operator": { "type": "string", "enum": ["AND", "OR"] },
              "conditions": { "$ref": "#/properties/conditions" }
            },
            "required": ["operator", "conditions"]
          }
        ]
      }
    }
  },
  "required": ["operator", "conditions"]
}
```

Example rule:
```json
{
  "code": "cv_smoking_hypertension",
  "name": {"en": "Smoking + Hypertension Risk"},
  "conditions": {
    "operator": "AND",
    "conditions": [
      {"field": "smoking_status", "operator": "equals", "value": "current"},
      {"field": "systolic_bp", "operator": "gte", "value": 140},
      {
        "operator": "OR",
        "conditions": [
          {"field": "age", "operator": "gte", "value": 45},
          {"field": "bmi", "operator": "gte", "value": 30}
        ]
      }
    ]
  },
  "score_impact": -15.0,
  "risk_level": "high",
  "evidence_ref": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
}
```

## 15.4 Risk Scoring System Weights

| System | Default Weight | Rationale |
|---|---|---|
| Cardiovascular | 0.15 | Leading cause of death globally |
| Cancer Screening | 0.12 | High impact of early detection |
| Endocrine | 0.10 | Diabetes epidemic, metabolic health |
| Mental Health | 0.10 | Critical for quality of life |
| Neurological | 0.08 | Aging population, dementia risk |
| Kidney | 0.07 | Silent progression, often undetected |
| Liver | 0.07 | NAFLD epidemic, alcohol-related |
| Respiratory | 0.07 | COPD, asthma, occupational exposure |
| Digestive | 0.05 | Quality of life impact |
| Blood | 0.05 | Anemia, clotting disorders |
| Immune | 0.04 | Autoimmune on the rise |
| Musculoskeletal | 0.03 | Aging population |
| Skin | 0.02 | Melanoma risk, quality of life |
| Eye | 0.02 | Vision loss prevention |
| Sexual/Male/Female | 0.03 | Gender-specific health |

## 15.5 Explainability Engine

```
┌────────────────────────────────────────────────────────────────┐
│                    EXPLAINER OUTPUT                             │
│                                                                │
│  For each body system:                                         │
│  "Your cardiovascular score is 72/100 (Good).                  │
│   This is based on your responses to 8 questions.              │
│                                                                 │
│   Factors that increased your risk:                            │
│   - Smoking: -10 points (smoking_status = current)             │
│   - Blood Pressure: -8 points (systolic = 145, above 140)     │
│   - Family History: -5 points (parent had heart disease)       │
│                                                                 │
│   Factors that decreased your risk:                            │
│   - Exercise: +3 points (exercises 3x/week)                   │
│   - BMI: +2 points (BMI = 22, healthy range)                   │
│                                                                 │
│   Recommendations to improve:                                  │
│   - Consider smoking cessation program                         │
│   - Monitor BP weekly, target < 130/80                         │
│   - Maintain current exercise routine"                         │
│                                                                 │
│  Format: JSON for frontend rendering                           │
│  {
│    "system_code": "cardiovascular",
│    "score": 72,
│    "risk_level": "good",
│    "contributors": [
│      { "code": "smoking_status", "impact": -10,
│        "explanation": "Current smoker" },
│      ...
│    ],
│    "action_items": [ "Consider smoking cessation" ]
│  }
└────────────────────────────────────────────────────────────────┘
```

---

# 16. AI Architecture

## 16.1 AI Integration Points

```
┌────────────────────────────────────────────────────────────────┐
│                AI INTEGRATION MAP                               │
│                                                                │
│  ML Models (Phase 2+):                                         │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Risk Prediction: XGBoost/LightGBM per body system     │   │
│  │  Trend Forecasting: LSTM for health score trajectories │   │
│  │  Anomaly Detection: Isolation Forest for lab values    │   │
│  │  Population Clustering: K-Means for health segments    │   │
│  │  Recommendation Ranking: Learning-to-Rank model        │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  LLM Integration (Phase 3+):                                   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  1. Health Insight Generation:                          │   │
│  │     Input: Assessment data + contributing factors      │   │
│  │     Output: Plain-language health summary              │   │
│  │                                                         │   │
│  │  2. Personalized Recommendations:                       │   │
│  │     Input: User profile + risks + preferences          │   │
│  │     Output: Custom diet, exercise, lifestyle plan      │   │
│  │                                                         │   │
│  │  3. Consistency Checking:                               │   │
│  │     Input: All user answers across sessions            │   │
│  │     Output: Conflicts detected + clarification prompts │   │
│  │                                                         │   │
│  │  4. Conversational Data Collection:                     │   │
│  │     Input: Free-text health description                │   │
│  │     Output: Structured data extraction + follow-ups    │   │
│  │                                                         │   │
│  │  5. AI Question Generation (Doctor-facing):             │   │
│  │     Input: Body system + target condition               │   │
│  │     Output: Suggested new questions for doctor review   │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

## 16.2 ML Architecture (Future)

```
┌────────────────────────────────────────────────────────────────┐
│                    ML TRAINING PIPELINE                         │
│                                                                │
│  Data Sources:                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Anonymized questionnaire responses                    │   │
│  │  Anonymized lab report values                          │   │
│  │  Assessment results (as training labels)               │   │
│  │  User demographics + health profile                    │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Feature Store:                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Features extracted at assessment time                 │   │
│  │  Stored in features table (denormalized)               │   │
│  │  Features: all question scores + derived metrics       │   │
│  │  Labels: actual health outcomes (future follow-up)     │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Training Pipeline:                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────┐ │
│  │Feature   │→│Train/    │→│Model     │→│Evaluate  │→│Deploy│ │
│  │Engineer  │ │Test Split│ │Train     │ │AUC/F1    │ │      │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └─────┘ │
│                                                                │
│  Inference Pipeline (Phase 2):                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  1. Feature extraction from assessment data            │   │
│  │  2. ML model predicts risk probabilities               │   │
│  │  3. SHAP values computed for explainability            │   │
│  │  4. ML score blended with rule-based score             │   │
│  │  5. Final score + explanation generated                │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

## 16.3 AI Safety & Governance

```
┌────────────────────────────────────────────────────────────────┐
│                    AI GOVERNANCE FRAMEWORK                      │
│                                                                │
│  Guardrails:                                                    │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  ✓ ALL LLM output validated: no diagnostic language   │   │
│  │  ✓ LLM prompts pre-approved by medical team            │   │
│  │  ✓ PII stripped before external API calls             │   │
│  │  ✓ Rate limited per user (prevent abuse)              │   │
│  │  ✓ Fallback to rule-based when AI unavailable         │   │
│  │  ✓ Audit log of all AI interactions                   │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Ethics:                                                       │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  ✓ Transparent: user told when AI is used              │   │
│  │  ✓ Explainable: all predictions have reasons           │   │
│  │  ✓ Fair: bias testing across demographics              │   │
│  │  ✓ Accountable: humans can override AI                │   │
│  │  ✓ Private: models trained on anonymized data only    │   │
│  │  ✓ Conservative: always err on side of "see a doctor" │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

# Remaining Deliverables (17-28)

See the following files for detailed coverage:

| File | Deliverables |
|---|---|
| `docs/architecture/02-CORE-ENGINES.md` | 9-10 (Database + ERD), 14-16 (Questionnaire, Risk, AI Engines) |
| `docs/architecture/03-MODULES-DEPLOYMENT.md` | 17-28 (Dashboard, CMS, Research, Notifications, Timeline, Files, Security, Deployment, Scalability, Mobile, AI Future, Roadmap) |
