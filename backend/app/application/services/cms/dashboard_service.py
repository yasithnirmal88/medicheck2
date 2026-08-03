from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.approval import ApprovalModel
from app.infrastructure.persistence.models.audit_log import AuditLogModel
from app.infrastructure.persistence.models.change_request import ChangeRequestModel
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.disease import DiseaseModel
from app.infrastructure.persistence.models.knowledge_graph import (
    KnowledgeGraphModel,
    KnowledgeGraphNodeModel,
)
from app.infrastructure.persistence.models.publishing_job import PublishingJobModel
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.recommendation import RecommendationModel
from app.infrastructure.persistence.models.review import ReviewModel
from app.infrastructure.persistence.models.symptom import SymptomModel

_ENTITY_MODELS: dict[str, Any] = {
    "questions": QuestionModel,
    "diseases": DiseaseModel,
    "symptoms": SymptomModel,
    "indicators": ClinicalIndicatorModel,
    "recommendations": RecommendationModel,
}


class CMSDashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_overview(self) -> dict[str, Any]:
        totals: dict[str, int] = {}
        for name, model in _ENTITY_MODELS.items():
            count = await self._count_active(model)
            totals[name] = count

        by_status: dict[str, dict[str, int]] = {}
        for name, model in _ENTITY_MODELS.items():
            if hasattr(model, "status"):
                by_status[name] = await self._count_by_status(model)

        kg_count = await self._count_active(KnowledgeGraphModel)
        node_count = await self._count_active(KnowledgeGraphNodeModel)

        pending_approvals = await self._count_by_field(
            ApprovalModel, "status", "pending"
        )
        pending_reviews = await self._count_by_field(
            ReviewModel, "status", "pending"
        )
        pending_jobs = await self._count_by_field(
            PublishingJobModel, "status", "pending"
        )
        approved_jobs = await self._count_by_field(
            PublishingJobModel, "status", "approved"
        )
        pending_changes = await self._count_by_field(
            ChangeRequestModel, "status", "pending"
        )

        recent_activity = await self._count_by_field(
            AuditLogModel, "action", "update"
        )
        total_audit: int = 0
        stmt = select(func.count(AuditLogModel.id)).where(
            AuditLogModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        total_audit = result.scalar() or 0

        return {
            "total_entities": sum(totals.values()),
            "by_type": totals,
            "by_status": by_status,
            "knowledge_graph": {
                "graphs": kg_count,
                "nodes": node_count,
            },
            "workflow_pending": {
                "approvals": pending_approvals,
                "reviews": pending_reviews,
                "publishing_jobs": pending_jobs,
                "approved_jobs": approved_jobs,
                "change_requests": pending_changes,
            },
            "audit": {
                "total_entries": total_audit,
                "recent_updates": recent_activity,
            },
        }

    async def get_recent_activity(
        self, limit: int = 20,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.deleted_at.is_(None))
            .order_by(AuditLogModel.changed_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [
            {
                "id": row.id,
                "actor_id": row.actor_id,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "action": row.action,
                "changed_at": row.changed_at.isoformat() if row.changed_at else None,
                "reason": row.reason,
            }
            for row in result.scalars().all()
        ]

    async def get_workflow_summary(self) -> dict[str, Any]:
        return {
            "approvals": {
                "pending": await self._count_by_field(ApprovalModel, "status", "pending"),
                "approved": await self._count_by_field(ApprovalModel, "status", "approved"),
                "rejected": await self._count_by_field(ApprovalModel, "status", "rejected"),
            },
            "reviews": {
                "pending": await self._count_by_field(ReviewModel, "status", "pending"),
                "completed": await self._count_by_field(ReviewModel, "status", "completed"),
            },
            "jobs": {
                "pending": await self._count_by_field(PublishingJobModel, "status", "pending"),
                "approved": await self._count_by_field(PublishingJobModel, "status", "approved"),
                "published": await self._count_by_field(PublishingJobModel, "status", "published"),
                "failed": await self._count_by_field(PublishingJobModel, "status", "failed"),
                "rolled_back": await self._count_by_field(PublishingJobModel, "status", "rolled_back"),
            },
            "change_requests": {
                "pending": await self._count_by_field(ChangeRequestModel, "status", "pending"),
                "approved": await self._count_by_field(ChangeRequestModel, "status", "approved"),
                "rejected": await self._count_by_field(ChangeRequestModel, "status", "rejected"),
            },
        }

    async def _count_active(self, model: Any) -> int:
        stmt = select(func.count(model.id)).where(model.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def _count_by_field(self, model: Any, field: str, value: Any) -> int:
        col = getattr(model, field, None)
        if col is None:
            return 0
        stmt = (
            select(func.count(model.id))
            .where(col == value, model.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def _count_by_status(self, model: Any) -> dict[str, int]:
        statuses = ["draft", "active", "archived", "pending"]
        counts: dict[str, int] = {}
        col = getattr(model, "status", None)
        if col is None:
            return {}
        for s in statuses:
            stmt = (
                select(func.count(model.id))
                .where(col == s, model.deleted_at.is_(None))
            )
            result = await self._session.execute(stmt)
            count = result.scalar() or 0
            if count > 0:
                counts[s] = count
        return counts
