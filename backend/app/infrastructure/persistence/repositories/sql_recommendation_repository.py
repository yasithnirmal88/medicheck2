from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.recommendation import Recommendation
from app.domain.repositories.recommendation_repository import RecommendationRepository
from app.infrastructure.persistence.models.recommendation import RecommendationModel


class SQLRecommendationRepository(RecommendationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> Recommendation | None:
        stmt = select(RecommendationModel).where(
            RecommendationModel.id == id,
            RecommendationModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[Recommendation]:
        stmt = (
            select(RecommendationModel)
            .where(
                RecommendationModel.body_system_id == body_system_id,
                RecommendationModel.deleted_at.is_(None),
            )
            .order_by(RecommendationModel.priority)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_disease(self, disease_id: str) -> list[Recommendation]:
        stmt = (
            select(RecommendationModel)
            .where(
                RecommendationModel.disease_id == disease_id,
                RecommendationModel.deleted_at.is_(None),
            )
            .order_by(RecommendationModel.priority)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_all_active(self) -> list[Recommendation]:
        stmt = (
            select(RecommendationModel)
            .where(
                RecommendationModel.is_active.is_(True),
                RecommendationModel.deleted_at.is_(None),
            )
            .order_by(RecommendationModel.priority)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, recommendation: Recommendation) -> Recommendation:
        model = RecommendationModel(
            id=recommendation.id,
            key=recommendation.title[:100].upper().replace(" ", "_"),
            body_system_id=recommendation.body_system_id,
            disease_id=recommendation.disease_id,
            category=recommendation.category,
            title=recommendation.title,
            text=recommendation.text,
            order=recommendation.priority,
            priority=recommendation.priority,
            urgency=recommendation.urgency,
            evidence_level=recommendation.evidence_level,
            is_active=recommendation.is_active,
            version=recommendation.version,
            status=recommendation.status,
            created_by=recommendation.created_by,
            updated_by=recommendation.updated_by,
            created_at=recommendation.created_at,
            updated_at=recommendation.updated_at,
            deleted_at=recommendation.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return recommendation

    async def update(self, recommendation: Recommendation) -> Recommendation:
        stmt = select(RecommendationModel).where(
            RecommendationModel.id == recommendation.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(
                f"Recommendation with id {recommendation.id} not found"
            )

        model.key = recommendation.title[:100].upper().replace(" ", "_")
        model.body_system_id = recommendation.body_system_id
        model.disease_id = recommendation.disease_id
        model.category = recommendation.category
        model.title = recommendation.title
        model.text = recommendation.text
        model.order = recommendation.priority
        model.priority = recommendation.priority
        model.urgency = recommendation.urgency
        model.evidence_level = recommendation.evidence_level
        model.is_active = recommendation.is_active
        model.version = recommendation.version
        model.status = recommendation.status
        model.updated_by = recommendation.updated_by
        model.updated_at = recommendation.updated_at
        model.deleted_at = recommendation.deleted_at

        await self._session.flush()
        return recommendation

    def _to_entity(self, model: RecommendationModel) -> Recommendation:
        return Recommendation(
            id=model.id,
            body_system_id=model.body_system_id,
            disease_id=model.disease_id,
            category=model.category,
            title=model.title,
            text=model.text,
            priority=model.priority,
            urgency=model.urgency,
            evidence_level=model.evidence_level,
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
