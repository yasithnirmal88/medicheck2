from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.base import BaseModel

T = TypeVar("T", bound=BaseModel)

_PAGE_SIZE = 20


class SQLGenericCMSRepository:
    def __init__(self, session: AsyncSession, model_cls: type[T]) -> None:
        self._session = session
        self._model = model_cls

    async def find_by_id(self, id: str) -> T | None:
        stmt = select(self._model).where(
            self._model.id == id,
            self._model.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(
        self,
        *,
        skip: int = 0,
        limit: int = _PAGE_SIZE,
        include_deleted: bool = False,
    ) -> list[T]:
        stmt = select(self._model)
        if not include_deleted:
            stmt = stmt.where(self._model.deleted_at.is_(None))
        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_active(
        self, *, skip: int = 0, limit: int = _PAGE_SIZE
    ) -> list[T]:
        stmt = (
            select(self._model)
            .where(
                self._model.is_active.is_(True),
                self._model.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_field(
        self, field: str, value: Any, *, skip: int = 0, limit: int = _PAGE_SIZE
    ) -> list[T]:
        col = getattr(self._model, field, None)
        if col is None:
            raise ValueError(f"Field {field} not found on {self._model.__name__}")
        stmt = (
            select(self._model)
            .where(col == value, self._model.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_one_by_field(self, field: str, value: Any) -> T | None:
        col = getattr(self._model, field, None)
        if col is None:
            raise ValueError(f"Field {field} not found on {self._model.__name__}")
        stmt = select(self._model).where(col == value, self._model.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_ids(
        self, ids: list[str], *, skip: int = 0, limit: int | None = None
    ) -> list[T]:
        if not ids:
            return []
        stmt = select(self._model).where(
            self._model.id.in_(ids), self._model.deleted_at.is_(None)
        )
        if limit:
            stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_body_system(
        self, body_system_id: str, *, skip: int = 0, limit: int = _PAGE_SIZE
    ) -> list[T]:
        return await self.find_by_field("body_system_id", body_system_id, skip=skip, limit=limit)

    async def find_by_code(self, code: str) -> T | None:
        return await self.find_one_by_field("code", code)

    async def find_by_status(
        self, status: str, *, skip: int = 0, limit: int = _PAGE_SIZE
    ) -> list[T]:
        return await self.find_by_field("status", status, skip=skip, limit=limit)

    async def count(self, include_deleted: bool = False) -> int:
        stmt = select(func.count(self._model.id))
        if not include_deleted:
            stmt = stmt.where(self._model.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def count_by_field(self, field: str, value: Any) -> int:
        col = getattr(self._model, field, None)
        if col is None:
            raise ValueError(f"Field {field} not found on {self._model.__name__}")
        stmt = (
            select(func.count(self._model.id))
            .where(col == value, self._model.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def search(
        self, text_field: str, query: str, *, skip: int = 0, limit: int = _PAGE_SIZE
    ) -> list[T]:
        col = getattr(self._model, text_field, None)
        if col is None:
            raise ValueError(f"Field {text_field} not found on {self._model.__name__}")
        stmt = (
            select(self._model)
            .where(col.ilike(f"%{query}%"), self._model.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, model: T) -> T:
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def update(self, model: T) -> T:
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def soft_delete(self, id: str) -> None:
        from datetime import UTC, datetime

        obj = await self.find_by_id(id)
        if obj:
            obj.deleted_at = datetime.now(UTC)
            await self._session.flush()

    async def restore(self, id: str) -> T | None:
        stmt = select(self._model).where(self._model.id == id)
        result = await self._session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj:
            obj.deleted_at = None
            await self._session.flush()
        return obj

    async def bulk_create(self, models: list[T]) -> list[T]:
        self._session.add_all(models)
        await self._session.flush()
        for m in models:
            await self._session.refresh(m)
        return models

    async def bulk_update_status(
        self, ids: list[str], status: str
    ) -> int:
        from datetime import UTC, datetime

        stmt = (
            select(self._model)
            .where(self._model.id.in_(ids), self._model.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        count = 0
        for obj in result.scalars().all():
            obj.status = status
            obj.updated_at = datetime.now(UTC)
            count += 1
        await self._session.flush()
        return count

    async def bulk_soft_delete(self, ids: list[str]) -> int:
        from datetime import UTC, datetime

        stmt = select(self._model).where(self._model.id.in_(ids))
        result = await self._session.execute(stmt)
        count = 0
        for obj in result.scalars().all():
            obj.deleted_at = datetime.now(UTC)
            count += 1
        await self._session.flush()
        return count
