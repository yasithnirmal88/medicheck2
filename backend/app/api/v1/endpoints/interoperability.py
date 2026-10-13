"""Phase 10 — Interoperability API: FHIR export, SDG export, care continuity.

All endpoints are authenticated + RBAC-controlled + consent-aware + auditable.
FHIR exports are IDOR-guarded (caller owns the data OR holds FHIR_EXPORT_ANY)
and consent-guarded (granted fhir_export consent required by default).
SDG/care-continuity exports are de-identified + k-anonymity-suppressed.
"""

from __future__ import annotations

import datetime
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.application.dtos.analytics_dtos import AnalyticsFilters
from app.application.dtos.fhir_dtos import FhirExportResponse
from app.application.dtos.interoperability_dtos import (
    SdgExportFormat,
    SdgExportResponse,
)
from app.application.services.care_continuity_service import CareContinuityService
from app.application.services.fhir_export_service import FhirExportService
from app.application.services.sdg_export_service import SdgExportService
from app.core.exceptions import AuthorizationError
from app.identity import User, get_current_user, get_sdg_export_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/interoperability", tags=["Interoperability (Phase 10)"]
)


def _build_filters(
    start_date: datetime.date | None,
    end_date: datetime.date | None,
) -> AnalyticsFilters:
    if start_date and end_date and end_date < start_date:
        raise AuthorizationError(detail="end_date cannot be before start_date.")
    return AnalyticsFilters(start_date=start_date, end_date=end_date)


@router.get(
    "/fhir/patient/{patient_id}",
    response_model=FhirExportResponse,
    summary="Export a patient FHIR Bundle (R4)",
    description=(
        "Produces a FHIR R4 Bundle (Patient, QuestionnaireResponse, Observation, "
        "DiagnosticReport, ServiceRequest, Task, CarePlan) from deterministic "
        "MediCheck data. IDOR-guarded, consent-aware, auditable. A 'possible "
        "condition' is never exported as a confirmed diagnosis."
    ),
)
async def export_patient_fhir(
    patient_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = FhirExportService(session)
    return await svc.export_patient_bundle(user, patient_id)


@router.get(
    "/fhir/session/{session_id}",
    response_model=FhirExportResponse,
    summary="Export a session-scoped FHIR Bundle (R4)",
)
async def export_session_fhir(
    session_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = FhirExportService(session)
    return await svc.export_session_bundle(user, session_id)


@router.get(
    "/exports",
    summary="Export history (audit manifest)",
    description="List prior export manifests. Caller sees own exports; clinicians/admins see all.",
)
async def list_exports(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
):
    svc = FhirExportService(session)
    return await svc.list_export_history(user, limit=limit)


@router.get(
    "/sdg",
    response_model=SdgExportResponse,
    summary="SDG / population export (JSON)",
    description=(
        "De-identified, k-anonymity-suppressed SDG-aligned aggregate export. "
        "Structured around SDG indicators, not DB tables. JSON format."
    ),
)
async def export_sdg(
    user: Annotated[User, Depends(get_sdg_export_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
):
    filters = _build_filters(start_date, end_date)
    svc = SdgExportService(session)
    return await svc.export(filters, fmt="json")


@router.get(
    "/sdg/csv",
    summary="SDG / population export (CSV)",
    description="Same SDG export as /sdg but returned as CSV (machine-readable).",
)
async def export_sdg_csv(
    user: Annotated[User, Depends(get_sdg_export_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
):
    filters = _build_filters(start_date, end_date)
    svc = SdgExportService(session)
    response = await svc.export(filters, fmt="csv")
    csv_text = svc.to_csv(response)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=medicheck_sdg_export.csv"},
    )


@router.get(
    "/care-continuity",
    summary="Care-continuity funnel analytics",
    description=(
        "De-identified, k-anonymity-suppressed care-continuity funnel: "
        "screened -> flagged -> referred -> received -> appointment -> care -> "
        "followup. Includes conversion/drop-off rates, median time-to-care, "
        "CHW-assisted completion. Outcome data does not modify clinical scoring."
    ),
)
async def get_care_continuity(
    user: Annotated[User, Depends(get_sdg_export_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
):
    filters = _build_filters(start_date, end_date)
    svc = CareContinuityService(session)
    return await svc.get_care_continuity(filters)
