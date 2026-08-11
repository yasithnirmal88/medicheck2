"""Phase 8 — Community Health Worker + offline/low-bandwidth API.

All endpoints require the CHW role (via ``get_chw_user``) which admits
COMMUNITY_HEALTH_WORKER and senior staff (medical_director+) for supervision.
Patients and CMS-only roles are denied at this router — CHWs never reach the
CMS content routers because their hierarchy level (3) is below the CMS gate.

Clinical boundary: this router NEVER scores or diagnoses locally. Sync
delegates to the existing ClinicalDecisionService + ReportService (the CDSE)
server-side. AI is never invoked here.

Privacy: every patient-scoped operation is gated by ChwService._assert_assigned
(the explicit CHW↔patient assignment check). No unrestricted patient search.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_chw_user, get_current_admin, get_db
from app.application.dtos.chw_dtos import (
    ChwDashboardResponse,
    ConsentRequest,
    ConsentResponse,
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
    OfflineContentBundleResponse,
    OfflineContentListResponse,
    QrHandoffRequest,
    QrHandoffResponse,
    SyncPackageRequest,
    SyncResultResponse,
)
from app.application.services.chw_service import ChwService
from app.domain.entities.user import User

router = APIRouter(prefix="/chw", tags=["Community Health Worker (Phase 8)"])


@router.get("/dashboard", response_model=ChwDashboardResponse)
async def get_chw_dashboard(
    current_user: Annotated[User, Depends(get_chw_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ChwDashboardResponse:
    """Task-focused CHW dashboard: today's assessments, drafts, waiting-to-sync,
    completed, sync errors, and assigned patients. Never exposes population
    analytics or CMS controls."""
    svc = ChwService(session)
    return await svc.get_dashboard(current_user.id)


@router.get("/patients")
async def list_assigned_patients(
    current_user: Annotated[User, Depends(get_chw_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """List patients explicitly assigned to this CHW (least-privilege)."""
    svc = ChwService(session)
    return await svc.list_assigned_patients(current_user.id)


@router.post("/consent", response_model=ConsentResponse)
async def record_consent(
    payload: ConsentRequest,
    current_user: Annotated[User, Depends(get_chw_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ConsentResponse:
    """Record patient consent before a CHW assessment. Consent is attested by
    the CHW; no signature or biometric is stored."""
    svc = ChwService(session)
    return await svc.record_consent(current_user.id, payload)


@router.post("/sync", response_model=SyncResultResponse)
async def sync_offline_assessment(
    payload: SyncPackageRequest,
    current_user: Annotated[User, Depends(get_chw_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SyncResultResponse:
    """Idempotent offline-assessment synchronization. Repeated syncs with the
    same ``idempotency_key`` are no-ops (return the already-created session).
    The CDSE processes server-side; no local scoring."""
    svc = ChwService(session)
    return await svc.sync_assessment(current_user.id, payload)


@router.get("/sessions/{session_id}")
async def get_chw_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_chw_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a CHW-assisted session's state. The CHW must have assisted the
    session (metadata.chw_user_id matches)."""
    from sqlalchemy import select

    from app.infrastructure.persistence.models.assessment_session import (
        AssessmentSessionModel,
    )
    from app.core.exceptions import AuthorizationError, NotFoundError

    stmt = select(AssessmentSessionModel).where(
        AssessmentSessionModel.id == session_id,
        AssessmentSessionModel.deleted_at.is_(None),
    )
    sess = (await session.execute(stmt)).scalar_one_or_none()
    if sess is None:
        raise NotFoundError(detail="Session not found")
    meta = sess.extra_metadata or {}
    if meta.get("chw_user_id") != current_user.id:
        raise AuthorizationError(detail="Not authorized for this session")
    return {
        "id": sess.id,
        "status": sess.status,
        "patient_user_id": sess.user_id,
        "language": meta.get("language", "en"),
        "chw_assisted": meta.get("chw_assisted", False),
        "offline": meta.get("offline", False),
        "content_version": meta.get("content_version", 1),
        "sync_status": meta.get("sync_status"),
        "started_at": sess.started_at.isoformat() if sess.started_at else None,
        "completed_at": (
            sess.completed_at.isoformat() if sess.completed_at else None
        ),
    }


@router.get("/offline-content", response_model=OfflineContentListResponse)
async def list_offline_content(
    current_user: Annotated[User, Depends(get_chw_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> OfflineContentListResponse:
    """List published/versioned questionnaires available for offline caching.
    Only active templates + their groups/questions/options are included."""
    svc = ChwService(session)
    return await svc.list_offline_content()


@router.get(
    "/offline-content/{template_id}",
    response_model=OfflineContentBundleResponse,
)
async def get_offline_content(
    template_id: str,
    current_user: Annotated[User, Depends(get_chw_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> OfflineContentBundleResponse:
    """Get a single versioned questionnaire bundle for offline caching. The
    ``content_version`` anchors reproducibility."""
    svc = ChwService(session)
    return await svc.get_offline_content(template_id)


@router.post("/qr-handoff", response_model=QrHandoffResponse)
async def create_qr_handoff(
    payload: QrHandoffRequest,
    current_user: Annotated[User, Depends(get_chw_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> QrHandoffResponse:
    """Generate a short-lived, opaque QR handoff token. Contains NO PHI."""
    svc = ChwService(session)
    return await svc.create_qr_handoff(current_user.id, payload)


@router.post("/devices", response_model=DeviceRegistrationResponse)
async def register_offline_device(
    payload: DeviceRegistrationRequest,
    current_user: Annotated[User, Depends(get_chw_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DeviceRegistrationResponse:
    """Register a device for offline use. Stores a SHA-256 fingerprint hash,
    never raw identifiers or credentials."""
    svc = ChwService(session)
    return await svc.register_device(current_user.id, payload)


# ── Device revocation (admin-only) ────────────────────────────────────


@router.post("/devices/{device_id}/revoke")
async def revoke_offline_device(
    device_id: str,
    current_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Revoke an offline device (admin/medical-director only). A lost device
    can be disabled so its offline cache can no longer sync."""
    svc = ChwService(session)
    return await svc.revoke_device(current_user.id, device_id)


@router.get("/devices")
async def list_offline_devices(
    current_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """List offline device registrations (admin-only)."""
    from sqlalchemy import select

    from app.infrastructure.persistence.models.offline_device_registration import (
        OfflineDeviceRegistrationModel,
    )

    stmt = select(OfflineDeviceRegistrationModel).where(
        OfflineDeviceRegistrationModel.deleted_at.is_(None)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "device_id": r.id,
            "chw_user_id": r.chw_user_id,
            "device_label": r.device_label,
            "status": r.status,
            "last_seen_at": r.last_seen_at.isoformat() if r.last_seen_at else None,
            "revoked_at": r.revoked_at.isoformat() if r.revoked_at else None,
        }
        for r in rows
    ]
