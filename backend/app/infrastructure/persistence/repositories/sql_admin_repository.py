from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.audit_log import AuditLogModel
from app.infrastructure.persistence.models.body_system import BodySystemModel
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.evidence_reference import (
    EvidenceReferenceModel,
)
from app.infrastructure.persistence.models.recommendation import RecommendationModel


class SQLAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Body Systems
    async def create_body_system(self, data: dict) -> BodySystemModel:
        keys = [c.name for c in BodySystemModel.__table__.columns]
        filtered = {k: v for k, v in data.items() if k in keys}
        model = BodySystemModel(**filtered)
        self.session.add(model)
        await self.session.flush()
        await self.session.commit()
        return model

    async def list_body_systems(self) -> list[BodySystemModel]:
        q = select(BodySystemModel).order_by(BodySystemModel.name)
        r = await self.session.execute(q)
        return r.scalars().all()

    async def get_body_system(self, bs_id: str) -> BodySystemModel | None:
        q = select(BodySystemModel).where(BodySystemModel.id == bs_id)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def update_body_system(self, bs_id: str, data: dict) -> BodySystemModel:
        stmt = update(BodySystemModel).where(BodySystemModel.id == bs_id).values(**data)
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_body_system(bs_id)

    async def delete_body_system(self, bs_id: str) -> None:
        stmt = delete(BodySystemModel).where(BodySystemModel.id == bs_id)
        await self.session.execute(stmt)
        await self.session.commit()

    # Indicators
    async def create_indicator(self, data: dict) -> ClinicalIndicatorModel:
        keys = [c.name for c in ClinicalIndicatorModel.__table__.columns]
        filtered = {k: v for k, v in data.items() if k in keys}
        model = ClinicalIndicatorModel(**filtered)
        self.session.add(model)
        await self.session.flush()
        await self.session.commit()
        return model

    async def update_indicator(self, ind_id: str, data: dict) -> ClinicalIndicatorModel:
        stmt = (
            update(ClinicalIndicatorModel)
            .where(ClinicalIndicatorModel.id == ind_id)
            .values(**data)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        q = select(ClinicalIndicatorModel).where(ClinicalIndicatorModel.id == ind_id)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_indicators(
        self, body_system_id: str | None = None
    ) -> list[ClinicalIndicatorModel]:
        q = select(ClinicalIndicatorModel)
        if body_system_id:
            q = q.where(ClinicalIndicatorModel.body_system_id == body_system_id)
        q = q.order_by(ClinicalIndicatorModel.order)
        r = await self.session.execute(q)
        return r.scalars().all()

    async def get_indicator(self, ind_id: str) -> ClinicalIndicatorModel | None:
        q = select(ClinicalIndicatorModel).where(ClinicalIndicatorModel.id == ind_id)
        r = await self.session.execute(q)
        return r.scalars().first()

    # Evidence refs
    async def create_evidence(self, data: dict) -> EvidenceReferenceModel:
        keys = [c.name for c in EvidenceReferenceModel.__table__.columns]
        filtered = {k: v for k, v in data.items() if k in keys}
        model = EvidenceReferenceModel(**filtered)
        self.session.add(model)
        await self.session.flush()
        await self.session.commit()
        return model

    async def list_evidence(self, limit: int = 50) -> list[EvidenceReferenceModel]:
        q = (
            select(EvidenceReferenceModel)
            .order_by(EvidenceReferenceModel.title)
            .limit(limit)
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def get_evidence(self, ev_id: str) -> EvidenceReferenceModel | None:
        q = select(EvidenceReferenceModel).where(EvidenceReferenceModel.id == ev_id)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def update_evidence(self, ev_id: str, data: dict) -> EvidenceReferenceModel:
        stmt = (
            update(EvidenceReferenceModel)
            .where(EvidenceReferenceModel.id == ev_id)
            .values(**data)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_evidence(ev_id)

    async def delete_evidence(self, ev_id: str) -> None:
        stmt = delete(EvidenceReferenceModel).where(EvidenceReferenceModel.id == ev_id)
        await self.session.execute(stmt)
        await self.session.commit()

    # Recommendations
    async def create_recommendation(self, data: dict) -> RecommendationModel:
        keys = [c.name for c in RecommendationModel.__table__.columns]
        filtered = {k: v for k, v in data.items() if k in keys}
        model = RecommendationModel(**filtered)
        self.session.add(model)
        await self.session.flush()
        await self.session.commit()
        return model

    async def list_recommendations(self, limit: int = 100) -> list[RecommendationModel]:
        q = select(RecommendationModel).order_by(RecommendationModel.priority).limit(limit)
        r = await self.session.execute(q)
        return r.scalars().all()

    async def get_recommendation(self, rec_id: str) -> RecommendationModel | None:
        q = select(RecommendationModel).where(RecommendationModel.id == rec_id)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def update_recommendation(self, rec_id: str, data: dict) -> RecommendationModel:
        stmt = update(RecommendationModel).where(RecommendationModel.id == rec_id).values(**data)
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_recommendation(rec_id)

    # Audit
    async def list_audit(self, entity_type: str | None = None, limit: int = 100) -> list[AuditLogModel]:
        q = select(AuditLogModel)
        if entity_type:
            q = q.where(AuditLogModel.entity_type == entity_type)
        q = q.order_by(AuditLogModel.changed_at.desc()).limit(limit)
        r = await self.session.execute(q)
        return r.scalars().all()

    async def create_audit(self, data: dict) -> AuditLogModel:
        model = AuditLogModel(**data)
        self.session.add(model)
        await self.session.flush()
        await self.session.commit()
        return model
