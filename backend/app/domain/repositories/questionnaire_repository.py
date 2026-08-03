from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.questionnaire_template import QuestionnaireTemplate
from app.domain.entities.questionnaire_version import QuestionnaireVersion


class QuestionnaireRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> QuestionnaireTemplate | None:
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> QuestionnaireTemplate | None:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[QuestionnaireTemplate]:
        pass

    @abstractmethod
    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[QuestionnaireTemplate]:
        pass

    @abstractmethod
    async def find_by_target_audience(
        self, audience: str
    ) -> list[QuestionnaireTemplate]:
        pass

    @abstractmethod
    async def create(self, template: QuestionnaireTemplate) -> QuestionnaireTemplate:
        pass

    @abstractmethod
    async def update(self, template: QuestionnaireTemplate) -> QuestionnaireTemplate:
        pass

    @abstractmethod
    async def find_version(
        self, template_id: str, version: int
    ) -> QuestionnaireVersion | None:
        pass

    @abstractmethod
    async def create_version(
        self, version: QuestionnaireVersion
    ) -> QuestionnaireVersion:
        pass
