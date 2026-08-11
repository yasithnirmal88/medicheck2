from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.cms.audit import router as cms_audit_router
from app.api.v1.cms.builder import router as cms_builder_router
from app.api.v1.cms.content import router as cms_content_router
from app.api.v1.cms.dashboard import router as cms_dashboard_router
from app.api.v1.cms.evidence import router as cms_evidence_router
from app.api.v1.cms.knowledge_graph import router as cms_kg_router
from app.api.v1.cms.publishing import router as cms_publishing_router
from app.api.v1.cms.questions import router as cms_router
from app.api.v1.cms.rules import router as cms_rules_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.ai_governance import router as ai_governance_router
from app.api.v1.endpoints.ai_intake import router as ai_intake_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.assessments import router as assessments_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.cdse import router as cdse_router
from app.api.v1.endpoints.chw import router as chw_router
from app.api.v1.endpoints.graph import router as graph_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.profile import router as profile_router
from app.api.v1.endpoints.questionnaires import router as questionnaires_router
from app.api.v1.endpoints.questions import router as questions_router
from app.api.v1.endpoints.report import router as report_router
from app.api.v1.endpoints.trajectory import router as trajectory_router
from app.api.v1.endpoints.users import router as users_router

router = APIRouter()

router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(profile_router)
router.include_router(questionnaires_router)
router.include_router(admin_router)
router.include_router(graph_router)
router.include_router(cdse_router)
router.include_router(report_router)
router.include_router(trajectory_router)
router.include_router(questions_router)
router.include_router(assessments_router)
router.include_router(ai_intake_router)
router.include_router(analytics_router)
router.include_router(ai_governance_router)
router.include_router(chw_router)
router.include_router(cms_router)
router.include_router(cms_content_router)
router.include_router(cms_builder_router)
router.include_router(cms_rules_router)
router.include_router(cms_kg_router)
router.include_router(cms_publishing_router)
router.include_router(cms_evidence_router)
router.include_router(cms_audit_router)
router.include_router(cms_dashboard_router)
