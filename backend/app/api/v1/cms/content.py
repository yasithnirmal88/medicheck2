from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cms_user, get_db
from app.api.schemas.cms import (
    CMSEntityCreate,
    CMSEntityUpdate,
    CMSStatusUpdate,
)
from app.application.services.cms.content_service import (
    ENTITY_REGISTRY,
    CMSContentService,
)
from app.core.security.rbac import (
    Permission,
    check_permission,
    get_role_permissions,
)
from app.core.security.rbac import (
    Role as RBACRole,
)
from app.domain.entities.user import User
from app.infrastructure.persistence.models.role import RoleModel
from app.infrastructure.persistence.models.user_role import user_role_table

router = APIRouter(prefix="/cms/content", tags=["CMS Content"])

ALL_ENTITY_TYPES = list(ENTITY_REGISTRY.keys())

# Frontend sends abbreviated entity names (e.g. "indicator") while the
# ENTITY_REGISTRY and permission maps use canonical names (e.g.
# "clinical_indicator"). This alias map reconciles them so the existing
# registry/permission layer does not need to be duplicated. Aliasing is a
# request-path concern only; no database tables are renamed.
ENTITY_ALIASES: dict[str, str] = {
    "indicator": "clinical_indicator",
    "lab_test": "laboratory_test",
    "imaging": "imaging_test",
    "evidence": "medical_evidence",
    "lifestyle": "lifestyle_advice",
    "exercise": "exercise_program",
    "nutrition": "nutrition_advice",
    "guideline": "clinical_guideline",
    "medication": "medication_recommendation",
    "rule": "decision_rule",
    "tag": "medical_tag",
    "specialty": "medical_specialty",
    "template": "template_library",
    "risk_threshold": "severity_threshold",
}


def _resolve(entity_type: str) -> str:
    """Return the canonical entity_type for a (possibly abbreviated) name."""
    return ENTITY_ALIASES.get(entity_type, entity_type)

_READ_PERM_MAP: dict[str, Permission] = {
    "disease": Permission.CMS_READ_DISEASE,
    "clinical_indicator": Permission.CMS_READ_INDICATOR,
    "symptom": Permission.CMS_READ_SYMPTOM,
    "laboratory_test": Permission.CMS_READ_LAB_TEST,
    "imaging_test": Permission.CMS_READ_IMAGING,
    "medical_evidence": Permission.CMS_READ_EVIDENCE,
    "recommendation": Permission.CMS_READ_RECOMMENDATION,
    "lifestyle_advice": Permission.CMS_READ_LIFESTYLE,
    "exercise_program": Permission.CMS_READ_EXERCISE,
    "nutrition_advice": Permission.CMS_READ_NUTRITION,
    "clinical_guideline": Permission.CMS_READ_CLINICAL_GUIDELINE,
    "medication_recommendation": Permission.CMS_READ_MEDICATION,
    "approval": Permission.CMS_READ_APPROVAL,
    "workflow": Permission.CMS_READ_WORKFLOW,
    "decision_rule": Permission.CMS_READ_RULE,
    "questionnaire_rule_set": Permission.CMS_READ_RULE,
    "scoring_profile": Permission.CMS_READ_SCORING,
    "severity_threshold": Permission.CMS_READ_SCORING,
    "risk_category": Permission.CMS_READ_RISK,
    "medical_specialty": Permission.CMS_READ_SPECIALTY,
    "medical_tag": Permission.CMS_READ_TAG,
    "reference_source": Permission.CMS_READ_REFERENCE,
    "research_paper": Permission.CMS_READ_REFERENCE,
    "clinical_trial": Permission.CMS_READ_REFERENCE,
    "medical_organization": Permission.CMS_READ_ORGANIZATION,
    "evidence_collection": Permission.CMS_READ_EVIDENCE,
    "disease_category": Permission.CMS_READ_CATEGORY,
    "body_system_category": Permission.CMS_READ_CATEGORY,
    "recommendation_category": Permission.CMS_READ_CATEGORY,
    "question_category": Permission.CMS_READ_CATEGORY,
    "question_tag": Permission.CMS_READ_TAG,
    "lab_panel": Permission.CMS_READ_LAB_TEST,
    "biomarker": Permission.CMS_READ_LAB_TEST,
    "rule_library": Permission.CMS_READ_LIBRARY,
    "template_library": Permission.CMS_READ_LIBRARY,
    "change_request": Permission.CMS_READ_CHANGE_REQUEST,
    "notification": Permission.CMS_READ_NOTIFICATION,
}

