from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.repositories.sql_admin_repository import (
    SQLAdminRepository,
)


class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SQLAdminRepository(session)

    # body systems
    async def create_body_system(self, user_id: str, data: dict):
        bs = await self.repo.create_body_system(data)
        await self._audit(user_id, "body_system", bs.id, "create", None, data)
        return bs

    async def update_body_system(self, user_id: str, bs_id: str, data: dict):
        old = await self.repo.get_body_system(bs_id)
        bs = await self.repo.update_body_system(bs_id, data)
        await self._audit(
            user_id,
            "body_system",
            bs_id,
            "update",
            old.to_dict() if old else None,
            data,
        )
        return bs

    # indicators
    async def create_indicator(self, user_id: str, data: dict):
        ind = await self.repo.create_indicator(data)
        await self._audit(user_id, "indicator", ind.id, "create", None, data)
        return ind

    async def update_indicator(self, user_id: str, ind_id: str, data: dict):
        old = await self.repo.get_indicator(ind_id)
        ind = await self.repo.update_indicator(ind_id, data)
        await self._audit(
            user_id, "indicator", ind_id, "update", old.to_dict() if old else None, data
        )
        return ind

    async def list_indicators(self, body_system_id: str | None = None):
        return await self.repo.list_indicators(body_system_id)

    # evidence
    async def create_evidence(self, user_id: str, data: dict):
        ev = await self.repo.create_evidence(data)
        await self._audit(user_id, "evidence", ev.id, "create", None, data)
        return ev

    async def list_evidence(self, limit: int = 50):
        return await self.repo.list_evidence(limit)

    # recommendations
    async def create_recommendation(self, user_id: str, data: dict):
        rec = await self.repo.create_recommendation(data)
        await self._audit(user_id, "recommendation", rec.id, "create", None, data)
        return rec

    async def update_recommendation(self, user_id: str, rec_id: str, data: dict):
        old = await self.repo.get_recommendation(rec_id)
        rec = await self.repo.update_recommendation(rec_id, data)
        await self._audit(
            user_id,
            "recommendation",
            rec_id,
            "update",
            old.to_dict() if old else None,
            data,
        )
        return rec

    async def list_recommendations(self, limit: int = 100):
        return await self.repo.list_recommendations(limit)

    async def list_audit_logs(self, entity_type: str | None = None, limit: int = 100):
        return await self.repo.list_audit(entity_type, limit)

    async def _audit(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str | None,
        action: str,
        old_value: dict | None,
        new_value: dict | None,
        reason: str | None = None,
    ):
        payload = {
            "actor_id": user_id,
            "actor_role": "medical_editor",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "changed_at": datetime.now(timezone.utc),
            "old_value": str(old_value) if old_value is not None else None,
            "new_value": str(new_value) if new_value is not None else None,
            "reason": reason,
        }
        await self.repo.create_audit(payload)
