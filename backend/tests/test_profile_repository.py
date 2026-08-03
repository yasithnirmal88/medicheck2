import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.personal_info import PersonalInfoModel
from app.infrastructure.persistence.repositories.sql_profile_repository import (
    SQLProfileRepository,
)


@pytest.mark.asyncio
async def test_profile_repository_create_and_personal_upsert(db_session: AsyncSession):
    session = db_session
    repo = SQLProfileRepository(session)
    user_id = "u1"
    profile = await repo.create_for_user(user_id)
    assert profile is not None
    await repo.upsert_personal_info(profile.id, {"full_name": "Test User"})

    # Query personal info directly to avoid lazy loading issues
    q = select(PersonalInfoModel).where(PersonalInfoModel.profile_id == profile.id)
    r = await session.execute(q)
    pi = r.scalars().first()
    assert pi is not None
    assert pi.full_name == "Test User"
