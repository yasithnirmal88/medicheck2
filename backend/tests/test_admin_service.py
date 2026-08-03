import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.admin_service import AdminService
from app.infrastructure.persistence.models.body_system import BodySystemModel


@pytest.mark.asyncio
async def test_admin_create_indicator_and_evidence(db_session: AsyncSession):
    session = db_session
    svc = AdminService(session)
    user_id = "test-user"

    bs = BodySystemModel(id="bs1", code="TEST", name="Test BS", display_order=1)
    session.add(bs)
    await session.commit()

    ind = await svc.create_indicator(
        user_id,
        {
            "key": "test-indicator",
            "name": "Test Indicator",
            "description": "Unit test indicator",
            "body_system_id": "bs1",
        },
    )
    assert ind is not None
    ev = await svc.create_evidence(
        user_id,
        {
            "key": "test-evidence",
            "title": "Test Evidence",
            "source": "Unit Test",
            "year": 2026,
            "url": "https://example.org",
        },
    )
    assert ev is not None
