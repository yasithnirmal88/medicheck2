from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from redis.asyncio import Redis

from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> Any | None:
        try:
            data = await self._redis.get(key)
            if data is not None:
                return json.loads(data)
            return None
        except Exception as exc:
            logger.warning("Cache get failed for key %s: %s", key, exc)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
    ) -> bool:
        try:
            data = json.dumps(value, default=str)
            await self._redis.setex(key, ttl, data)
            return True
        except Exception as exc:
            logger.warning("Cache set failed for key %s: %s", key, exc)
            return False

    async def delete(self, key: str) -> bool:
        try:
            await self._redis.delete(key)
            return True
        except Exception as exc:
            logger.warning("Cache delete failed for key %s: %s", key, exc)
            return False

    async def exists(self, key: str) -> bool:
        try:
            return await self._redis.exists(key) > 0
        except Exception as exc:
            logger.warning("Cache exists check failed for key %s: %s", key, exc)
            return False

    async def clear_pattern(self, pattern: str) -> int:
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor=cursor, match=pattern, count=100
                )
                if keys:
                    await self._redis.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
            return deleted
        except Exception as exc:
            logger.warning("Cache clear pattern failed for %s: %s", pattern, exc)
            return 0

    async def remember(
        self,
        key: str,
        ttl: int,
        callback: Callable[[], Any],
    ) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await callback()
        await self.set(key, value, ttl)
        return value

    @property
    def client(self) -> Redis:
        return self._redis
