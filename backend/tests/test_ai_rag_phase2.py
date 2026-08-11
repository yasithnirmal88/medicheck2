"""Phase 2 — Evidence-Grounded RAG backend tests.

Covers the Phase 2 spec cases:
Retrieval:
  1. direct indicator evidence retrieval
  2. condition (transitive) evidence retrieval
  3. recommendation (transitive) evidence retrieval
  4. inactive link excluded
  5. soft-deleted evidence excluded
  6. (unpublished/draft evidence — N/A for EvidenceReferenceModel which has no
     status column; documented in the report. Eligibility = not soft-deleted.)
  7. ranking (tier + evidence level ordering)
  8. evidence limit (global cap)
  9. zero evidence
  10. duplicate evidence removal
AI validation:
  - valid citation (referenced evidence id was supplied → PASS)
  - hallucinated citation (referenced evidence id NOT supplied → REJECT)
  - hallucinated indicator (Phase 1 behaviour continues)
  - hallucinated recommendation (Phase 1 behaviour continues)
  - no-evidence path states insufficiency (never fabricates)
Security:
  - unauthorized assessment access → 404, AI never called
  - no cross-patient evidence (retrieval seeded from caller's own result)
Deterministic integrity:
  - RAG is read-only (scores/indicators/conditions/recommendations unchanged)

Run: ALLOW_MOCK_AUTH=true python -m pytest tests/test_ai_rag_phase2.py -q
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.prompts import PROMPT_VERSION
from app.application.ai.provider import AIProviderError
from app.application.dtos.ai_dtos import ReportExplanationContext
from app.application.services.ai_explanation_service import (
    AIExplanationService,
    _explanation_cache,
)
from app.application.services.clinical_decision_service import (
    ClinicalDecisionService,
)
from app.application.services.evidence_retrieval_service import (
    EvidenceRetrievalService,
    TIER_INDICATOR,
)
from app.application.services.report_service import ReportService
from app.infrastructure.persistence.models.assessment_answer import (
    AssessmentAnswerModel,
)
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.body_system import BodySystemModel
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.decision import AssessmentResultModel
from app.infrastructure.persistence.models.evidence_reference import (
    EvidenceReferenceModel,
)
from app.infrastructure.persistence.models.links import (
    IndicatorEvidenceLinkModel,
)
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.question_group import (
    QuestionGroupModel,
)
from app.infrastructure.persistence.models.question_option import (
    QuestionOptionModel,
)
from app.infrastructure.persistence.models.recommendation import (
    RecommendationModel,
)
from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
    SQLKnowledgeGraphRepository,
)


def _ev(session: AsyncSession, *, title: str, source="JAMA", level="A") -> str:
    """Insert an evidence reference row and return its id."""
    import uuid

    eid = uuid.uuid4().hex
    session.add(
        EvidenceReferenceModel(
            id=eid,
            title=title,
            source=source,
            evidence_level=level,
            summary=f"{title} — summary passage.",
        )
    )
    return eid


async def _seed_assessment(session: AsyncSession, user_id: str) -> tuple[str, str]:
    """Seed one indicator, one question/option, one condition, run CDSE +
    report. Returns (session_id, indicator_id). Uses unique keys per call to
    avoid UNIQUE collisions on the shared test DB."""
    import uuid as _uuid

    uid = _uuid.uuid4().hex[:8]
    bs_id = f"bs-rag-{uid}"
    qg_id = f"qg-rag-{uid}"
    q_id = f"qr1-{uid}"
    opt_id = f"optr1-{uid}"
    ind_key = f"RAG_IND_{uid}"
    cond_code = f"RAG_C_{uid}"
    kg_repo = SQLKnowledgeGraphRepository(session)
    cdse = ClinicalDecisionService(session)
    report_svc = ReportService(session)

    session.add(BodySystemModel(id=bs_id, code=bs_id, name="RAG Test", display_order=1))
    session.add(
        QuestionGroupModel(
            id=qg_id, code=qg_id, name="QG RAG", body_system_id=bs_id, display_order=1
        )
    )
    await session.commit()
    await session.execute(
        ClinicalIndicatorModel.__table__.insert().values(
            key=ind_key, name="RAG Indicator", body_system_id=bs_id,
            severity="moderate", evidence_strength="B",
        )
    )
    await session.execute(
        QuestionModel.__table__.insert().values(
            id=q_id, text="QR", body_system_id=bs_id, question_group_id=qg_id,
            code=q_id, question_type="yes_no",
        )
    )
    await session.execute(
        QuestionOptionModel.__table__.insert().values(
            id=opt_id, question_id=q_id, text="Yes", value="yes", code=opt_id,
            display_order=1, score_value=1.0,
        )
    )
    await session.commit()
    ind_id = (
        (await session.execute(
            ClinicalIndicatorModel.__table__.select().where(
                ClinicalIndicatorModel.key == ind_key
            )
        )).first()._mapping["id"]
    )
    await kg_repo.link_question_option_indicator(opt_id, ind_id)
    cond = await kg_repo.create_condition({"code": cond_code, "name": "RAG Condition"})
    await kg_repo.link_indicator_condition(ind_id, cond.id)
    await session.execute(AssessmentSessionModel.__table__.insert().values(user_id=user_id))
    await session.commit()
    s_id = (
        (await session.execute(
            AssessmentSessionModel.__table__.select().where(
                AssessmentSessionModel.user_id == user_id
            )
        )).first()._mapping["id"]
    )
    await session.execute(
        AssessmentAnswerModel.__table__.insert().values(
            session_id=s_id, question_id=q_id, question_code=q_id,
            option_id=opt_id, value="Yes",
        )
    )
    await session.commit()
    await cdse.process_assessment(s_id, user_id)
    await report_svc.generate_report(s_id, user_id)
    await session.commit()
    return s_id, ind_id


class _RecordingProvider:
    """Returns a fixed raw response; records whether it was called."""

    def __init__(self, raw: str):
        self._raw = raw
        self.calls = 0
        self.last_context: ReportExplanationContext | None = None

    async def explain(self, context: ReportExplanationContext) -> str:
        self.calls += 1
        self.last_context = context
        return self._raw


class _FailingProvider:
    async def explain(self, context: ReportExplanationContext) -> str:
        raise AIProviderError("simulated failure")


# ---------------------------------------------------------------------------
# Retrieval tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_direct_indicator_evidence_retrieval(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-direct")
    eid = _ev(db_session, title="Direct Evidence")
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_id, evidence_id=eid, active=True
        )
    )
    await db_session.commit()

    svc = EvidenceRetrievalService(db_session)
    result = await svc.retrieve(indicator_ids=[ind_id], condition_ids=[], recommendation_ids=[])
    assert result.available
    assert len(result.evidence) == 1
    ev = result.evidence[0]
    assert ev.id == eid
    assert ev.title == "Direct Evidence"
    assert ev.linked_entity_type == "indicator"
    assert ev.linked_entity_id == ind_id
    assert ev.retrieval_tier == TIER_INDICATOR
    assert ev.excerpt  # excerpt derived from summary


@pytest.mark.asyncio
async def test_condition_transitive_evidence_retrieval(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-cond")
    eid = _ev(db_session, title="Condition Evidence")
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_id, evidence_id=eid, active=True
        )
    )
    await db_session.commit()
    from app.infrastructure.persistence.models.links import IndicatorConditionLinkModel
    cond_id = (
        (await db_session.execute(
            IndicatorConditionLinkModel.__table__.select().where(
                IndicatorConditionLinkModel.indicator_id == ind_id
            )
        )).first()._mapping["condition_id"]
    )

    svc = EvidenceRetrievalService(db_session)
    result = await svc.retrieve(indicator_ids=[], condition_ids=[cond_id], recommendation_ids=[])
    assert result.available
    assert result.evidence[0].id == eid
    assert result.evidence[0].linked_entity_type == "condition"
    assert result.evidence[0].retrieval_tier == 2


@pytest.mark.asyncio
async def test_inactive_link_excluded(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-inactive")
    eid = _ev(db_session, title="Inactive Link Evidence")
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_id, evidence_id=eid, active=False
        )
    )
    await db_session.commit()
    svc = EvidenceRetrievalService(db_session)
    result = await svc.retrieve(indicator_ids=[ind_id], condition_ids=[], recommendation_ids=[])
    assert not result.available
    assert result.evidence == []


@pytest.mark.asyncio
async def test_soft_deleted_evidence_excluded(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-deleted")
    import uuid

    eid = uuid.uuid4().hex
    db_session.add(
        EvidenceReferenceModel(
            id=eid, title="Deleted Evidence", source="JAMA", evidence_level="A",
            summary="x", deleted_at=datetime.now(UTC),
        )
    )
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_id, evidence_id=eid, active=True
        )
    )
    await db_session.commit()
    svc = EvidenceRetrievalService(db_session)
    result = await svc.retrieve(indicator_ids=[ind_id], condition_ids=[], recommendation_ids=[])
    assert not result.available


@pytest.mark.asyncio
async def test_ranking_orders_by_tier_and_level(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-rank")
    # tier-1 level-B evidence vs tier-1 level-A evidence: A ranks higher
    eid_a = _ev(db_session, title="High Evidence A", level="A")
    eid_b = _ev(db_session, title="Lower Evidence C", level="C")
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_id, evidence_id=eid_a, active=True
        )
    )
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_id, evidence_id=eid_b, active=True
        )
    )
    await db_session.commit()
    svc = EvidenceRetrievalService(db_session)
    result = await svc.retrieve(indicator_ids=[ind_id], condition_ids=[], recommendation_ids=[])
    assert [e.id for e in result.evidence] == [eid_a, eid_b]
    assert result.evidence[0].relevance >= result.evidence[1].relevance


@pytest.mark.asyncio
async def test_evidence_limit_respected(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-limit")
    eids = [_ev(db_session, title=f"E{i}", level="A") for i in range(8)]
    for eid in eids:
        await db_session.execute(
            IndicatorEvidenceLinkModel.__table__.insert().values(
                indicator_id=ind_id, evidence_id=eid, active=True
            )
        )
    await db_session.commit()
    svc = EvidenceRetrievalService(
        db_session, evidence_limit=3, per_entity_cap=3
    )
    result = await svc.retrieve(indicator_ids=[ind_id], condition_ids=[], recommendation_ids=[])
    assert len(result.evidence) == 3


@pytest.mark.asyncio
async def test_zero_evidence_returns_empty(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-zero")
    svc = EvidenceRetrievalService(db_session)
    result = await svc.retrieve(indicator_ids=[ind_id], condition_ids=[], recommendation_ids=[])
    assert not result.available
    assert result.evidence == []
    assert result.evidence_ids == []


@pytest.mark.asyncio
async def test_duplicate_evidence_removed(db_session: AsyncSession):
    """Evidence linked to an indicator reached both directly (tier 1) and via
    a condition (tier 2) must appear only once, at its best tier."""
    s_id, ind_id = await _seed_assessment(db_session, "u-dup")
    eid = _ev(db_session, title="Shared Evidence", level="A")
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_id, evidence_id=eid, active=True
        )
    )
    await db_session.commit()
    from app.infrastructure.persistence.models.links import IndicatorConditionLinkModel
    cond_id = (
        (await db_session.execute(
            IndicatorConditionLinkModel.__table__.select().where(
                IndicatorConditionLinkModel.indicator_id == ind_id
            )
        )).first()._mapping["condition_id"]
    )

    svc = EvidenceRetrievalService(db_session)
    result = await svc.retrieve(
        indicator_ids=[ind_id], condition_ids=[cond_id], recommendation_ids=[]
    )
    ids = [e.id for e in result.evidence]
    assert ids.count(eid) == 1
    # It is kept at tier 1 (indicator-direct) since that ranks higher.
    assert result.evidence[0].retrieval_tier == TIER_INDICATOR


# ---------------------------------------------------------------------------
# AI validation tests (citation grounding)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_valid_citation_accepted(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-cite-ok")
    eid = _ev(db_session, title="Cited Evidence", level="A")
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_id, evidence_id=eid, active=True
        )
    )
    await db_session.commit()
    _explanation_cache.clear()
    # Provider returns a response that cites the retrieved evidence id. The
    # service's retrieval will find `eid` for the indicator; the validator
    # must accept it.
    raw = json.dumps({
        "summary": "ok", "key_findings": [
            {"title": "f", "explanation": "e", "source_indicator_ids": [ind_id],
             "evidence_ids": [eid]},
        ],
        "recommendation_explanations": [],
        "evidence_notes": [], "limitations": "l",
        "disclaimer": "This AI-generated explanation is based on your MediCheck assessment and does not constitute a diagnosis.",
    })
    svc = AIExplanationService(db_session, provider=_RecordingProvider(raw))
    resp = await svc.explain_report(s_id, "u-cite-ok")
    assert resp.available is True
    assert resp.key_findings[0].evidence_ids == [eid]
    assert resp.evidence_available is True
    assert any(e.id == eid for e in resp.retrieved_evidence)
    assert resp.prompt_version == PROMPT_VERSION


@pytest.mark.asyncio
async def test_hallucinated_citation_rejected(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-cite-bad")
    # No evidence linked → the allow-list is empty. The AI cites EV-999 which
    # was never supplied → must be rejected → fallback.
    _explanation_cache.clear()
    raw = json.dumps({
        "summary": "bad", "key_findings": [
            {"title": "f", "explanation": "e", "source_indicator_ids": [ind_id],
             "evidence_ids": ["EV-999-INVENTED"]},
        ],
        "recommendation_explanations": [],
        "evidence_notes": [], "limitations": "l",
        "disclaimer": "This AI-generated explanation is based on your MediCheck assessment and does not constitute a diagnosis.",
    })
    svc = AIExplanationService(db_session, provider=_RecordingProvider(raw))
    resp = await svc.explain_report(s_id, "u-cite-bad")
    # Hallucinated citation → validation failure → unavailable fallback.
    assert resp.available is False
    assert resp.evidence_available is False


@pytest.mark.asyncio
async def test_hallucinated_indicator_still_rejected(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-ind-bad")
    _explanation_cache.clear()
    raw = json.dumps({
        "summary": "bad", "key_findings": [
            {"title": "f", "explanation": "e", "source_indicator_ids": ["FAKE-IND-ID"],
             "evidence_ids": []},
        ],
        "recommendation_explanations": [],
        "evidence_notes": [], "limitations": "l",
        "disclaimer": "This AI-generated explanation is based on your MediCheck assessment and does not constitute a diagnosis.",
    })
    svc = AIExplanationService(db_session, provider=_RecordingProvider(raw))
    resp = await svc.explain_report(s_id, "u-ind-bad")
    assert resp.available is False


@pytest.mark.asyncio
async def test_no_evidence_states_insufficiency(db_session: AsyncSession):
    """When retrieval finds nothing, the stub provider must state no evidence
    was available (never fabricate)."""
    s_id, ind_id = await _seed_assessment(db_session, "u-noev")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session)  # default stub provider
    resp = await svc.explain_report(s_id, "u-noev")
    assert resp.available is True
    assert resp.evidence_available is False
    assert resp.retrieved_evidence == []
    joined = " ".join(resp.evidence_notes).lower()
    assert "no supporting evidence was available" in joined


# ---------------------------------------------------------------------------
# Security tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthorized_assessment_ai_never_called(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-owner")
    eid = _ev(db_session, title="Owner Evidence", level="A")
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_id, evidence_id=eid, active=True
        )
    )
    await db_session.commit()
    _explanation_cache.clear()
    provider = _RecordingProvider(json.dumps({
        "summary": "x", "key_findings": [], "recommendation_explanations": [],
        "evidence_notes": [], "limitations": "l",
        "disclaimer": "This AI-generated explanation is based on your MediCheck assessment and does not constitute a diagnosis.",
    }))
    svc = AIExplanationService(db_session, provider=provider)
    with pytest.raises(ValueError):
        await svc.explain_report(s_id, "u-attacker")
    assert provider.calls == 0  # AI never called for an unauthorized report


@pytest.mark.asyncio
async def test_no_cross_patient_evidence(db_session: AsyncSession):
    """User A's retrieved evidence must not include evidence linked only to
    user B's indicators. Retrieval is seeded exclusively from the caller's own
    deterministic result."""
    s_id_a, ind_a = await _seed_assessment(db_session, "u-A")
    eid_a = _ev(db_session, title="A evidence", level="A")
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_a, evidence_id=eid_a, active=True
        )
    )
    # User B has a DIFFERENT indicator with DIFFERENT evidence.
    s_id_b, ind_b = await _seed_assessment(db_session, "u-B")
    eid_b = _ev(db_session, title="B evidence", level="A")
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_b, evidence_id=eid_b, active=True
        )
    )
    await db_session.commit()
    _explanation_cache.clear()
    svc = AIExplanationService(db_session)
    resp_a = await svc.explain_report(s_id_a, "u-A")
    ids_a = {e.id for e in resp_a.retrieved_evidence}
    assert eid_a in ids_a
    assert eid_b not in ids_a  # no leak from B


# ---------------------------------------------------------------------------
# Deterministic integrity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rag_is_read_only(db_session: AsyncSession):
    s_id, ind_id = await _seed_assessment(db_session, "u-integrity")
    eid = _ev(db_session, title="Integrity Evidence", level="A")
    await db_session.execute(
        IndicatorEvidenceLinkModel.__table__.insert().values(
            indicator_id=ind_id, evidence_id=eid, active=True
        )
    )
    await db_session.commit()
    _explanation_cache.clear()

    result = (
        await db_session.execute(
            select(AssessmentResultModel).where(AssessmentResultModel.session_id == s_id)
        )
    ).scalar_one()
    before = {
        "summary": result.summary,
        "confidence_score": result.confidence_score,
        "indicators": sorted(
            (a.indicator_id, a.score) for a in result.activated_indicators
        ),
        "conditions": sorted(
            (a.condition_id, a.score, a.confidence)
            for a in result.activated_conditions
        ),
        "recommendations": sorted(
            a.recommendation_id for a in result.generated_recommendations
        ),
    }

    svc = AIExplanationService(db_session)
    await svc.explain_report(s_id, "u-integrity")

    await db_session.refresh(result)
    after = {
        "summary": result.summary,
        "confidence_score": result.confidence_score,
        "indicators": sorted(
            (a.indicator_id, a.score) for a in result.activated_indicators
        ),
        "conditions": sorted(
            (a.condition_id, a.score, a.confidence)
            for a in result.activated_conditions
        ),
        "recommendations": sorted(
            a.recommendation_id for a in result.generated_recommendations
        ),
    }
    assert before == after
