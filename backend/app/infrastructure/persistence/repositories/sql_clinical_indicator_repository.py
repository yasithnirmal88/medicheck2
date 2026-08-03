from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.clinical_indicator import ClinicalIndicator
from app.domain.repositories.clinical_indicator_repository import (
    ClinicalIndicatorRepository,
)
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)


class SQLClinicalIndicatorRepository(ClinicalIndicatorRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> ClinicalIndicator | None:
        stmt = select(ClinicalIndicatorModel).where(
            ClinicalIndicatorModel.id == id, ClinicalIndicatorModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_key(self, key: str) -> ClinicalIndicator | None:
        stmt = select(ClinicalIndicatorModel).where(
            ClinicalIndicatorModel.key == key,
            ClinicalIndicatorModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[ClinicalIndicator]:
        stmt = (
            select(ClinicalIndicatorModel)
            .where(
                ClinicalIndicatorModel.body_system_id == body_system_id,
                ClinicalIndicatorModel.deleted_at.is_(None),
            )
            .order_by(ClinicalIndicatorModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_disease(self, disease_id: str) -> list[ClinicalIndicator]:
        stmt = select(ClinicalIndicatorModel).where(
            ClinicalIndicatorModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        all_models = result.scalars().all()
        return [
            self._to_entity(m)
            for m in all_models
            if m.related_disease_ids and disease_id in m.related_disease_ids
        ]

    async def find_all_active(self) -> list[ClinicalIndicator]:
        stmt = (
            select(ClinicalIndicatorModel)
            .where(
                ClinicalIndicatorModel.is_active.is_(True),
                ClinicalIndicatorModel.deleted_at.is_(None),
            )
            .order_by(ClinicalIndicatorModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, indicator: ClinicalIndicator) -> ClinicalIndicator:
        model = ClinicalIndicatorModel(
            id=indicator.id,
            body_system_id=indicator.body_system_id,
            key=indicator.key,
            name=indicator.name,
            description=indicator.description,
            severity=indicator.severity,
            evidence_strength=indicator.evidence_strength,
            confidence=indicator.confidence,
            positive_weight=indicator.positive_weight,
            negative_weight=indicator.negative_weight,
            neutral_weight=indicator.neutral_weight,
            related_disease_ids=indicator.related_disease_ids,
            related_symptom_ids=indicator.related_symptom_ids,
            is_active=indicator.is_active,
            version=indicator.version,
            status=indicator.status,
            created_by=indicator.created_by,
            updated_by=indicator.updated_by,
            created_at=indicator.created_at,
            updated_at=indicator.updated_at,
            deleted_at=indicator.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return indicator

    async def update(self, indicator: ClinicalIndicator) -> ClinicalIndicator:
        stmt = select(ClinicalIndicatorModel).where(
            ClinicalIndicatorModel.id == indicator.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"ClinicalIndicator with id {indicator.id} not found")

        model.body_system_id = indicator.body_system_id
        model.key = indicator.key
        model.name = indicator.name
        model.description = indicator.description
        model.severity = indicator.severity
        model.evidence_strength = indicator.evidence_strength
        model.confidence = indicator.confidence
        model.positive_weight = indicator.positive_weight
        model.negative_weight = indicator.negative_weight
        model.neutral_weight = indicator.neutral_weight
        model.related_disease_ids = indicator.related_disease_ids
        model.related_symptom_ids = indicator.related_symptom_ids
        model.is_active = indicator.is_active
        model.version = indicator.version
        model.status = indicator.status
        model.updated_by = indicator.updated_by
        model.updated_at = indicator.updated_at
        model.deleted_at = indicator.deleted_at

        await self._session.flush()
        return indicator

    def _to_entity(self, model: ClinicalIndicatorModel) -> ClinicalIndicator:
        return ClinicalIndicator(
            id=model.id,
            body_system_id=model.body_system_id,
            key=model.key,
            name=model.name,
            description=model.description or "",
            severity=model.severity,
            evidence_strength=model.evidence_strength,
            confidence=model.confidence,
            positive_weight=model.positive_weight,
            negative_weight=model.negative_weight,
            neutral_weight=model.neutral_weight,
            related_disease_ids=model.related_disease_ids or [],
            related_symptom_ids=model.related_symptom_ids or [],
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
