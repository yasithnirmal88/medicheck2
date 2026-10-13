from __future__ import annotations

import uuid
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.body_system import BodySystemModel
from app.infrastructure.persistence.models.decision import AssessmentResultModel
from app.infrastructure.persistence.models.question_group import QuestionGroupModel
from app.infrastructure.persistence.models.report import HealthAssessmentModel
from app.infrastructure.persistence.repositories.sql_decision_repository import (
    SQLDecisionRepository,
)
from app.infrastructure.persistence.repositories.sql_report_repository import (
    SQLReportRepository,
)

_MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "20261013_referral_lookup_indexes.py"
)


def test_referral_lookup_index_migration_is_idempotent():
    spec = spec_from_file_location("referral_lookup_indexes", _MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE referrals (id VARCHAR(32) PRIMARY KEY, "
            "facility_id VARCHAR(32), receiving_status VARCHAR(20))"
        )
        operations = MigrationContext.configure(connection)
        with Operations.context(operations):
            migration.upgrade()
            migration.upgrade()

        indexes = {
            index["name"] for index in sa.inspect(connection).get_indexes("referrals")
        }
        assert indexes == {
            "ix_referrals_facility_id",
            "ix_referrals_receiving_status",
        }

        with Operations.context(operations):
            migration.downgrade()
        assert sa.inspect(connection).get_indexes("referrals") == []

    engine.dispose()


@pytest.mark.parametrize(
    "model",
    [
        AssessmentSessionModel,
        BodySystemModel,
        QuestionGroupModel,
    ],
)
def test_to_dict_serializes_python_attribute_for_metadata_column(model):
    item = model(extra_metadata={"source": "test"})

    assert item.to_dict()["metadata"] == {"source": "test"}


@pytest.mark.asyncio
async def test_create_result_reuses_existing_session_result(db_session: AsyncSession):
    repository = SQLDecisionRepository(db_session)
    session_id = uuid.uuid4().hex
    data = {
        "session_id": session_id,
        "user_id": uuid.uuid4().hex,
        "summary": None,
        "confidence_score": None,
        "created_at": None,
    }

    first = await repository.create_result(data)
    second = await repository.create_result(data)

    assert first.id == second.id
    assert await db_session.scalar(
        select(func.count()).select_from(AssessmentResultModel).where(
            AssessmentResultModel.session_id == session_id
        )
    ) == 1


@pytest.mark.asyncio
async def test_create_health_assessment_reuses_existing_session_report(
    db_session: AsyncSession,
):
    repository = SQLReportRepository(db_session)
    session_id = uuid.uuid4().hex
    data = {
        "session_id": session_id,
        "user_id": uuid.uuid4().hex,
        "summary": None,
        "created_at": None,
    }

    first = await repository.create_health_assessment(data)
    second = await repository.create_health_assessment(data)

    assert first.id == second.id
    assert await db_session.scalar(
        select(func.count()).select_from(HealthAssessmentModel).where(
            HealthAssessmentModel.session_id == session_id
        )
    ) == 1


@pytest.mark.asyncio
async def test_insert_methods_return_the_specific_inserted_row(db_session: AsyncSession):
    result = await SQLDecisionRepository(db_session).create_result(
        {
            "session_id": uuid.uuid4().hex,
            "user_id": uuid.uuid4().hex,
            "summary": None,
            "confidence_score": None,
            "created_at": None,
        }
    )
    report = await SQLReportRepository(db_session).create_health_assessment(
        {
            "session_id": uuid.uuid4().hex,
            "user_id": uuid.uuid4().hex,
            "summary": None,
            "created_at": None,
        }
    )

    first_indicator = await SQLDecisionRepository(db_session).add_activated_indicator(
        result.id, "indicator-one", 1.0, 0, None
    )
    second_indicator = await SQLDecisionRepository(db_session).add_activated_indicator(
        result.id, "indicator-two", 2.0, 0, None
    )
    first_body_system = await SQLReportRepository(db_session).add_body_system_assessment(
        report.id, "body-system-one", "Normal", 0.0, None
    )
    second_body_system = await SQLReportRepository(db_session).add_body_system_assessment(
        report.id, "body-system-two", "Monitor", 1.0, None
    )

    assert (first_indicator.indicator_id, first_indicator.score) == ("indicator-one", 1.0)
    assert (second_indicator.indicator_id, second_indicator.score) == ("indicator-two", 2.0)
    assert first_indicator.id != second_indicator.id
    assert (first_body_system.body_system_id, first_body_system.category) == (
        "body-system-one",
        "Normal",
    )
    assert (second_body_system.body_system_id, second_body_system.category) == (
        "body-system-two",
        "Monitor",
    )
    assert first_body_system.id != second_body_system.id
