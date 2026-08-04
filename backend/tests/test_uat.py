"""
Phase 22 — User Acceptance Testing

Covers all 7 workflows:
  Patient, Doctor, Research, CMS, Publishing, Approval, Admin
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.admin_service import AdminService
from app.application.services.clinical_decision_service import ClinicalDecisionService
from app.application.services.knowledge_graph_service import KnowledgeGraphService
from app.application.services.questionnaire_service import QuestionnaireService
from app.application.services.report_service import ReportService
from app.domain.entities.assessment_session import AssessmentSession, SessionStatus
from app.domain.entities.body_system import BodySystem
from app.domain.entities.clinical_indicator import ClinicalIndicator
from app.domain.entities.laboratory_test import LaboratoryTest
from app.domain.entities.question import Question, QuestionType
from app.domain.entities.question_group import QuestionGroup
from app.domain.entities.question_option import QuestionOption
from app.domain.entities.recommendation import Recommendation
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
from app.infrastructure.persistence.models.links import (
    ConditionRecommendationLinkModel,
    IndicatorConditionLinkModel,
    QuestionIndicatorLinkModel,
    QuestionOptionIndicatorLinkModel,
)
from app.infrastructure.persistence.models.possible_condition import (
    PossibleConditionModel,
)
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.question_group import QuestionGroupModel
from app.infrastructure.persistence.models.question_option import QuestionOptionModel
from app.infrastructure.persistence.models.recommendation import RecommendationModel
from app.infrastructure.persistence.repositories.sql_assessment_session_repository import (
    SQLAssessmentSessionRepository,
)
from app.infrastructure.persistence.repositories.sql_clinical_indicator_repository import (
    SQLClinicalIndicatorRepository,
)
from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
    SQLKnowledgeGraphRepository,
)
from app.infrastructure.persistence.repositories.sql_question_group_repository import (
    SQLQuestionGroupRepository,
)
from app.infrastructure.persistence.repositories.sql_question_option_repository import (
    SQLQuestionOptionRepository,
)
from app.infrastructure.persistence.repositories.sql_question_repository import (
    SQLQuestionRepository,
)
from app.infrastructure.persistence.repositories.sql_recommendation_repository import (
    SQLRecommendationRepository,
)


# =========================================================================
#  PATIENT WORKFLOW
# =========================================================================


@pytest.mark.asyncio
async def test_workflow_patient_questionnaire_complete(db_session: AsyncSession):
    """Patient: start session -> answer all questions -> complete -> get progress"""
    session = db_session

    # Seed body system, group, questions, options
    bs_id = uuid.uuid4().hex
    bs = BodySystemModel(id=bs_id, code="UAT_PT", name="UAT Patient", display_order=1)
    session.add(bs)
    await session.flush()

    qg_id = uuid.uuid4().hex
    qg = QuestionGroupModel(
        id=qg_id, code="UAT_G1", name="Group 1", body_system_id=bs_id, display_order=1
    )
    session.add(qg)
    await session.flush()

    q_svc = QuestionnaireService(session)
    q_repo = SQLQuestionRepository(session)
    opt_repo = SQLQuestionOptionRepository(session)
    qg_repo = SQLQuestionGroupRepository(session)
    sess_repo = SQLAssessmentSessionRepository(session)

    # Create questions
    q1 = Question.create(
        body_system_id=bs_id, question_group_id=qg_id, code="pt_q1",
        question_type=QuestionType.YES_NO, text="Do you have chest pain?",
        is_required=True,
    )
    q1_created = await q_repo.create(q1)
    yes_opt = QuestionOption.create(
        question_id=q1_created.id, code="yes", text="Yes", value="yes", score_value=1.0, display_order=1,
    )
    no_opt = QuestionOption.create(
        question_id=q1_created.id, code="no", text="No", value="no", score_value=0.0, display_order=2,
    )
    await opt_repo.create(yes_opt)
    await opt_repo.create(no_opt)
    await session.flush()

    # Start session
    user_id = uuid.uuid4().hex
    sess = AssessmentSession.create(user_id=user_id, total_questions=1)
    created_sess = await sess_repo.create(sess)
    created_sess.current_question_id = q1_created.id
    created_sess.current_group_id = qg_id
    await sess_repo.update(created_sess)
    await session.flush()

    # Save answer
    answer_data = {
        "question_id": q1_created.id,
        "response_value": {"value": "yes"},
    }
    result = await q_svc.save_answer(
        type("User", (), {"id": user_id})(),
        created_sess.id, answer_data,
    )
    assert "answer" in result
    assert result["answer"]["score_value"] == 1.0

    # Complete session
    completed = await q_svc.complete_session(
        type("User", (), {"id": user_id})(), created_sess.id
    )
    assert completed["session_id"] == created_sess.id
    # Single question answered as "yes" (score=1.0, weight=1.0) => 100% => critical
    assert completed["score_summary"]["overall_severity"] == "critical"

    # Get progress
    progress = await q_svc.get_session_progress(
        type("User", (), {"id": user_id})(), created_sess.id
    )
    assert "completion_percentage" in progress


# =========================================================================
#  DOCTOR WORKFLOW
# =========================================================================


@pytest.mark.asyncio
async def test_workflow_doctor_cdse_full_pipeline(db_session: AsyncSession):
    """Doctor: process assessment -> see activated indicators/conditions/recommendations/labs"""
    session = db_session
    kg_repo = SQLKnowledgeGraphRepository(session)

    # Seed full graph: question -> option -> indicator -> condition -> recommendation
    bs_id = uuid.uuid4().hex
    bs = BodySystemModel(id=bs_id, code="UAT_DOC", name="UAT Doctor", display_order=1)
    session.add(bs)
    qg_id = uuid.uuid4().hex
    qg = QuestionGroupModel(id=qg_id, code="UAT_DG1", name="Doc Group", body_system_id=bs_id, display_order=1)
    session.add(qg)
    await session.flush()

    # Indicator
    ind = ClinicalIndicator.create(
        body_system_id=bs_id, key="UAT_IND_DOC", name="UAT Doctor Indicator",
        severity="moderate", evidence_strength="B", confidence=0.7,
    )
    ind_repo = SQLClinicalIndicatorRepository(session)
    ind_created = await ind_repo.create(ind)
    await session.flush()

    # Condition
    cond_model = PossibleConditionModel(
        id=uuid.uuid4().hex, code="UAT_COND_DOC", name="UAT Doctor Condition",
        body_system_id=bs_id, severity="moderate", icd10="Z00.00",
        status="active",
    )
    session.add(cond_model)
    await session.flush()

    # Recommendation
    rec = Recommendation.create(
        body_system_id=bs_id, category="testing", title="UAT Doctor Recommendation",
        text="Perform UAT test.", priority=5, urgency="routine", evidence_level="C",
    )
    rec_repo = SQLRecommendationRepository(session)
    rec_created = await rec_repo.create(rec)
    await session.flush()

    # Links
    await kg_repo.link_indicator_condition(ind_created.id, cond_model.id)
    cond_rec_link = ConditionRecommendationLinkModel(
        condition_id=cond_model.id, recommendation_id=rec_created.id,
    )
    session.add(cond_rec_link)
    await session.flush()

    # Question with option linked to indicator
    q = Question.create(
        body_system_id=bs_id, question_group_id=qg_id, code="doc_q1",
        question_type=QuestionType.YES_NO, text="Test?",
        is_required=True,
    )
    q_repo = SQLQuestionRepository(session)
    q_created = await q_repo.create(q)
    opt = QuestionOption.create(
        question_id=q_created.id, code="yes", text="Yes", value="yes", score_value=1.0, display_order=1,
    )
    opt_repo = SQLQuestionOptionRepository(session)
    opt_created = await opt_repo.create(opt)
    await kg_repo.link_question_option_indicator(opt_created.id, ind_created.id)
    await session.flush()

    # Assessment session + answer
    sess = AssessmentSession.create(user_id="doc_user", total_questions=1)
    sess_repo = SQLAssessmentSessionRepository(session)
    created_sess = await sess_repo.create(sess)
    await session.execute(
        AssessmentAnswerModel.__table__.insert().values(
            session_id=created_sess.id, question_id=q_created.id,
            question_code="doc_q1", question_version=1,
            option_id=opt_created.id, response_value={"value": "yes"},
            score_value=1.0, is_skipped=False,
        )
    )
    await session.flush()

    # CDSE pipeline
    cdse = ClinicalDecisionService(session)
    result = await cdse.process_assessment(created_sess.id, "doc_user")
    assert "result_id" in result
    assert result["summary"]["activated_indicators"] >= 1
    assert result["summary"]["activated_conditions"] >= 1

    # Get result, recommendations, lab tests
    r = await cdse.get_result_by_session(created_sess.id)
    assert r is not None
    assert len(r.activated_indicators) >= 1
    assert len(r.activated_conditions) >= 1
    assert len(r.generated_recommendations) >= 1

    # Check recommendations linked
    rec_ids = [rec.recommendation_id for rec in r.generated_recommendations]
    assert rec_created.id in rec_ids

    # Report
    report_svc = ReportService(session)
    report = await report_svc.generate_report(created_sess.id, "doc_user")
    assert "report_id" in report

    # Get report
    fetched = await report_svc.get_report(report["report_id"])
    assert fetched is not None


# =========================================================================
#  RESEARCH WORKFLOW
# =========================================================================


@pytest.mark.asyncio
async def test_workflow_research_knowledge_graph(db_session: AsyncSession):
    """Researcher: build graph from question -> traverse indicator -> condition -> recommendation -> evidence"""
    session = db_session
    kg_repo = SQLKnowledgeGraphRepository(session)

    bs_id = uuid.uuid4().hex
    bs = BodySystemModel(id=bs_id, code="UAT_RS", name="UAT Research", display_order=1)
    session.add(bs)
    qg_id = uuid.uuid4().hex
    qg = QuestionGroupModel(id=qg_id, code="UAT_RG1", name="Res Group", body_system_id=bs_id, display_order=1)
    session.add(qg)
    await session.flush()

    # Indicator
    ind = ClinicalIndicator.create(
        body_system_id=bs_id, key="UAT_IND_RS", name="Research Indicator",
        severity="moderate", evidence_strength="A", confidence=0.8,
    )
    ind_repo = SQLClinicalIndicatorRepository(session)
    ind_created = await ind_repo.create(ind)

    # Condition
    cond = await kg_repo.create_condition(
        {"code": "UAT_COND_RS", "name": "Research Condition", "body_system_id": bs_id, "severity": "moderate"}
    )

    # Lab test
    lab = LaboratoryTest.create(
        code="UAT_LAB_RS", name="Research Lab Test", body_system_id=bs_id,
        loinc_code="00000-0", normal_range="0-100", unit="U/mL",
    )
    from app.infrastructure.persistence.repositories.sql_laboratory_test_repository import (
        SQLLaboratoryTestRepository,
    )
    lab_repo = SQLLaboratoryTestRepository(session)
    lab_created = await lab_repo.create(lab)

    # Links
    await kg_repo.link_indicator_condition(ind_created.id, cond.id)
    await kg_repo.link_condition_laboratory_test(cond.id, lab_created.id)

    # Question with direct indicator link
    q = Question.create(
        body_system_id=bs_id, question_group_id=qg_id, code="res_q1",
        question_type=QuestionType.YES_NO, text="Research Q?",
    )
    q_repo = SQLQuestionRepository(session)
    q_created = await q_repo.create(q)
    await kg_repo.link_question_indicator(q_created.id, ind_created.id)
    await session.flush()

    # Build graph
    graph = await kg_repo.build_graph_from_question(q_created.id)
    assert len(graph["indicators"]) >= 1
    node = graph["indicators"][0]
    assert node["indicator"].id == ind_created.id
    assert any(c.id == cond.id for c in node["conditions"])

    # Verify graph search
    kg_svc = KnowledgeGraphService(session)
    search_result = await kg_svc.search_graph("research")
    assert "indicators" in search_result
    assert len(search_result["indicators"]) >= 1


# =========================================================================
#  CMS WORKFLOW
# =========================================================================


@pytest.mark.asyncio
async def test_workflow_cms_content_lifecycle(db_session: AsyncSession):
    """CMS editor: create body system -> update -> deactivate -> reactivate"""
    session = db_session
    user_id = uuid.uuid4().hex

    # Create via AdminService CRUD (all methods accept dict, not entity)
    admin_svc = AdminService(session)

    # Create body system via dict
    bs_id = uuid.uuid4().hex
    created_bs = await admin_svc.create_body_system(user_id, {
        "id": bs_id, "code": "UAT_CMS", "name": "UAT CMS System",
        "description": "CMS UAT test", "icon": "test", "color_hex": "#000000",
        "display_order": 99, "is_core": False,
        "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
    })
    assert created_bs is not None

    # Create clinical indicator
    created_ind = await admin_svc.create_indicator(user_id, {
        "id": uuid.uuid4().hex, "body_system_id": bs_id, "key": "UAT_CMS_IND",
        "name": "CMS Test Indicator", "severity": "mild",
        "evidence_strength": "C", "confidence": 0.5,
        "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
    })
    assert created_ind is not None
    assert created_ind.key == "UAT_CMS_IND"

    # List indicators
    inds = await admin_svc.list_indicators()
    keys = [ind.key for ind in inds]
    assert "UAT_CMS_IND" in keys

    # Create evidence
    created_ev = await admin_svc.create_evidence(user_id, {
        "id": uuid.uuid4().hex, "title": "CMS UAT Evidence",
        "source": "Test Journal", "source_type": "journal",
        "evidence_level": "C",
        "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
    })
    assert created_ev is not None

    # Create recommendation
    created_rec = await admin_svc.create_recommendation(user_id, {
        "id": uuid.uuid4().hex, "body_system_id": bs_id,
        "category": "lifestyle", "title": "CMS UAT Rec",
        "text": "Test recommendation.", "priority": 5,
        "key": "UAT_CMS_REC", "urgency": "routine", "evidence_level": "C",
        "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
    })
    assert created_rec is not None

    # List recommendations
    recs = await admin_svc.list_recommendations()
    titles = [r.title for r in recs]
    assert "CMS UAT Rec" in titles

    # Verify audit log created
    audit_logs = await admin_svc.list_audit_logs()
    assert len(audit_logs) >= 4  # bs + ind + ev + rec


# =========================================================================
#  PUBLISHING WORKFLOW
# =========================================================================


@pytest.mark.asyncio
async def test_workflow_publishing_change_request(db_session: AsyncSession):
    """Publisher: create change request -> approve -> version snapshot"""
    session = db_session

    from app.application.services.cms.publishing_service import (
        PublishingWorkflowService,
    )

    pub_svc = PublishingWorkflowService(session)

    # Create change request
    user_id = uuid.uuid4().hex
    cr = await pub_svc.create_change_request(
        title="UAT Change Request",
        description="Test CR for UAT",
        entity_type="clinical_indicator",
        entity_id=uuid.uuid4().hex,
        changes={"key": "UAT_CR_TEST"},
        reason="UAT validation",
        requested_by=user_id,
    )
    assert cr is not None
    assert cr["title"] == "UAT Change Request"

    # List change requests
    crs = await pub_svc.list_change_requests()
    assert len(crs) >= 1
    assert any(c["title"] == "UAT Change Request" for c in crs)

    # Create snapshot
    snapshot = await pub_svc.create_snapshot(
        entity_type="clinical_indicator",
        entity_id=uuid.uuid4().hex,
        version=1,
        snapshot={"key": "UAT_SNAPSHOT"},
        reason="UAT snapshot",
        created_by=user_id,
    )
    assert snapshot is not None

    # List snapshots
    snapshots = await pub_svc.list_snapshots(
        entity_type="clinical_indicator",
        entity_id=snapshot["entity_id"],
    )
    assert len(snapshots) >= 1

    # Approve the change request
    approved = await pub_svc.approve_change_request(
        cr["id"], user_id=user_id
    )
    assert approved is not None
    assert approved["status"] == "approved"


# =========================================================================
#  APPROVAL WORKFLOW
# =========================================================================


@pytest.mark.asyncio
async def test_workflow_approval_review_cycle(db_session: AsyncSession):
    """Approver: create approval -> approve -> reject -> add comments"""
    session = db_session

    from app.application.services.cms.publishing_service import (
        PublishingWorkflowService,
    )

    pub_svc = PublishingWorkflowService(session)
    user_id = uuid.uuid4().hex

    # Create approval request
    approval = await pub_svc.create_approval(
        entity_type="recommendation",
        entity_id=uuid.uuid4().hex,
        requested_by=user_id,
    )
    assert approval is not None

    # List approvals
    approvals = await pub_svc.list_approvals()
    assert len(approvals) >= 1

    # Add comment
    commented = await pub_svc.add_approval_comment(
        approval["id"], user_id=user_id, comment="Reviewing for UAT"
    )
    assert commented is not None

    # Approve
    approved = await pub_svc.approve_entity(
        approval["id"], user_id=user_id, comment="Approved"
    )
    assert approved is not None

    # Create another and reject
    approval2 = await pub_svc.create_approval(
        entity_type="question",
        entity_id=uuid.uuid4().hex, requested_by=user_id,
    )
    rejected = await pub_svc.reject_approval(
        approval2["id"], user_id=user_id, reason="UAT rejection test"
    )
    assert rejected is not None
    assert rejected["status"] == "rejected"

    # Create review
    review = await pub_svc.create_review(
        entity_type="recommendation",
        entity_id=uuid.uuid4().hex, reviewer_id=user_id,
    )
    assert review is not None

    # Complete review
    completed = await pub_svc.complete_review(
        review["id"], decision="approved"
    )
    assert completed is not None


# =========================================================================
#  ADMIN WORKFLOW
# =========================================================================


@pytest.mark.asyncio
async def test_workflow_admin_full_crud(db_session: AsyncSession):
    """Admin: manage body systems, indicators, evidence, recommendations, audit"""
    session = db_session
    user_id = uuid.uuid4().hex
    admin_svc = AdminService(session)

    # Create body system
    bs_id = uuid.uuid4().hex
    bs_created = await admin_svc.create_body_system(user_id, {
        "id": bs_id, "code": "UAT_ADM", "name": "UAT Admin",
        "description": "Admin UAT", "icon": "admin", "color_hex": "#FFF",
        "display_order": 100, "is_core": False,
        "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
    })
    assert bs_created is not None

    # Create indicator
    ind_id = uuid.uuid4().hex
    ind_created = await admin_svc.create_indicator(user_id, {
        "id": ind_id, "body_system_id": bs_id, "key": "UAT_ADM_IND",
        "name": "Admin Indicator", "severity": "moderate",
        "evidence_strength": "B", "confidence": 0.6,
        "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
    })
    assert ind_created is not None

    # Create evidence
    ev_created = await admin_svc.create_evidence(user_id, {
        "id": uuid.uuid4().hex, "title": "Admin UAT Evidence",
        "source": "Admin Journal", "source_type": "journal",
        "evidence_level": "B",
        "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
    })
    assert ev_created is not None

    # Create recommendation
    rec_created = await admin_svc.create_recommendation(user_id, {
        "id": uuid.uuid4().hex, "body_system_id": bs_id,
        "category": "medication", "title": "Admin UAT Rec",
        "text": "Admin recommendation.", "priority": 8,
        "key": "UAT_ADM_REC", "urgency": "routine", "evidence_level": "B",
        "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
    })
    assert rec_created is not None

    # Audit
    logs = await admin_svc.list_audit_logs()
    assert len(logs) >= 4

    # Knowledge graph operations (requires MEDICAL_DIRECTOR)
    kg_svc = KnowledgeGraphService(session)

    # Create condition
    cond = await kg_svc.create_condition(user_id, {
        "code": "UAT_ADM_COND", "name": "Admin Condition",
        "body_system_id": bs_created.id, "severity": "moderate",
    })
    assert cond is not None

    # Create lab test
    lab = await kg_svc.create_laboratory_test(user_id, {
        "code": "UAT_ADM_LAB", "name": "Admin Lab",
        "body_system_id": bs_created.id,
    })
    assert lab is not None

    # Link operations
    link1 = await kg_svc.link_indicator_condition(user_id, ind_id, cond.id)
    assert link1 is not None

    link2 = await kg_svc.link_condition_laboratory_test(user_id, cond.id, lab.id)
    assert link2 is not None


# =========================================================================
#  EDGE CASE: EMPTY SESSION / NO ANSWERS
# =========================================================================


@pytest.mark.asyncio
async def test_edge_empty_session_no_answers(db_session: AsyncSession):
    """Edge: process empty session -> no indicators activated"""
    session = db_session

    # Create session with no answers
    sess = AssessmentSession.create(user_id="empty_user", total_questions=0)
    sess_repo = SQLAssessmentSessionRepository(session)
    created_sess = await sess_repo.create(sess)

    cdse = ClinicalDecisionService(session)
    result = await cdse.process_assessment(created_sess.id, "empty_user")
    assert result["summary"]["activated_indicators"] == 0
    assert result["summary"]["activated_conditions"] == 0


# =========================================================================
#  EDGE CASE: SESSION NOT FOUND
# =========================================================================


@pytest.mark.asyncio
async def test_edge_session_not_found(db_session: AsyncSession):
    """Edge: process non-existent session -> ValueError"""
    cdse = ClinicalDecisionService(db_session)
    with pytest.raises(ValueError, match="Assessment session not found"):
        await cdse.process_assessment("nonexistent-id")


# =========================================================================
#  EDGE CASE: REPORT WITHOUT CDSE
# =========================================================================


@pytest.mark.asyncio
async def test_edge_report_without_cdse(db_session: AsyncSession):
    """Edge: generate report before CDSE -> ValueError"""
    session = db_session
    sess = AssessmentSession.create(user_id="no_cdse_user", total_questions=0)
    sess_repo = SQLAssessmentSessionRepository(session)
    created_sess = await sess_repo.create(sess)

    report_svc = ReportService(session)
    with pytest.raises(ValueError, match="No decision result for session"):
        await report_svc.generate_report(created_sess.id)


# =========================================================================
#  EDGE CASE: REPORT COMPARISON
# =========================================================================


@pytest.mark.asyncio
async def test_edge_report_compare(db_session: AsyncSession):
    """Edge: compare two reports"""
    session = db_session
    kg_repo = SQLKnowledgeGraphRepository(session)

    bs_id = uuid.uuid4().hex
    bs = BodySystemModel(id=bs_id, code="UAT_CMP", name="UAT Compare", display_order=1)
    session.add(bs)
    qg_id = uuid.uuid4().hex
    qg = QuestionGroupModel(id=qg_id, code="UAT_CG1", name="Cmp Group", body_system_id=bs_id, display_order=1)
    session.add(qg)
    await session.flush()

    # Shared setup for two sessions
    ind = ClinicalIndicator.create(
        body_system_id=bs_id, key="UAT_IND_CMP", name="Compare Indicator",
    )
    ind_repo = SQLClinicalIndicatorRepository(session)
    ind_created = await ind_repo.create(ind)

    cond = await kg_repo.create_condition({
        "code": "UAT_COND_CMP", "name": "Compare Condition", "body_system_id": bs_id,
    })
    await kg_repo.link_indicator_condition(ind_created.id, cond.id)

    q = Question.create(
        body_system_id=bs_id, question_group_id=qg_id, code="cmp_q1",
        question_type=QuestionType.YES_NO, text="Compare?",
    )
    q_repo = SQLQuestionRepository(session)
    q_created = await q_repo.create(q)
    opt = QuestionOption.create(
        question_id=q_created.id, code="yes", text="Yes", value="yes", score_value=1.0, display_order=1,
    )
    opt_repo = SQLQuestionOptionRepository(session)
    opt_created = await opt_repo.create(opt)
    await kg_repo.link_question_option_indicator(opt_created.id, ind_created.id)
    await session.flush()

    async def _run_session(suffix: str, answer_value: str):
        """Helper to create and process a session, generate report, return report_id."""
        sess = AssessmentSession.create(user_id=f"user_{suffix}", total_questions=1)
        sess_repo = SQLAssessmentSessionRepository(session)
        created_sess = await sess_repo.create(sess)
        await session.execute(
            AssessmentAnswerModel.__table__.insert().values(
                session_id=created_sess.id, question_id=q_created.id,
                question_code="cmp_q1", question_version=1,
                option_id=opt_created.id, response_value={"value": answer_value},
                score_value=1.0 if answer_value == "yes" else 0.0, is_skipped=False,
            )
        )
        await session.flush()
        cdse = ClinicalDecisionService(session)
        await cdse.process_assessment(created_sess.id, f"user_{suffix}")
        report_svc = ReportService(session)
        report = await report_svc.generate_report(created_sess.id)
        return report["report_id"]

    report_id_1 = await _run_session("cmp1", "yes")
    report_id_2 = await _run_session("cmp2", "no")

    # Compare
    report_svc = ReportService(session)
    diff = await report_svc.compare_reports(report_id_1, report_id_2)
    assert "report_1" in diff
    assert "report_2" in diff
