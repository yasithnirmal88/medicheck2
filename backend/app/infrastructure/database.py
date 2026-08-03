from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from alembic import command
from alembic.config import Config

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

_engine: Any = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=_NAMING_CONVENTION)


def create_engine() -> Any:
    global _engine
    if _engine is not None:
        return _engine

    connect_args = {}
    engine_kwargs: dict[str, Any] = {
        "echo": settings.is_development,
    }

    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args
    else:
        engine_kwargs.update(
            {
                "pool_size": 20,
                "max_overflow": 10,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            }
        )

    _engine = create_async_engine(settings.database_url, **engine_kwargs)
    logger.info("Database engine created for %s", settings.database_url)
    return _engine


def create_session_factory() -> async_sessionmaker[AsyncSession]:
    global _async_session_factory
    if _async_session_factory is not None:
        return _async_session_factory

    engine = create_engine()
    _async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = create_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def init_db() -> None:
    """Run Alembic migrations."""
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    logger.info("Database migrations applied successfully")


async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    logger.info("Database engine disposed")
