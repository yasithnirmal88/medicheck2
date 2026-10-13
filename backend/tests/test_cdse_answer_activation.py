"""Regression tests for CDSE answer-aware activation.

These exercise the REAL ``save_answer -> process_assessment`` path (not a raw
SQL insert of answers) so they protect against the class of bug where a
question-level indicator link activates for ANY answer, including "no" /
skipped. YES/NO answers arrive from the UI as booleans, so the persistence
layer must resolve them to the canonical option before the deterministic
engine runs.

Covers the two canonical examples: "No chest pain" and "non-smoker" must not
activate CV_CHEST_PAIN / CV_TOBACCO.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.clinical_decision_service import ClinicalDecisionService
from app.application.services.questionnaire_service import QuestionnaireService
from app.domain.entities.assessment_session import AssessmentSession
from app.domain.entities.clinical_indicator import ClinicalIndicator
from app.domain.entities.question import Question, QuestionType
from app.domain.entities.question_option import QuestionOption
from app.infrastructure.persistence.models.assessment_answer import (
    AssessmentAnswerModel,
)
from app.infrastructure.persistence.models.body_system import BodySystemModel
from app.infrastructure.persistence.models.links import QuestionIndicatorLinkModel
from app.infrastructure.persistence.models.question_group import QuestionGroupModel
from app.infrastructure.persistence.models.question_option import QuestionOptionModel
from app.infrastructure.persistence.repositories.sql_assessment_session_repository import (
    SQLAssessmentSessionRepository,
)
from app.infrastructure.persistence.repositories.sql_clinical_indicator_repository import (
    SQLClinicalIndicatorRepository,
)
from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
    SQLKnowledgeGraphRepository,
)
from app.infrastructure.persistence.repositories.sql_question_option_repository import (
    SQLQuestionOptionRepository,
)
from app.infrastructure.persistence.repositories.sql_question_repository import (
    SQLQuestionRepository,
)


async def _seed_yes_no_question(
    session: AsyncSession, *, q_code: str, ind_key: str
) -> tuple[str, str]:
    """Seed a YES/NO question with a question-level indicator link.

    Mirrors the real seed shape (``cv_chest_pain`` -> ``CV_CHEST_PAIN``): a
    "yes" option (score 1.0) and a "no" option (score 0.0), with the indicator
    linked at the QUESTION level (the path that was broken). A uuid suffix
    keeps the codes unique across tests on the shared test database.
    """
    tag = uuid.uuid4().hex[:8]
    bs_id = f"bs-{tag}"
    qg_id = f"qg-{tag}"
    session.add(
        BodySystemModel(
            id=bs_id, code=f"BS_{tag}", name="CDSE Activation", display_order=1
        )
    )
    session.add(
        QuestionGroupModel(
            id=qg_id,
            code=f"QG_{tag}",
            name="Group",
            body_system_id=bs_id,
            display_order=1,
        )
    )
    await session.flush()

    indicator = await SQLClinicalIndicatorRepository(session).create(
        ClinicalIndicator.create(
            body_system_id=bs_id,
            key=f"{ind_key}_{tag}",
            name="Indicator",
        )
    )
    question = await SQLQuestionRepository(session).create(
        Question.create(
            body_system_id=bs_id,
            question_group_id=qg_id,
            code=f"{q_code}_{tag}",
            question_type=QuestionType.YES_NO,
            text="Do you have the finding?",
        )
    )

    option_repo = SQLQuestionOptionRepository(session)
    await option_repo.create(
        QuestionOption.create(
            question_id=question.id,
            code="yes",
            text="Yes",
            value="yes",
            score_value=1.0,
            display_order=1,
        )
    )
    await option_repo.create(
        QuestionOption.create(
            question_id=question.id,
            code="no",
            text="No",
            value="no",
            score_value=0.0,
            display_order=2,
        )
    )

    await SQLKnowledgeGraphRepository(session).link_question_indicator(
        question.id, indicator.id
    )
    return question.id, indicator.id


async def _new_session(session: AsyncSession, user_id: str) -> str:
    created = await SQLAssessmentSessionRepository(session).create(
        AssessmentSession.create(user_id=user_id, total_questions=1)
    )
    return created.id


async def _run(
    session: AsyncSession,
    *,
    q_code: str,
    ind_key: str,
    response_value: dict,
    is_skipped: bool = False,
) -> dict:
    q_id, ind_id = await _seed_yes_no_question(session, q_code=q_code, ind_key=ind_key)
    user_id = f"u-{q_code}-{uuid.uuid4().hex[:8]}"
    s_id = await _new_session(session, user_id)
    payload: dict = {"question_id": q_id, "response_value": response_value}
    if is_skipped:
        payload["is_skipped"] = True
    await QuestionnaireService(session).save_answer(
        SimpleNamespace(id=user_id), s_id, payload
    )
    await session.commit()
    session.expire_all()
    return {
        "indicator_id": ind_id,
        "session_id": s_id,
        "user_id": user_id,
        "result": await ClinicalDecisionService(session).process_assessment(
            s_id, user_id
        ),
    }


async def _load_answer(session: AsyncSession, s_id: str) -> AssessmentAnswerModel:
    rows = await session.execute(
        select(AssessmentAnswerModel).where(AssessmentAnswerModel.session_id == s_id)
    )
    return rows.scalars().one()


@pytest.mark.asyncio
async def test_chest_pain_yes_activates(db_session: AsyncSession):
    out = await _run(
        db_session,
        q_code="cv_chest_pain",
        ind_key="CV_CHEST_PAIN",
        response_value={"value": True},
    )
    assert out["indicator_id"] in out["result"]["summary"]["indicator_scores"]
    assert out["result"]["summary"]["activated_indicators"] == 1


@pytest.mark.asyncio
async def test_chest_pain_no_does_not_activate(db_session: AsyncSession):
    out = await _run(
        db_session,
        q_code="cv_chest_pain",
        ind_key="CV_CHEST_PAIN",
        response_value={"value": False},
    )
    assert out["indicator_id"] not in out["result"]["summary"]["indicator_scores"]
    assert out["result"]["summary"]["activated_indicators"] == 0


@pytest.mark.asyncio
async def test_smoking_yes_activates(db_session: AsyncSession):
    out = await _run(
        db_session,
        q_code="cv_smoking",
        ind_key="CV_TOBACCO",
        response_value={"value": True},
    )
    assert out["indicator_id"] in out["result"]["summary"]["indicator_scores"]
    assert out["result"]["summary"]["activated_indicators"] == 1


@pytest.mark.asyncio
async def test_smoking_no_does_not_activate(db_session: AsyncSession):
    out = await _run(
        db_session,
        q_code="cv_smoking",
        ind_key="CV_TOBACCO",
        response_value={"value": False},
    )
    assert out["indicator_id"] not in out["result"]["summary"]["indicator_scores"]
    assert out["result"]["summary"]["activated_indicators"] == 0


@pytest.mark.asyncio
async def test_yes_persists_option_and_values(db_session: AsyncSession):
    out = await _run(
        db_session,
        q_code="cv_chest_pain",
        ind_key="CV_CHEST_PAIN",
        response_value={"value": True},
    )
    answer = await _load_answer(db_session, out["session_id"])
    assert answer.value == "yes"
    assert answer.numeric_value == 1.0
    assert answer.option_id is not None
    assert answer.score_value == 1.0


@pytest.mark.asyncio
async def test_no_persists_option_and_values(db_session: AsyncSession):
    out = await _run(
        db_session,
        q_code="cv_chest_pain",
        ind_key="CV_CHEST_PAIN",
        response_value={"value": False},
    )
    answer = await _load_answer(db_session, out["session_id"])
    assert answer.value == "no"
    assert answer.numeric_value == 0.0
    assert answer.option_id is not None
    assert answer.score_value == 0.0


@pytest.mark.asyncio
async def test_skipped_does_not_activate(db_session: AsyncSession):
    out = await _run(
        db_session,
        q_code="cv_chest_pain",
        ind_key="CV_CHEST_PAIN",
        response_value={"value": ""},
        is_skipped=True,
    )
    assert out["indicator_id"] not in out["result"]["summary"]["indicator_scores"]
    assert out["result"]["summary"]["activated_indicators"] == 0


@pytest.mark.asyncio
async def test_option_level_linking_still_works(db_session: AsyncSession):
    """Sanity: option-level linking keeps working (unchanged behaviour)."""
    session = db_session
    q_id, ind_id = await _seed_yes_no_question(
        session, q_code="cv_chest_pain", ind_key="CV_CHEST_PAIN"
    )
    # Re-point the link from question-level to option-level.
    await session.execute(
        QuestionIndicatorLinkModel.__table__.delete().where(
            QuestionIndicatorLinkModel.indicator_id == ind_id
        )
    )
    opt_rows = await session.execute(
        select(QuestionOptionModel).where(QuestionOptionModel.question_id == q_id)
    )
    yes_opt = next(o for o in opt_rows.scalars().all() if o.value == "yes")
    await SQLKnowledgeGraphRepository(session).link_question_option_indicator(
        yes_opt.id, ind_id
    )

    user_id = f"u-opt-{uuid.uuid4().hex[:8]}"
    s_id = await _new_session(session, user_id)
    await QuestionnaireService(session).save_answer(
        SimpleNamespace(id=user_id),
        s_id,
        {"question_id": q_id, "response_value": {"value": True}},
    )
    await session.commit()
    session.expire_all()

    result = await ClinicalDecisionService(session).process_assessment(s_id, user_id)
    assert ind_id in result["summary"]["indicator_scores"]
    assert result["summary"]["activated_indicators"] == 1
