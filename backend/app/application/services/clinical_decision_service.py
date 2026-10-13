from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.answer_values import is_affirmative
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.decision import AssessmentResultModel
from app.infrastructure.persistence.models.question_option import (
    QuestionOptionModel,
)
from app.infrastructure.persistence.repositories.sql_decision_repository import (
    SQLDecisionRepository,
)
from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
    SQLKnowledgeGraphRepository,
)
from app.infrastructure.persistence.repositories.sql_profile_repository import (
    SQLProfileRepository,
)


class ClinicalDecisionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.kg_repo = SQLKnowledgeGraphRepository(session)
        self.dec_repo = SQLDecisionRepository(session)
        self.profile_repo = SQLProfileRepository(session)

    async def process_assessment(
        self, session_id: str, user_id: str | None = None
    ) -> dict[str, Any]:
        # load session and answers
        sess = await self.session.get(AssessmentSessionModel, session_id)
        if sess is None:
            raise ValueError("Assessment session not found")
        if user_id is not None and sess.user_id != user_id:
            raise ValueError("Assessment session not found")
        # Skipped answers carry no clinical finding and must never activate a
        # linked indicator.
        answers = [a for a in sess.answers if not a.is_skipped]

        # build answer map
        answer_map: dict[str, list] = {}
        for a in answers:
            answer_map.setdefault(a.question_id, []).append(a)

        # Batch-load indicators by question
        all_qids = list(answer_map.keys())
        q_indicators_map = await self.kg_repo.get_indicators_by_question_batch(all_qids)

        # Batch-load all option IDs
        all_option_ids = list({a.option_id for a in answers if a.option_id})
        opt_indicators_map = await self.kg_repo.get_indicators_by_option_batch(all_option_ids)
        opt_models = {}
        if all_option_ids:
            opt_rows = await self.session.execute(
                select(QuestionOptionModel).where(QuestionOptionModel.id.in_(all_option_ids))
            )
            opt_models = {o.id: o for o in opt_rows.scalars().all()}

        indicator_confidences = {
            indicator.id: indicator.confidence
            for indicators in (*q_indicators_map.values(), *opt_indicators_map.values())
            for indicator in indicators
        }

        # Generate trace ID for reproducibility
        trace_id = uuid.uuid4().hex[:16]

        # aggregate indicator scores
        indicator_scores: dict[str, float] = {}
        indicator_sources: dict[str, list] = {}

        for qid, ans_list in answer_map.items():
            # Question-level indicators activate ONLY on an affirmative answer
            # ("yes", True, or a positive numeric score/value). A negative or
            # empty answer ("no", False, 0, "") must not activate them.
            affirmative_answers = [
                a
                for a in ans_list
                if is_affirmative(
                    score_value=a.score_value,
                    numeric_value=a.numeric_value,
                    value=a.value,
                    response_value=a.response_value,
                )
            ]
            if affirmative_answers:
                q_indicators = q_indicators_map.get(qid, [])
                for ind in q_indicators:
                    indicator_scores[ind.id] = (
                        indicator_scores.get(ind.id, 0.0) + 1.0
                    )
                    indicator_sources.setdefault(ind.id, []).append(
                        {
                            "question_id": qid,
                            "type": "question",
                            "value": [a.value for a in affirmative_answers],
                        }
                    )

            # option-level
            for a in ans_list:
                if a.option_id:
                    opt_inds = opt_indicators_map.get(a.option_id, [])
                    opt = opt_models.get(a.option_id)
                    w = opt.score_value if opt and opt.score_value is not None else 1.0
                    for ind in opt_inds:
                        indicator_scores[ind.id] = indicator_scores.get(
                            ind.id, 0.0
                        ) + float(w)
                        indicator_sources.setdefault(ind.id, []).append(
                            {
                                "question_id": qid,
                                "option_id": a.option_id,
                                "type": "option",
                                "weight": w,
                                "value": a.value,
                            }
                        )

        # determine activated indicators (threshold configurable - using 1.0 default)
        threshold = 1.0
        activated_indicators = [
            (ind_id, score)
            for ind_id, score in indicator_scores.items()
            if score >= threshold
        ]

        # create result record
        result = await self.dec_repo.create_result(
            {
                "session_id": session_id,
                "user_id": sess.user_id,
                "summary": None,
                "confidence_score": None,
                "created_at": None,
            }
        )
        await self.dec_repo.clear_result_details(result.id)

        # Batch-load evidence for all activated indicators
        activated_ind_ids = [iid for iid, _ in activated_indicators]
        evidence_map = await self.kg_repo.get_evidence_by_indicator_batch(activated_ind_ids)

        # persist activated indicators with full traceable explanations
        for ind_id, score in activated_indicators:
            evid = evidence_map.get(ind_id, [])
            evidence_count = len(evid)
            await self.dec_repo.add_activated_indicator(
                result.id, ind_id, score, evidence_count, None
            )
            sources = indicator_sources.get(ind_id, [])
            text = (
                f"[trace:{trace_id}] Indicator {ind_id}: score={score}, "
                f"evidence_count={evidence_count}, "
                f"sources={sources}"
            )
            await self.dec_repo.add_explanation(result.id, "indicator", ind_id, text)

        # Batch-load conditions for all activated indicators
        conditions_map = await self.kg_repo.get_conditions_by_indicator_batch(activated_ind_ids)

        # conditions aggregation
        condition_scores: dict[str, float] = {}
        condition_indicator_map: dict[str, list] = {}
        for ind_id, score in activated_indicators:
            conds = conditions_map.get(ind_id, [])
            for c in conds:
                condition_scores[c.id] = condition_scores.get(c.id, 0.0) + score
                condition_indicator_map.setdefault(c.id, []).append(ind_id)

        activated_conditions = [
            (cid, sc) for cid, sc in condition_scores.items() if sc > 0
        ]

        # Batch-load recommendations and lab tests for all activated conditions
        activated_condition_ids = [cid for cid, _ in activated_conditions]
        recs_map = await self.kg_repo.get_recommendations_by_condition_batch(activated_condition_ids)
        labs_map = await self.kg_repo.get_laboratory_tests_by_condition_batch(activated_condition_ids)

        # Condition confidence summarizes the configured confidence of its
        # contributing indicators; it is independent of other conditions.
        condition_confidences: list[float] = []
        for cid, sc in activated_conditions:
            contributors = list(dict.fromkeys(condition_indicator_map.get(cid, [])))
            confidence_weights = [
                (indicator_scores[ind_id], indicator_confidences[ind_id])
                for ind_id in contributors
                if indicator_scores.get(ind_id, 0.0) > 0
                and ind_id in indicator_confidences
            ]
            total_weight = sum(weight for weight, _ in confidence_weights)
            confidence = (
                sum(
                    weight * max(0.0, min(1.0, indicator_confidence))
                    for weight, indicator_confidence in confidence_weights
                )
                / total_weight
                if total_weight > 0
                else 0.0
            )
            condition_confidences.append(confidence)
            await self.dec_repo.add_activated_condition(
                result.id, cid, sc, confidence, None
            )
            text = (
                f"[trace:{trace_id}] Condition {cid}: score={sc}, "
                f"contributing_indicators={contributors}, confidence={confidence}"
            )
            await self.dec_repo.add_explanation(result.id, "condition", cid, text)

            # recommendations with explainable source
            recs = recs_map.get(cid, [])
            for r in recs:
                await self.dec_repo.add_recommendation(
                    result.id, r.id,
                    source=f"condition:{cid}",
                    notes=f"[trace:{trace_id}] Score {sc} triggered recommendation {r.id}",
                )

            # laboratory tests
            labs = labs_map.get(cid, [])
            for lab in labs:
                await self.dec_repo.add_laboratory_test(
                    result.id, lab.id,
                    reason=f"[trace:{trace_id}] Condition {cid} (score={sc}) requires lab test {lab.id}",
                )

        # body system aggregation (collect body system ids from indicators -> conditions mapping)
        # For now, produce summary
        summary = {
            "trace_id": trace_id,
            "activated_indicators": len(activated_indicators),
            "activated_conditions": len(activated_conditions),
            "indicator_scores": {k: v for k, v in indicator_scores.items()},
        }
        # The overall value averages the independent condition confidences.
        overall_confidence = (
            sum(condition_confidences) / len(condition_confidences)
            if condition_confidences
            else 0.0
        )
        await self.session.execute(
            AssessmentSessionModel.__table__.update()
            .where(AssessmentSessionModel.id == session_id)
            .values(status="processed")
        )

        # update result
        await self.session.execute(
            AssessmentResultModel.__table__.update()
            .where(AssessmentResultModel.id == result.id)
            .values(summary=str(summary), confidence_score=float(overall_confidence))
        )
        await self.session.refresh(
            result,
            attribute_names=[
                "activated_indicators",
                "activated_conditions",
                "generated_recommendations",
                "generated_laboratory_tests",
                "generated_screenings",
                "explanations",
            ],
        )

        return {
            "result_id": result.id,
            "summary": summary,
            "confidence_score": overall_confidence,
        }

    # getters
    async def get_result_by_session(self, session_id: str, user_id: str | None = None):
        result = await self.dec_repo.get_result_by_session(session_id)
        if result and user_id and result.user_id != user_id:
            # Check if user has elevated permissions (doctors can view patient results)
            # For now, we only allow access if the user owns the result
            # In a real application, you'd check for elevated roles here
            return None
        return result

    async def get_result(self, result_id: str, user_id: str | None = None):
        result = await self.dec_repo.get_result(result_id)
        if result and user_id and result.user_id != user_id:
            # Check if user has elevated permissions
            return None
        return result
