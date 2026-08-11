"""Deterministic question-discovery service (Phase 3).

Once candidate indicators are validated against the knowledge graph, this
service finds the EXISTING questions and question groups linked to those
indicators. The AI never invents questions; the knowledge graph is authoritative.

Flow:
    validated candidate indicator IDs
        → batched query QuestionIndicatorLinkModel (active)
        → batched query QuestionModel (status=active, deleted_at IS NULL)
        → group by QuestionGroupModel (is_active=True, deleted_at IS NULL)
        → deterministic ranking (group display_order, then question order_index)
        → dedup (one question per id; one group per id)
        → respect active links only

No N+1 queries: indicator→questions and question→group are batched. The
deterministic branching engine still owns final question order at runtime;
this service only DISCOVERS candidate questions/groups for the intake UX.

Template scope: when an assessment template scope is supplied
(``template_question_ids``), only questions within that scope are returned as
candidate questions; groups are still surfaced as recommendations. This keeps
AI intake from pulling in questions outside the chosen assessment.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.intake_dtos import (
    CandidateQuestionDTO,
    CandidateQuestionGroupDTO,
)
from app.infrastructure.persistence.models.links import QuestionIndicatorLinkModel
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.question_group import QuestionGroupModel

#: Soft caps to keep the intake UI bounded.
MAX_QUESTIONS = 20
MAX_GROUPS = 10


@dataclass
class QuestionDiscoveryResult:
    question_groups: list[CandidateQuestionGroupDTO] = field(default_factory=list)
    questions: list[CandidateQuestionDTO] = field(default_factory=list)
    #: indicator IDs that had no active question link (for observability).
    indicators_without_questions: list[str] = field(default_factory=list)


class AIIntakeQuestionService:
    """Deterministic question-group/question discovery from validated candidates."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def discover(
        self,
        candidate_indicator_ids: list[str],
        *,
        template_question_ids: set[str] | None = None,
    ) -> QuestionDiscoveryResult:
        if not candidate_indicator_ids:
            return QuestionDiscoveryResult()

        # 1. indicator → question ids via active links (batched).
        qid_by_ind: dict[str, list[str]] = {}
        rows = await self.session.execute(
            select(
                QuestionIndicatorLinkModel.indicator_id,
                QuestionIndicatorLinkModel.question_id,
            ).where(
                QuestionIndicatorLinkModel.indicator_id.in_(candidate_indicator_ids),
                QuestionIndicatorLinkModel.active.is_(True),
            )
        )
        for ind_id, qid in rows.all():
            qid_by_ind.setdefault(ind_id, []).append(qid)

        all_qids = sorted({qid for qids in qid_by_ind.values() for qid in qids})
        for ind_id in candidate_indicator_ids:
            if ind_id not in qid_by_ind:
                self._record_missing(ind_id)

        if not all_qids:
            return QuestionDiscoveryResult(
                indicators_without_questions=list(candidate_indicator_ids)
            )

        # 2. questions (active + not deleted), batched.
        qrows = await self.session.execute(
            select(QuestionModel).where(
                QuestionModel.id.in_(all_qids),
                QuestionModel.status == "active",
                QuestionModel.deleted_at.is_(None),
            )
        )
        questions_by_id: dict[str, QuestionModel] = {
            q.id: q for q in qrows.scalars().all()
        }

        # 3. question groups (active + not deleted), batched.
        group_ids = sorted({q.question_group_id for q in questions_by_id.values()})
        groups_by_id: dict[str, QuestionGroupModel] = {}
        if group_ids:
            grows = await self.session.execute(
                select(QuestionGroupModel).where(
                    QuestionGroupModel.id.in_(group_ids),
                    QuestionGroupModel.is_active.is_(True),
                    QuestionGroupModel.deleted_at.is_(None),
                )
            )
            groups_by_id = {g.id: g for g in grows.scalars().all()}

        # Build reverse map: question_id -> linked indicator ids (active).
        ind_by_qid: dict[str, list[str]] = {}
        for ind_id, qids in qid_by_ind.items():
            for qid in qids:
                if qid in questions_by_id:
                    ind_by_qid.setdefault(qid, []).append(ind_id)

        # 4. Candidate questions (template scope respected).
        scope = template_question_ids
        questions_out: list[CandidateQuestionDTO] = []
        seen_q: set[str] = set()
        # Deterministic order: group display_order, then question order_index.
        ordered_qids = sorted(
            questions_by_id.values(),
            key=lambda q: (
                groups_by_id[q.question_group_id].display_order
                if q.question_group_id in groups_by_id
                else 10**9,
                q.order_index,
                q.id,
            ),
        )
        for q in ordered_qids:
            if q.id in seen_q:
                continue
            if q.question_group_id not in groups_by_id:
                # group inactive/deleted → exclude question.
                continue
            if scope is not None and q.id not in scope:
                continue
            seen_q.add(q.id)
            g = groups_by_id[q.question_group_id]
            questions_out.append(
                CandidateQuestionDTO(
                    question_id=q.id,
                    question_code=q.code,
                    text=q.text,
                    question_group_id=g.id,
                    question_group_name=g.name,
                    body_system_id=q.body_system_id,
                    linked_indicator_ids=sorted(set(ind_by_qid.get(q.id, []))),
                    source="cms",
                )
            )
            if len(questions_out) >= MAX_QUESTIONS:
                break

        # 5. Candidate groups (aggregated, deduped).
        groups_out: list[CandidateQuestionGroupDTO] = []
        seen_g: set[str] = set()
        # Order groups by display_order then name.
        for g in sorted(
            groups_by_id.values(),
            key=lambda gr: (gr.display_order, gr.name, gr.id),
        ):
            if g.id in seen_g:
                continue
            linked: set[str] = set()
            count = 0
            for q in questions_by_id.values():
                if q.question_group_id == g.id:
                    linked.update(ind_by_qid.get(q.id, []))
                    count += 1
            if not linked:
                continue
            seen_g.add(g.id)
            groups_out.append(
                CandidateQuestionGroupDTO(
                    question_group_id=g.id,
                    code=g.code,
                    name=g.name,
                    body_system_id=g.body_system_id,
                    linked_indicator_ids=sorted(linked),
                    question_count=count,
                    source="cms",
                )
            )
            if len(groups_out) >= MAX_GROUPS:
                break

        missing = [ind_id for ind_id in candidate_indicator_ids if ind_id not in qid_by_ind]
        return QuestionDiscoveryResult(
            question_groups=groups_out,
            questions=questions_out,
            indicators_without_questions=missing,
        )

    def _record_missing(self, _ind_id: str) -> None:
        # Stateless in Phase 3; observability uses the returned trace.
        return None
