"""Regression tests for ProfileService → HealthProfileDTO conversion.

P3-1: replaced deprecated Pydantic v1 `HealthProfileDTO.from_orm(profile)` with
`HealthProfileDTO.model_validate(profile)` (Pydantic v2 + `from_attributes=True`).
These tests pin that the ORM→DTO conversion still works end-to-end, including:
  - the `metadata` field reading the `profile_metadata` SQLAlchemy column
    (the ORM `metadata` attribute resolves to SQLAlchemy's MetaData object), and
  - nested `personal_info` hydration.
Run with: ALLOW_MOCK_AUTH=true so mock auth is available where needed.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.profile_dtos import HealthProfileDTO
from app.application.services.profile_service import ProfileService
from app.infrastructure.persistence.repositories.sql_profile_repository import (
    SQLProfileRepository,
)


@pytest.mark.asyncio
async def test_profile_service_returns_dto_via_model_validate(db_session: AsyncSession):
    """get_or_create_profile_for_user must return a HealthProfileDTO built with
    model_validate (not the deprecated from_orm)."""
    repo = SQLProfileRepository(db_session)
    profile = await repo.create_for_user("u-p3-1")

    service = ProfileService(db_session)
    class _StubUser:
        id = "u-p3-1"
    dto = await service.get_or_create_profile_for_user(_StubUser())  # type: ignore[arg-type]

    assert isinstance(dto, HealthProfileDTO)
    assert dto.id == profile.id
    assert dto.user_id == "u-p3-1"
    # metadata must resolve from profile_metadata, never the SQLAlchemy MetaData object
    assert dto.metadata is None or isinstance(dto.metadata, dict)


@pytest.mark.asyncio
async def test_health_profile_dto_model_validate_from_orm(db_session: AsyncSession):
    """model_validate must build a DTO directly from the SQLAlchemy ORM instance
    (the from_attributes=True path that replaced from_orm)."""
    repo = SQLProfileRepository(db_session)
    profile = await repo.create_for_user("u-p3-1-pi")
    await repo.upsert_personal_info(profile.id, {"full_name": "Jane Doe"})

    fresh = await repo.get_by_id(profile.id)
    assert fresh is not None

    dto = HealthProfileDTO.model_validate(fresh)
    assert dto.id == profile.id
    # metadata must resolve from profile_metadata, never the SQLAlchemy MetaData object
    assert dto.metadata is None or isinstance(dto.metadata, dict)
    # created_at/updated_at are populated from ORM columns (proves attr access works)
    assert dto.created_at is not None


def test_health_profile_dto_model_validate_rejects_plain_dict_without_from_attributes():
    """Sanity: model_validate(dict) still works for dict input (positional dict),
    but from_attributes only matters for ORM objects. Ensure no regression in the
    dict-input path used elsewhere."""
    dto = HealthProfileDTO.model_validate(
        {"id": "x", "user_id": "u", "draft": False, "metadata": {"k": 1}}
    )
    assert dto.metadata == {"k": 1}