_WRITE_PERM_MAP: dict[str, Permission] = {
    "disease": Permission.CMS_WRITE_DISEASE,
    "clinical_indicator": Permission.CMS_WRITE_INDICATOR,
    "symptom": Permission.CMS_WRITE_SYMPTOM,
    "laboratory_test": Permission.CMS_WRITE_LAB_TEST,
    "imaging_test": Permission.CMS_WRITE_IMAGING,
    "medical_evidence": Permission.CMS_WRITE_EVIDENCE,
    "recommendation": Permission.CMS_WRITE_RECOMMENDATION,
    "lifestyle_advice": Permission.CMS_WRITE_LIFESTYLE,
    "exercise_program": Permission.CMS_WRITE_EXERCISE,
    "nutrition_advice": Permission.CMS_WRITE_NUTRITION,
    "clinical_guideline": Permission.CMS_WRITE_CLINICAL_GUIDELINE,
    "medication_recommendation": Permission.CMS_WRITE_MEDICATION,
    "approval": Permission.CMS_WRITE_APPROVAL,
    "workflow": Permission.CMS_WRITE_WORKFLOW,
    "decision_rule": Permission.CMS_WRITE_RULE,
    "questionnaire_rule_set": Permission.CMS_WRITE_RULE,
    "scoring_profile": Permission.CMS_WRITE_SCORING,
    "severity_threshold": Permission.CMS_WRITE_SCORING,
    "risk_category": Permission.CMS_WRITE_RISK,
    "medical_specialty": Permission.CMS_WRITE_SPECIALTY,
    "medical_tag": Permission.CMS_WRITE_TAG,
    "reference_source": Permission.CMS_WRITE_REFERENCE,
    "research_paper": Permission.CMS_WRITE_REFERENCE,
    "clinical_trial": Permission.CMS_WRITE_REFERENCE,
    "medical_organization": Permission.CMS_WRITE_ORGANIZATION,
    "evidence_collection": Permission.CMS_WRITE_EVIDENCE,
    "disease_category": Permission.CMS_WRITE_CATEGORY,
    "body_system_category": Permission.CMS_WRITE_CATEGORY,
    "recommendation_category": Permission.CMS_WRITE_CATEGORY,
    "question_category": Permission.CMS_WRITE_CATEGORY,
    "question_tag": Permission.CMS_WRITE_TAG,
    "lab_panel": Permission.CMS_WRITE_LAB_TEST,
    "biomarker": Permission.CMS_WRITE_LAB_TEST,
    "rule_library": Permission.CMS_WRITE_LIBRARY,
    "template_library": Permission.CMS_WRITE_LIBRARY,
    "change_request": Permission.CMS_WRITE_CHANGE_REQUEST,
    "notification": Permission.CMS_WRITE_NOTIFICATION,
}


async def _get_user_permissions(
    session: AsyncSession, user_id: str
) -> set[Permission]:
    stmt = (
        select(RoleModel.code)
        .select_from(user_role_table)
        .join(RoleModel, RoleModel.id == user_role_table.c.role_id)
        .where(user_role_table.c.user_id == user_id)
    )
    result = await session.execute(stmt)
    perms: set[Permission] = set()
    for row in result.all():
        try:
            role = RBACRole(row[0])
            perms.update(get_role_permissions(role))
        except ValueError:
            continue
    return perms


