"""Phase 1 AI explanation — backend tests.

Covers the required cases from the Phase 1 spec:
- happy path (valid report → provider → valid structured response)
- AI unavailable (provider failure → graceful fallback → report unaffected)
- invalid AI output (malformed → validation failure → safe failure)
- hallucinated ID (AI references an indicator not in the report → rejected)
- unauthorized assessment (user requests another user's assessment → 404, AI
  never called)
- no report (missing report → 404, AI never called)
- deterministic integrity (calling the explanation endpoint does NOT modify
  scores/indicators/conditions/recommendations/severity/answers)

The deterministic CDSE / ReportService are not modified. These tests use the
existing test database + the deterministic stub provider by default, and inject
custom providers for the failure/hallucination cases.

Run: ALLOW_MOCK_AUTH=true python -m pytest tests/test_ai_explanation_phase1.py -q
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.provider import AIProviderError
from app.application.dtos.ai_dtos import ReportExplanationContext
from app.application.services.ai_explanation_service import (
    AIExplanationService,
    _explanation_cache,
)
from app.application.services.clinical_decision_service import ClinicalDecisionService
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
from app.infrastructure.persistence.models.decision import (
    AssessmentResultModel,
    ActivatedIndicatorModel,
    ActivatedConditionModel,
    GeneratedRecommendationModel,
)
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.question_group import QuestionGroupModel
from app.infrastructure.persistence.models.question_option import QuestionOptionModel
from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
    SQLKnowledgeGraphRepository,
)

_MOCK_TOKEN = "mock-firebase-id-token"


class _RecordingProvider:
    """A test provider whose response is fixed at construction.

    Records whether it was called, so unauthorized/no-report cases can assert
    the AI was never invoked.
    """

    def __init__(self, raw: str):
        self._raw = raw
        self.calls = 0

    async def explain(self, context: ReportExplanationContext) -> str:
        self.calls += 1
        return self._raw


class _FailingProvider:
    async def explain(self, context: ReportExplanationContext) -> str:
        raise AIProviderError("simulated provider failure")


async def _seed_and_run_assessment(session: AsyncSession, user_id: str) -> str:
    """Seed minimal knowledge-graph + run CDSE + generate report, return the
    assessment session id (owned by ``user_id``)."""
    kg_repo = SQLKnowledgeGraphRepository(session)
    cdse = ClinicalDecisionService(session)
    report_svc = ReportService(session)

    bs = BodySystemModel(id="bs-ai", code="AI", name="AI Test", display_order=1)
    session.add(bs)
    qg = QuestionGroupModel(
        id="qg-ai", code="QG_AI", name="QG AI", body_system_id="bs-ai", display_order=1
    )
    session.add(qg)
    await session.commit()

    await session.execute(
        ClinicalIndicatorModel.__table__.insert().values(
            key="AI_IND_1",
            name="Indicator One",
            body_system_id="bs-ai",
            severity="moderate",
            evidence_strength="B",
        )
    )
    await session.execute(
        QuestionModel.__table__.insert().values(
            text="Q1",
            body_system_id="bs-ai",
            question_group_id="qg-ai",
            code="q1",
            question_type="yes_no",
        )
    )
    await session.execute(
        QuestionOptionModel.__table__.insert().values(
            question_id="q1",
            text="Yes",
            value="yes",
            code="opt1",
            display_order=1,
            score_value=1.0,
        )
    )
    await session.commit()

    ind_id = (
        (
            await session.execute(
                ClinicalIndicatorModel.__table__.select().where(
                    ClinicalIndicatorModel.key == "AI_IND_1"
                )
            )
        ).first()._mapping["id"]
    )
    q_id = (
        (
            await session.execute(
                QuestionModel.__table__.select().where(QuestionModel.code == "q1")
            )
        ).first()._mapping["id"]
    )
    opt_id = (
        (
            await session.execute(
                QuestionOptionModel.__table__.select().where(
                    QuestionOptionModel.code == "opt1"
                )
            )
        ).first()._mapping["id"]
    )

    await kg_repo.link_question_option_indicator(opt_id, ind_id)
    cond = await kg_repo.create_condition({"code": "AI_C1", "name": "Condition One"})
    await kg_repo.link_indicator_condition(ind_id, cond.id)

    await session.execute(
        AssessmentSessionModel.__table__.insert().values(user_id=user_id)
    )
    await session.commit()
    s_id = (
        (
            await session.execute(
                AssessmentSessionModel.__table__.select().where(
                    AssessmentSessionModel.user_id == user_id
                )
            )
        ).first()._mapping["id"]
    )

    await session.execute(
        AssessmentAnswerModel.__table__.insert().values(
            session_id=s_id,
            question_id=q_id,
            question_code="q1",
            option_id=opt_id,
            value="Yes",
        )
    )
    await session.commit()

    await cdse.process_assessment(s_id, user_id)
    await report_svc.generate_report(s_id, user_id)
    await session.commit()
    return s_id


def _snapshot_result(result: AssessmentResultModel) -> dict[str, Any]:
    return {
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


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_returns_valid_explanation(db_session: AsyncSession):
    s_id = await _seed_and_run_assessment(db_session, "u-happy")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session)
    resp = await svc.explain_report(s_id, "u-happy")
    assert resp.available is True
    assert resp.summary
    assert resp.disclaimer
    assert any(f.source_indicator_ids for f in resp.key_findings)
    # every referenced indicator id is a real indicator from this report
    result = (
        await db_session.execute(
            select(AssessmentResultModel).where(
                AssessmentResultModel.session_id == s_id
            )
        )
    ).scalar_one()
    real_ind_ids = {a.indicator_id for a in result.activated_indicators}
    for f in resp.key_findings:
        for iid in f.source_indicator_ids:
            assert iid in real_ind_ids


@pytest.mark.asyncio
async def test_ai_unavailable_returns_fallback(db_session: AsyncSession):
    s_id = await _seed_and_run_assessment(db_session, "u-unavail")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=_FailingProvider())
    resp = await svc.explain_report(s_id, "u-unavail")
    assert resp.available is False
    assert "unavailable" in resp.summary.lower() or "couldn't" in resp.summary.lower()


@pytest.mark.asyncio
async def test_invalid_ai_output_returns_fallback(db_session: AsyncSession):
    s_id = await _seed_and_run_assessment(db_session, "u-invalid")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=_RecordingProvider("not json {"))
    resp = await svc.explain_report(s_id, "u-invalid")
    assert resp.available is False


@pytest.mark.asyncio
async def test_hallucinated_indicator_id_rejected(db_session: AsyncSession):
    s_id = await _seed_and_run_assessment(db_session, "u-hall")
    _explanation_cache.clear()
    bad = json.dumps(
        {
            "summary": "x",
            "key_findings": [
                {
                    "title": "T",
                    "explanation": "E",
                    "source_indicator_ids": ["fake-indicator-id"],
                }
            ],
            "severity_explanation": "",
            "recommendation_explanations": [],
            "evidence_notes": [],
            "limitations": "",
            "disclaimer": "d",
        }
    )
    svc = AIExplanationService(db_session, provider=_RecordingProvider(bad))
    resp = await svc.explain_report(s_id, "u-hall")
    # hallucinated id → validation failure → safe fallback
    assert resp.available is False


@pytest.mark.asyncio
async def test_hallucinated_recommendation_id_rejected(db_session: AsyncSession):
    s_id = await _seed_and_run_assessment(db_session, "u-hallrec")
    _explanation_cache.clear()
    bad = json.dumps(
        {
            "summary": "x",
            "key_findings": [],
            "severity_explanation": "",
            "recommendation_explanations": [
                {"recommendation_id": "fake-rec-id", "explanation": "e"}
            ],
            "evidence_notes": [],
            "limitations": "",
            "disclaimer": "d",
        }
    )
    svc = AIExplanationService(db_session, provider=_RecordingProvider(bad))
    resp = await svc.explain_report(s_id, "u-hallrec")
    assert resp.available is False


@pytest.mark.asyncio
async def test_unauthorized_raises_and_ai_not_called(db_session: AsyncSession):
    s_id = await _seed_and_run_assessment(db_session, "owner-a")
    _explanation_cache.clear()
    provider = _RecordingProvider(json.dumps({"summary": "x", "disclaimer": "d"}))
    svc = AIExplanationService(db_session, provider=provider)
    with pytest.raises(ValueError):
        await svc.explain_report(s_id, "intruder-b")
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_no_report_raises_and_ai_not_called(db_session: AsyncSession):
    _explanation_cache.clear()
    provider = _RecordingProvider(json.dumps({"summary": "x", "disclaimer": "d"}))
    svc = AIExplanationService(db_session, provider=provider)
    with pytest.raises(ValueError):
        await svc.explain_report("nonexistent-session", "u-noreport")
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_deterministic_integrity(db_session: AsyncSession):
    s_id = await _seed_and_run_assessment(db_session, "u-integrity")
    result = (
        await db_session.execute(
            select(AssessmentResultModel).where(
                AssessmentResultModel.session_id == s_id
            )
        )
    ).scalar_one()
    before = _snapshot_result(result)

    _explanation_cache.clear()
    svc = AIExplanationService(db_session)
    resp = await svc.explain_report(s_id, "u-integrity")
    assert resp.available is True

    # refresh a fresh view of the result
    db_session.expire_all()
    result2 = (
        await db_session.execute(
            select(AssessmentResultModel).where(
                AssessmentResultModel.session_id == s_id
            )
        )
    ).scalar_one()
    after = _snapshot_result(result2)
    assert before == after

    # answers unchanged
    answers = (
        await db_session.execute(
            select(AssessmentAnswerModel).where(
                AssessmentAnswerModel.session_id == s_id
            )
        )
    ).scalars().all()
    assert len(answers) == 1
    assert answers[0].value == "Yes"


@pytest.mark.asyncio
async def test_cache_hit_does_not_recall_provider(db_session: AsyncSession):
    s_id = await _seed_and_run_assessment(db_session, "u-cache")
    _explanation_cache.clear()
    provider = _RecordingProvider(
        json.dumps(
            {
                "summary": "cached",
                "key_findings": [],
                "severity_explanation": "",
                "recommendation_explanations": [],
                "evidence_notes": [],
                "limitations": "",
                "disclaimer": "d",
            }
        )
    )
    svc = AIExplanationService(db_session, provider=provider)
    r1 = await svc.explain_report(s_id, "u-cache")
    assert r1.available is True
    assert provider.calls == 1
    r2 = await svc.explain_report(s_id, "u-cache")
    assert provider.calls == 1  # served from cache


# ---------------------------------------------------------------------------
# HTTP endpoint tests (auth + ownership + response shape)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_endpoint_happy_path(client: AsyncClient, db_session: AsyncSession):
    # Trigger app lifespan (DB seed) on a first request BEFORE seeding the
    # assessment through the shared session, to avoid SQLite write contention
    # between the lifespan's seed connection and db_session. Also obtain the
    # real authenticated user id (mock-auth creates a user with a generated
    # UUID id, not equal to the token).
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {_MOCK_TOKEN}"}
    )
    assert me.status_code == 200
    user_id = me.json()["id"]
    s_id = await _seed_and_run_assessment(db_session, user_id)
    _explanation_cache.clear()
    resp = await client.post(
        f"/api/v1/report/{s_id}/explanation",
        headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert data["summary"]
    assert data["disclaimer"]


@pytest.mark.asyncio
async def test_endpoint_unauthorized_other_user(
    client: AsyncClient, db_session: AsyncSession
):
    await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {_MOCK_TOKEN}"}
    )
    s_id = await _seed_and_run_assessment(db_session, "someone-else")
    _explanation_cache.clear()
    resp = await client.post(
        f"/api/v1/report/{s_id}/explanation",
        headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
    )
    # not owned by the caller → 404 (no information leak)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_endpoint_missing_report(client: AsyncClient):
    _explanation_cache.clear()
    resp = await client.post(
        "/api/v1/report/does-not-exist/explanation",
        headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_endpoint_requires_auth(client: AsyncClient):
    _explanation_cache.clear()
    resp = await client.post("/api/v1/report/anything/explanation")
    assert resp.status_code in (401, 403)
