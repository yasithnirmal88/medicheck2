from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.questionnaire_template import QuestionnaireTemplate
from app.domain.entities.questionnaire_version import QuestionnaireVersion
from app.domain.repositories.questionnaire_repository import QuestionnaireRepository
from app.infrastructure.persistence.models.questionnaire_template import (
    QuestionnaireTemplateModel,
)
from app.infrastructure.persistence.models.questionnaire_version import (
    QuestionnaireVersionModel,
)


class SQLQuestionnaireRepository(QuestionnaireRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> QuestionnaireTemplate | None:
        stmt = select(QuestionnaireTemplateModel).where(
            QuestionnaireTemplateModel.id == id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_code(self, code: str) -> QuestionnaireTemplate | None:
        stmt = select(QuestionnaireTemplateModel).where(
            QuestionnaireTemplateModel.code == code
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_all_active(self) -> list[QuestionnaireTemplate]:
        stmt = (
            select(QuestionnaireTemplateModel)
            .where(
                QuestionnaireTemplateModel.is_active.is_(True),
                QuestionnaireTemplateModel.deleted_at.is_(None),
            )
            .order_by(QuestionnaireTemplateModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[QuestionnaireTemplate]:
        stmt = (
            select(QuestionnaireTemplateModel)
            .where(
                QuestionnaireTemplateModel.body_system_id == body_system_id,
                QuestionnaireTemplateModel.deleted_at.is_(None),
            )
            .order_by(QuestionnaireTemplateModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_target_audience(
        self, audience: str
    ) -> list[QuestionnaireTemplate]:
        stmt = (
            select(QuestionnaireTemplateModel)
            .where(
                QuestionnaireTemplateModel.target_audience == audience,
                QuestionnaireTemplateModel.is_active.is_(True),
                QuestionnaireTemplateModel.deleted_at.is_(None),
            )
            .order_by(QuestionnaireTemplateModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, template: QuestionnaireTemplate) -> QuestionnaireTemplate:
        model = QuestionnaireTemplateModel(
            id=template.id,
            code=template.code,
            name=template.name,
            description=template.description,
            body_system_id=template.body_system_id,
            target_audience=template.target_audience,
            estimated_time_minutes=template.estimated_time_minutes,
            is_active=template.is_active,
            is_template=template.is_template,
            version=template.version,
            extra_metadata=template.metadata,
            created_at=template.created_at,
            updated_at=template.updated_at,
            deleted_at=template.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return template

    async def update(self, template: QuestionnaireTemplate) -> QuestionnaireTemplate:
        stmt = select(QuestionnaireTemplateModel).where(
            QuestionnaireTemplateModel.id == template.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"QuestionnaireTemplate with id {template.id} not found")

        model.code = template.code
        model.name = template.name
        model.description = template.description
        model.body_system_id = template.body_system_id
        model.target_audience = template.target_audience
        model.estimated_time_minutes = template.estimated_time_minutes
        model.is_active = template.is_active
        model.is_template = template.is_template
        model.version = template.version
        model.extra_metadata = template.metadata
        model.updated_at = template.updated_at
        model.deleted_at = template.deleted_at

        await self._session.flush()
        return template

    async def find_version(
        self, template_id: str, version: int
    ) -> QuestionnaireVersion | None:
        stmt = select(QuestionnaireVersionModel).where(
            QuestionnaireVersionModel.questionnaire_template_id == template_id,
            QuestionnaireVersionModel.version == version,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_version_entity(model) if model else None

    async def create_version(
        self, version: QuestionnaireVersion
    ) -> QuestionnaireVersion:
        model = QuestionnaireVersionModel(
            id=version.id,
            questionnaire_template_id=version.questionnaire_template_id,
            version=version.version,
            snapshot=version.snapshot,
            change_notes=version.change_notes,
            created_by=version.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return version

    def _to_entity(self, model: QuestionnaireTemplateModel) -> QuestionnaireTemplate:
        return QuestionnaireTemplate(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description,
            body_system_id=model.body_system_id,
            target_audience=model.target_audience,
            estimated_time_minutes=model.estimated_time_minutes,
            is_active=model.is_active,
            is_template=model.is_template,
            version=model.version,
            metadata=model.extra_metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    def _to_version_entity(
        self, model: QuestionnaireVersionModel
    ) -> QuestionnaireVersion:
        return QuestionnaireVersion(
            id=model.id,
            questionnaire_template_id=model.questionnaire_template_id,
            version=model.version,
            snapshot=model.snapshot,
            change_notes=model.change_notes,
            created_by=model.created_by,
            created_at=model.created_at,
        )
