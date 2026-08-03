from __future__ import annotations

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.application.services.knowledge_graph_service import KnowledgeGraphService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.post("/question-indicators")
async def link_question_indicator(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(session)
    question_id = payload.get("question_id")
    indicator_id = payload.get("indicator_id")
    return await svc.link_question_indicator(current_user.id, question_id, indicator_id)


@router.post("/question-option-indicators")
async def link_question_option_indicator(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(session)
    question_option_id = payload.get("question_option_id")
    indicator_id = payload.get("indicator_id")
    return await svc.link_question_option_indicator(
        current_user.id, question_option_id, indicator_id
    )


@router.post("/indicator-conditions")
async def link_indicator_condition(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(session)
    indicator_id = payload.get("indicator_id")
    condition_id = payload.get("condition_id")
    return await svc.link_indicator_condition(
        current_user.id, indicator_id, condition_id
    )


@router.post("/indicator-evidence")
async def link_indicator_evidence(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(session)
    indicator_id = payload.get("indicator_id")
    evidence_id = payload.get("evidence_id")
    return await svc.link_indicator_evidence(current_user.id, indicator_id, evidence_id)


@router.post("/indicator-recommendations")
async def link_indicator_recommendation(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(session)
    indicator_id = payload.get("indicator_id")
    recommendation_id = payload.get("recommendation_id")
    return await svc.link_indicator_recommendation(
        current_user.id, indicator_id, recommendation_id
    )


@router.post("/condition-recommendations")
async def link_condition_recommendation(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(session)
    condition_id = payload.get("condition_id")
    recommendation_id = payload.get("recommendation_id")
    return await svc.link_condition_recommendation(
        current_user.id, condition_id, recommendation_id
    )


@router.post("/condition-laboratory-tests")
async def link_condition_laboratory_test(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(session)
    condition_id = payload.get("condition_id")
    laboratory_test_id = payload.get("laboratory_test_id")
    return await svc.link_condition_laboratory_test(
        current_user.id, condition_id, laboratory_test_id
    )


@router.post("/body-system-conditions")
async def link_body_system_condition(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(session)
    body_system_id = payload.get("body_system_id")
    condition_id = payload.get("condition_id")
    return await svc.link_body_system_condition(
        current_user.id, body_system_id, condition_id
    )


@router.get("/question/{question_id}")
async def graph_for_question(question_id: str, session: AsyncSession = Depends(get_db)):
    svc = KnowledgeGraphService(session)
    return await svc.build_graph_from_question(question_id)


@router.get("/indicator/{indicator_id}")
async def graph_for_indicator(
    indicator_id: str, session: AsyncSession = Depends(get_db)
):
    svc = KnowledgeGraphService(session)
    conds = await svc.get_conditions_by_indicator(indicator_id)
    evidence = await svc.get_evidence_by_indicator(indicator_id)
    return {"indicator_id": indicator_id, "conditions": conds, "evidence": evidence}


@router.get("/condition/{condition_id}")
async def graph_for_condition(
    condition_id: str, session: AsyncSession = Depends(get_db)
):
    svc = KnowledgeGraphService(session)
    recs = await svc.get_recommendations_by_condition(condition_id)
    labs = await svc.get_laboratory_tests_by_condition(condition_id)
    return {
        "condition_id": condition_id,
        "recommendations": recs,
        "laboratory_tests": labs,
    }


@router.post("/conditions")
async def create_condition(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(session)
    return await svc.create_condition(current_user.id, payload)


@router.post("/laboratory-tests")
async def create_laboratory_test(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = KnowledgeGraphService(session)
    return await svc.create_laboratory_test(current_user.id, payload)
