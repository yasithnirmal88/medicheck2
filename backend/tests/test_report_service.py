import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.clinical_decision_service import ClinicalDecisionService
from app.application.services.report_service import ReportService
from app.infrastructure.persistence.models.assessment_answer import (
    AssessmentAnswerModel,
)
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.body_system import BodySystemModel
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.question_group import QuestionGroupModel
from app.infrastructure.persistence.models.question_option import QuestionOptionModel


@pytest.mark.asyncio
async def test_report_generation_flow(db_session: AsyncSession):
    session = db_session
    cdse = ClinicalDecisionService(session)
    report_svc = ReportService(session)

    bs = BodySystemModel(id="bs-rpt", code="RPT", name="RPT Test", display_order=1)
    session.add(bs)
    qg = QuestionGroupModel(id="qg-rpt", code="QG_RPT", name="QG RPT", body_system_id="bs-rpt", display_order=1)
    session.add(qg)
    await session.commit()

    await session.execute(
        ClinicalIndicatorModel.__table__.insert().values(key="i1", name="Ind 1", body_system_id="bs-rpt")
    )
    await session.execute(
        QuestionModel.__table__.insert().values(
            text="Q1", body_system_id="bs-rpt", question_group_id="qg-rpt", code="q1", question_type="yes_no"
        )
    )
    await session.execute(
        QuestionOptionModel.__table__.insert().values(
            question_id="q1", text="Yes", value="yes", code="opt1", display_order=1,
            score_value=1.0,
        )
    )
    await session.commit()

    ind_row = await session.execute(
        ClinicalIndicatorModel.__table__.select().where(
            ClinicalIndicatorModel.key == "i1"
        )
    )
    ind_id = ind_row.first()._mapping["id"]
    q_row = await session.execute(
        QuestionModel.__table__.select().where(QuestionModel.code == "q1")
    )
    q_id = q_row.first()._mapping["id"]
    opt_row = await session.execute(
        QuestionOptionModel.__table__.select().where(
            QuestionOptionModel.code == "opt1"
        )
    )
    opt_id = opt_row.first()._mapping["id"]

    from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
        SQLKnowledgeGraphRepository,
    )

    kg_repo = SQLKnowledgeGraphRepository(session)
    await kg_repo.link_question_option_indicator(opt_id, ind_id)
    cond = await kg_repo.create_condition({"code": "C1", "name": "Cond 1"})
    await kg_repo.link_indicator_condition(ind_id, cond.id)

    await session.execute(
        AssessmentSessionModel.__table__.insert().values(user_id="u1")
    )
    await session.commit()
    s_row = await session.execute(
        AssessmentSessionModel.__table__.select().where(
            AssessmentSessionModel.user_id == "u1"
        )
    )
    s_id = s_row.first()._mapping["id"]

    await session.execute(
        AssessmentAnswerModel.__table__.insert().values(
            session_id=s_id, question_id=q_id, question_code="q1",
            option_id=opt_id, value="Yes",
        )
    )
    await session.commit()

    res = await cdse.process_assessment(s_id, "u1")
    assert "result_id" in res

    rpt = await report_svc.generate_report(s_id, "u1")
    assert "report_id" in rpt
    r = await report_svc.get_report_by_session(s_id)
    assert r is not None
    assert len(r.body_systems) >= 0
    assert len(r.conditions) >= 0
    assert len(r.advices) >= 0


@pytest.mark.asyncio
async def test_report_getters_enforce_ownership(db_session: AsyncSession):
    session = db_session
    cdse = ClinicalDecisionService(session)
    report_svc = ReportService(session)

    bs = BodySystemModel(id="bs-own", code="OWN", name="OWN Test", display_order=1)
    session.add(bs)
    qg = QuestionGroupModel(id="qg-own", code="QG_OWN", name="QG OWN", body_system_id="bs-own", display_order=1)
    session.add(qg)
    await session.commit()

    await session.execute(
        ClinicalIndicatorModel.__table__.insert().values(key="i1", name="Ind 1", body_system_id="bs-own")
    )
    await session.execute(
        QuestionModel.__table__.insert().values(
            text="Q1", body_system_id="bs-own", question_group_id="qg-own", code="q1", question_type="yes_no"
        )
    )
    await session.execute(
        QuestionOptionModel.__table__.insert().values(
            question_id="q1", text="Yes", value="yes", code="opt1", display_order=1,
            score_value=1.0,
        )
    )
    await session.commit()

    ind_row = await session.execute(
        ClinicalIndicatorModel.__table__.select().where(ClinicalIndicatorModel.key == "i1")
    )
    ind_id = ind_row.first()._mapping["id"]
    q_row = await session.execute(
        QuestionModel.__table__.select().where(QuestionModel.code == "q1")
    )
    q_id = q_row.first()._mapping["id"]
    opt_row = await session.execute(
        QuestionOptionModel.__table__.select().where(QuestionOptionModel.code == "opt1")
    )
    opt_id = opt_row.first()._mapping["id"]

    from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
        SQLKnowledgeGraphRepository,
    )

    kg_repo = SQLKnowledgeGraphRepository(session)
    await kg_repo.link_question_option_indicator(opt_id, ind_id)
    cond = await kg_repo.create_condition({"code": "C1", "name": "Cond 1"})
    await kg_repo.link_indicator_condition(ind_id, cond.id)

    await session.execute(
        AssessmentSessionModel.__table__.insert().values(user_id="u1")
    )
    await session.commit()
    s_row = await session.execute(
        AssessmentSessionModel.__table__.select().where(AssessmentSessionModel.user_id == "u1")
    )
    s_id = s_row.first()._mapping["id"]

    await session.execute(
        AssessmentAnswerModel.__table__.insert().values(
            session_id=s_id, question_id=q_id, question_code="q1",
            option_id=opt_id, value="Yes",
        )
    )
    await session.commit()

    await cdse.process_assessment(s_id, "u1")
    await report_svc.generate_report(s_id, "u1")

    # owner can read; other users cannot
    assert await report_svc.get_report_by_session(s_id, user_id="u1") is not None
    assert await report_svc.get_report_by_session(s_id, user_id="u2") is None

    r = await report_svc.get_report_by_session(s_id, user_id="u1")
    assert await report_svc.get_report(r.id, user_id="u1") is not None
    assert await report_svc.get_report(r.id, user_id="u2") is None

    # generate_report refuses to build report from another user's session
    with pytest.raises(ValueError):
        await report_svc.generate_report(s_id, "u2")

    # compare_reports requires ownership of both reports
    r2 = await report_svc.get_report_by_session(s_id, user_id="u1")
    with pytest.raises(ValueError):
        await report_svc.compare_reports(r.id, r2.id, user_id="u2")
