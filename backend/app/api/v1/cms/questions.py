from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_cms_user, get_db
from app.application.dtos.questionnaire_dtos import QuestionResponse
from app.domain.entities.question import (
    Question,
    QuestionDifficulty,
    QuestionStatus,
    QuestionType,
)
from app.domain.entities.question_dependency import QuestionDependency
from app.domain.entities.question_group import QuestionGroup
from app.domain.entities.question_option import QuestionOption
from app.domain.entities.questionnaire_template import QuestionnaireTemplate
from app.domain.entities.user import User
from app.infrastructure.persistence.repositories.sql_body_system_repository import (
    SQLBodySystemRepository,
)
from app.infrastructure.persistence.repositories.sql_question_group_repository import (
    SQLQuestionGroupRepository,
)
from app.infrastructure.persistence.repositories.sql_question_option_repository import (
    SQLQuestionOptionRepository,
)
from app.infrastructure.persistence.repositories.sql_question_repository import (
    SQLQuestionRepository,
)
from app.infrastructure.persistence.repositories.sql_questionnaire_repository import (
    SQLQuestionnaireRepository,
)

router = APIRouter(prefix="/cms", tags=["CMS"])


@router.get("/questions")
async def cms_list_questions(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    repo = SQLQuestionRepository(session)
    opt_repo = SQLQuestionOptionRepository(session)
    questions = await repo.find_active()
    result = []
    for q in questions:
        opts = await opt_repo.find_by_question(q.id)
        result.append(QuestionResponse.from_entity(q, opts))
    return result


@router.post("/questions")
async def cms_create_question(
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    repo = SQLQuestionRepository(session)
    qtype = QuestionType(payload.get("question_type", "free_text"))
    difficulty = QuestionDifficulty(payload.get("difficulty", "basic"))
    status = QuestionStatus(payload.get("status", "active"))

    question = Question.create(
        body_system_id=payload["body_system_id"],
        question_group_id=payload["question_group_id"],
        code=payload["code"],
        question_type=qtype,
        text=payload.get("text", ""),
        description=payload.get("description"),
        tooltip=payload.get("tooltip"),
        medical_notes=payload.get("medical_notes"),
        evidence_ref=payload.get("evidence_ref"),
        order_index=payload.get("order_index", 0),
        priority=payload.get("priority", 3),
        difficulty=difficulty,
        status=status,
        is_required=payload.get("is_required", False),
        validation_rules=payload.get("validation_rules"),
        scoring_weight=payload.get("scoring_weight", 1.0),
        created_by=admin.id,
        updated_by=admin.id,
    )

    created = await repo.create(question)
    opt_repo = SQLQuestionOptionRepository(session)
    opts = await opt_repo.find_by_question(created.id)
    return QuestionResponse.from_entity(created, opts)


@router.put("/questions/{id}")
async def cms_update_question(
    id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    repo = SQLQuestionRepository(session)
    existing = await repo.find_by_id(id)
    if not existing:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Question not found")

    if "question_type" in payload:
        existing.question_type = QuestionType(payload["question_type"])
    if "difficulty" in payload:
        existing.difficulty = QuestionDifficulty(payload["difficulty"])
    if "status" in payload:
        existing.status = QuestionStatus(payload["status"])
    for field in (
        "body_system_id",
        "question_group_id",
        "code",
        "text",
        "description",
        "tooltip",
        "medical_notes",
        "evidence_ref",
        "order_index",
        "priority",
        "is_required",
        "validation_rules",
        "scoring_weight",
        "activation_date",
        "expiration_date",
    ):
        if field in payload:
            setattr(existing, field, payload[field])
    existing.updated_by = admin.id
    existing.updated_at = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )

    updated = await repo.update(existing)
    opt_repo = SQLQuestionOptionRepository(session)
    opts = await opt_repo.find_by_question(updated.id)
    return QuestionResponse.from_entity(updated, opts)


@router.delete("/questions/{id}")
async def cms_delete_question(
    id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    repo = SQLQuestionRepository(session)
    await repo.delete(id)
    return {"message": "Question deactivated"}


@router.get("/questions/{id}/versions")
async def cms_get_question_versions(
    id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    from sqlalchemy import select

    from app.infrastructure.persistence.models.questionnaire_version import (
        QuestionnaireVersionModel,
    )

    stmt = (
        select(QuestionnaireVersionModel)
        .where(QuestionnaireVersionModel.questionnaire_template_id == id)
        .order_by(QuestionnaireVersionModel.version.desc())
    )
    result = await session.execute(stmt)
    return [v.to_dict() for v in result.scalars().all()]


@router.post("/questions/{id}/versions")
async def cms_create_question_version(
    id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    from sqlalchemy import func, select

    from app.infrastructure.persistence.models.questionnaire_version import (
        QuestionnaireVersionModel,
    )

    stmt = select(func.max(QuestionnaireVersionModel.version)).where(
        QuestionnaireVersionModel.questionnaire_template_id == id
    )
    result = await session.execute(stmt)
    max_ver = result.scalar() or 0

    from app.domain.entities.questionnaire_version import QuestionnaireVersion

    version = QuestionnaireVersion.create(
        questionnaire_template_id=id,
        version=max_ver + 1,
        snapshot=payload.get("snapshot", {}),
        change_notes=payload.get("change_notes"),
        created_by=admin.id,
    )
    model = QuestionnaireVersionModel(
        id=version.id,
        questionnaire_template_id=version.questionnaire_template_id,
        version=version.version,
        snapshot=version.snapshot,
        change_notes=version.change_notes,
        created_by=version.created_by,
    )
    session.add(model)
    await session.flush()
    return version.to_dict()


@router.post("/questions/{id}/options")
async def cms_add_option(
    id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    opt = QuestionOption.create(
        question_id=id,
        code=payload["code"],
        text=payload.get("text", ""),
        value=payload.get("value", payload["code"]),
        score_value=payload.get("score_value", 0.0),
        severity=payload.get("severity", "none"),
        color_hex=payload.get("color_hex"),
        recommendation_trigger=payload.get("recommendation_trigger"),
        follow_up_trigger=payload.get("follow_up_trigger"),
        display_order=payload.get("display_order", 0),
        is_active=payload.get("is_active", True),
    )
    repo = SQLQuestionOptionRepository(session)
    created = await repo.create(opt)
    return created.to_dict()


@router.put("/questions/{id}/options/{opt_id}")
async def cms_update_option(
    id: str,
    opt_id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    repo = SQLQuestionOptionRepository(session)
    existing = await repo.find_by_id(opt_id)
    if not existing:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Option not found")

    for field in (
        "code",
        "text",
        "value",
        "score_value",
        "severity",
        "color_hex",
        "recommendation_trigger",
        "follow_up_trigger",
        "display_order",
        "is_active",
    ):
        if field in payload:
            setattr(existing, field, payload[field])
    existing.updated_at = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )

    updated = await repo.update(existing)
    return updated.to_dict()


@router.delete("/questions/{id}/options/{opt_id}")
async def cms_delete_option(
    id: str,
    opt_id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    repo = SQLQuestionOptionRepository(session)
    existing = await repo.find_by_id(opt_id)
    if not existing:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Option not found")
    existing.is_active = False
    existing.updated_at = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )
    await repo.update(existing)
    return {"message": "Option deactivated"}


@router.post("/questions/{id}/dependencies")
async def cms_add_dependency(
    id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    from app.infrastructure.persistence.models.question_dependency import (
        QuestionDependencyModel,
    )

    dep = QuestionDependency.create(
        question_id=id,
        depends_on_question_id=payload["depends_on_question_id"],
        condition_type=payload.get("condition_type", "equals"),
        condition_value=payload.get("condition_value", {}),
        logic_operator=payload.get("logic_operator", "AND"),
        group_id=payload.get("group_id", 0),
    )
    model = QuestionDependencyModel(
        id=dep.id,
        question_id=dep.question_id,
        depends_on_question_id=dep.depends_on_question_id,
        condition_type=dep.condition_type,
        condition_value=dep.condition_value,
        logic_operator=dep.logic_operator,
        group_id=dep.group_id,
    )
    session.add(model)
    await session.flush()
    return dep.to_dict()


@router.delete("/questions/{id}/dependencies/{dep_id}")
async def cms_remove_dependency(
    id: str,
    dep_id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    from sqlalchemy import select

    from app.infrastructure.persistence.models.question_dependency import (
        QuestionDependencyModel,
    )

    stmt = select(QuestionDependencyModel).where(QuestionDependencyModel.id == dep_id)
    result = await session.execute(stmt)
    model = result.scalar_one_or_none()
    if model is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Dependency not found")
    await session.delete(model)
    await session.flush()
    return {"message": "Dependency removed"}


@router.get("/body-systems")
async def cms_list_body_systems(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    repo = SQLBodySystemRepository(session)
    systems = await repo.find_all_active()
    return [s.to_dict() for s in systems]


@router.put("/body-systems/{code}")
async def cms_update_body_system(
    code: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    repo = SQLBodySystemRepository(session)
    existing = await repo.find_by_code(code)
    if not existing:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Body system not found")

    for field in (
        "name",
        "description",
        "icon",
        "color_hex",
        "display_order",
        "module_version",
        "is_active",
        "is_core",
        "scoring_weight",
        "metadata",
    ):
        if field in payload:
            setattr(existing, field, payload[field])
    existing.updated_at = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )

    updated = await repo.update(existing)
    return updated.to_dict()


@router.get("/question-groups")
async def cms_list_question_groups(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    body_system_id: str | None = None,
):
    repo = SQLQuestionGroupRepository(session)
    if body_system_id:
        groups = await repo.find_by_body_system(body_system_id)
    else:
        from sqlalchemy import select

        from app.infrastructure.persistence.models.question_group import (
            QuestionGroupModel,
        )

        stmt = select(QuestionGroupModel).order_by(QuestionGroupModel.display_order)
        result = await session.execute(stmt)
        groups = [repo._to_entity(m) for m in result.scalars().all()]
    return [g.to_dict() for g in groups]


@router.post("/question-groups")
async def cms_create_question_group(
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    group = QuestionGroup.create(
        body_system_id=payload["body_system_id"],
        code=payload["code"],
        name=payload.get("name", ""),
        description=payload.get("description"),
        display_order=payload.get("display_order", 0),
        is_active=payload.get("is_active", True),
        metadata=payload.get("metadata"),
    )
    repo = SQLQuestionGroupRepository(session)
    created = await repo.create(group)
    return created.to_dict()


@router.put("/question-groups/{id}")
async def cms_update_question_group(
    id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    repo = SQLQuestionGroupRepository(session)
    existing = await repo.find_by_id(id)
    if not existing:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Question group not found")

    for field in (
        "body_system_id",
        "code",
        "name",
        "description",
        "display_order",
        "is_active",
        "metadata",
    ):
        if field in payload:
            setattr(existing, field, payload[field])
    existing.updated_at = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )

    updated = await repo.update(existing)
    return updated.to_dict()


@router.get("/templates")
async def cms_list_templates(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    repo = SQLQuestionnaireRepository(session)
    templates = await repo.find_all_active()
    return [t.to_dict() for t in templates]


@router.post("/templates")
async def cms_create_template(
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    template = QuestionnaireTemplate.create(
        code=payload["code"],
        name=payload.get("name", ""),
        description=payload.get("description"),
        body_system_id=payload.get("body_system_id"),
        target_audience=payload.get("target_audience", "all"),
        estimated_time_minutes=payload.get("estimated_time_minutes", 10),
        is_active=payload.get("is_active", True),
        is_template=payload.get("is_template", True),
        metadata=payload.get("metadata"),
    )
    repo = SQLQuestionnaireRepository(session)
    created = await repo.create(template)
    return created.to_dict()


@router.put("/templates/{id}")
async def cms_update_template(
    id: str,
    admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict[str, Any] = Body(...),
):
    repo = SQLQuestionnaireRepository(session)
    existing = await repo.find_by_id(id)
    if not existing:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Template not found")

    for field in (
        "code",
        "name",
        "description",
        "body_system_id",
        "target_audience",
        "estimated_time_minutes",
        "is_active",
        "is_template",
        "version",
        "metadata",
    ):
        if field in payload:
            setattr(existing, field, payload[field])
    existing.updated_at = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )

    updated = await repo.update(existing)
    return updated.to_dict()
