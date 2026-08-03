from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.repositories.sql_admin_repository import (
    SQLAdminRepository,
)
from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
    SQLKnowledgeGraphRepository,
)


class KnowledgeGraphService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SQLKnowledgeGraphRepository(session)
        self.admin_repo = SQLAdminRepository(session)

    # Entity creation
    async def create_condition(self, user_id: str, data: dict) -> Any:
        cond = await self.repo.create_condition(data)
        await self._audit(user_id, "condition", cond.id, "create", None, data)
        return cond

    async def create_laboratory_test(self, user_id: str, data: dict) -> Any:
        lt = await self.repo.create_laboratory_test(data)
        await self._audit(user_id, "laboratory_test", lt.id, "create", None, data)
        return lt

    # Linking operations
    async def link_question_indicator(
        self, user_id: str, question_id: str, indicator_id: str
    ) -> Any:
        link = await self.repo.link_question_indicator(question_id, indicator_id)
        await self._audit(
            user_id,
            "question_indicator_link",
            link.id,
            "create",
            None,
            {"question_id": question_id, "indicator_id": indicator_id},
        )
        return link

    async def link_question_option_indicator(
        self, user_id: str, question_option_id: str, indicator_id: str
    ) -> Any:
        link = await self.repo.link_question_option_indicator(
            question_option_id, indicator_id
        )
        await self._audit(
            user_id,
            "question_option_indicator_link",
            link.id,
            "create",
            None,
            {"question_option_id": question_option_id, "indicator_id": indicator_id},
        )
        return link

    async def link_indicator_condition(
        self, user_id: str, indicator_id: str, condition_id: str
    ) -> Any:
        link = await self.repo.link_indicator_condition(indicator_id, condition_id)
        await self._audit(
            user_id,
            "indicator_condition_link",
            link.id,
            "create",
            None,
            {"indicator_id": indicator_id, "condition_id": condition_id},
        )
        return link

    async def link_indicator_evidence(
        self, user_id: str, indicator_id: str, evidence_id: str
    ) -> Any:
        link = await self.repo.link_indicator_evidence(indicator_id, evidence_id)
        await self._audit(
            user_id,
            "indicator_evidence_link",
            link.id,
            "create",
            None,
            {"indicator_id": indicator_id, "evidence_id": evidence_id},
        )
        return link

    async def link_indicator_recommendation(
        self, user_id: str, indicator_id: str, recommendation_id: str
    ) -> Any:
        link = await self.repo.link_indicator_recommendation(
            indicator_id, recommendation_id
        )
        await self._audit(
            user_id,
            "indicator_recommendation_link",
            link.id,
            "create",
            None,
            {"indicator_id": indicator_id, "recommendation_id": recommendation_id},
        )
        return link

    async def link_condition_recommendation(
        self, user_id: str, condition_id: str, recommendation_id: str
    ) -> Any:
        link = await self.repo.link_condition_recommendation(
            condition_id, recommendation_id
        )
        await self._audit(
            user_id,
            "condition_recommendation_link",
            link.id,
            "create",
            None,
            {"condition_id": condition_id, "recommendation_id": recommendation_id},
        )
        return link

    async def link_condition_laboratory_test(
        self, user_id: str, condition_id: str, laboratory_test_id: str
    ) -> Any:
        link = await self.repo.link_condition_laboratory_test(
            condition_id, laboratory_test_id
        )
        await self._audit(
            user_id,
            "condition_laboratory_test_link",
            link.id,
            "create",
            None,
            {"condition_id": condition_id, "laboratory_test_id": laboratory_test_id},
        )
        return link

    async def link_body_system_condition(
        self, user_id: str, body_system_id: str, condition_id: str
    ) -> Any:
        link = await self.repo.link_body_system_condition(body_system_id, condition_id)
        await self._audit(
            user_id,
            "body_system_condition_link",
            link.id,
            "create",
            None,
            {"body_system_id": body_system_id, "condition_id": condition_id},
        )
        return link

    # Graph getters
    async def get_indicators_by_question(self, question_id: str):
        return await self.repo.get_indicators_by_question(question_id)

    async def get_conditions_by_indicator(self, indicator_id: str):
        return await self.repo.get_conditions_by_indicator(indicator_id)

    async def get_recommendations_by_condition(self, condition_id: str):
        return await self.repo.get_recommendations_by_condition(condition_id)

    async def get_evidence_by_indicator(self, indicator_id: str):
        return await self.repo.get_evidence_by_indicator(indicator_id)

    async def get_laboratory_tests_by_condition(self, condition_id: str):
        return await self.repo.get_laboratory_tests_by_condition(condition_id)

    async def build_graph_from_question(self, question_id: str) -> dict[str, Any]:
        return await self.repo.build_graph_from_question(question_id)

    # simple search wrapper
    async def search_graph(self, query: str) -> dict[str, Any]:
        # naive search across names and titles for now
        results: dict[str, list] = {
            "questions": [],
            "indicators": [],
            "conditions": [],
            "recommendations": [],
            "evidence": [],
        }
        # delegated to admin repo for some lists/search
        # TODO: better full-text search with indexing
        indicators = await self.admin_repo.list_indicators()
        for ind in indicators:
            if (
                query.lower() in (ind.name or "").lower()
                or query.lower() in (ind.description or "").lower()
            ):
                results["indicators"].append(ind)
        # conditions
        # This repository does not yet provide list_all_conditions; build via repo session
        # For simplicity, return what we have
        return results

    async def _audit(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str | None,
        action: str,
        old_value: dict | None,
        new_value: dict | None,
        reason: str | None = None,
    ):
        payload = {
            "actor_id": user_id,
            "actor_role": "medical_editor",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "changed_at": datetime.utcnow(),
            "old_value": str(old_value) if old_value is not None else None,
            "new_value": str(new_value) if new_value is not None else None,
            "reason": reason,
        }
        # let admin repo persist audit
        await self.admin_repo.create_audit(payload)
