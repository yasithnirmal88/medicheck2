from __future__ import annotations

from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.evidence_reference import (
    EvidenceReferenceModel,
)
from app.infrastructure.persistence.models.laboratory_test import LaboratoryTestModel
from app.infrastructure.persistence.models.links import (
    BodySystemConditionLinkModel,
    ConditionLaboratoryTestLinkModel,
    ConditionRecommendationLinkModel,
    IndicatorConditionLinkModel,
    IndicatorEvidenceLinkModel,
    IndicatorRecommendationLinkModel,
    QuestionIndicatorLinkModel,
    QuestionOptionIndicatorLinkModel,
)
from app.infrastructure.persistence.models.possible_condition import (
    PossibleConditionModel,
)
from app.infrastructure.persistence.models.recommendation import RecommendationModel


class SQLKnowledgeGraphRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # Create entities
    async def create_condition(self, data: dict) -> PossibleConditionModel:
        stmt = insert(PossibleConditionModel).values(**data)
        await self.session.execute(stmt)
        q = select(PossibleConditionModel).where(
            PossibleConditionModel.code == data.get("code")
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def create_laboratory_test(self, data: dict) -> LaboratoryTestModel:
        stmt = insert(LaboratoryTestModel).values(**data)
        await self.session.execute(stmt)
        q = select(LaboratoryTestModel).where(
            LaboratoryTestModel.code == data.get("code")
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    # Link creation with duplicate prevention (reactivate if soft-deleted)
    async def link_question_indicator(
        self, question_id: str, indicator_id: str
    ) -> QuestionIndicatorLinkModel:
        q = select(QuestionIndicatorLinkModel).where(
            QuestionIndicatorLinkModel.question_id == question_id,
            QuestionIndicatorLinkModel.indicator_id == indicator_id,
        )
        r = await self.session.execute(q)
        existing = r.scalars().first()
        if existing:
            if not existing.active:
                stmt = (
                    update(QuestionIndicatorLinkModel)
                    .where(QuestionIndicatorLinkModel.id == existing.id)
                    .values(active=True)
                )
                await self.session.execute(stmt)
            return existing

        stmt = insert(QuestionIndicatorLinkModel).values(
            question_id=question_id, indicator_id=indicator_id
        )
        await self.session.execute(stmt)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def link_question_option_indicator(
        self, question_option_id: str, indicator_id: str
    ) -> QuestionOptionIndicatorLinkModel:
        q = select(QuestionOptionIndicatorLinkModel).where(
            QuestionOptionIndicatorLinkModel.question_option_id == question_option_id,
            QuestionOptionIndicatorLinkModel.indicator_id == indicator_id,
        )
        r = await self.session.execute(q)
        existing = r.scalars().first()
        if existing:
            if not existing.active:
                stmt = (
                    update(QuestionOptionIndicatorLinkModel)
                    .where(QuestionOptionIndicatorLinkModel.id == existing.id)
                    .values(active=True)
                )
                await self.session.execute(stmt)
            return existing

        stmt = insert(QuestionOptionIndicatorLinkModel).values(
            question_option_id=question_option_id, indicator_id=indicator_id
        )
        await self.session.execute(stmt)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def link_indicator_condition(
        self, indicator_id: str, condition_id: str
    ) -> IndicatorConditionLinkModel:
        q = select(IndicatorConditionLinkModel).where(
            IndicatorConditionLinkModel.indicator_id == indicator_id,
            IndicatorConditionLinkModel.condition_id == condition_id,
        )
        r = await self.session.execute(q)
        existing = r.scalars().first()
        if existing:
            if not existing.active:
                stmt = (
                    update(IndicatorConditionLinkModel)
                    .where(IndicatorConditionLinkModel.id == existing.id)
                    .values(active=True)
                )
                await self.session.execute(stmt)
            return existing
        stmt = insert(IndicatorConditionLinkModel).values(
            indicator_id=indicator_id, condition_id=condition_id
        )
        await self.session.execute(stmt)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def link_indicator_evidence(
        self, indicator_id: str, evidence_id: str
    ) -> IndicatorEvidenceLinkModel:
        q = select(IndicatorEvidenceLinkModel).where(
            IndicatorEvidenceLinkModel.indicator_id == indicator_id,
            IndicatorEvidenceLinkModel.evidence_id == evidence_id,
        )
        r = await self.session.execute(q)
        existing = r.scalars().first()
        if existing:
            if not existing.active:
                stmt = (
                    update(IndicatorEvidenceLinkModel)
                    .where(IndicatorEvidenceLinkModel.id == existing.id)
                    .values(active=True)
                )
                await self.session.execute(stmt)
            return existing
        stmt = insert(IndicatorEvidenceLinkModel).values(
            indicator_id=indicator_id, evidence_id=evidence_id
        )
        await self.session.execute(stmt)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def link_indicator_recommendation(
        self, indicator_id: str, recommendation_id: str
    ) -> IndicatorRecommendationLinkModel:
        q = select(IndicatorRecommendationLinkModel).where(
            IndicatorRecommendationLinkModel.indicator_id == indicator_id,
            IndicatorRecommendationLinkModel.recommendation_id == recommendation_id,
        )
        r = await self.session.execute(q)
        existing = r.scalars().first()
        if existing:
            if not existing.active:
                stmt = (
                    update(IndicatorRecommendationLinkModel)
                    .where(IndicatorRecommendationLinkModel.id == existing.id)
                    .values(active=True)
                )
                await self.session.execute(stmt)
            return existing
        stmt = insert(IndicatorRecommendationLinkModel).values(
            indicator_id=indicator_id, recommendation_id=recommendation_id
        )
        await self.session.execute(stmt)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def link_condition_recommendation(
        self, condition_id: str, recommendation_id: str
    ) -> ConditionRecommendationLinkModel:
        q = select(ConditionRecommendationLinkModel).where(
            ConditionRecommendationLinkModel.condition_id == condition_id,
            ConditionRecommendationLinkModel.recommendation_id == recommendation_id,
        )
        r = await self.session.execute(q)
        existing = r.scalars().first()
        if existing:
            if not existing.active:
                stmt = (
                    update(ConditionRecommendationLinkModel)
                    .where(ConditionRecommendationLinkModel.id == existing.id)
                    .values(active=True)
                )
                await self.session.execute(stmt)
            return existing
        stmt = insert(ConditionRecommendationLinkModel).values(
            condition_id=condition_id, recommendation_id=recommendation_id
        )
        await self.session.execute(stmt)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def link_condition_laboratory_test(
        self, condition_id: str, laboratory_test_id: str
    ) -> ConditionLaboratoryTestLinkModel:
        q = select(ConditionLaboratoryTestLinkModel).where(
            ConditionLaboratoryTestLinkModel.condition_id == condition_id,
            ConditionLaboratoryTestLinkModel.laboratory_test_id == laboratory_test_id,
        )
        r = await self.session.execute(q)
        existing = r.scalars().first()
        if existing:
            if not existing.active:
                stmt = (
                    update(ConditionLaboratoryTestLinkModel)
                    .where(ConditionLaboratoryTestLinkModel.id == existing.id)
                    .values(active=True)
                )
                await self.session.execute(stmt)
            return existing
        stmt = insert(ConditionLaboratoryTestLinkModel).values(
            condition_id=condition_id, laboratory_test_id=laboratory_test_id
        )
        await self.session.execute(stmt)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def link_body_system_condition(
        self, body_system_id: str, condition_id: str
    ) -> BodySystemConditionLinkModel:
        q = select(BodySystemConditionLinkModel).where(
            BodySystemConditionLinkModel.body_system_id == body_system_id,
            BodySystemConditionLinkModel.condition_id == condition_id,
        )
        r = await self.session.execute(q)
        existing = r.scalars().first()
        if existing:
            if not existing.active:
                stmt = (
                    update(BodySystemConditionLinkModel)
                    .where(BodySystemConditionLinkModel.id == existing.id)
                    .values(active=True)
                )
                await self.session.execute(stmt)
            return existing
        stmt = insert(BodySystemConditionLinkModel).values(
            body_system_id=body_system_id, condition_id=condition_id
        )
        await self.session.execute(stmt)
        r = await self.session.execute(q)
        return r.scalars().first()

    # Graph retrieval helpers
    async def get_indicators_by_question(
        self, question_id: str
    ) -> list[ClinicalIndicatorModel]:
        q = (
            select(ClinicalIndicatorModel)
            .join(
                QuestionIndicatorLinkModel,
                QuestionIndicatorLinkModel.indicator_id == ClinicalIndicatorModel.id,
            )
            .where(QuestionIndicatorLinkModel.question_id == question_id)
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def get_indicators_by_question_option(
        self, question_option_id: str
    ) -> list[ClinicalIndicatorModel]:
        q = (
            select(ClinicalIndicatorModel)
            .join(
                QuestionOptionIndicatorLinkModel,
                QuestionOptionIndicatorLinkModel.indicator_id
                == ClinicalIndicatorModel.id,
            )
            .where(
                QuestionOptionIndicatorLinkModel.question_option_id
                == question_option_id
            )
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def get_indicators_by_question_batch(
        self, question_ids: list[str]
    ) -> dict[str, list[ClinicalIndicatorModel]]:
        if not question_ids:
            return {}
        q = (
            select(ClinicalIndicatorModel, QuestionIndicatorLinkModel.question_id)
            .join(
                QuestionIndicatorLinkModel,
                QuestionIndicatorLinkModel.indicator_id == ClinicalIndicatorModel.id,
            )
            .where(QuestionIndicatorLinkModel.question_id.in_(question_ids))
        )
        r = await self.session.execute(q)
        result: dict[str, list[ClinicalIndicatorModel]] = {}
        for ind, qid in r.all():
            result.setdefault(qid, []).append(ind)
        return result

    async def get_indicators_by_option_batch(
        self, option_ids: list[str]
    ) -> dict[str, list[ClinicalIndicatorModel]]:
        if not option_ids:
            return {}
        q = (
            select(ClinicalIndicatorModel, QuestionOptionIndicatorLinkModel.question_option_id)
            .join(
                QuestionOptionIndicatorLinkModel,
                QuestionOptionIndicatorLinkModel.indicator_id == ClinicalIndicatorModel.id,
            )
            .where(QuestionOptionIndicatorLinkModel.question_option_id.in_(option_ids))
        )
        r = await self.session.execute(q)
        result: dict[str, list[ClinicalIndicatorModel]] = {}
        for ind, opt_id in r.all():
            result.setdefault(opt_id, []).append(ind)
        return result

    async def get_conditions_by_indicator_batch(
        self, indicator_ids: list[str]
    ) -> dict[str, list[PossibleConditionModel]]:
        if not indicator_ids:
            return {}
        q = (
            select(PossibleConditionModel, IndicatorConditionLinkModel.indicator_id)
            .join(
                IndicatorConditionLinkModel,
                IndicatorConditionLinkModel.condition_id == PossibleConditionModel.id,
            )
            .where(IndicatorConditionLinkModel.indicator_id.in_(indicator_ids))
        )
        r = await self.session.execute(q)
        result: dict[str, list[PossibleConditionModel]] = {}
        for cond, ind_id in r.all():
            result.setdefault(ind_id, []).append(cond)
        return result

    async def get_recommendations_by_condition_batch(
        self, condition_ids: list[str]
    ) -> dict[str, list[RecommendationModel]]:
        if not condition_ids:
            return {}
        q = (
            select(RecommendationModel, ConditionRecommendationLinkModel.condition_id)
            .join(
                ConditionRecommendationLinkModel,
                ConditionRecommendationLinkModel.recommendation_id
                == RecommendationModel.id,
            )
            .where(ConditionRecommendationLinkModel.condition_id.in_(condition_ids))
        )
        r = await self.session.execute(q)
        result: dict[str, list[RecommendationModel]] = {}
        for rec, cid in r.all():
            result.setdefault(cid, []).append(rec)
        return result

    async def get_evidence_by_indicator_batch(
        self, indicator_ids: list[str]
    ) -> dict[str, list[EvidenceReferenceModel]]:
        if not indicator_ids:
            return {}
        q = (
            select(EvidenceReferenceModel, IndicatorEvidenceLinkModel.indicator_id)
            .join(
                IndicatorEvidenceLinkModel,
                IndicatorEvidenceLinkModel.evidence_id == EvidenceReferenceModel.id,
            )
            .where(IndicatorEvidenceLinkModel.indicator_id.in_(indicator_ids))
        )
        r = await self.session.execute(q)
        result: dict[str, list[EvidenceReferenceModel]] = {}
        for ev, ind_id in r.all():
            result.setdefault(ind_id, []).append(ev)
        return result

    async def get_laboratory_tests_by_condition_batch(
        self, condition_ids: list[str]
    ) -> dict[str, list[LaboratoryTestModel]]:
        if not condition_ids:
            return {}
        q = (
            select(LaboratoryTestModel, ConditionLaboratoryTestLinkModel.condition_id)
            .join(
                ConditionLaboratoryTestLinkModel,
                ConditionLaboratoryTestLinkModel.laboratory_test_id
                == LaboratoryTestModel.id,
            )
            .where(ConditionLaboratoryTestLinkModel.condition_id.in_(condition_ids))
        )
        r = await self.session.execute(q)
        result: dict[str, list[LaboratoryTestModel]] = {}
        for lab, cid in r.all():
            result.setdefault(cid, []).append(lab)
        return result

    async def get_conditions_by_indicator(
        self, indicator_id: str
    ) -> list[PossibleConditionModel]:
        q = (
            select(PossibleConditionModel)
            .join(
                IndicatorConditionLinkModel,
                IndicatorConditionLinkModel.condition_id == PossibleConditionModel.id,
            )
            .where(IndicatorConditionLinkModel.indicator_id == indicator_id)
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def get_recommendations_by_condition(
        self, condition_id: str
    ) -> list[RecommendationModel]:
        q = (
            select(RecommendationModel)
            .join(
                ConditionRecommendationLinkModel,
                ConditionRecommendationLinkModel.recommendation_id
                == RecommendationModel.id,
            )
            .where(ConditionRecommendationLinkModel.condition_id == condition_id)
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def get_evidence_by_indicator(
        self, indicator_id: str
    ) -> list[EvidenceReferenceModel]:
        q = (
            select(EvidenceReferenceModel)
            .join(
                IndicatorEvidenceLinkModel,
                IndicatorEvidenceLinkModel.evidence_id == EvidenceReferenceModel.id,
            )
            .where(IndicatorEvidenceLinkModel.indicator_id == indicator_id)
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def get_laboratory_tests_by_condition(
        self, condition_id: str
    ) -> list[LaboratoryTestModel]:
        q = (
            select(LaboratoryTestModel)
            .join(
                ConditionLaboratoryTestLinkModel,
                ConditionLaboratoryTestLinkModel.laboratory_test_id
                == LaboratoryTestModel.id,
            )
            .where(ConditionLaboratoryTestLinkModel.condition_id == condition_id)
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    # Graph search/traverse returning structured graph starting from question -> indicators -> conditions -> recommendations -> evidence
    async def build_graph_from_question(self, question_id: str) -> dict[str, Any]:
        indicators = await self.get_indicators_by_question(question_id)
        if not indicators:
            return {"question_id": question_id, "indicators": []}

        ind_ids = [ind.id for ind in indicators]
        conditions_map = await self.get_conditions_by_indicator_batch(ind_ids)
        evidence_map = await self.get_evidence_by_indicator_batch(ind_ids)

        all_cond_ids = [
            c.id for conds in conditions_map.values() for c in conds
        ]
        recs_map = await self.get_recommendations_by_condition_batch(all_cond_ids)

        graph = {"question_id": question_id, "indicators": []}
        for ind in indicators:
            conds = conditions_map.get(ind.id, [])
            evid = evidence_map.get(ind.id, [])
            recs = []
            for c in conds:
                recs_for_c = recs_map.get(c.id, [])
                recs.append({"condition": c, "recommendations": recs_for_c})
            graph["indicators"].append(
                {
                    "indicator": ind,
                    "conditions": conds,
                    "evidence": evid,
                    "condition_recommendations": recs,
                }
            )
        return graph
