"""Audit-schema separation tests.

Proves the physical/logical isolation of the high-volume audit tables
(``ai_interaction_audits``, ``audit_logs``) from the hot clinical schema:

- schema resolution is a pure function of the database URL (PostgreSQL ->
  ``audit``, SQLite -> default namespace);
- both audit models carry the resolved schema marker and are structurally
  join-proof (no foreign keys, no relationships);
- nothing else in the schema references them (no inbound FKs), so no
  clinical query can ever need to join against them;
- the write path (AIAuditService) and aggregate reads work through the
  schema-qualified models.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_audit_service import AIAuditService
from app.infrastructure.database import Base
from app.infrastructure.persistence.models.ai_interaction_audit import (
    AIInteractionAuditModel,
)
from app.infrastructure.persistence.models.audit_log import AuditLogModel
from app.infrastructure.persistence.models.base import resolve_audit_schema

_AUDIT_TABLES = {"ai_interaction_audits", "audit_logs"}


class TestAuditSchemaResolution:
    def test_postgres_urls_resolve_to_audit_schema(self):
        assert (
            resolve_audit_schema("postgresql+asyncpg://u:p@host/db") == "audit"
        )
        assert resolve_audit_schema("postgres://u:p@host/db") == "audit"
        assert (
            resolve_audit_schema("postgresql://u:p@host/db?sslmode=require")
            == "audit"
        )

    def test_sqlite_urls_resolve_to_default_namespace(self):
        assert resolve_audit_schema("sqlite+aiosqlite:///./test.db") is None
        assert resolve_audit_schema("sqlite+aiosqlite:///:memory:") is None
        assert resolve_audit_schema("sqlite:///local.db") is None

    def test_models_carry_the_resolved_schema(self):
        from app.infrastructure.persistence.models.base import AUDIT_SCHEMA

        assert AIInteractionAuditModel.__table__.schema == AUDIT_SCHEMA
        assert AuditLogModel.__table__.schema == AUDIT_SCHEMA


class TestAuditTablesAreJoinProof:
    @pytest.mark.parametrize(
        "model", [AIInteractionAuditModel, AuditLogModel]
    )
    def test_no_foreign_keys_or_relationships(self, model):
        assert list(model.__table__.foreign_keys) == []
        assert list(model.__mapper__.relationships) == []

    def test_nothing_references_the_audit_tables(self):
        for table in Base.metadata.tables.values():
            if table.name in _AUDIT_TABLES:
                continue
            referred = {fk.column.table.name for fk in table.foreign_keys}
            assert not (referred & _AUDIT_TABLES), (
                f"{table.name} has a foreign key into an audit table: "
                f"{referred & _AUDIT_TABLES}"
            )


class TestAuditWritePathThroughSchema:
    @pytest.mark.asyncio
    async def test_ai_audit_roundtrip(self, db_session: AsyncSession):
        svc = AIAuditService(db_session)
        await svc.record(
            trace_id="trace-audit-schema",
            session_id="sess-audit-schema",
            request_type="report_explanation",
            provider="stub",
            model="",
            prompt_version="2.0",
            language="en",
            literacy_level="standard",
            status="valid",
        )
        await db_session.commit()
        count = (
            await db_session.execute(
                select(func.count(AIInteractionAuditModel.id)).where(
                    AIInteractionAuditModel.trace_id == "trace-audit-schema"
                )
            )
        ).scalar_one()
        assert count == 1

    @pytest.mark.asyncio
    async def test_audit_log_roundtrip(self, db_session: AsyncSession):
        from datetime import UTC, datetime

        db_session.add(
            AuditLogModel(
                actor_id="admin-1",
                entity_type="user",
                entity_id="u-1",
                action="update",
                changed_at=datetime.now(UTC),
            )
        )
        await db_session.commit()
        count = (
            await db_session.execute(
                select(func.count(AuditLogModel.id)).where(
                    AuditLogModel.actor_id == "admin-1"
                )
            )
        ).scalar_one()
        assert count == 1
