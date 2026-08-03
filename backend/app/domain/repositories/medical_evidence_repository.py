from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.medical_evidence import MedicalEvidence


class MedicalEvidenceRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> MedicalEvidence | None:
        pass

    @abstractmethod
    async def find_by_doi(self, doi: str) -> MedicalEvidence | None:
        pass

    @abstractmethod
    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[MedicalEvidence]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[MedicalEvidence]:
        pass

    @abstractmethod
    async def create(self, evidence: MedicalEvidence) -> MedicalEvidence:
        pass

    @abstractmethod
    async def update(self, evidence: MedicalEvidence) -> MedicalEvidence:
        pass
