import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.body_system import BodySystemModel
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.question_group import QuestionGroupModel
from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
    SQLKnowledgeGraphRepository,
)


@pytest.mark.asyncio
async def test_links_and_graph_build(db_session: AsyncSession):
    session = db_session
    repo = SQLKnowledgeGraphRepository(session)

    bs = BodySystemModel(id="bs-kg", code="KG", name="KG Test", display_order=1)
    session.add(bs)
    qg = QuestionGroupModel(id="qg-kg", code="QG_KG", name="QG KG", body_system_id="bs-kg", display_order=1)
    session.add(qg)
    await session.commit()

    cond = await repo.create_condition(
        {"code": "C001", "name": "Test Condition", "description": "desc"}
    )
    lt = await repo.create_laboratory_test(
        {
            "code": "L001",
            "name": "Test Lab",
            "normal_range": "4-8",
            "unit": "mmol/L",
            "body_system_id": "bs-kg",
        }
    )

    await session.execute(
        ClinicalIndicatorModel.__table__.insert().values(
            key="ind-1", name="Indicator 1", body_system_id="bs-kg"
        )
    )
    await session.execute(
        QuestionModel.__table__.insert().values(
            text="Do you cough?", body_system_id="bs-kg", question_group_id="qg-kg", code="q-1", question_type="yes_no"
        )
    )
    await session.commit()

    inds = await repo.get_indicators_by_question("nonexistent")
    assert isinstance(inds, list)

    ind_q = await session.execute(
        ClinicalIndicatorModel.__table__.select().where(
            ClinicalIndicatorModel.key == "ind-1"
        )
    )
    ind_row = ind_q.first()
    q_q = await session.execute(
        QuestionModel.__table__.select().where(QuestionModel.code == "q-1")
    )
    q_row = q_q.first()
    assert ind_row is not None and q_row is not None
    ind_id = ind_row._mapping["id"]
    q_id = q_row._mapping["id"]

    link = await repo.link_question_indicator(q_id, ind_id)
    assert link is not None

    link2 = await repo.link_indicator_condition(ind_id, cond.id)
    assert link2 is not None

    link3 = await repo.link_condition_laboratory_test(cond.id, lt.id)
    assert link3 is not None

    graph = await repo.build_graph_from_question(q_id)
    assert "indicators" in graph
    assert len(graph["indicators"]) == 1
    node = graph["indicators"][0]
    assert node["indicator"].id == ind_id
    assert any(c.id == cond.id for c in node["conditions"])
