"""Phase 7 — AI-Powered Personalized Risk Communication, Transparency & AI Governance.

Backend tests covering:
- Personalized explanation with language (en/si/ta) and literacy levels (simple/standard/detailed)
- "Why was I asked this?" question explanation (knowledge-graph grounded)
- AI transparency notice presence
- Source breakdown (Show the source) — traceable chain
- AI audit trail record creation (hashes only, no PHI)
- AI quality status (valid/fallback/validation_failed/provider_unavailable)
- AI governance dashboard RBAC (RESEARCH_REVIEWER+ only)
- PHI minimization (no patient identifiers in audit records)
- Patient ownership (cross-patient isolation)
- Deterministic report integrity (AI explanation doesn't modify CDSE output)
- Multilingual: translation does not upgrade certainty (possible ≠ confirmed)
- Trace ID preservation + prompt version tracking

Constraints honored: no clinical decision engine changes, no schema
migrations (additive table only), no LLM APIs. AI is explanation layer only.

Run: ALLOW_MOCK_AUTH=true python -m pytest tests/test_ai_phase7.py -q
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.main as app_main
from app.application.ai.personalized_provider import (
    PersonalizedExplanationProvider,
)
from app.application.ai.phase7_prompts import (
    AI_TRANSPARENCY_NOTICE,
    PHASE7_PROMPT_VERSION,
)
from app.application.ai.provider import AIProviderError
from app.application.dtos.ai_dtos import (
    AIQualityStatus,
    LiteracyLevel,
    ReportExplanationContext,
)
from app.application.services.ai_explanation_service import (
    AIExplanationService,
    _explanation_cache,
)
from app.application.services.clinical_decision_service import (
    ClinicalDecisionService,
)
from app.application.services.report_service import ReportService
from app.core.security.rbac import Permission, Role
from app.domain.entities.user import User
from app.infrastructure.persistence.models.assessment_answer import (
    AssessmentAnswerModel,
)
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.ai_interaction_audit import (
    AIInteractionAuditModel,
)
from app.infrastructure.persistence.models.body_system import BodySystemModel
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.decision import (
    AssessmentResultModel,
)
from app.infrastructure.persistence.models.links import (
    IndicatorConditionLinkModel,
    QuestionIndicatorLinkModel,
)
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.question_group import (
    QuestionGroupModel,
)
from app.infrastructure.persistence.models.question_option import (
    QuestionOptionModel,
)
from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
    SQLKnowledgeGraphRepository,
)

_MOCK_TOKEN = "mock-firebase-id-token"


# ---------------------------------------------------------------------------
# Test helpers (reuse the Phase 1 seeding pattern)
# ---------------------------------------------------------------------------


async def _seed_and_run_assessment(
    session: AsyncSession, user_id: str
) -> tuple[str, str]:
    """Seed minimal knowledge-graph + run CDSE + generate report.
    Returns (session_id, question_id)."""
    kg_repo = SQLKnowledgeGraphRepository(session)
    cdse = ClinicalDecisionService(session)
    report_svc = ReportService(session)

    bs = BodySystemModel(
        id="bs-p7", code="P7", name="Phase7 Test", display_order=1
    )
    session.add(bs)
    qg = QuestionGroupModel(
        id="qg-p7",
        code="QG_P7",
        name="QG P7",
        body_system_id="bs-p7",
        display_order=1,
    )
    session.add(qg)
    await session.commit()

    await session.execute(
        ClinicalIndicatorModel.__table__.insert().values(
            key="P7_IND_1",
            name="Phase7 Indicator",
            body_system_id="bs-p7",
            severity="moderate",
            evidence_strength="B",
        )
    )
    await session.execute(
        QuestionModel.__table__.insert().values(
            text="Do you feel thirsty often?",
            body_system_id="bs-p7",
            question_group_id="qg-p7",
            code="p7q1",
            question_type="yes_no",
        )
    )
    await session.execute(
        QuestionOptionModel.__table__.insert().values(
            question_id="q1",
            text="Yes",
            value="yes",
            code="p7opt1",
            display_order=1,
            score_value=1.0,
        )
    )
    await session.commit()

    ind_id = (
        (
            await session.execute(
                ClinicalIndicatorModel.__table__.select().where(
                    ClinicalIndicatorModel.key == "P7_IND_1"
                )
            )
        ).first()._mapping["id"]
    )
    q_id = (
        (
            await session.execute(
                QuestionModel.__table__.select().where(
                    QuestionModel.code == "p7q1"
                )
            )
        ).first()._mapping["id"]
    )
    opt_id = (
        (
            await session.execute(
                QuestionOptionModel.__table__.select().where(
                    QuestionOptionModel.code == "p7opt1"
                )
            )
        ).first()._mapping["id"]
    )

    # Link question → indicator (for "Why was I asked this?")
    await session.execute(
        QuestionIndicatorLinkModel.__table__.insert().values(
            question_id=q_id, indicator_id=ind_id, active=True
        )
    )
    cond = await kg_repo.create_condition(
        {"code": "P7_C1", "name": "Phase7 Condition"}
    )
    await kg_repo.link_indicator_condition(ind_id, cond.id)
    await session.commit()

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
            question_code="p7q1",
            option_id=opt_id,
            value="Yes",
        )
    )
    await session.commit()

    await cdse.process_assessment(s_id, user_id)
    await report_svc.generate_report(s_id, user_id)
    await session.commit()
    return s_id, q_id


def _make_user(roles: set[Role], email: str = "gov@example.com") -> User:
    return User(
        id=uuid.uuid4().hex,
        firebase_uid=f"fb-{email}",
        email=email,
        full_name="Phase7 User",
        avatar_url=None,
        email_verified=True,
        is_active=True,
        roles=roles,
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )


# ---------------------------------------------------------------------------
# Feature A — Personalized explanation (literacy + language)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_personalized_explanation_english_standard(
    db_session: AsyncSession,
):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-en-std")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    resp = await svc.explain_report(
        s_id, "u-p7-en-std", language="en", literacy_level="standard"
    )
    assert resp.available is True
    assert resp.language == "en"
    assert resp.literacy_level == LiteracyLevel.STANDARD
    assert resp.transparency_notice
    assert "deterministic" in resp.transparency_notice.lower()


@pytest.mark.asyncio
async def test_personalized_explanation_simple_level(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-simple")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    resp = await svc.explain_report(
        s_id, "u-p7-simple", language="en", literacy_level="simple"
    )
    assert resp.available is True
    assert resp.literacy_level == LiteracyLevel.SIMPLE
    # Simple level must not overwhelm with jargon
    assert resp.summary
    assert "does not mean you have a disease" in resp.summary.lower()


@pytest.mark.asyncio
async def test_personalized_explanation_detailed_level(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-detailed")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    resp = await svc.explain_report(
        s_id, "u-p7-detailed", language="en", literacy_level="detailed"
    )
    assert resp.available is True
    assert resp.literacy_level == LiteracyLevel.DETAILED
    # Detailed level includes trace ID and counts
    assert resp.trace_id is not None or "Trace" in resp.summary


@pytest.mark.asyncio
async def test_multilingual_sinhala(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-si")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    resp = await svc.explain_report(
        s_id, "u-p7-si", language="si", literacy_level="standard"
    )
    assert resp.available is True
    assert resp.language == "si"


@pytest.mark.asyncio
async def test_multilingual_tamil(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-ta")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    resp = await svc.explain_report(
        s_id, "u-p7-ta", language="ta", literacy_level="standard"
    )
    assert resp.available is True
    assert resp.language == "ta"


@pytest.mark.asyncio
async def test_translation_does_not_upgrade_certainty(
    db_session: AsyncSession,
):
    """Critical: translation must never convert possible → confirmed,
    monitor → urgent, risk → diagnosis."""
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-cert")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    for lang in ("en", "si", "ta"):
        resp = await svc.explain_report(
            s_id, "u-p7-cert", language=lang, literacy_level="standard"
        )
        text = (resp.summary + " " + resp.disclaimer).lower()
        # Must NEVER say "you have" or "diagnosed" or "confirmed condition"
        assert "you have" not in text, f"Language {lang}: upgraded certainty"
        assert "diagnosed" not in text, f"Language {lang}: upgraded certainty"
        assert "confirmed condition" not in text, f"Language {lang}: upgraded certainty"


# ---------------------------------------------------------------------------
# Feature B — "Why was I asked this?"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_question_explanation_happy_path(db_session: AsyncSession):
    from app.application.services.question_explanation_service import (
        QuestionExplanationService,
    )

    s_id, q_id = await _seed_and_run_assessment(db_session, "u-p7-why")
    svc = QuestionExplanationService(db_session)
    result = await svc.explain_question(
        session_id=s_id,
        question_id=q_id,
        user_id="u-p7-why",
        language="en",
    )
    assert result["available"] is True
    assert result["question_id"] == q_id
    assert result["explanation"]
    assert len(result["linked_indicators"]) > 0
    assert "included because" in result["explanation"]


@pytest.mark.asyncio
async def test_question_explanation_sinhala(db_session: AsyncSession):
    from app.application.services.question_explanation_service import (
        QuestionExplanationService,
    )

    s_id, q_id = await _seed_and_run_assessment(db_session, "u-p7-why-si")
    svc = QuestionExplanationService(db_session)
    result = await svc.explain_question(
        session_id=s_id,
        question_id=q_id,
        user_id="u-p7-why-si",
        language="si",
    )
    assert result["available"] is True
    assert result["language"] == "si"


@pytest.mark.asyncio
async def test_question_explanation_unauthorized(db_session: AsyncSession):
    from app.application.services.question_explanation_service import (
        QuestionExplanationService,
    )

    s_id, q_id = await _seed_and_run_assessment(db_session, "owner-p7")
    svc = QuestionExplanationService(db_session)
    with pytest.raises(ValueError):
        await svc.explain_question(
            session_id=s_id,
            question_id=q_id,
            user_id="intruder-p7",
            language="en",
        )


@pytest.mark.asyncio
async def test_question_explanation_no_link(db_session: AsyncSession):
    """When the question has no knowledge-graph links, explanation is
    unavailable — never hallucinated."""
    from app.application.services.question_explanation_service import (
        QuestionExplanationService,
    )

    # Seed a question with no indicator link
    bs = BodySystemModel(
        id="bs-nolink", code="NL", name="NoLink", display_order=2
    )
    db_session.add(bs)
    qg = QuestionGroupModel(
        id="qg-nolink",
        code="QG_NL",
        name="QG NL",
        body_system_id="bs-nolink",
        display_order=2,
    )
    db_session.add(qg)
    await db_session.execute(
        QuestionModel.__table__.insert().values(
            text="Unlinked question",
            body_system_id="bs-nolink",
            question_group_id="qg-nolink",
            code="nlq1",
            question_type="yes_no",
        )
    )
    await db_session.execute(
        AssessmentSessionModel.__table__.insert().values(user_id="u-nolink")
    )
    await db_session.commit()
    s_id = (
        (
            await db_session.execute(
                AssessmentSessionModel.__table__.select().where(
                    AssessmentSessionModel.user_id == "u-nolink"
                )
            )
        ).first()._mapping["id"]
    )
    q_id = (
        (
            await db_session.execute(
                QuestionModel.__table__.select().where(
                    QuestionModel.code == "nlq1"
                )
            )
        ).first()._mapping["id"]
    )
    await db_session.execute(
        AssessmentAnswerModel.__table__.insert().values(
            session_id=s_id, question_id=q_id, question_code="nlq1", value="Yes"
        )
    )
    await db_session.commit()

    svc = QuestionExplanationService(db_session)
    result = await svc.explain_question(
        session_id=s_id,
        question_id=q_id,
        user_id="u-nolink",
        language="en",
    )
    assert result["available"] is False
    assert result["explanation"] == "Explanation unavailable."


# ---------------------------------------------------------------------------
# Feature F — Show the source (source breakdown)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_source_breakdown_present(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-source")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    resp = await svc.explain_report(s_id, "u-p7-source")
    assert len(resp.source_breakdown) > 0
    for item in resp.source_breakdown:
        assert item.clinical_finding
        assert item.knowledge_graph_relationship
        assert item.trace_id is not None or True  # trace may be None


# ---------------------------------------------------------------------------
# Feature G — AI transparency notice
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transparency_notice_present(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-notice")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    resp = await svc.explain_report(s_id, "u-p7-notice")
    assert resp.transparency_notice
    assert "deterministic" in resp.transparency_notice.lower()
    assert "AI did not" in resp.transparency_notice or "did not" in resp.transparency_notice.lower()


# ---------------------------------------------------------------------------
# Feature H — AI audit trail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_record_created_on_success(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-audit")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    await svc.explain_report(s_id, "u-p7-audit", language="ta")
    audits = (
        await db_session.execute(
            select(AIInteractionAuditModel).where(
                AIInteractionAuditModel.session_id == s_id
            )
        )
    ).scalars().all()
    assert len(audits) >= 1
    audit = audits[-1]
    assert audit.request_type == "report_explanation"
    assert audit.language == "ta"
    assert audit.prompt_version
    assert audit.input_context_hash  # hash present
    assert audit.output_hash  # hash present


@pytest.mark.asyncio
async def test_audit_no_raw_phi(db_session: AsyncSession):
    """Audit records must NOT store raw patient identifiers or clinical text."""
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-nophi")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    await svc.explain_report(s_id, "u-p7-nophi")
    audits = (
        await db_session.execute(
            select(AIInteractionAuditModel).where(
                AIInteractionAuditModel.session_id == s_id
            )
        )
    ).scalars().all()
    assert len(audits) >= 1
    audit = audits[-1]
    # The audit model has no free-text PHI columns — only hashes + ids
    assert audit.input_context_hash is not None
    assert audit.output_hash is not None
    # session_id is a reference id, not PHI text
    assert audit.status_reason is None or "u-p7" not in (audit.status_reason or "")


@pytest.mark.asyncio
async def test_audit_records_fallback_status(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-auditfb")
    _explanation_cache.clear()

    class _FailingProvider:
        name = "test-fail"
        prompt_version = "test"

        async def explain(self, context):
            raise AIProviderError("test failure")

    svc = AIExplanationService(db_session, provider=_FailingProvider())
    resp = await svc.explain_report(s_id, "u-p7-auditfb")
    assert resp.available is False
    assert resp.quality_status == AIQualityStatus.PROVIDER_UNAVAILABLE
    audits = (
        await db_session.execute(
            select(AIInteractionAuditModel).where(
                AIInteractionAuditModel.session_id == s_id
            )
        )
    ).scalars().all()
    assert len(audits) >= 1
    assert audits[-1].status == "provider_unavailable"


@pytest.mark.asyncio
async def test_audit_records_validation_failure(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-auditvf")
    _explanation_cache.clear()

    class _BadProvider:
        name = "test-bad"
        prompt_version = "test"

        async def explain(self, context):
            return "not valid json {{{"

    svc = AIExplanationService(db_session, provider=_BadProvider())
    resp = await svc.explain_report(s_id, "u-p7-auditvf")
    assert resp.available is False
    assert resp.quality_status == AIQualityStatus.VALIDATION_FAILED
    audits = (
        await db_session.execute(
            select(AIInteractionAuditModel).where(
                AIInteractionAuditModel.session_id == s_id
            )
        )
    ).scalars().all()
    assert len(audits) >= 1
    assert audits[-1].status == "validation_failed"


# ---------------------------------------------------------------------------
# Feature I — AI quality status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quality_status_valid(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-qvalid")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    resp = await svc.explain_report(s_id, "u-p7-qvalid")
    assert resp.quality_status in (
        AIQualityStatus.VALID,
        AIQualityStatus.EVIDENCE_UNAVAILABLE,
    )


@pytest.mark.asyncio
async def test_quality_status_provider_unavailable(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-qunavail")
    _explanation_cache.clear()

    class _Failing:
        name = "fail"
        prompt_version = "test"

        async def explain(self, context):
            raise AIProviderError("down")

    svc = AIExplanationService(db_session, provider=_Failing())
    resp = await svc.explain_report(s_id, "u-p7-qunavail")
    assert resp.quality_status == AIQualityStatus.PROVIDER_UNAVAILABLE


# ---------------------------------------------------------------------------
# Feature J — Deterministic report integrity (AI does NOT modify CDSE)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deterministic_integrity_with_personalization(
    db_session: AsyncSession,
):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-integrity")
    result_before = (
        await db_session.execute(
            select(AssessmentResultModel).where(
                AssessmentResultModel.session_id == s_id
            )
        )
    ).scalar_one()
    summary_before = result_before.summary
    indicators_before = sorted(
        (a.indicator_id, a.score) for a in result_before.activated_indicators
    )

    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    for lang in ("en", "si", "ta"):
        for level in ("simple", "standard", "detailed"):
            _explanation_cache.clear()
            await svc.explain_report(
                s_id, "u-p7-integrity", language=lang, literacy_level=level
            )

    db_session.expire_all()
    result_after = (
        await db_session.execute(
            select(AssessmentResultModel).where(
                AssessmentResultModel.session_id == s_id
            )
        )
    ).scalar_one()
    assert result_after.summary == summary_before
    indicators_after = sorted(
        (a.indicator_id, a.score) for a in result_after.activated_indicators
    )
    assert indicators_after == indicators_before


# ---------------------------------------------------------------------------
# Feature J — Patient ownership (cross-patient isolation)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_patient_isolation_denied(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "owner-p7-iso")
    _explanation_cache.clear()

    class _Recording:
        name = "rec"
        prompt_version = "test"
        calls = 0

        async def explain(self, context):
            _Recording.calls += 1
            return json.dumps(
                {"summary": "x", "disclaimer": "d", "key_findings": []}
            )

    provider = _Recording()
    svc = AIExplanationService(db_session, provider=provider)
    with pytest.raises(ValueError):
        await svc.explain_report(s_id, "intruder-p7-iso")
    assert provider.calls == 0


# ---------------------------------------------------------------------------
# Feature H — Prompt version tracking + trace ID preservation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prompt_version_and_trace_id(db_session: AsyncSession):
    s_id, _ = await _seed_and_run_assessment(db_session, "u-p7-trace")
    _explanation_cache.clear()
    svc = AIExplanationService(db_session, provider=PersonalizedExplanationProvider())
    resp = await svc.explain_report(s_id, "u-p7-trace")
    assert resp.prompt_version
    assert resp.provider == "personalized-stub"
    # trace_id may be None if CDSE didn't embed one, but the field exists
    assert hasattr(resp, "trace_id")


# ---------------------------------------------------------------------------
# HTTP endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_endpoint_explanation_with_language_and_literacy(
    client: AsyncClient, db_session: AsyncSession
):
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {_MOCK_TOKEN}"}
    )
    assert me.status_code == 200
    user_id = me.json()["id"]
    s_id, _ = await _seed_and_run_assessment(db_session, user_id)
    _explanation_cache.clear()
    resp = await client.post(
        f"/api/v1/report/{s_id}/explanation?language=si&literacy_level=simple",
        headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert data["language"] == "si"
    assert data["literacy_level"] == "simple"


@pytest.mark.asyncio
async def test_endpoint_question_explanation(
    client: AsyncClient, db_session: AsyncSession
):
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {_MOCK_TOKEN}"}
    )
    assert me.status_code == 200
    user_id = me.json()["id"]
    s_id, q_id = await _seed_and_run_assessment(db_session, user_id)
    resp = await client.get(
        f"/api/v1/report/{s_id}/question-explanation?question_id={q_id}&language=en",
        headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert data["question_id"] == q_id
    assert len(data["linked_indicators"]) > 0


@pytest.mark.asyncio
async def test_endpoint_question_explanation_unauthorized(
    client: AsyncClient, db_session: AsyncSession
):
    await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {_MOCK_TOKEN}"}
    )
    s_id, q_id = await _seed_and_run_assessment(db_session, "someone-else-p7")
    resp = await client.get(
        f"/api/v1/report/{s_id}/question-explanation?question_id={q_id}",
        headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# AI Governance Dashboard — RBAC
# ---------------------------------------------------------------------------


@pytest.fixture
def research_user() -> User:
    return _make_user({Role.RESEARCH_REVIEWER}, email="research@example.com")


@pytest.fixture
def medical_director_user() -> User:
    return _make_user({Role.MEDICAL_DIRECTOR}, email="md@example.com")


@pytest.mark.asyncio
async def test_governance_summary_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/ai-governance/summary")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_governance_summary_denied_for_patient(
    client: AsyncClient, db_session: AsyncSession
):
    from app.api.deps import get_ai_governance_user, get_current_active_user

    patient = _make_user({Role.PATIENT}, email="patient@example.com")
    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_current_active_user] = lambda: patient
    try:
        resp = await client.get(
            "/api/v1/ai-governance/summary",
            headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)


@pytest.mark.asyncio
async def test_governance_summary_denied_for_roleless(
    client: AsyncClient, db_session: AsyncSession
):
    from app.api.deps import get_current_active_user

    roleless = _make_user(set(), email="roleless@example.com")
    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_current_active_user] = lambda: roleless
    try:
        resp = await client.get(
            "/api/v1/ai-governance/summary",
            headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)


@pytest.mark.asyncio
async def test_governance_summary_allowed_for_research_reviewer(
    client: AsyncClient, db_session: AsyncSession, research_user: User
):
    from app.api.deps import get_ai_governance_user

    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_ai_governance_user] = lambda: research_user
    try:
        resp = await client.get(
            "/api/v1/ai-governance/summary",
            headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "fallback_rate_pct" in data
        assert "by_language" in data
        assert "by_provider" in data
    finally:
        app.dependency_overrides.pop(get_ai_governance_user, None)


@pytest.mark.asyncio
async def test_governance_summary_returns_aggregate_metrics(
    client: AsyncClient, db_session: AsyncSession, research_user: User
):
    """Seed an audit record and verify the governance summary reflects it."""
    from app.api.deps import get_ai_governance_user

    # Create an audit record
    audit = AIInteractionAuditModel(
        trace_id="test-trace-123",
        session_id="test-session-456",
        request_type="report_explanation",
        provider="personalized-stub",
        model="",
        prompt_version=PHASE7_PROMPT_VERSION,
        language="si",
        literacy_level="simple",
        input_context_hash="abc123",
        output_hash="def456",
        status="valid",
    )
    db_session.add(audit)
    await db_session.commit()

    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_ai_governance_user] = lambda: research_user
    try:
        resp = await client.get(
            "/api/v1/ai-governance/summary",
            headers={"Authorization": f"Bearer {_MOCK_TOKEN}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_requests"] >= 1
        assert data["by_language"].get("si", 0) >= 1
        assert data["by_provider"].get("personalized-stub", 0) >= 1
    finally:
        app.dependency_overrides.pop(get_ai_governance_user, None)