@router.get("/{entity_type}")
async def list_content(
    entity_type: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    body_system_id: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    canonical = _resolve(entity_type)
    if canonical not in ALL_ENTITY_TYPES:
        raise HTTPException(404, f"Unknown entity type: {entity_type}")
    perms = await _get_user_permissions(session, user.id)
    req_perm = _READ_PERM_MAP.get(canonical, Permission.CMS_READ_DASHBOARD)
    if not check_permission(perms, req_perm):
        raise HTTPException(403, "Insufficient permissions")

    svc = CMSContentService(session)
    items = await svc.list_entities(
        canonical, body_system_id=body_system_id,
        status=status, search=search, skip=skip, limit=limit
    )
    total = await svc.count_entities(canonical, status=status)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/{entity_type}/{entity_id}")
async def get_content(
    entity_type: str,
    entity_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    canonical = _resolve(entity_type)
    if canonical not in ALL_ENTITY_TYPES:
        raise HTTPException(404, f"Unknown entity type: {entity_type}")
    perms = await _get_user_permissions(session, user.id)
    req_perm = _READ_PERM_MAP.get(canonical, Permission.CMS_READ_DASHBOARD)
    if not check_permission(perms, req_perm):
        raise HTTPException(403, "Insufficient permissions")

    svc = CMSContentService(session)
    item = await svc.get_entity(canonical, entity_id)
    if item is None:
        raise HTTPException(404, f"{entity_type} not found")
    return item


@router.post("/{entity_type}")
async def create_content(
    entity_type: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: CMSEntityCreate = Body(...),
):
    canonical = _resolve(entity_type)
    if canonical not in ALL_ENTITY_TYPES:
        raise HTTPException(404, f"Unknown entity type: {entity_type}")
    perms = await _get_user_permissions(session, user.id)
    req_perm = _WRITE_PERM_MAP.get(canonical, Permission.CMS_WRITE_PUBLISH)
    if not check_permission(perms, req_perm):
        raise HTTPException(403, "Insufficient permissions")

    svc = CMSContentService(session)
    data = payload.model_dump(exclude_none=True, exclude={"extra"})
    try:
        item = await svc.create_entity(canonical, data, user.id)
        return item
    except ValueError as e:
        raise HTTPException(400, str(e))
    except TypeError as e:
        raise HTTPException(400, f"Invalid data: {e}")


@router.put("/{entity_type}/{entity_id}")
async def update_content(
    entity_type: str,
    entity_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: CMSEntityUpdate = Body(...),
):
    canonical = _resolve(entity_type)
    if canonical not in ALL_ENTITY_TYPES:
        raise HTTPException(404, f"Unknown entity type: {entity_type}")
    perms = await _get_user_permissions(session, user.id)
    req_perm = _WRITE_PERM_MAP.get(canonical, Permission.CMS_WRITE_PUBLISH)
    if not check_permission(perms, req_perm):
        raise HTTPException(403, "Insufficient permissions")

    svc = CMSContentService(session)
    data = payload.model_dump(exclude_none=True, exclude={"extra"})
    try:
        item = await svc.update_entity(canonical, entity_id, data, user.id)
        return item
    except ValueError as e:
        raise HTTPException(404 if "not found" in str(e) else 400, str(e))


@router.delete("/{entity_type}/{entity_id}")
async def delete_content(
    entity_type: str,
    entity_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    canonical = _resolve(entity_type)
    if canonical not in ALL_ENTITY_TYPES:
        raise HTTPException(404, f"Unknown entity type: {entity_type}")
    perms = await _get_user_permissions(session, user.id)
    req_perm = _WRITE_PERM_MAP.get(canonical, Permission.CMS_WRITE_PUBLISH)
    if not check_permission(perms, req_perm):
        raise HTTPException(403, "Insufficient permissions")

    svc = CMSContentService(session)
    await svc.delete_entity(canonical, entity_id, user.id)
    return {"message": f"{entity_type} deleted"}


@router.put("/{entity_type}/{entity_id}/status")
async def update_content_status(
    entity_type: str,
    entity_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: CMSStatusUpdate = Body(...),
):
    canonical = _resolve(entity_type)
    if canonical not in ALL_ENTITY_TYPES:
        raise HTTPException(404, f"Unknown entity type: {entity_type}")
    perms = await _get_user_permissions(session, user.id)
    if not check_permission(perms, Permission.CMS_WRITE_PUBLISH):
        raise HTTPException(403, "Insufficient permissions")

    svc = CMSContentService(session)
    try:
        item = await svc.update_status(
            canonical, entity_id, payload.status, user.id
        )
        return item
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{entity_type}/count")
async def count_content(
    entity_type: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(None),
):
    canonical = _resolve(entity_type)
    if canonical not in ALL_ENTITY_TYPES:
        raise HTTPException(404, f"Unknown entity type: {entity_type}")

    svc = CMSContentService(session)
    count = await svc.count_entities(canonical, status=status)
    return {"entity_type": entity_type, "count": count}


@router.post("/{entity_type}/bulk/status")
async def bulk_update_content_status(
    entity_type: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    canonical = _resolve(entity_type)
    if canonical not in ALL_ENTITY_TYPES:
        raise HTTPException(404, f"Unknown entity type: {entity_type}")
    perms = await _get_user_permissions(session, user.id)
    if not check_permission(perms, Permission.CMS_WRITE_PUBLISH):
        raise HTTPException(403, "Insufficient permissions")

    ids = payload.get("ids", [])
    status = payload.get("status", "archived")
    svc = CMSContentService(session)
    count = await svc.bulk_update_status(canonical, ids, status)
    return {"updated": count}


@router.post("/{entity_type}/bulk/delete")
async def bulk_delete_content(
    entity_type: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    canonical = _resolve(entity_type)
    if canonical not in ALL_ENTITY_TYPES:
        raise HTTPException(404, f"Unknown entity type: {entity_type}")
    perms = await _get_user_permissions(session, user.id)
    req_perm = _WRITE_PERM_MAP.get(canonical, Permission.CMS_WRITE_PUBLISH)
    if not check_permission(perms, req_perm):
        raise HTTPException(403, "Insufficient permissions")

    ids = payload.get("ids", [])
    svc = CMSContentService(session)
    count = await svc.bulk_delete(canonical, ids)
    return {"deleted": count}
