from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        answers = sess.answers  # loaded with selectin earlier

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

        # Generate trace ID for reproducibility
        trace_id = uuid.uuid4().hex[:16]

        # aggregate indicator scores
        indicator_scores: dict[str, float] = {}
        indicator_sources: dict[str, list] = {}

        for qid, ans_list in answer_map.items():
            # question-level indicators (already batched)
            q_indicators = q_indicators_map.get(qid, [])
            for ind in q_indicators:
                indicator_scores[ind.id] = indicator_scores.get(ind.id, 0.0) + 1.0
                indicator_sources.setdefault(ind.id, []).append(
                    {
                        "question_id": qid,
                        "type": "question",
                        "value": [a.value for a in ans_list],
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

        # persist conditions with normalized confidence scores
        max_possible_condition_score = max(
            (sc for _, sc in activated_conditions), default=0.0
        )
        for cid, sc in activated_conditions:
            contributors = condition_indicator_map.get(cid, [])
            # Normalize confidence to 0-1: actual_score / max_possible_score
            confidence = (
                sc / max_possible_condition_score if max_possible_condition_score > 0 else 0.0
            )
            # Clamp to [0, 1]
            confidence = max(0.0, min(1.0, confidence))
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
            for l in labs:
                await self.dec_repo.add_laboratory_test(
                    result.id, l.id,
                    reason=f"[trace:{trace_id}] Condition {cid} (score={sc}) requires lab test {l.id}",
                )

        # body system aggregation (collect body system ids from indicators -> conditions mapping)
        # For now, produce summary
        summary = {
            "trace_id": trace_id,
            "activated_indicators": len(activated_indicators),
            "activated_conditions": len(activated_conditions),
            "indicator_scores": {k: v for k, v in indicator_scores.items()},
        }
        # update result summary and confidence
        # Normalized confidence: mean of per-condition confidences (each is already 0-1)
        confs = []
        for cid, sc in activated_conditions:
            contributors = condition_indicator_map.get(cid, [])
            c_conf = (
                sc / max_possible_condition_score if max_possible_condition_score > 0 else 0.0
            )
            confs.append(max(0.0, min(1.0, c_conf)))
        overall_confidence = sum(confs) / len(confs) if confs else 0.0
        await self.session.execute(
            AssessmentSessionModel.__table__.update()
            .where(AssessmentSessionModel.id == session_id)
            .values(status="processed")
        )
        await self.session.commit()

        # update result
        await self.session.execute(
            AssessmentResultModel.__table__.update()
            .where(AssessmentResultModel.id == result.id)
            .values(summary=str(summary), confidence_score=float(overall_confidence))
        )
        await self.session.commit()

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
            from app.core.security.rbac import Role, has_role
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
