from __future__ import annotations

from collections.abc import AsyncGenerator

from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.connection import ConnectionPool

from app.core.cache import CacheService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_pool: ConnectionPool | None = None
_redis_client: AsyncRedis | None = None
_cache_service: CacheService | None = None


async def create_redis_pool() -> ConnectionPool:
    global _pool
    if _pool is not None:
        return _pool

    _pool = ConnectionPool.from_url(
        settings.redis_url,
        max_connections=20,
        decode_responses=True,
    )
    logger.info("Redis connection pool created")
    return _pool


async def get_redis_client() -> AsyncRedis:
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    pool = await create_redis_pool()
    _redis_client = AsyncRedis(connection_pool=pool)
    await _redis_client.ping()
    logger.info("Redis client initialized")
    return _redis_client


async def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is not None:
        return _cache_service

    client = await get_redis_client()
    _cache_service = CacheService(client)
    return _cache_service


async def get_redis() -> AsyncGenerator[AsyncRedis, None]:
    client = await get_redis_client()
    try:
        yield client
    except Exception:
        raise
    finally:
        pass


async def close_redis() -> None:
    global _pool, _redis_client, _cache_service
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None
    _cache_service = None
    logger.info("Redis connection closed")


async def redis_health_check() -> bool:
    try:
        client = await get_redis_client()
        return await client.ping()
    except Exception:
        return False
