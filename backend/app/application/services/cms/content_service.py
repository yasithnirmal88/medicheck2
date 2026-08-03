from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.approval import Approval
from app.domain.entities.biomarker import Biomarker
from app.domain.entities.body_system_category import BodySystemCategory
from app.domain.entities.change_request import ChangeRequest
from app.domain.entities.clinical_guideline import ClinicalGuideline
from app.domain.entities.clinical_indicator import ClinicalIndicator
from app.domain.entities.clinical_trial import ClinicalTrial
from app.domain.entities.decision_rule import DecisionRule
from app.domain.entities.disease import Disease
from app.domain.entities.disease_category import DiseaseCategory
from app.domain.entities.evidence_collection import EvidenceCollection
from app.domain.entities.exercise_program import ExerciseProgram
from app.domain.entities.imaging_test import ImagingTest
from app.domain.entities.lab_panel import LabPanel
from app.domain.entities.laboratory_test import LaboratoryTest
from app.domain.entities.lifestyle_advice import LifestyleAdvice
from app.domain.entities.medical_evidence import MedicalEvidence
from app.domain.entities.medical_organization import MedicalOrganization
from app.domain.entities.medical_specialty import MedicalSpecialty
from app.domain.entities.medical_tag import MedicalTag
from app.domain.entities.medication_recommendation import MedicationRecommendation
from app.domain.entities.notifications import Notification
from app.domain.entities.nutrition_advice import NutritionAdvice
from app.domain.entities.publishing_job import PublishingJob
from app.domain.entities.question_category import QuestionCategory
from app.domain.entities.question_tag import QuestionTag
from app.domain.entities.questionnaire_rule_set import QuestionnaireRuleSet
from app.domain.entities.recommendation import Recommendation
from app.domain.entities.recommendation_category import RecommendationCategory
from app.domain.entities.reference_source import ReferenceSource
from app.domain.entities.research_paper import ResearchPaper
from app.domain.entities.review import Review
from app.domain.entities.review_comment import ReviewComment
from app.domain.entities.risk_category import RiskCategory
from app.domain.entities.rule_library import RuleLibrary
from app.domain.entities.scoring_profile import ScoringProfile
from app.domain.entities.severity_threshold import SeverityThreshold
from app.domain.entities.symptom import Symptom
from app.domain.entities.template_library import TemplateLibrary
from app.domain.entities.version_snapshot import VersionSnapshot
from app.domain.entities.workflow import Workflow
from app.infrastructure.persistence.models.approval import ApprovalModel
from app.infrastructure.persistence.models.biomarker import BiomarkerModel
from app.infrastructure.persistence.models.body_system_category import (
    BodySystemCategoryModel,
)
from app.infrastructure.persistence.models.change_request import ChangeRequestModel
from app.infrastructure.persistence.models.clinical_guideline import (
    ClinicalGuidelineModel,
)
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.clinical_trial import ClinicalTrialModel
from app.infrastructure.persistence.models.decision_rule import DecisionRuleModel
from app.infrastructure.persistence.models.disease import DiseaseModel
from app.infrastructure.persistence.models.disease_category import DiseaseCategoryModel
from app.infrastructure.persistence.models.evidence_collection import (
    EvidenceCollectionModel,
)
from app.infrastructure.persistence.models.exercise_program import ExerciseProgramModel
from app.infrastructure.persistence.models.imaging_test import ImagingTestModel
from app.infrastructure.persistence.models.lab_panel import LabPanelModel
from app.infrastructure.persistence.models.laboratory_test import LaboratoryTestModel
from app.infrastructure.persistence.models.lifestyle_advice import LifestyleAdviceModel
from app.infrastructure.persistence.models.medical_evidence import MedicalEvidenceModel
from app.infrastructure.persistence.models.medical_organization import (
    MedicalOrganizationModel,
)
from app.infrastructure.persistence.models.medical_specialty import (
    MedicalSpecialtyModel,
)
from app.infrastructure.persistence.models.medical_tag import MedicalTagModel
from app.infrastructure.persistence.models.medication_recommendation import (
    MedicationRecommendationModel,
)
from app.infrastructure.persistence.models.notification import NotificationModel
from app.infrastructure.persistence.models.nutrition_advice import NutritionAdviceModel
from app.infrastructure.persistence.models.publishing_job import PublishingJobModel
from app.infrastructure.persistence.models.question_category import (
    QuestionCategoryModel,
)
from app.infrastructure.persistence.models.question_tag import QuestionTagModel
from app.infrastructure.persistence.models.questionnaire_rule_set import (
    QuestionnaireRuleSetModel,
)
from app.infrastructure.persistence.models.recommendation import RecommendationModel
from app.infrastructure.persistence.models.recommendation_category import (
    RecommendationCategoryModel,
)
from app.infrastructure.persistence.models.reference_source import ReferenceSourceModel
from app.infrastructure.persistence.models.research_paper import ResearchPaperModel
from app.infrastructure.persistence.models.review import ReviewModel
from app.infrastructure.persistence.models.review_comment import ReviewCommentModel
from app.infrastructure.persistence.models.risk_category import RiskCategoryModel
from app.infrastructure.persistence.models.rule_library import RuleLibraryModel
from app.infrastructure.persistence.models.scoring_profile import ScoringProfileModel
from app.infrastructure.persistence.models.severity_threshold import (
    SeverityThresholdModel,
)
from app.infrastructure.persistence.models.symptom import SymptomModel
from app.infrastructure.persistence.models.template_library import TemplateLibraryModel
from app.infrastructure.persistence.models.version_snapshot import (
    VersionSnapshotModel,
)
from app.infrastructure.persistence.models.workflow import WorkflowModel
from app.infrastructure.persistence.repositories.sql_generic_cms_repository import (
    SQLGenericCMSRepository,
)

