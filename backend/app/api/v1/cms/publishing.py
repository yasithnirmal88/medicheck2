from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cms_user, get_db
from app.application.services.cms.publishing_service import (
    PublishingWorkflowService,
)
from app.domain.entities.user import User

router = APIRouter(prefix="/cms/publishing", tags=["CMS Publishing Workflow"])


# --- Workflows ---

@router.get("/workflows")
async def list_workflows(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    entity_type: str | None = Query(None),
):
    svc = PublishingWorkflowService(session)
    return await svc.list_workflows(entity_type)


@router.post("/workflows")
async def create_workflow(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    return await svc.create_workflow(
        name=payload["name"],
        entity_type=payload["entity_type"],
        steps=payload.get("steps"),
        description=payload.get("description"),
        created_by=user.id,
    )


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = PublishingWorkflowService(session)
    wf = await svc.get_workflow(workflow_id)
    if wf is None:
        raise HTTPException(404, "Workflow not found")
    return wf


@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.update_workflow(workflow_id, payload)
    except ValueError as e:
        raise HTTPException(404, str(e))


# --- Publishing Jobs ---

@router.get("/jobs")
async def list_jobs(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(None),
    entity_type: str | None = Query(None),
):
    svc = PublishingWorkflowService(session)
    return await svc.list_jobs(status, entity_type)


@router.post("/jobs")
async def create_job(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    return await svc.create_job(
        entity_type=payload["entity_type"],
        entity_id=payload["entity_id"],
        version=payload["version"],
        requested_by=user.id,
        schedule_at=payload.get("schedule_at"),
        notes=payload.get("notes"),
    )


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = PublishingWorkflowService(session)
    job = await svc.get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/jobs/{job_id}/approve")
async def approve_job(
    job_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.approve_job(job_id, user.id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/jobs/{job_id}/publish")
async def execute_publish(
    job_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.execute_publish(job_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/jobs/{job_id}/fail")
async def fail_job(
    job_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.fail_job(job_id, payload.get("reason", ""))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/jobs/{job_id}/rollback")
async def rollback_job(
    job_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.rollback_job(job_id, payload["rollback_version"])
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/jobs/process-scheduled")
async def process_scheduled(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = PublishingWorkflowService(session)
    return await svc.process_scheduled_jobs()


# --- Approvals ---

@router.get("/approvals")
async def list_approvals(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(None),
    entity_type: str | None = Query(None),
):
    svc = PublishingWorkflowService(session)
    return await svc.list_approvals(status, entity_type)


@router.post("/approvals")
async def create_approval(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    return await svc.create_approval(
        entity_type=payload["entity_type"],
        entity_id=payload["entity_id"],
        requested_by=user.id,
        assigned_to=payload.get("assigned_to"),
        role_required=payload.get("role_required"),
    )


@router.post("/approvals/{approval_id}/approve")
async def approve_entity(
    approval_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body({}),
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.approve_entity(
            approval_id, user.id, payload.get("comment")
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/approvals/{approval_id}/reject")
async def reject_approval(
    approval_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.reject_approval(
            approval_id, user.id, payload.get("reason", "No reason provided")
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/approvals/{approval_id}/comment")
async def add_approval_comment(
    approval_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.add_approval_comment(
            approval_id, user.id, payload["comment"]
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


# --- Reviews ---

@router.get("/reviews")
async def list_reviews(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(None),
    entity_type: str | None = Query(None),
):
    svc = PublishingWorkflowService(session)
    return await svc.list_reviews(status, entity_type)


@router.post("/reviews")
async def create_review(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    return await svc.create_review(
        entity_type=payload["entity_type"],
        entity_id=payload["entity_id"],
        reviewer_id=payload.get("reviewer_id", user.id),
        review_type=payload.get("review_type", "medical"),
    )


@router.post("/reviews/{review_id}/complete")
async def complete_review(
    review_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.complete_review(
            review_id=review_id,
            decision=payload["decision"],
            comments=payload.get("comments"),
            score=payload.get("score"),
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


# --- Change Requests ---

@router.get("/change-requests")
async def list_change_requests(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(None),
    entity_type: str | None = Query(None),
):
    svc = PublishingWorkflowService(session)
    return await svc.list_change_requests(status, entity_type)


@router.post("/change-requests")
async def create_change_request(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    return await svc.create_change_request(
        entity_type=payload["entity_type"],
        entity_id=payload["entity_id"],
        requested_by=user.id,
        title=payload["title"],
        changes=payload.get("changes", {}),
        description=payload.get("description"),
        reason=payload.get("reason"),
    )


@router.post("/change-requests/{cr_id}/approve")
async def approve_change_request(
    cr_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.approve_change_request(cr_id, user.id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/change-requests/{cr_id}/reject")
async def reject_change_request(
    cr_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    try:
        return await svc.reject_change_request(
            cr_id, user.id, payload.get("reason", "No reason provided")
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/change-requests/conflicts")
async def detect_conflicts(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    entity_type: str = Query(...),
    entity_id: str = Query(...),
):
    svc = PublishingWorkflowService(session)
    return await svc.detect_conflicts(entity_type, entity_id)


# --- Version Snapshots ---

@router.get("/snapshots")
async def list_snapshots(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    entity_type: str = Query(...),
    entity_id: str = Query(...),
):
    svc = PublishingWorkflowService(session)
    return await svc.list_snapshots(entity_type, entity_id)


@router.post("/snapshots")
async def create_snapshot(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = PublishingWorkflowService(session)
    return await svc.create_snapshot(
        entity_type=payload["entity_type"],
        entity_id=payload["entity_id"],
        version=payload["version"],
        snapshot=payload.get("snapshot", {}),
        snapshot_type=payload.get("snapshot_type", "manual"),
        reason=payload.get("reason"),
        created_by=user.id,
    )
