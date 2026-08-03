from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.approval import Approval
from app.domain.entities.change_request import ChangeRequest
from app.domain.entities.review import Review
from app.infrastructure.persistence.models.approval import ApprovalModel
from app.infrastructure.persistence.models.change_request import ChangeRequestModel
from app.infrastructure.persistence.models.publishing_job import PublishingJobModel
from app.infrastructure.persistence.models.review import ReviewModel
from app.infrastructure.persistence.models.version_snapshot import VersionSnapshotModel
from app.infrastructure.persistence.models.workflow import WorkflowModel
from app.infrastructure.persistence.repositories.sql_generic_cms_repository import (
    SQLGenericCMSRepository,
)

ModelT = ApprovalModel | ChangeRequestModel | PublishingJobModel | ReviewModel | VersionSnapshotModel | WorkflowModel


def _model_to_dict(m: ModelT) -> dict[str, Any]:
    return {c.key: getattr(m, c.key) for c in m.__table__.columns}


class PublishingWorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._approval_repo = SQLGenericCMSRepository(session, ApprovalModel)
        self._change_repo = SQLGenericCMSRepository(session, ChangeRequestModel)
        self._job_repo = SQLGenericCMSRepository(session, PublishingJobModel)
        self._review_repo = SQLGenericCMSRepository(session, ReviewModel)
        self._snapshot_repo = SQLGenericCMSRepository(session, VersionSnapshotModel)
        self._workflow_repo = SQLGenericCMSRepository(session, WorkflowModel)

    # --- Workflow Definitions ---

    async def create_workflow(
        self, name: str, entity_type: str,
        steps: list[dict[str, Any]] | None = None,
        description: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        wf = WorkflowModel(
            name=name, entity_type=entity_type,
            steps=steps or [], description=description,
            current_step=0, status="active", is_active=True, version=1,
            created_by=created_by, updated_by=created_by,
        )
        created = await self._workflow_repo.create(wf)
        return _model_to_dict(created)

    async def list_workflows(
        self, entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        if entity_type:
            items = await self._workflow_repo.find_by_field("entity_type", entity_type)
        else:
            items = await self._workflow_repo.find_all()
        return [_model_to_dict(w) for w in items]

    async def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        wf = await self._workflow_repo.find_by_id(workflow_id)
        return _model_to_dict(wf) if wf else None

    async def update_workflow(
        self, workflow_id: str, data: dict[str, Any],
    ) -> dict[str, Any]:
        wf = await self._workflow_repo.find_by_id(workflow_id)
        if wf is None:
            raise ValueError(f"Workflow {workflow_id} not found")
        for field in ("name", "description", "steps", "status", "current_step"):
            if field in data and data[field] is not None:
                setattr(wf, field, data[field])
        wf.updated_at = datetime.now(UTC)
        updated = await self._workflow_repo.update(wf)
        return _model_to_dict(updated)

    # --- Publishing Jobs ---

    async def create_job(
        self, entity_type: str, entity_id: str, version: int,
        requested_by: str, schedule_at: datetime | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        job = PublishingJobModel(
            entity_type=entity_type, entity_id=entity_id,
            version=version, requested_by=requested_by,
            status="pending", schedule_at=schedule_at, notes=notes,
            is_active=True, created_by=requested_by, updated_by=requested_by,
        )
        created = await self._job_repo.create(job)
        return _model_to_dict(created)

    async def list_jobs(
        self, status: str | None = None, entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        if status:
            items = await self._job_repo.find_by_field("status", status)
        elif entity_type:
            items = await self._job_repo.find_by_field("entity_type", entity_type)
        else:
            items = await self._job_repo.find_all()
        return [_model_to_dict(j) for j in items]

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        job = await self._job_repo.find_by_id(job_id)
        return _model_to_dict(job) if job else None

    async def approve_job(self, job_id: str, user_id: str) -> dict[str, Any]:
        job = await self._job_repo.find_by_id(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        job.approved_by = user_id
        job.status = "approved"
        job.updated_at = datetime.now(UTC)
        updated = await self._job_repo.update(job)
        return _model_to_dict(updated)

    async def execute_publish(self, job_id: str) -> dict[str, Any]:
        job = await self._job_repo.find_by_id(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        if job.status != "approved":
            raise ValueError(f"Job {job_id} is not approved (status: {job.status})")

        snapshot = VersionSnapshotModel(
            entity_type=job.entity_type, entity_id=job.entity_id,
            version=job.version, snapshot={},
            snapshot_type="publish", reason="Published via job",
            created_by=job.approved_by,
        )
        await self._snapshot_repo.create(snapshot)

        job.status = "published"
        job.published_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)
        updated = await self._job_repo.update(job)
        return _model_to_dict(updated)

    async def fail_job(self, job_id: str, reason: str) -> dict[str, Any]:
        job = await self._job_repo.find_by_id(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        job.status = "failed"
        job.notes = reason
        job.updated_at = datetime.now(UTC)
        updated = await self._job_repo.update(job)
        return _model_to_dict(updated)

    async def rollback_job(
        self, job_id: str, rollback_version: int,
    ) -> dict[str, Any]:
        job = await self._job_repo.find_by_id(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")

        snap = await self._get_snapshot_model(
            job.entity_type, job.entity_id, rollback_version
        )
        if snap is None:
            raise ValueError(
                f"No snapshot found for {job.entity_type}/{job.entity_id} "
                f"at version {rollback_version}"
            )

        new_snap = VersionSnapshotModel(
            entity_type=job.entity_type, entity_id=job.entity_id,
            version=job.version + 1, snapshot=snap.snapshot,
            snapshot_type="rollback",
            reason=f"Rollback to version {rollback_version}",
            created_by=job.approved_by,
        )
        await self._snapshot_repo.create(new_snap)

        job.rollback_version = rollback_version
        job.status = "rolled_back"
        job.updated_at = datetime.now(UTC)
        updated = await self._job_repo.update(job)
        return _model_to_dict(updated)

    # --- Approvals ---

    async def create_approval(
        self, entity_type: str, entity_id: str,
        requested_by: str, assigned_to: str | None = None,
        role_required: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        model = ApprovalModel(
            entity_type=entity_type, entity_id=entity_id,
            requested_by=requested_by, assigned_to=assigned_to,
            role_required=role_required, status="pending",
            comments=[], decided_at=None, is_active=True, version=1,
            created_by=requested_by, updated_by=requested_by,
            created_at=now, updated_at=now,
        )
        created = await self._approval_repo.create(model)
        return _model_to_dict(created)

    async def list_approvals(
        self, status: str | None = None, entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        if status:
            items = await self._approval_repo.find_by_field("status", status)
        elif entity_type:
            items = await self._approval_repo.find_by_field("entity_type", entity_type)
        else:
            items = await self._approval_repo.find_all()
        return [_model_to_dict(a) for a in items]

    async def approve_entity(
        self, approval_id: str, user_id: str, comment: str | None = None,
    ) -> dict[str, Any]:
        model = await self._approval_repo.find_by_id(approval_id)
        if model is None:
            raise ValueError(f"Approval {approval_id} not found")
        approval = Approval(
            id=model.id, entity_type=model.entity_type,
            entity_id=model.entity_id, requested_by=model.requested_by,
            assigned_to=model.assigned_to,
            role_required=model.role_required,
            status=model.status, comments=model.comments or [],
            decided_at=model.decided_at, is_active=model.is_active,
            version=model.version, created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at, updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
        approval.approve(user_id, comment)
        model.status = approval.status
        model.decided_at = approval.decided_at
        model.assigned_to = approval.assigned_to
        model.comments = approval.comments
        model.updated_at = approval.updated_at
        updated = await self._approval_repo.update(model)
        return _model_to_dict(updated)

    async def reject_approval(
        self, approval_id: str, user_id: str, reason: str,
    ) -> dict[str, Any]:
        model = await self._approval_repo.find_by_id(approval_id)
        if model is None:
            raise ValueError(f"Approval {approval_id} not found")
        approval = Approval(
            id=model.id, entity_type=model.entity_type,
            entity_id=model.entity_id, requested_by=model.requested_by,
            assigned_to=model.assigned_to,
            role_required=model.role_required,
            status=model.status, comments=model.comments or [],
            decided_at=model.decided_at, is_active=model.is_active,
            version=model.version, created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at, updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
        approval.reject(user_id, reason)
        model.status = approval.status
        model.decided_at = approval.decided_at
        model.assigned_to = approval.assigned_to
        model.comments = approval.comments
        model.updated_at = approval.updated_at
        updated = await self._approval_repo.update(model)
        return _model_to_dict(updated)

    async def add_approval_comment(
        self, approval_id: str, user_id: str, comment: str,
    ) -> dict[str, Any]:
        model = await self._approval_repo.find_by_id(approval_id)
        if model is None:
            raise ValueError(f"Approval {approval_id} not found")
        comments = model.comments or []
        comments.append({
            "user_id": user_id, "comment": comment,
            "created_at": datetime.now(UTC).isoformat(),
        })
        model.comments = comments
        model.updated_at = datetime.now(UTC)
        updated = await self._approval_repo.update(model)
        return _model_to_dict(updated)

    # --- Reviews ---

    async def create_review(
        self, entity_type: str, entity_id: str,
        reviewer_id: str, review_type: str = "medical",
    ) -> dict[str, Any]:
        model = ReviewModel(
            entity_type=entity_type, entity_id=entity_id,
            reviewer_id=reviewer_id, review_type=review_type,
            status="pending", decision=None, comments=None, score=None,
            is_active=True, version=1,
            created_by=reviewer_id, updated_by=reviewer_id,
        )
        created = await self._review_repo.create(model)
        return _model_to_dict(created)

    async def list_reviews(
        self, status: str | None = None, entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        if status:
            items = await self._review_repo.find_by_field("status", status)
        elif entity_type:
            items = await self._review_repo.find_by_field("entity_type", entity_type)
        else:
            items = await self._review_repo.find_all()
        return [_model_to_dict(r) for r in items]

    async def complete_review(
        self, review_id: str, decision: str,
        comments: str | None = None, score: int | None = None,
    ) -> dict[str, Any]:
        model = await self._review_repo.find_by_id(review_id)
        if model is None:
            raise ValueError(f"Review {review_id} not found")
        review = Review(
            id=model.id, entity_type=model.entity_type,
            entity_id=model.entity_id, reviewer_id=model.reviewer_id,
            review_type=model.review_type, status=model.status,
            decision=model.decision, comments=model.comments,
            score=model.score, is_active=model.is_active,
            version=model.version, created_by=model.created_by,
            updated_by=model.updated_by, created_at=model.created_at,
            updated_at=model.updated_at, deleted_at=model.deleted_at,
            completed_at=model.completed_at,
        )
        review.complete(decision, comments, score)
        model.status = review.status
        model.decision = review.decision
        model.comments = review.comments
        model.score = review.score
        model.completed_at = review.completed_at
        model.updated_at = review.updated_at
        updated = await self._review_repo.update(model)
        return _model_to_dict(updated)

    # --- Change Requests ---

    async def create_change_request(
        self, entity_type: str, entity_id: str,
        requested_by: str, title: str, changes: dict[str, Any],
        description: str | None = None, reason: str | None = None,
    ) -> dict[str, Any]:
        model = ChangeRequestModel(
            entity_type=entity_type, entity_id=entity_id,
            requested_by=requested_by, title=title,
            description=description, changes=changes,
            reason=reason, status="pending", is_active=True, version=1,
            created_by=requested_by, updated_by=requested_by,
        )
        created = await self._change_repo.create(model)
        return _model_to_dict(created)

    async def list_change_requests(
        self, status: str | None = None, entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        if status:
            items = await self._change_repo.find_by_field("status", status)
        elif entity_type:
            items = await self._change_repo.find_by_field("entity_type", entity_type)
        else:
            items = await self._change_repo.find_all()
        return [_model_to_dict(c) for c in items]

    async def approve_change_request(
        self, cr_id: str, user_id: str,
    ) -> dict[str, Any]:
        model = await self._change_repo.find_by_id(cr_id)
        if model is None:
            raise ValueError(f"ChangeRequest {cr_id} not found")
        cr = ChangeRequest(
            id=model.id, entity_type=model.entity_type,
            entity_id=model.entity_id, requested_by=model.requested_by,
            title=model.title, description=model.description,
            changes=model.changes, reason=model.reason,
            status=model.status, is_active=model.is_active,
            version=model.version, created_by=model.created_by,
            updated_by=model.updated_by, created_at=model.created_at,
            updated_at=model.updated_at, deleted_at=model.deleted_at,
            resolved_at=model.resolved_at, resolved_by=model.resolved_by,
        )
        cr.approve(user_id)
        model.status = cr.status
        model.resolved_by = cr.resolved_by
        model.resolved_at = cr.resolved_at
        model.updated_at = cr.updated_at
        updated = await self._change_repo.update(model)
        return _model_to_dict(updated)

    async def reject_change_request(
        self, cr_id: str, user_id: str, reason: str,
    ) -> dict[str, Any]:
        model = await self._change_repo.find_by_id(cr_id)
        if model is None:
            raise ValueError(f"ChangeRequest {cr_id} not found")
        cr = ChangeRequest(
            id=model.id, entity_type=model.entity_type,
            entity_id=model.entity_id, requested_by=model.requested_by,
            title=model.title, description=model.description,
            changes=model.changes, reason=model.reason,
            status=model.status, is_active=model.is_active,
            version=model.version, created_by=model.created_by,
            updated_by=model.updated_by, created_at=model.created_at,
            updated_at=model.updated_at, deleted_at=model.deleted_at,
            resolved_at=model.resolved_at, resolved_by=model.resolved_by,
        )
        cr.reject(user_id, reason)
        model.status = cr.status
        model.resolved_by = cr.resolved_by
        model.resolved_at = cr.resolved_at
        model.reason = cr.reason
        model.updated_at = cr.updated_at
        updated = await self._change_repo.update(model)
        return _model_to_dict(updated)

    async def detect_conflicts(
        self, entity_type: str, entity_id: str,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(ChangeRequestModel)
            .where(
                ChangeRequestModel.entity_type == entity_type,
                ChangeRequestModel.entity_id == entity_id,
                ChangeRequestModel.status == "pending",
                ChangeRequestModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        pending = result.scalars().all()

        conflicts = []
        for i, a in enumerate(pending):
            for b in pending[i + 1:]:
                a_changes = a.changes or {}
                b_changes = b.changes or {}
                overlapping = set(a_changes.keys()) & set(b_changes.keys())
                if overlapping:
                    conflicts.append({
                        "request_a": a.id, "request_b": b.id,
                        "overlapping_fields": list(overlapping),
                    })
        return conflicts

    # --- Version Snapshots ---

    async def create_snapshot(
        self, entity_type: str, entity_id: str, version: int,
        snapshot: dict[str, Any], snapshot_type: str = "manual",
        reason: str | None = None, created_by: str | None = None,
    ) -> dict[str, Any]:
        snap = VersionSnapshotModel(
            entity_type=entity_type, entity_id=entity_id,
            version=version, snapshot=snapshot,
            snapshot_type=snapshot_type, reason=reason,
            created_by=created_by,
        )
        created = await self._snapshot_repo.create(snap)
        return _model_to_dict(created)

    async def list_snapshots(
        self, entity_type: str, entity_id: str,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(VersionSnapshotModel)
            .where(
                VersionSnapshotModel.entity_type == entity_type,
                VersionSnapshotModel.entity_id == entity_id,
                VersionSnapshotModel.deleted_at.is_(None),
            )
            .order_by(VersionSnapshotModel.version.desc())
        )
        result = await self._session.execute(stmt)
        return [_model_to_dict(s) for s in result.scalars().all()]

    async def _get_snapshot_model(
        self, entity_type: str, entity_id: str, version: int,
    ) -> VersionSnapshotModel | None:
        stmt = (
            select(VersionSnapshotModel)
            .where(
                VersionSnapshotModel.entity_type == entity_type,
                VersionSnapshotModel.entity_id == entity_id,
                VersionSnapshotModel.version == version,
                VersionSnapshotModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # --- Bulk scheduled job processing ---

    async def process_scheduled_jobs(self) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        stmt = (
            select(PublishingJobModel)
            .where(
                PublishingJobModel.status == "approved",
                PublishingJobModel.schedule_at.is_not(None),
                PublishingJobModel.schedule_at <= now,
                PublishingJobModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        jobs = result.scalars().all()

        processed = []
        for job in jobs:
            try:
                snap = VersionSnapshotModel(
                    entity_type=job.entity_type, entity_id=job.entity_id,
                    version=job.version, snapshot={},
                    snapshot_type="publish",
                    reason="Scheduled publish",
                    created_by=job.approved_by,
                )
                self._session.add(snap)
                job.status = "published"
                job.published_at = datetime.now(UTC)
                job.updated_at = datetime.now(UTC)
                await self._session.flush()
                processed.append(_model_to_dict(job))
            except Exception as exc:
                await self._session.rollback()
                processed.append({"job_id": job.id, "error": str(exc)})

        return processed
