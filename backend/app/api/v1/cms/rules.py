from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cms_user, get_db
from app.application.services.cms.rule_engine_service import RuleEngineService
from app.domain.entities.user import User

router = APIRouter(prefix="/cms/rules", tags=["CMS Rule Engine"])


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
