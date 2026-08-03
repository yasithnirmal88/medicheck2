from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.question import Question
from app.domain.entities.question_dependency import QuestionDependency
from app.domain.entities.questionnaire_version import QuestionnaireVersion
from app.infrastructure.persistence.models.branch_rule import BranchRuleModel
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.question_dependency import (
    QuestionDependencyModel,
)
from app.infrastructure.persistence.models.question_group import QuestionGroupModel
from app.infrastructure.persistence.models.questionnaire_template import (
    QuestionnaireTemplateModel,
)
from app.infrastructure.persistence.models.questionnaire_version import (
    QuestionnaireVersionModel,
)
from app.infrastructure.persistence.repositories.sql_generic_cms_repository import (
    SQLGenericCMSRepository,
)


class QuestionnaireBuilderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- Group hierarchy management ---

    async def reorder_groups(
        self, group_ids: list[str]
    ) -> list[dict[str, Any]]:
        updated = []
        for idx, gid in enumerate(group_ids):
            stmt = select(QuestionGroupModel).where(QuestionGroupModel.id == gid)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            if model:
                model.display_order = idx
                updated.append(
                    {
                        "id": model.id,
                        "display_order": idx,
                    }
                )
        await self._session.flush()
        return updated

    async def move_group(
        self, group_id: str, target_parent_id: str | None, new_order: int
    ) -> dict[str, Any]:
        stmt = select(QuestionGroupModel).where(QuestionGroupModel.id == group_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Group {group_id} not found")

        model.parent_group_id = target_parent_id
        model.display_order = new_order
        await self._session.flush()
        return {
            "id": model.id,
            "parent_group_id": model.parent_group_id,
            "display_order": model.display_order,
        }

    async def clone_question(
        self, question_id: str, target_group_id: str | None = None
    ) -> dict[str, Any]:
        stmt = select(QuestionModel).where(QuestionModel.id == question_id)
        result = await self._session.execute(stmt)
        src = result.scalar_one_or_none()
        if src is None:
            raise ValueError(f"Question {question_id} not found")

        import uuid

        new_q = Question.create(
            body_system_id=src.body_system_id,
            question_group_id=target_group_id or src.question_group_id,
            code=f"{src.code}_CLONE_{uuid.uuid4().hex[:6]}",
            question_type=src.question_type,
            text=src.text,
            description=src.description,
            tooltip=src.tooltip,
            medical_notes=src.medical_notes,
            evidence_ref=src.evidence_ref,
            order_index=src.order_index,
            priority=src.priority,
            difficulty=src.difficulty,
            status=src.status,
            is_required=src.is_required,
            validation_rules=src.validation_rules,
            scoring_weight=src.scoring_weight,
        )

        model = QuestionModel(
            id=new_q.id,
            body_system_id=new_q.body_system_id,
            question_group_id=new_q.question_group_id,
            code=new_q.code,
            question_type=new_q.question_type,
            text=new_q.text,
            description=new_q.description,
            tooltip=new_q.tooltip,
            medical_notes=new_q.medical_notes,
            evidence_ref=new_q.evidence_ref,
            order_index=new_q.order_index,
            priority=new_q.priority,
            difficulty=new_q.difficulty,
            status=new_q.status,
            is_required=new_q.is_required,
            validation_rules=new_q.validation_rules,
            scoring_weight=new_q.scoring_weight,
            created_by=new_q.created_by,
            updated_by=new_q.updated_by,
            created_at=new_q.created_at,
            updated_at=new_q.updated_at,
        )
        self._session.add(model)

        await self._session.flush()

        return new_q.to_dict()

    # --- Dependencies ---

    async def set_dependency(
        self,
        question_id: str,
        depends_on_question_id: str,
        condition: dict[str, Any],
        operator: str = "AND",
    ) -> dict[str, Any]:
        dep = QuestionDependency.create(
            question_id=question_id,
            depends_on_question_id=depends_on_question_id,
            condition=condition,
            operator=operator,
        )
        model = QuestionDependencyModel(
            id=dep.id,
            question_id=dep.question_id,
            depends_on_question_id=dep.depends_on_question_id,
            condition=dep.condition,
            operator=dep.operator,
            created_at=dep.created_at,
            updated_at=dep.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return dep.to_dict()

    async def remove_dependency(self, dependency_id: str) -> None:
        stmt = select(QuestionDependencyModel).where(
            QuestionDependencyModel.id == dependency_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_question_dependencies(
        self, question_id: str
    ) -> list[dict[str, Any]]:
        stmt = select(QuestionDependencyModel).where(
            QuestionDependencyModel.question_id == question_id
        )
        result = await self._session.execute(stmt)
        return [m.to_dict() for m in result.scalars().all()]

    # --- Branch rules ---

    async def set_branch_rule(
        self, body_system_id: str, rules: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        import uuid

        created = []
        for rule_data in rules:
            model = BranchRuleModel(
                id=uuid.uuid4().hex,
                body_system_id=body_system_id,
                rule_type=rule_data.get("rule_type", "condition"),
                condition=rule_data.get("condition", {}),
                action=rule_data.get("action", {}),
                priority=rule_data.get("priority", 5),
                is_active=True,
            )
            self._session.add(model)
            created.append(model.to_dict())
        await self._session.flush()
        return created

    async def get_branch_rules(
        self, body_system_id: str
    ) -> list[dict[str, Any]]:
        stmt = (
            select(BranchRuleModel)
            .where(BranchRuleModel.body_system_id == body_system_id)
            .order_by(BranchRuleModel.priority)
        )
        result = await self._session.execute(stmt)
        return [m.to_dict() for m in result.scalars().all()]

    # --- Questionnaire simulation ---

    async def simulate_questionnaire(
        self, template_id: str, answers: dict[str, Any]
    ) -> dict[str, Any]:
        stmt = select(QuestionnaireTemplateModel).where(
            QuestionnaireTemplateModel.id == template_id
        )
        result = await self._session.execute(stmt)
        template = result.scalar_one_or_none()
        if template is None:
            raise ValueError(f"Template {template_id} not found")

        questions_stmt = (
            select(QuestionModel)
            .where(QuestionModel.body_system_id == template.body_system_id)
            .order_by(QuestionModel.order_index)
        )
        questions_result = await self._session.execute(questions_stmt)
        all_questions = list(questions_result.scalars().all())

        visible = []
        skipped = []
        for q in all_questions:
            deps_stmt = select(QuestionDependencyModel).where(
                QuestionDependencyModel.question_id == q.id
            )
            deps_result = await self._session.execute(deps_stmt)
            deps = list(deps_result.scalars().all())

            if deps:
                conditions_met = all(
                    answers.get(d.depends_on_question_id) in d.condition.get("values", [])
                    for d in deps
                )
                if not conditions_met:
                    skipped.append(
                        {
                            "question_id": q.id,
                            "code": q.code,
                            "reason": "dependency_not_met",
                        }
                    )
                    continue

            visible.append(
                {
                    "question_id": q.id,
                    "code": q.code,
                    "text": q.text,
                    "question_type": q.question_type,
                    "is_required": q.is_required,
                }
            )

        return {
            "template_id": template_id,
            "total_questions": len(all_questions),
            "visible_questions": len(visible),
            "skipped_questions": len(skipped),
            "questions": visible,
            "skipped": skipped,
            "answers_provided": len(answers),
        }

    # --- Version management ---

    async def create_snapshot(
        self,
        questionnaire_id: str,
        snapshot_data: dict[str, Any],
        reason: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        stmt = (
            select(QuestionnaireVersionModel)
            .where(
                QuestionnaireVersionModel.questionnaire_template_id == questionnaire_id
            )
            .order_by(QuestionnaireVersionModel.version.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        latest = result.scalar_one_or_none()
        next_ver = (latest.version + 1) if latest else 1

        version = QuestionnaireVersion.create(
            questionnaire_template_id=questionnaire_id,
            version=next_ver,
            snapshot=snapshot_data,
            created_by=created_by,
        )
        model = QuestionnaireVersionModel(
            id=version.id,
            questionnaire_template_id=version.questionnaire_template_id,
            version=version.version,
            snapshot=version.snapshot,
            change_summary=reason or f"Version {next_ver}",
            created_by=version.created_by,
            created_at=version.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return version.to_dict()

    async def get_version_history(
        self, questionnaire_id: str
    ) -> list[dict[str, Any]]:
        repo = SQLGenericCMSRepository(
            self._session, QuestionnaireVersionModel
        )
        models = await repo.find_by_field(
            "questionnaire_template_id", questionnaire_id
        )
        return [m.to_dict() for m in models]

    async def restore_version(
        self, questionnaire_id: str, version_number: int
    ) -> dict[str, Any]:
        stmt = (
            select(QuestionnaireVersionModel)
            .where(
                QuestionnaireVersionModel.questionnaire_template_id == questionnaire_id,
                QuestionnaireVersionModel.version == version_number,
            )
        )
        result = await self._session.execute(stmt)
        version = result.scalar_one_or_none()
        if version is None:
            raise ValueError(
                f"Version {version_number} not found for {questionnaire_id}"
            )
        return version.snapshot
