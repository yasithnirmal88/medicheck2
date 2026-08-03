# Release Notes — v1.0.0-RC1

**Date**: 2026-07-23
**Status**: Release Candidate 1

## Overview

Medicheck v1.0.0-RC1 is the first release candidate of a clinical decision support system (CDSS) that processes patient questionnaire responses through a rule-based clinical reasoning engine to generate health assessments and evidence-based recommendations.

## New Features

### Core Clinical Engine
- **Questionnaire Engine**: Supports 7 question types (yes/no, multiple choice, scale, numeric, decimal, date, text) with validation rules, branching logic, and dependency evaluation
- **Clinical Decision Support Engine (CDSE)**: 7-stage rule-based processing pipeline that maps answers → indicators → conditions → recommendations
- **Scoring Engine**: Normalized scoring (0–100%) with configurable severity thresholds (low/moderate/high/critical)
- **Report Engine**: Structured health assessment reports with comparison capability

### Knowledge Graph
- Complete clinical ontology with 29 indicators, 19 conditions, 30 recommendations, 15 lab tests
- Link tables: question→indicator, option→indicator, indicator→condition, condition→recommendation, condition→lab, indicator→evidence
- ICD-10 codes for conditions, LOINC codes for lab tests
- Evidence levels (A–D) with source traceability

### API
- 80+ REST endpoints organized across 11 router groups
- Full CRUD for all clinical content via CMS API
- Knowledge graph search and traversal
- Report generation and comparison

### Admin & CMS
- Body system management (18 medical systems)
- Clinical indicator management
- Medical evidence reference management
- Recommendation management
- Publishing workflow (change request → approval → snapshot)
- Full audit logging for all content changes
- Role-based access control (9 roles)

### Security
- Firebase JWT authentication
- Role-based authorization with granular permissions
- Rate limiting (100 requests/60s)
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- CSRF protection
- Request ID tracking and audit logging

### Performance
- Redis caching (300s TTL)
- Batch-loaded CDSE (7 queries max per assessment)
- 6 database indexes on frequently queried columns
- N+1 query elimination

### Infrastructure
- Docker Compose deployment (api, ui, postgres, redis, nginx)
- Prometheus + Grafana monitoring
- Alembic database migrations
- Automated seed data loading

## Breaking Changes

None — this is the initial release.

## Known Issues

See [Known Issues](KNOWN_ISSUES.md) for complete list.

## Upgrade Notes

N/A — fresh installation.

## System Requirements

- Docker 24+ (recommended) or Python 3.12+ / Node.js 20+
- PostgreSQL 16+ or SQLite (development only)
- Redis 7+
- 2 GB RAM minimum, 4 GB recommended