# Maps entity_type string -> (domain_entity_class, orm_model_class)
ENTITY_REGISTRY: dict[str, tuple[type, type]] = {
    "disease": (Disease, DiseaseModel),
    "clinical_indicator": (ClinicalIndicator, ClinicalIndicatorModel),
    "symptom": (Symptom, SymptomModel),
    "laboratory_test": (LaboratoryTest, LaboratoryTestModel),
    "imaging_test": (ImagingTest, ImagingTestModel),
    "medical_evidence": (MedicalEvidence, MedicalEvidenceModel),
    "recommendation": (Recommendation, RecommendationModel),
    "lifestyle_advice": (LifestyleAdvice, LifestyleAdviceModel),
    "exercise_program": (ExerciseProgram, ExerciseProgramModel),
    "nutrition_advice": (NutritionAdvice, NutritionAdviceModel),
    "clinical_guideline": (ClinicalGuideline, ClinicalGuidelineModel),
    "medication_recommendation": (MedicationRecommendation, MedicationRecommendationModel),
    "approval": (Approval, ApprovalModel),
    "review": (Review, ReviewModel),
    "publishing_job": (PublishingJob, PublishingJobModel),
    "workflow": (Workflow, WorkflowModel),
    "decision_rule": (DecisionRule, DecisionRuleModel),
    "questionnaire_rule_set": (QuestionnaireRuleSet, QuestionnaireRuleSetModel),
    "scoring_profile": (ScoringProfile, ScoringProfileModel),
    "severity_threshold": (SeverityThreshold, SeverityThresholdModel),
    "risk_category": (RiskCategory, RiskCategoryModel),
    "medical_specialty": (MedicalSpecialty, MedicalSpecialtyModel),
    "medical_tag": (MedicalTag, MedicalTagModel),
    "evidence_collection": (EvidenceCollection, EvidenceCollectionModel),
    "reference_source": (ReferenceSource, ReferenceSourceModel),
    "research_paper": (ResearchPaper, ResearchPaperModel),
    "clinical_trial": (ClinicalTrial, ClinicalTrialModel),
    "medical_organization": (MedicalOrganization, MedicalOrganizationModel),
    "notification": (Notification, NotificationModel),
    "disease_category": (DiseaseCategory, DiseaseCategoryModel),
    "body_system_category": (BodySystemCategory, BodySystemCategoryModel),
    "recommendation_category": (RecommendationCategory, RecommendationCategoryModel),
    "lab_panel": (LabPanel, LabPanelModel),
    "biomarker": (Biomarker, BiomarkerModel),
    "version_snapshot": (VersionSnapshot, VersionSnapshotModel),
    "review_comment": (ReviewComment, ReviewCommentModel),
    "change_request": (ChangeRequest, ChangeRequestModel),
    "rule_library": (RuleLibrary, RuleLibraryModel),
    "template_library": (TemplateLibrary, TemplateLibraryModel),
    "question_category": (QuestionCategory, QuestionCategoryModel),
    "question_tag": (QuestionTag, QuestionTagModel),
}

VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"medical_review", "archived"},
    "medical_review": {"approved", "draft", "archived"},
    "approved": {"published", "draft", "archived"},
    "published": {"archived", "draft"},
    "archived": {"draft"},
}


class CMSContentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repos: dict[str, SQLGenericCMSRepository] = {}

    def _get_repo(self, entity_type: str) -> SQLGenericCMSRepository:
        if entity_type not in self._repos:
            entry = ENTITY_REGISTRY.get(entity_type)
            if entry is None:
                raise ValueError(f"Unknown entity type: {entity_type}")
            _, model_cls = entry
            self._repos[entity_type] = SQLGenericCMSRepository(
                self._session, model_cls
            )
        return self._repos[entity_type]

    def _get_entity_cls(self, entity_type: str) -> type:
        entry = ENTITY_REGISTRY.get(entity_type)
        if entry is None:
            raise ValueError(f"Unknown entity type: {entity_type}")
        return entry[0]

    def _get_model_cls(self, entity_type: str) -> type:
        entry = ENTITY_REGISTRY.get(entity_type)
        if entry is None:
            raise ValueError(f"Unknown entity type: {entity_type}")
        return entry[1]

    async def list_entities(
        self,
        entity_type: str,
        body_system_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        repo = self._get_repo(entity_type)
        model_cls = self._get_model_cls(entity_type)

        if status:
            models = await repo.find_by_status(status, skip=skip, limit=limit)
        elif search:
            name_col = "name" if hasattr(model_cls, "name") else "title"
            models = await repo.search(name_col, search, skip=skip, limit=limit)
        elif body_system_id and hasattr(model_cls, "body_system_id"):
            models = await repo.find_by_body_system(
                body_system_id, skip=skip, limit=limit
            )
        else:
            models = await repo.find_active(skip=skip, limit=limit)

        entity_cls = self._get_entity_cls(entity_type)
        return [entity_cls(**m.to_dict()).to_dict() for m in models]

    async def get_entity(
        self, entity_type: str, entity_id: str
    ) -> dict[str, Any] | None:
        repo = self._get_repo(entity_type)
        model = await repo.find_by_id(entity_id)
        if model is None:
            return None
        entity_cls = self._get_entity_cls(entity_type)
        return entity_cls(**model.to_dict()).to_dict()

    async def create_entity(
        self, entity_type: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        entity_cls = self._get_entity_cls(entity_type)
        model_cls = self._get_model_cls(entity_type)
        repo = self._get_repo(entity_type)

        entity = entity_cls.create(**data, created_by=user_id)
        model = model_cls(**entity.to_dict())
        created = await repo.create(model)

        entity_cls = self._get_entity_cls(entity_type)
        return entity_cls(**created.to_dict()).to_dict()

    async def update_entity(
        self, entity_type: str, entity_id: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        repo = self._get_repo(entity_type)
        model = await repo.find_by_id(entity_id)
        if model is None:
            raise ValueError(f"{entity_type} with id {entity_id} not found")

        for field, value in data.items():
            if hasattr(model, field) and value is not None:
                setattr(model, field, value)

        model.updated_by = user_id
        model.updated_at = datetime.now(UTC)
        if hasattr(model, "version"):
            model.version = (model.version or 0) + 1

        updated = await repo.update(model)
        entity_cls = self._get_entity_cls(entity_type)
        return entity_cls(**updated.to_dict()).to_dict()

    async def delete_entity(
        self, entity_type: str, entity_id: str, user_id: str
    ) -> None:
        repo = self._get_repo(entity_type)
        await repo.soft_delete(entity_id)

    async def restore_entity(
        self, entity_type: str, entity_id: str
    ) -> dict[str, Any]:
        repo = self._get_repo(entity_type)
        model = await repo.restore(entity_id)
        if model is None:
            raise ValueError(f"{entity_type} with id {entity_id} not found")
        entity_cls = self._get_entity_cls(entity_type)
        return entity_cls(**model.to_dict()).to_dict()

    async def update_status(
        self,
        entity_type: str,
        entity_id: str,
        new_status: str,
        user_id: str,
    ) -> dict[str, Any]:
        repo = self._get_repo(entity_type)
        model = await repo.find_by_id(entity_id)
        if model is None:
            raise ValueError(f"{entity_type} with id {entity_id} not found")

        current = model.status
        allowed = VALID_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from {current} to {new_status}. "
                f"Allowed: {allowed}"
            )

        model.status = new_status
        model.updated_by = user_id
        model.updated_at = datetime.now(UTC)

        updated = await repo.update(model)
        entity_cls = self._get_entity_cls(entity_type)
        return entity_cls(**updated.to_dict()).to_dict()

    async def count_entities(
        self, entity_type: str, status: str | None = None
    ) -> int:
        repo = self._get_repo(entity_type)
        if status:
            return await repo.count_by_field("status", status)
        return await repo.count()

    async def search_entities(
        self,
        entity_type: str,
        query: str,
        field: str = "name",
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        repo = self._get_repo(entity_type)
        models = await repo.search(field, query, skip=skip, limit=limit)
        entity_cls = self._get_entity_cls(entity_type)
        return [entity_cls(**m.to_dict()).to_dict() for m in models]

    async def bulk_update_status(
        self, entity_type: str, ids: list[str], status: str
    ) -> int:
        repo = self._get_repo(entity_type)
        return await repo.bulk_update_status(ids, status)

    async def bulk_delete(
        self, entity_type: str, ids: list[str]
    ) -> int:
        repo = self._get_repo(entity_type)
        return await repo.bulk_soft_delete(ids)
