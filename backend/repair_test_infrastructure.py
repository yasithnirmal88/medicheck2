from pathlib import Path

root = Path(r"C:\Users\DELL\Documents\GitHub\medicheck")
conftest = root / "backend/tests/conftest.py"
text = conftest.read_text(encoding="utf-8")
text = text.replace(
    "async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:\n    test_settings = get_test_settings()",
    "async def client(\n    db_session: AsyncSession, test_settings: Settings\n) -> AsyncGenerator[AsyncClient, None]:"
)
text = text.replace(
    "    config_module.settings = test_settings\n    app_main.settings = test_settings\n    database_module.settings = test_settings\n    database_module._engine = None\n    database_module._async_session_factory = None\n\n    app = create_app()",
    "    originals = (\n        config_module.settings, app_main.settings, database_module.settings,\n        database_module._engine, database_module._async_session_factory,\n    )\n    config_module.settings = test_settings\n    app_main.settings = test_settings\n    database_module.settings = test_settings\n    database_module._engine = None\n    database_module._async_session_factory = None\n\n    app = create_app()"
)
text = text.replace(
    "    app.dependency_overrides.clear()\n\n\n@pytest.fixture\ndef sample_user",
    "    app.dependency_overrides.clear()\n    (\n        config_module.settings, app_main.settings, database_module.settings,\n        database_module._engine, database_module._async_session_factory,\n    ) = originals\n\n\n@pytest.fixture\ndef sample_user"
)
conftest.write_text(text, encoding="utf-8")

for path in (root / "backend/tests").glob("test_*.py"):
    text = path.read_text(encoding="utf-8")
    if 'sqlite+aiosqlite:///:memory:' not in text:
        continue
    text = text.replace("from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine\n", "from sqlalchemy.ext.asyncio import AsyncSession\n")
    text = text.replace("from sqlalchemy.pool import NullPool\n", "")
    text = text.replace("from app.infrastructure.database import Base\n", "")
    text = text.replace("async def test_admin_create_indicator_and_evidence():", "async def test_admin_create_indicator_and_evidence(db_session: AsyncSession):")
    text = text.replace("async def test_cdse_process_simple_flow():", "async def test_cdse_process_simple_flow(db_session: AsyncSession):")
    text = text.replace("async def test_links_and_graph_build(tmp_path):", "async def test_links_and_graph_build(db_session: AsyncSession):")
    text = text.replace("async def test_profile_repository_create_and_personal_upsert(tmp_path):", "async def test_profile_repository_create_and_personal_upsert(db_session: AsyncSession):")
    text = text.replace("async def test_report_generation_flow():", "async def test_report_generation_flow(db_session: AsyncSession):")
    start = '    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=NullPool)\n    async with engine.begin() as conn:\n        await conn.run_sync(Base.metadata.create_all)\n    Session = async_sessionmaker(engine, expire_on_commit=False)\n    async with Session() as session:\n'
    text = text.replace(start, "    session = db_session\n")
    # Dedent the body formerly nested under async with.
    lines = text.splitlines()
    marker = next((i for i,l in enumerate(lines) if l.strip() == "session = db_session"), None)
    if marker is not None:
        for i in range(marker + 1, len(lines)):
            if lines[i].startswith("        "):
                lines[i] = lines[i][4:]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
