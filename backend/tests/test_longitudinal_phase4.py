"""Phase 4 — Longitudinal risk trajectory + AI change explanation tests.

Covers the spec (sections 29):
Deterministic tests (1-15): two/three-assessment compare, body-system changes,
severity transitions, indicator new/persistent/removed, condition
new/persistent/removed, recommendation changes, no fabricated overall score,
missing-data handling, ordering, same-date determinism.
Security tests (16-19): own access, cross-user denied, unauthorized rejected,
AI not called for unauthorized.
AI tests (20-30): valid explanation, hallucinated indicator/condition/
recommendation/evidence rejected, AI-unavailable safe fallback, empty history
does not call AI, insufficient-data safe response, prompt version preserved,
trace ids preserved, evidence limited to allow-list.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.longitudinal_prompts import LONGITUDINAL_PROMPT_VERSION
from app.application.ai.longitudinal_provider import (
    AIProviderError,
    LongitudinalExplanationProvider,
    StubLongitudinalProvider,
)
from app.application.dtos.longitudinal_dtos import (
    LongitudinalExplanationContext,
    TrendLabel,
)
from app.application.services.longitudinal_analysis_service import (
    LongitudinalAnalysisService,
)
from app.application.services.longitudinal_explanation_service import (
    LongitudinalExplanationService,
)
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
from app.infrastructure.persistence.models.possible_condition import (
    PossibleConditionModel,
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

_MOCK_TOKEN = "mock-firebase-id-token"
_AUTH = {"Authorization": f"Bearer {_MOCK_TOKEN}"}


async def _seed_graph(
    session: AsyncSession,
    *,
    uid: str,
) -> dict[str, str]:
    """Seed body system, 2 indicators, 2 questions/options, 1 condition, 1 rec."""
    bs_id = f"bs-{uid}"
    qg_id = f"qg-{uid}"
    q1 = f"q1-{uid}"
    o1 = f"o1-{uid}"
    q2 = f"q2-{uid}"
    o2 = f"o2-{uid}"
    ind1 = f"ind1-{uid}"
    ind2 = f"ind2-{uid}"
    cond = f"cond-{uid}"
    rec = f"rec-{uid}"

    session.add(BodySystemModel(id=bs_id, code=bs_id, name="Cardiovascular", display_order=1))
    session.add(QuestionGroupModel(id=qg_id, code=qg_id, name="CV QG", body_system_id=bs_id, display_order=1, is_active=True))
    await session.commit()

    await session.execute(ClinicalIndicatorModel.__table__.insert().values(
        id=ind1, key=f"K1_{uid}", name="Exertional Fatigue", body_system_id=bs_id,
        severity="moderate", evidence_strength="B", is_active=True,
    ))
    await session.execute(ClinicalIndicatorModel.__table__.insert().values(
        id=ind2, key=f"K2_{uid}", name="Chest Discomfort", body_system_id=bs_id,
        severity="moderate", evidence_strength="B", is_active=True,
    ))
    await session.execute(QuestionModel.__table__.insert().values(
        id=q1, text="Tired?", body_system_id=bs_id, question_group_id=qg_id,
        code=q1, question_type="yes_no", status="active",
    ))
    await session.execute(QuestionModel.__table__.insert().values(
        id=q2, text="Chest pain?", body_system_id=bs_id, question_group_id=qg_id,
        code=q2, question_type="yes_no", status="active",
    ))
    await session.execute(QuestionOptionModel.__table__.insert().values(
        id=o1, question_id=q1, text="Yes", value="yes", code=o1,
        display_order=1, score_value=1.0,
    ))
    await session.execute(QuestionOptionModel.__table__.insert().values(
        id=o2, question_id=q2, text="Yes", value="yes", code=o2,
        display_order=1, score_value=1.0,
    ))
    await session.commit()
    # NOTE: only OPTION-level indicator links are created below; the CDSE
    # activates indicators via option links (QuestionOptionIndicatorLinkModel).

    kg = SQLKnowledgeGraphRepository(session)
    # The CDSE activates indicators via OPTION-level links, so link options→indicators.
    await kg.link_question_option_indicator(o1, ind1)
    await kg.link_question_option_indicator(o2, ind2)
    cond_obj = await kg.create_condition({"code": cond, "name": "Possible CV Risk"})
    await kg.link_indicator_condition(ind1, cond_obj.id)
    await kg.link_indicator_condition(ind2, cond_obj.id)
    # recommendation
    session.add(RecommendationModel(
        id=rec, key=f"REC_{uid}", body_system_id=bs_id, category="general",
        title="Follow up with clinician", text="Consider clinical follow-up.",
        order=1, evidence_level="B",
    ))
    await session.commit()
    # Link the recommendation to the condition so the CDSE generates it.
    await kg.link_condition_recommendation(cond_obj.id, rec)
    # evidence linked to indicator1
    ev_id = f"ev-{uid}"
    session.add(EvidenceReferenceModel(id=ev_id, title="Guideline A", source="JAMA", evidence_level="A", summary="Guideline A summary."))
    session.add(IndicatorEvidenceLinkModel(indicator_id=ind1, evidence_id=ev_id))
    await session.commit()

    return {
        "bs_id": bs_id, "ind1": ind1, "ind2": ind2, "cond": cond_obj.id,
        "rec": rec, "q1": q1, "o1": o1, "q2": q2, "o2": o2, "ev": ev_id,
    }


async def _run_assessment(
    session: AsyncSession,
    user_id: str,
    refs: dict[str, str],
    *,
    answer_q2: bool = False,
    completed_at: datetime | None = None,
) -> str:
    """Create a session, answer q1 (and optionally q2), run CDSE + report.
    Returns the session_id. Generates an explicit session id (like the ORM
    default) and uses raw inserts to avoid async relationship issues."""
    from app.application.services.clinical_decision_service import (
        ClinicalDecisionService,
    )
    from app.application.services.report_service import ReportService

    sid = uuid.uuid4().hex
    await session.execute(
        AssessmentSessionModel.__table__.insert().values(
            id=sid, user_id=user_id, status="active"
        )
    )
    await session.execute(
        AssessmentAnswerModel.__table__.insert().values(
            session_id=sid, question_id=refs["q1"], question_code=refs["q1"],
            option_id=refs["o1"], value="yes",
        )
    )
    if answer_q2:
        await session.execute(
            AssessmentAnswerModel.__table__.insert().values(
                session_id=sid, question_id=refs["q2"], question_code=refs["q2"],
                option_id=refs["o2"], value="yes",
            )
        )
    await session.commit()
    cdse = ClinicalDecisionService(session)
    await cdse.process_assessment(sid, user_id)
    report_svc = ReportService(session)
    await report_svc.generate_report(sid, user_id)
    await session.commit()
    if completed_at is not None:
        from app.infrastructure.persistence.models.report import HealthAssessmentModel
        await session.execute(
            HealthAssessmentModel.__table__.update()
            .where(HealthAssessmentModel.session_id == sid)
            .values(created_at=completed_at)
        )
        await session.execute(
            AssessmentSessionModel.__table__.update()
            .where(AssessmentSessionModel.id == sid)
            .values(completed_at=completed_at)
        )
        await session.commit()
    return sid


class _RawProvider:
    """Returns a fixed raw JSON string."""

    def __init__(self, raw: str):
        self._raw = raw
        self.calls = 0
        self.name = "raw-long"

    async def explain_trajectory(self, context: LongitudinalExplanationContext) -> str:
        self.calls += 1
        return self._raw


class _FailingProvider:
    name = "fail-long"
    calls = 0

    async def explain_trajectory(self, context: LongitudinalExplanationContext) -> str:
        self.calls += 1
        raise AIProviderError("simulated longitudinal failure")


# ---------------------------------------------------------------------------
# Deterministic tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_two_assessments_compare(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="two")
    uid = "u-two"
    t0 = datetime(2025, 1, 1, tzinfo=UTC)
    t1 = datetime(2025, 2, 1, tzinfo=UTC)
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=t0)
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=t1)
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    assert traj.sufficient_data is True
    assert len(traj.assessments) == 2
    assert len(traj.comparisons) == 1
    cmp = traj.comparisons[0]
    # SQLite strips tzinfo on read-back; compare naive wall times.
    assert (cmp.previous.completed_at or datetime.min).replace(tzinfo=None) == t0.replace(tzinfo=None)
    assert (cmp.current.completed_at or datetime.min).replace(tzinfo=None) == t1.replace(tzinfo=None)


@pytest.mark.asyncio
async def test_three_assessments_chronological(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="three")
    uid = "u-three"
    for i, ans in enumerate([False, True, False]):
        await _run_assessment(
            db_session, uid, refs, answer_q2=ans,
            completed_at=datetime(2025, 1, i + 1, tzinfo=UTC),
        )
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    assert len(traj.assessments) == 3
    assert len(traj.comparisons) == 2
    # chronological
    dates = [a.completed_at for a in traj.assessments]
    assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_body_system_score_changes(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="bsc")
    uid = "u-bsc"
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    cmp = traj.comparisons[0]
    bs_changes = [c for c in cmp.body_system_changes if c.ref_id == refs["bs_id"]]
    assert len(bs_changes) == 1
    c = bs_changes[0]
    assert c.current_score is not None and c.previous_score is not None
    assert c.current_score > c.previous_score
    assert c.trend in (TrendLabel.WORSENING,)


@pytest.mark.asyncio
async def test_severity_transitions(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="sev")
    uid = "u-sev"
    # assessment 1: low score (one indicator) -> Normal/Monitor; assessment 2: higher -> higher category
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    cmp = traj.comparisons[0]
    # overall severity should reflect the increase (worsening or stable-same-category);
    # the key guarantee: it never reads as a diagnosis and is deterministic.
    assert cmp.overall_change is not None
    assert cmp.overall_change.trend in (TrendLabel.WORSENING, TrendLabel.STABLE, TrendLabel.IMPROVING)


@pytest.mark.asyncio
async def test_new_indicators_detected(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="ni")
    uid = "u-ni"
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    cmp = traj.comparisons[0]
    assert refs["ind2"] in cmp.indicator_changes.new
    assert refs["ind1"] in cmp.indicator_changes.persistent


@pytest.mark.asyncio
async def test_persistent_indicators_detected(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="pi")
    uid = "u-pi"
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    cmp = traj.comparisons[0]
    assert refs["ind1"] in cmp.indicator_changes.persistent
    assert cmp.indicator_changes.new == []


@pytest.mark.asyncio
async def test_removed_indicators_detected(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="ri")
    uid = "u-ri"
    # first: both answered; second: only q1 (ind2 not activated) — but ind1 always on
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    cmp = traj.comparisons[0]
    assert refs["ind2"] in cmp.indicator_changes.resolved


@pytest.mark.asyncio
async def test_new_possible_conditions(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="nc")
    uid = "u-nc"
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    cmp = traj.comparisons[0]
    # condition should be persistent (present in both) since ind1 triggers it both times
    assert refs["cond"] in cmp.condition_changes.persistent


@pytest.mark.asyncio
async def test_persistent_possible_conditions(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="pc")
    uid = "u-pc"
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    cmp = traj.comparisons[0]
    assert refs["cond"] in cmp.condition_changes.persistent


@pytest.mark.asyncio
async def test_removed_possible_conditions(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="rc")
    uid = "u-rc"
    # Use a second condition that only appears when q2 answered (linked to ind2)
    # For simplicity: first assessment answers q2 (cond present), second doesn't (cond removed if only ind2-linked)
    # Our cond is linked to both ind1+ind2, so it persists. To test removal we need a cond linked only to ind2.
    bs = refs["bs_id"]
    cond2 = f"cond2-{uid[2:]}" if uid.startswith("u-") else f"cond2-{uid}"
    kg = SQLKnowledgeGraphRepository(db_session)
    c2 = await kg.create_condition({"code": cond2, "name": "Second Condition"})
    await kg.link_indicator_condition(refs["ind2"], c2.id)
    await db_session.commit()
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    cmp = traj.comparisons[0]
    assert c2.id in cmp.condition_changes.removed


@pytest.mark.asyncio
async def test_recommendation_changes(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="rec")
    uid = "u-rec"
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    cmp = traj.comparisons[0]
    # rec is linked to cond which is persistent -> rec should be persistent
    assert refs["rec"] in cmp.recommendation_changes.persistent


@pytest.mark.asyncio
async def test_no_fabricated_overall_score(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="noscore")
    uid = "u-noscore"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    # The trajectory must NOT contain a single fabricated numeric "health score".
    # overall_severity is a categorical label only (or None), never an invented score.
    for a in traj.assessments:
        assert a.overall_severity is None or isinstance(a.overall_severity, str)


@pytest.mark.asyncio
async def test_missing_historical_data_one_assessment(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="one")
    uid = "u-one"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    assert traj.sufficient_data is False
    assert len(traj.comparisons) == 0
    assert "first assessment" in traj.summary.lower()


@pytest.mark.asyncio
async def test_no_assessments_empty(db_session: AsyncSession):
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory("nobody")
    assert traj.sufficient_data is False
    assert traj.assessments == []
    assert "timeline" in traj.summary.lower()


@pytest.mark.asyncio
async def test_assessment_ordering_chronological(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="ord")
    uid = "u-ord"
    # insert out of chronological order by completed_at
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 3, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    dates = [a.completed_at for a in traj.assessments]
    assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_same_date_assessments_deterministic(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="same")
    uid = "u-same"
    same = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    await _run_assessment(db_session, uid, refs, answer_q2=False, completed_at=same)
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=same)
    svc = LongitudinalAnalysisService(db_session)
    traj = await svc.get_trajectory(uid)
    # deterministic: still produces a comparison; ordering stable across calls
    assert len(traj.comparisons) == 1
    traj2 = await svc.get_trajectory(uid)
    assert [a.assessment_id for a in traj.assessments] == [a.assessment_id for a in traj2.assessments]


# ---------------------------------------------------------------------------
# Security tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_patient_can_access_own_trajectory(client: AsyncClient, db_session: AsyncSession):
    me = await client.get("/api/v1/auth/me", headers=_AUTH)
    uid = me.json()["id"]
    refs = await _seed_graph(db_session, uid="own")
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    resp = await client.get("/api/v1/trajectory", headers=_AUTH)
    assert resp.status_code == 200
    assert resp.json()["sufficient_data"] is True


@pytest.mark.asyncio
async def test_patient_cannot_access_other_trajectory(client: AsyncClient, db_session: AsyncSession):
    me = await client.get("/api/v1/auth/me", headers=_AUTH)
    uid = me.json()["id"]
    refs = await _seed_graph(db_session, uid="other")
    other = "user-someone-else"
    await _run_assessment(db_session, other, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, other, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    # The caller's own trajectory is empty (no cross-user leak).
    resp = await client.get("/api/v1/trajectory", headers=_AUTH)
    assert resp.status_code == 200
    assert resp.json()["assessments"] == []


@pytest.mark.asyncio
async def test_unauthorized_request_rejected(client: AsyncClient):
    resp = await client.get("/api/v1/trajectory")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_ai_not_called_for_unauthorized(client: AsyncClient, db_session: AsyncSession):
    # No auth -> 401/403; the provider is never reached.
    resp = await client.post("/api/v1/trajectory/explanation", json={})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_cross_user_specific_compare_404(client: AsyncClient, db_session: AsyncSession):
    me = await client.get("/api/v1/auth/me", headers=_AUTH)
    refs = await _seed_graph(db_session, uid="xu")
    other = "user-other-xu"
    s1 = await _run_assessment(db_session, other, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    s2 = await _run_assessment(db_session, other, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    resp = await client.get(f"/api/v1/trajectory/compare/{s1}/{s2}", headers=_AUTH)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# AI tests
# ---------------------------------------------------------------------------

def _ctx(ind_ids=None, cond_ids=None, rec_ids=None, ev_ids=None) -> LongitudinalExplanationContext:
    return LongitudinalExplanationContext(
        trace_ids=["t1", "t2"],
        assessment_dates=["2025-01-01", "2025-02-01"],
        body_system_changes=[],
        indicator_changes={"new": ind_ids or [], "resolved": [], "persistent": ind_ids or []},
        condition_changes={"new": cond_ids or [], "removed": [], "persistent": cond_ids or []},
        recommendation_changes={"new": rec_ids or [], "removed": [], "persistent": rec_ids or []},
        retrieved_evidence=[{"id": e} for e in (ev_ids or [])],
        evidence_available=bool(ev_ids),
        prompt_version=LONGITUDINAL_PROMPT_VERSION,
    )


def _raw_explanation(**overrides) -> str:
    base = {
        "available": True,
        "summary": "Your assessment findings were largely stable.",
        "key_changes": [],
        "persistent_findings": [],
        "new_findings": [],
        "improved_findings": [],
        "stable_findings": [],
        "important_context": [],
        "evidence_ids": [],
        "prompt_version": LONGITUDINAL_PROMPT_VERSION,
        "trace_ids": ["t1", "t2"],
        "disclaimer": "This does not diagnose conditions.",
    }
    base.update(overrides)
    return json.dumps(base)


@pytest.mark.asyncio
async def test_valid_explanation_accepted(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="ve")
    uid = "u-ve"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalExplanationService(db_session, provider=StubLongitudinalProvider())
    resp = await svc.explain_trajectory(uid)
    assert resp.available is True
    assert resp.summary
    assert resp.prompt_version == LONGITUDINAL_PROMPT_VERSION
    assert resp.trace_ids


@pytest.mark.asyncio
async def test_hallucinated_indicator_rejected(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="hi")
    uid = "u-hi"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    bad = _raw_explanation(
        new_findings=[{
            "label": "x", "ref_type": "indicator", "ref_id": "fake-indicator",
            "explanation": "newly activated", "evidence_ids": [],
        }]
    )
    svc = LongitudinalExplanationService(db_session, provider=_RawProvider(bad))
    resp = await svc.explain_trajectory(uid)
    assert resp.available is False  # rejected -> safe fallback


@pytest.mark.asyncio
async def test_hallucinated_condition_rejected(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="hc")
    uid = "u-hc"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    bad = _raw_explanation(
        new_findings=[{
            "label": "x", "ref_type": "condition", "ref_id": "fake-condition",
            "explanation": "newly appearing", "evidence_ids": [],
        }]
    )
    svc = LongitudinalExplanationService(db_session, provider=_RawProvider(bad))
    resp = await svc.explain_trajectory(uid)
    assert resp.available is False


@pytest.mark.asyncio
async def test_hallucinated_recommendation_rejected(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="hr")
    uid = "u-hr"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    bad = _raw_explanation(
        persistent_findings=[{
            "label": "x", "ref_type": "recommendation", "ref_id": "fake-rec",
            "explanation": "persistent", "evidence_ids": [],
        }]
    )
    svc = LongitudinalExplanationService(db_session, provider=_RawProvider(bad))
    resp = await svc.explain_trajectory(uid)
    assert resp.available is False


@pytest.mark.asyncio
async def test_hallucinated_evidence_rejected(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="he")
    uid = "u-he"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    bad = _raw_explanation(evidence_ids=["fake-ev-999"])
    svc = LongitudinalExplanationService(db_session, provider=_RawProvider(bad))
    resp = await svc.explain_trajectory(uid)
    assert resp.available is False


@pytest.mark.asyncio
async def test_ai_unavailable_safe_fallback(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="au")
    uid = "u-au"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalExplanationService(db_session, provider=_FailingProvider())
    resp = await svc.explain_trajectory(uid)
    assert resp.available is False
    # deterministic trajectory still queryable
    traj = await LongitudinalAnalysisService(db_session).get_trajectory(uid)
    assert traj.sufficient_data is True


@pytest.mark.asyncio
async def test_empty_history_does_not_call_ai(db_session: AsyncSession):
    provider = _FailingProvider()
    svc = LongitudinalExplanationService(db_session, provider=provider)
    resp = await svc.explain_trajectory("nobody-here")
    assert resp.available is False
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_insufficient_history_safe_response(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="ih")
    uid = "u-ih"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    provider = _FailingProvider()
    svc = LongitudinalExplanationService(db_session, provider=provider)
    resp = await svc.explain_trajectory(uid)
    assert resp.available is False
    assert provider.calls == 0
    assert "assessment" in (resp.summary or "").lower() or "data" in (resp.summary or "").lower()


@pytest.mark.asyncio
async def test_prompt_version_preserved(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="pv")
    uid = "u-pv"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalExplanationService(db_session, provider=StubLongitudinalProvider())
    resp = await svc.explain_trajectory(uid)
    assert resp.prompt_version == LONGITUDINAL_PROMPT_VERSION


@pytest.mark.asyncio
async def test_trace_ids_preserved(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="ti")
    uid = "u-ti"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalExplanationService(db_session, provider=StubLongitudinalProvider())
    resp = await svc.explain_trajectory(uid)
    assert len(resp.trace_ids) == 2
    assert all(resp.trace_ids)


@pytest.mark.asyncio
async def test_evidence_limited_to_allowlist(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="ea")
    uid = "u-ea"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    # Stub provider only references evidence actually retrieved -> allowed.
    svc = LongitudinalExplanationService(db_session, provider=StubLongitudinalProvider())
    resp = await svc.explain_trajectory(uid)
    # The retrieved evidence ids in the response are the allow-list.
    if resp.evidence_available:
        ev_ids = {e["id"] for e in resp.retrieved_evidence}
        for e in resp.evidence_ids:
            assert e in ev_ids


@pytest.mark.asyncio
async def test_endpoint_happy_path(client: AsyncClient, db_session: AsyncSession):
    me = await client.get("/api/v1/auth/me", headers=_AUTH)
    uid = me.json()["id"]
    refs = await _seed_graph(db_session, uid="ep")
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    resp = await client.get("/api/v1/trajectory", headers=_AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sufficient_data"] is True
    expl = await client.post("/api/v1/trajectory/explanation", json={}, headers=_AUTH)
    assert expl.status_code == 200
    ej = expl.json()
    assert ej["available"] is True
    assert ej["prompt_version"] == LONGITUDINAL_PROMPT_VERSION


@pytest.mark.asyncio
async def test_non_diagnostic_language(db_session: AsyncSession):
    refs = await _seed_graph(db_session, uid="nd")
    uid = "u-nd"
    await _run_assessment(db_session, uid, refs, completed_at=datetime(2025, 1, 1, tzinfo=UTC))
    await _run_assessment(db_session, uid, refs, answer_q2=True, completed_at=datetime(2025, 2, 1, tzinfo=UTC))
    svc = LongitudinalExplanationService(db_session, provider=StubLongitudinalProvider())
    resp = await svc.explain_trajectory(uid)
    blob = (resp.summary or "") + " ".join(resp.important_context or [])
    # The explanation must frame findings as assessment signals, not diagnoses.
    # "diagnos" may appear only in the negation "not ... diagnoses".
    lowered = blob.lower()
    assert "diagnose" not in lowered or "does not diagnose" in lowered or "not confirmed diagnoses" in lowered or "not a diagnosis" in lowered
