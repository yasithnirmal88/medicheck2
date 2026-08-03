from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.audit_log import AuditLogModel
from app.infrastructure.persistence.repositories.sql_generic_cms_repository import (
    SQLGenericCMSRepository,
)

_PAGE_SIZE = 50


class CMSAuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SQLGenericCMSRepository(session, AuditLogModel)

    async def log(
        self,
        actor_id: str | None,
        actor_role: str | None,
        entity_type: str,
        entity_id: str | None,
        action: str,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
        status_code: int | None = None,
        method: str | None = None,
        path: str | None = None,
    ) -> dict[str, Any]:
        entry = AuditLogModel(
            actor_id=actor_id,
            actor_role=actor_role,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changed_at=datetime.now(UTC),
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id,
            status_code=status_code,
            method=method,
            path=path,
        )
        created = await self._repo.create(entry)
        return created.to_dict()

    async def search(
        self,
        actor_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        action: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        query: str | None = None,
        skip: int = 0,
        limit: int = _PAGE_SIZE,
    ) -> dict[str, Any]:
        stmt = select(AuditLogModel).where(AuditLogModel.deleted_at.is_(None))

        if actor_id:
            stmt = stmt.where(AuditLogModel.actor_id == actor_id)
        if entity_type:
            stmt = stmt.where(AuditLogModel.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(AuditLogModel.entity_id == entity_id)
        if action:
            stmt = stmt.where(AuditLogModel.action == action)
        if date_from:
            stmt = stmt.where(AuditLogModel.changed_at >= date_from)
        if date_to:
            stmt = stmt.where(AuditLogModel.changed_at <= date_to)
        if query:
            stmt = stmt.where(
                or_(
                    AuditLogModel.entity_type.ilike(f"%{query}%"),
                    AuditLogModel.entity_id.ilike(f"%{query}%"),
                    AuditLogModel.actor_id.ilike(f"%{query}%"),
                    AuditLogModel.reason.ilike(f"%{query}%"),
                    AuditLogModel.action.ilike(f"%{query}%"),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = stmt.order_by(AuditLogModel.changed_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        items = [row.to_dict() for row in result.scalars().all()]

        return {"items": items, "total": total, "skip": skip, "limit": limit}

    async def get_timeline(
        self, entity_type: str, entity_id: str,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(AuditLogModel)
            .where(
                AuditLogModel.entity_type == entity_type,
                AuditLogModel.entity_id == entity_id,
                AuditLogModel.deleted_at.is_(None),
            )
            .order_by(AuditLogModel.changed_at.asc())
        )
        result = await self._session.execute(stmt)
        return [row.to_dict() for row in result.scalars().all()]

    async def get_diffs(
        self, entity_type: str, entity_id: str,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(AuditLogModel)
            .where(
                AuditLogModel.entity_type == entity_type,
                AuditLogModel.entity_id == entity_id,
                AuditLogModel.deleted_at.is_(None),
                AuditLogModel.old_value.is_not(None),
                AuditLogModel.new_value.is_not(None),
            )
            .order_by(AuditLogModel.changed_at.asc())
        )
        result = await self._session.execute(stmt)
        entries = result.scalars().all()

        diffs = []
        for entry in entries:
            old = {}
            new = {}
            try:
                if entry.old_value:
                    old = json.loads(entry.old_value)
                if entry.new_value:
                    new = json.loads(entry.new_value)
            except (json.JSONDecodeError, TypeError):
                pass

            changed_fields = []
            all_keys = set(old.keys()) | set(new.keys())
            for key in sorted(all_keys):
                old_val = old.get(key)
                new_val = new.get(key)
                if old_val != new_val:
                    changed_fields.append({
                        "field": key,
                        "old_value": old_val,
                        "new_value": new_val,
                    })

            diffs.append({
                "id": entry.id,
                "action": entry.action,
                "changed_at": entry.changed_at.isoformat(),
                "actor_id": entry.actor_id,
                "reason": entry.reason,
                "changed_fields": changed_fields,
            })
        return diffs

    async def export(
        self,
        entity_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        format: str = "json",
    ) -> list[dict[str, Any]] | str:
        stmt = select(AuditLogModel).where(AuditLogModel.deleted_at.is_(None))
        if entity_type:
            stmt = stmt.where(AuditLogModel.entity_type == entity_type)
        if date_from:
            stmt = stmt.where(AuditLogModel.changed_at >= date_from)
        if date_to:
            stmt = stmt.where(AuditLogModel.changed_at <= date_to)
        stmt = stmt.order_by(AuditLogModel.changed_at.desc())

        result = await self._session.execute(stmt)
        items = [row.to_dict() for row in result.scalars().all()]

        if format == "csv":
            header = "id,actor_id,actor_role,entity_type,entity_id,action,changed_at,reason,ip_address,method,path\n"
            rows = [
                f"{e['id']},{e.get('actor_id','')},{e.get('actor_role','')},"
                f"{e['entity_type']},{e.get('entity_id','')},{e['action']},"
                f"{e.get('changed_at','')},{e.get('reason','')},"
                f"{e.get('ip_address','')},{e.get('method','')},{e.get('path','')}"
                for e in items
            ]
            return header + "\n".join(rows)
        return items

    async def get_stats(
        self, days: int = 30,
    ) -> dict[str, Any]:
        from datetime import timedelta

        since = datetime.now(UTC) - timedelta(days=days)

        count_stmt = select(func.count(AuditLogModel.id)).where(
            AuditLogModel.changed_at >= since,
            AuditLogModel.deleted_at.is_(None),
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        action_stmt = (
            select(AuditLogModel.action, func.count(AuditLogModel.id).label("count"))
            .where(AuditLogModel.changed_at >= since, AuditLogModel.deleted_at.is_(None))
            .group_by(AuditLogModel.action)
        )
        action_result = await self._session.execute(action_stmt)
        by_action = {row.action: row.count for row in action_result.all()}

        entity_stmt = (
            select(AuditLogModel.entity_type, func.count(AuditLogModel.id).label("count"))
            .where(AuditLogModel.changed_at >= since, AuditLogModel.deleted_at.is_(None))
            .group_by(AuditLogModel.entity_type)
            .order_by(func.count(AuditLogModel.id).desc())
            .limit(10)
        )
        entity_result = await self._session.execute(entity_stmt)
        by_entity = {row.entity_type: row.count for row in entity_result.all()}

        actor_stmt = (
            select(AuditLogModel.actor_id, func.count(AuditLogModel.id).label("count"))
            .where(AuditLogModel.changed_at >= since, AuditLogModel.deleted_at.is_(None))
            .group_by(AuditLogModel.actor_id)
            .order_by(func.count(AuditLogModel.id).desc())
            .limit(10)
        )
        actor_result = await self._session.execute(actor_stmt)
        top_actors = [
            {"actor_id": row.actor_id, "actions": row.count}
            for row in actor_result.all() if row.actor_id
        ]

        return {
            "period_days": days,
            "total_actions": total,
            "by_action": by_action,
            "by_entity_type": by_entity,
            "top_actors": top_actors,
        }
