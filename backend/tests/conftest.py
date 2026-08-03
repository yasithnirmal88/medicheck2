from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.core.config as config_module
import app.infrastructure.database as database_module
import app.main as app_main
from app.core.config import Settings
from app.domain.entities.user import User
from app.infrastructure.database import Base, get_db
from app.main import create_app


def get_test_settings(database_url: str) -> Settings:
    return Settings(
        environment="development",
        log_level="DEBUG",
        database_url=database_url,
        redis_url="redis://localhost:6379/15",
        cors_origins="*",
        allowed_hosts="*",
        firebase_credentials_json='{"type": "service_account"}',
    )


@pytest.fixture(scope="session")
def test_settings(tmp_path_factory) -> Settings:
    tmp_dir = tmp_path_factory.mktemp("pytest-db")
    db_file = tmp_dir / "test_db.sqlite"
    database_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    return get_test_settings(database_url)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session(test_settings: Settings) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an isolated temporary SQLite database per test session.

    Uses a shared test_settings fixture so the database URL is consistent
    across the HTTP client and SQLAlchemy engine.
    """
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Use checkfirst=True semantics to avoid attempting to recreate existing indexes
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(bind=sync_conn, checkfirst=True))

    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(bind=sync_conn, checkfirst=True))

    await engine.dispose()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, test_settings: Settings
) -> AsyncGenerator[AsyncClient, None]:
    originals = (
        config_module.settings, app_main.settings, database_module.settings,
        database_module._engine, database_module._async_session_factory,
    )
    config_module.settings = test_settings
    app_main.settings = test_settings
    database_module.settings = test_settings
    database_module._engine = None
    database_module._async_session_factory = None

    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    (
        config_module.settings, app_main.settings, database_module.settings,
        database_module._engine, database_module._async_session_factory,
    ) = originals


@pytest.fixture
def sample_user() -> User:
    return User(
        id=uuid.uuid4().hex,
        firebase_uid="test-firebase-uid-123",
        email="test@example.com",
        full_name="Test User",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles=set(),
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )


@pytest.fixture
def sample_inactive_user() -> User:
    return User(
        id=uuid.uuid4().hex,
        firebase_uid="test-firebase-uid-inactive",
        email="inactive@example.com",
        full_name="Inactive User",
        avatar_url=None,
        email_verified=False,
        is_active=False,
        roles=set(),
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )


@pytest.fixture
def mock_firebase_token() -> str:
    return "mock-firebase-id-token"
