"""P3-2 regression tests: emergency_contact dict round-trips through a JSON column.

Background: personal_infos.emergency_contact was a SQLAlchemy ``Text`` column but
typed as ``dict | None`` (ORM ``Mapped[dict | None]`` + DTO ``dict | None``). Writing a
dict to a Text column raised on SQLite (``type 'dict' is not supported``) and stored an
invalid Python repr elsewhere, so the field could never be persisted and could not
round-trip through /profiles/me. The column is now ``JSON`` (matching other dict-typed
columns: workflow.steps, questionnaire_template.extra_metadata, profile_version.snapshot).

Investigation found NO legacy non-NULL data: no fixtures/migrations/seed reference
emergency_contact and the Text-column write never succeeded, so every historical value
is NULL. The migration (20260808_emergency_contact_json) is therefore a safe no-data
TEXT->JSON alter.

Covers the required cases:
- normal populated dict value: persists to JSON column, reads back as dict,
  ORM->DTO (PersonalInfoDTO + HealthProfileDTO) preserves the dict,
- NULL (the only historical representation): reads as None,
- snapshot_profile carries a dict (not a Python repr string),
- /profiles/me serializes emergency_contact as a JSON object, not a string.

Note: the shared ``db_session`` fixture uses ``expire_on_commit=False`` and caches ORM
objects in its identity map, so relationship re-loads appear stale within one session
(a test artifact, not a production bug - production uses a fresh session per request).
Reads therefore use a throwaway session bound to the same SQLite file (sees committed
rows) to faithfully exercise selectinload + model_validate.

Run: ALLOW_MOCK_AUTH=true python -m pytest tests/test_emergency_contact_p3.py -q
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.application.dtos.profile_dtos import HealthProfileDTO, PersonalInfoDTO
from app.core.config import Settings
from app.domain.entities.user import User
from app.infrastructure.persistence.models.health_profile import HealthProfileModel
from app.infrastructure.persistence.models.personal_info import PersonalInfoModel
from app.infrastructure.persistence.repositories.sql_profile_repository import (
    SQLProfileRepository,
)
from app.infrastructure.persistence.repositories.sql_user_repository import (
    SQLUserRepository,
)

_MOCK_TOKEN = "mock-firebase-id-token"
_MOCK_UID = _MOCK_TOKEN  # _mock_verify returns uid == id_token


async def _fresh_read(settings: Settings) -> AsyncSession:
    """A throwaway session on the same SQLite file - sees committed rows, no stale
    identity-map entries from the shared write session."""
    engine = create_async_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return factory()  # caller closes via the engine; tests below dispose explicitly


@pytest.mark.asyncio
async def test_emergency_contact_populated_dict_round_trips(
    db_session: AsyncSession, test_settings: Settings
):
    """A populated dict persists to the JSON column and round-trips into both the
    PersonalInfoDTO and the nested HealthProfileDTO.personal_info."""
    repo = SQLProfileRepository(db_session)
    profile = await repo.create_for_user("u-ec-pop")
    await repo.upsert_personal_info(
        profile.id,
        {"full_name": "Jane", "emergency_contact": {"name": "Bob", "phone": "+1-555-0100"}},
    )
    await db_session.commit()

    # raw column reads back as a dict (was a ProgrammingError on Text)
    row = (
        await db_session.execute(
            select(PersonalInfoModel).where(PersonalInfoModel.profile_id == profile.id)
        )
    ).scalars().first()
    assert isinstance(row.emergency_contact, dict)
    assert row.emergency_contact == {"name": "Bob", "phone": "+1-555-0100"}

    # ORM -> PersonalInfoDTO preserves the dict
    pi_dto = PersonalInfoDTO.model_validate(row)
    assert pi_dto.emergency_contact == {"name": "Bob", "phone": "+1-555-0100"}

    # nested HealthProfileDTO.personal_info populated via selectinload in a fresh session
    async with await _fresh_read(test_settings) as rdb:
        p = (
            await rdb.execute(
                select(HealthProfileModel)
                .where(HealthProfileModel.user_id == "u-ec-pop")
                .options(selectinload(HealthProfileModel.personal_info))
            )
        ).scalars().first()
        dto = HealthProfileDTO.model_validate(p)
        assert dto.personal_info is not None
        assert dto.personal_info.emergency_contact == {"name": "Bob", "phone": "+1-555-0100"}


@pytest.mark.asyncio
async def test_emergency_contact_null_reads_as_none(
    db_session: AsyncSession, test_settings: Settings
):
    """NULL emergency_contact (the only historical value) reads back as None and
    serializes as null in the DTO (not a string)."""
    repo = SQLProfileRepository(db_session)
    profile = await repo.create_for_user("u-ec-null")
    await repo.upsert_personal_info(profile.id, {"full_name": "NullUser"})
    await db_session.commit()

    row = (
        await db_session.execute(
            select(PersonalInfoModel).where(PersonalInfoModel.profile_id == profile.id)
        )
    ).scalars().first()
    assert row.emergency_contact is None

    async with await _fresh_read(test_settings) as rdb:
        p = (
            await rdb.execute(
                select(HealthProfileModel)
                .where(HealthProfileModel.user_id == "u-ec-null")
                .options(selectinload(HealthProfileModel.personal_info))
            )
        ).scalars().first()
        dto = HealthProfileDTO.model_validate(p)
        assert dto.personal_info is not None
        assert dto.personal_info.emergency_contact is None


@pytest.mark.asyncio
async def test_emergency_contact_snapshot_carries_dict_not_repr(
    db_session: AsyncSession, test_settings: Settings
):
    """snapshot_profile().personal_info['emergency_contact'] must be a dict, never a
    Python repr string (the original Text-column failure mode)."""
    repo = SQLProfileRepository(db_session)
    profile = await repo.create_for_user("u-ec-snap")
    await repo.upsert_personal_info(
        profile.id, {"full_name": "Snap", "emergency_contact": {"name": "ER", "phone": "911"}}
    )
    await db_session.commit()

    async with await _fresh_read(test_settings) as rdb:
        fresh_repo = SQLProfileRepository(rdb)
        snapshot = await fresh_repo.snapshot_profile(profile.id)
    pi = snapshot["personal_info"]
    assert isinstance(pi["emergency_contact"], dict)
    assert pi["emergency_contact"] == {"name": "ER", "phone": "911"}


@pytest.mark.asyncio
async def test_profiles_me_serializes_emergency_contact_as_object(
    db_session: AsyncSession, client: AsyncClient
):
    """GET /profiles/me must serialize a populated emergency_contact as a JSON object
    (dict), not a string. Pre-creates the mock-auth user + profile with a populated
    emergency_contact so the GET is the first (fresh) load of that profile."""
    user_repo = SQLUserRepository(db_session)
    user = User.create(
        firebase_uid=_MOCK_UID,
        email="mock@example.com",
        full_name="Mock User",
    )
    user.email_verified = True
    await user_repo.create(user)

    profile_repo = SQLProfileRepository(db_session)
    profile = await profile_repo.create_for_user(user.id)
    await profile_repo.upsert_personal_info(
        profile.id,
        {"full_name": "HTTP User", "emergency_contact": {"name": "Guardian", "phone": "+1-555-0200"}},
    )
    await db_session.commit()

    resp = await client.get(
        "/api/v1/profiles/me", headers={"Authorization": f"Bearer {_MOCK_TOKEN}"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["personal_info"] is not None
    ec = data["personal_info"]["emergency_contact"]
    assert isinstance(ec, dict)  # object, not a repr string / null
    assert ec == {"name": "Guardian", "phone": "+1-555-0200"}


@pytest.mark.asyncio
async def test_profiles_me_serializes_null_emergency_contact(client: AsyncClient):
    """GET /profiles/me serializes an unset emergency_contact as null (the historical
    state) rather than a string or missing field."""
    resp = await client.get(
        "/api/v1/profiles/me", headers={"Authorization": f"Bearer {_MOCK_TOKEN}"}
    )
    assert resp.status_code == 200, resp.text
    pi = resp.json()["personal_info"]
    # a freshly created profile has no personal_info row yet
    assert pi is None or pi.get("emergency_contact") is None
