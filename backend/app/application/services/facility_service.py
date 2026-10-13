"""Phase 10 — Facility service: operational metadata CRUD.

Facilities are operational destinations for referrals (no clinical content,
no patient data). Read access is open to authenticated referral users;
write/manage requires INTEROP_MANAGE (admin). Seeded demo facilities only —
no real hospital data is invented.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.referral_dtos import (
    FacilityCreateRequest,
    FacilityListResponse,
    FacilityResponse,
    FacilityServiceResponse,
)
from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.persistence.models.facility import FacilityModel
from app.infrastructure.persistence.models.facility_service import (
    FacilityServiceModel,
)

logger = logging.getLogger(__name__)


class FacilityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_facilities(
        self, *, active_only: bool = True
    ) -> FacilityListResponse:
        stmt = select(FacilityModel).where(FacilityModel.deleted_at.is_(None))
        if active_only:
            stmt = stmt.where(FacilityModel.is_active.is_(True))
        stmt = stmt.order_by(FacilityModel.name.asc())
        facilities = (await self.session.execute(stmt)).scalars().all()
        items = [await self._to_response(f) for f in facilities]
        return FacilityListResponse(items=items, total=len(items))

    async def get_facility(self, facility_id: str) -> FacilityResponse:
        f = await self.session.get(FacilityModel, facility_id)
        if f is None or f.is_deleted:
            raise NotFoundError(detail="Facility not found")
        return await self._to_response(f)

    async def create_facility(self, req: FacilityCreateRequest) -> FacilityResponse:
        # Check code uniqueness.
        existing = (
            await self.session.execute(
                select(FacilityModel).where(FacilityModel.code == req.code)
            )
        ).scalar_one_or_none()
        if existing is not None and not existing.is_deleted:
            raise ConflictError(detail=f"Facility code '{req.code}' already exists")
        facility = FacilityModel(
            code=req.code,
            name=req.name,
            service_type=req.service_type,
            region=req.region,
            contact_channel=req.contact_channel,
            availability_status=req.availability_status,
            description=req.description,
            is_active=True,
        )
        self.session.add(facility)
        await self.session.flush()
        for svc in req.services:
            self.session.add(
                FacilityServiceModel(
                    facility_id=facility.id,
                    service_type=svc.get("service_type", "general"),
                    name=svc.get("name", "Service"),
                    is_active=True,
                )
            )
        await self.session.flush()
        return await self._to_response(facility)

    async def _to_response(self, facility: FacilityModel) -> FacilityResponse:
        from sqlalchemy import inspect as sa_inspect

        state = sa_inspect(facility)
        if "created_at" in state.unloaded or "services" in state.unloaded:
            await self.session.refresh(facility, ["services", "created_at", "updated_at"])
        services = [
            FacilityServiceResponse(
                id=s.id,
                facility_id=s.facility_id,
                service_type=s.service_type,
                name=s.name,
                is_active=s.is_active,
            )
            for s in (facility.services or []) if not s.is_deleted
        ]
        return FacilityResponse(
            id=facility.id,
            code=facility.code,
            name=facility.name,
            service_type=facility.service_type,
            region=facility.region,
            contact_channel=facility.contact_channel,
            availability_status=facility.availability_status,  # type: ignore[arg-type]
            is_active=facility.is_active,
            description=facility.description,
            services=services,
        )
