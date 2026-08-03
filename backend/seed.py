import asyncio
from app.infrastructure.database import create_engine, create_session_factory
from app.infrastructure.seed import seed_database

async def run():
    create_engine()
    factory = create_session_factory()
    async with factory() as session:
        await seed_database(session)
    print("Seed completed")

asyncio.run(run())
