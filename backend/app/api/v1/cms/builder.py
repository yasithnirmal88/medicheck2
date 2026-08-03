from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cms_user, get_db
from app.application.services.cms.builder_service import (
    QuestionnaireBuilderService,
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

router = APIRouter(prefix="/cms/builder", tags=["CMS Questionnaire Builder"])


async def _check_write_perm(
    session: AsyncSession, user_id: str
) -> None:
    from sqlalchemy import select

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
    if not check_permission(perms, Permission.CMS_WRITE_QUESTION):
        raise HTTPException(403, "Insufficient permissions to edit questions")


# --- Group hierarchy ---

@router.put("/groups/reorder")
async def reorder_groups(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: list[str] = Body(...),
):
    await _check_write_perm(session, user.id)
    svc = QuestionnaireBuilderService(session)
    return await svc.reorder_groups(payload)


@router.put("/groups/{group_id}/move")
async def move_group(
    group_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    await _check_write_perm(session, user.id)
    svc = QuestionnaireBuilderService(session)
    try:
        return await svc.move_group(
            group_id,
            payload.get("parent_group_id"),
            payload.get("new_order", 0),
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


# --- Question cloning ---

@router.post("/questions/{question_id}/clone")
async def clone_question(
    question_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    target_group_id: str | None = Query(None),
):
    await _check_write_perm(session, user.id)
    svc = QuestionnaireBuilderService(session)
    try:
        return await svc.clone_question(question_id, target_group_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


# --- Dependencies ---

@router.post("/dependencies")
async def create_dependency(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    await _check_write_perm(session, user.id)
    svc = QuestionnaireBuilderService(session)
    try:
        dep = await svc.set_dependency(
            question_id=payload["question_id"],
            depends_on_question_id=payload["depends_on_question_id"],
            condition=payload.get("condition", {}),
            operator=payload.get("operator", "AND"),
        )
        return dep
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/dependencies/{dependency_id}")
async def delete_dependency(
    dependency_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    await _check_write_perm(session, user.id)
    svc = QuestionnaireBuilderService(session)
    await svc.remove_dependency(dependency_id)
    return {"message": "Dependency removed"}


@router.get("/questions/{question_id}/dependencies")
async def get_question_dependencies(
    question_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireBuilderService(session)
    return await svc.get_question_dependencies(question_id)


# --- Branch rules ---

@router.post("/branch-rules/{body_system_id}")
async def set_branch_rules(
    body_system_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: list[dict] = Body(...),
):
    await _check_write_perm(session, user.id)
    svc = QuestionnaireBuilderService(session)
    return await svc.set_branch_rule(body_system_id, payload)


@router.get("/branch-rules/{body_system_id}")
async def get_branch_rules(
    body_system_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireBuilderService(session)
    return await svc.get_branch_rules(body_system_id)


# --- Questionnaire simulation ---

@router.post("/simulate/{template_id}")
async def simulate_questionnaire(
    template_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, object] = Body(...),
):
    svc = QuestionnaireBuilderService(session)
    try:
        return await svc.simulate_questionnaire(
            template_id, payload.get("answers", {})
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


# --- Version management ---

@router.post("/versions/{questionnaire_id}")
async def create_version_snapshot(
    questionnaire_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    await _check_write_perm(session, user.id)
    svc = QuestionnaireBuilderService(session)
    return await svc.create_snapshot(
        questionnaire_id,
        payload.get("snapshot", {}),
        reason=payload.get("reason"),
        created_by=user.id,
    )


@router.get("/versions/{questionnaire_id}")
async def get_version_history(
    questionnaire_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireBuilderService(session)
    return await svc.get_version_history(questionnaire_id)


@router.post("/versions/{questionnaire_id}/restore/{version}")
async def restore_version(
    questionnaire_id: str,
    version: int,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    await _check_write_perm(session, user.id)
    svc = QuestionnaireBuilderService(session)
    try:
        return await svc.restore_version(questionnaire_id, version)
    except ValueError as e:
        raise HTTPException(404, str(e))
