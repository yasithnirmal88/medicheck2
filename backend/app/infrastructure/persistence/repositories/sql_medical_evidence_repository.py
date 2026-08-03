from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.medical_evidence import MedicalEvidence
from app.domain.repositories.medical_evidence_repository import (
    MedicalEvidenceRepository,
)
from app.infrastructure.persistence.models.medical_evidence import MedicalEvidenceModel


class SQLMedicalEvidenceRepository(MedicalEvidenceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> MedicalEvidence | None:
        stmt = select(MedicalEvidenceModel).where(
            MedicalEvidenceModel.id == id,
            MedicalEvidenceModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_doi(self, doi: str) -> MedicalEvidence | None:
        stmt = select(MedicalEvidenceModel).where(
            MedicalEvidenceModel.doi == doi,
            MedicalEvidenceModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[MedicalEvidence]:
        stmt = (
            select(MedicalEvidenceModel)
            .where(
                MedicalEvidenceModel.body_system_id == body_system_id,
                MedicalEvidenceModel.deleted_at.is_(None),
            )
            .order_by(MedicalEvidenceModel.title)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_all_active(self) -> list[MedicalEvidence]:
        stmt = (
            select(MedicalEvidenceModel)
            .where(
                MedicalEvidenceModel.is_active.is_(True),
                MedicalEvidenceModel.deleted_at.is_(None),
            )
            .order_by(MedicalEvidenceModel.title)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, evidence: MedicalEvidence) -> MedicalEvidence:
        model = MedicalEvidenceModel(
            id=evidence.id,
            title=evidence.title,
            source=evidence.source,
            source_type=evidence.source_type,
            doi=evidence.doi,
            pmid=evidence.pmid,
            url=evidence.url,
            authors=evidence.authors,
            publication_year=evidence.publication_year,
            evidence_level=evidence.evidence_level,
            summary=evidence.summary,
            body_system_id=evidence.body_system_id,
            disease_ids=evidence.disease_ids,
            indicator_ids=evidence.indicator_ids,
            is_active=evidence.is_active,
            version=evidence.version,
            status=evidence.status,
            created_by=evidence.created_by,
            updated_by=evidence.updated_by,
            created_at=evidence.created_at,
            updated_at=evidence.updated_at,
            deleted_at=evidence.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return evidence

    async def update(self, evidence: MedicalEvidence) -> MedicalEvidence:
        stmt = select(MedicalEvidenceModel).where(
            MedicalEvidenceModel.id == evidence.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"MedicalEvidence with id {evidence.id} not found")

        model.title = evidence.title
        model.source = evidence.source
        model.source_type = evidence.source_type
        model.doi = evidence.doi
        model.pmid = evidence.pmid
        model.url = evidence.url
        model.authors = evidence.authors
        model.publication_year = evidence.publication_year
        model.evidence_level = evidence.evidence_level
        model.summary = evidence.summary
        model.body_system_id = evidence.body_system_id
        model.disease_ids = evidence.disease_ids
        model.indicator_ids = evidence.indicator_ids
        model.is_active = evidence.is_active
        model.version = evidence.version
        model.status = evidence.status
        model.updated_by = evidence.updated_by
        model.updated_at = evidence.updated_at
        model.deleted_at = evidence.deleted_at

        await self._session.flush()
        return evidence

    def _to_entity(self, model: MedicalEvidenceModel) -> MedicalEvidence:
        return MedicalEvidence(
            id=model.id,
            title=model.title,
            source=model.source,
            source_type=model.source_type,
            doi=model.doi,
            pmid=model.pmid,
            url=model.url,
            authors=model.authors or [],
            publication_year=model.publication_year,
            evidence_level=model.evidence_level,
            summary=model.summary or "",
            body_system_id=model.body_system_id or "",
            disease_ids=model.disease_ids or [],
            indicator_ids=model.indicator_ids or [],
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
