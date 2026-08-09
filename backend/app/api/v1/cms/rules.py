from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cms_user, get_db
from app.application.services.cms.rule_engine_service import RuleEngineService
from app.domain.entities.user import User
from app.infrastructure.persistence.models.questionnaire_rule_set import (
    QuestionnaireRuleSetModel,
)

router = APIRouter(prefix="/cms/rules", tags=["CMS Rule Engine"])


def _rule_set_to_dict(rs: QuestionnaireRuleSetModel) -> dict[str, Any]:
    return {
        "id": rs.id,
        "name": rs.name,
        "description": None,
        "body_system_id": None,
        "questionnaire_id": rs.questionnaire_id,
        "rules": rs.rules or [],
        "logic": rs.logic,
        "expression": rs.rules or {},
        "version": rs.version,
        "status": rs.status,
        "is_active": rs.is_active,
        "created_by": rs.created_by,
        "updated_by": rs.updated_by,
        "created_at": rs.created_at,
        "updated_at": rs.updated_at,
    }


@router.get("")
async def list_rule_sets(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    questionnaire_id: str | None = Query(None),
):
    """List questionnaire rule sets. The generic /cms/content/decision_rule
    router also exposes decision rules; this endpoint covers persisted rule
    sets used by the rule builder. Returns a bare array to match the frontend
    RuleSet[] contract."""
    stmt = select(QuestionnaireRuleSetModel).where(
        QuestionnaireRuleSetModel.deleted_at.is_(None)
    )
    if questionnaire_id:
        stmt = stmt.where(QuestionnaireRuleSetModel.questionnaire_id == questionnaire_id)
    stmt = stmt.order_by(QuestionnaireRuleSetModel.created_at.desc())
    result = await session.execute(stmt)
    return [_rule_set_to_dict(rs) for rs in result.scalars().all()]


@router.get("/{rule_set_id}")
async def get_rule_set(
    rule_set_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(QuestionnaireRuleSetModel).where(
        QuestionnaireRuleSetModel.id == rule_set_id,
        QuestionnaireRuleSetModel.deleted_at.is_(None),
    )
    rs = (await session.execute(stmt)).scalar_one_or_none()
    if rs is None:
        raise HTTPException(404, f"Rule set {rule_set_id} not found")
    return _rule_set_to_dict(rs)


@router.post("")
async def create_rule_set(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    model = QuestionnaireRuleSetModel(
        questionnaire_id=payload.get("questionnaire_id", ""),
        name=payload.get("name", ""),
        rules=payload.get("rules") or payload.get("expression") or [],
        logic=payload.get("logic", "ALL"),
        status=payload.get("status", "draft"),
        version=1,
        created_by=user.id,
        updated_by=user.id,
    )
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return _rule_set_to_dict(model)


@router.put("/{rule_set_id}")
async def update_rule_set(
    rule_set_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    stmt = select(QuestionnaireRuleSetModel).where(
        QuestionnaireRuleSetModel.id == rule_set_id,
        QuestionnaireRuleSetModel.deleted_at.is_(None),
    )
    rs = (await session.execute(stmt)).scalar_one_or_none()
    if rs is None:
        raise HTTPException(404, f"Rule set {rule_set_id} not found")
    for field in ("name", "rules", "logic", "status", "questionnaire_id"):
        if field in payload:
            setattr(rs, field, payload[field])
    rs.version = (rs.version or 1) + 1
    rs.updated_by = user.id
    await session.commit()
    await session.refresh(rs)
    return _rule_set_to_dict(rs)


@router.post("/evaluate")
async def evaluate_rule(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = RuleEngineService(session)
    rule = payload.get("rule", {})
    context = payload.get("context", {})
    return svc.evaluate_rule(rule, context)


@router.post("/evaluate/batch")
async def evaluate_ruleset(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = RuleEngineService(session)
    rules = payload.get("rules", [])
    context = payload.get("context", {})
    logic = payload.get("logic", "ALL")

    results = svc.evaluate_ruleset(rules, context)

    if logic == "ANY":
        matched = any(r["matched"] for r in results)
    else:
        matched = all(r["matched"] for r in results)

    return {
        "matched": matched,
        "logic": logic,
        "rule_count": len(rules),
        "matched_count": sum(1 for r in results if r["matched"]),
        "results": results,
    }


@router.post("/simulate")
async def simulate_rules(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = RuleEngineService(session)
    rules = payload.get("rules", [])
    context = payload.get("context", {})
    return svc.simulate(rules, context)


@router.post("/validate")
async def validate_expression(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = RuleEngineService(session)
    expression = payload.get("expression", {})
    context = payload.get("context", {})
    try:
        result = svc.evaluate_expression(expression, context)
        return {"valid": True, "result": result}
    except Exception as e:
        return {"valid": False, "error": str(e)}


@router.post("/compute")
async def compute_variable(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = RuleEngineService(session)
    variable = payload.get("variable", "")
    context = payload.get("context", {})
    value = svc.compute_variable(variable, context)
    return {"variable": variable, "value": value}


@router.post("/detect-conflicts")
async def detect_conflicts(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = RuleEngineService(session)
    rules = payload.get("rules", [])
    conflicts = svc.detect_conflicts(rules)
    cycles = svc.detect_circular_dependencies(rules)
    return {
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "cycle_count": len(cycles),
        "cycles": cycles,
    }
