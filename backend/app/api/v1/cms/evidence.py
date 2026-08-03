from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cms_user, get_db
from app.application.services.cms.clinical_evidence_service import ClinicalEvidenceService
from app.domain.entities.user import User

router = APIRouter(prefix="/cms/evidence", tags=["CMS Clinical Evidence"])


@router.get("")
async def list_evidence(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ClinicalEvidenceService(session)
    return await svc.list_evidence_references()


@router.post("")
async def create_evidence(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = ClinicalEvidenceService(session)
    return await svc.add_evidence_reference(
        title=payload["title"],
        citation=payload["citation"],
        pmid=payload.get("pmid"),
        doi=payload.get("doi"),
        evidence_level=payload.get("evidence_level", "Level I"),
        confidence_score=payload.get("confidence_score", 0.90),
        summary=payload.get("summary"),
        created_by=user.id,
    )


@router.get("/pubmed/lookup")
async def lookup_pubmed(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    pmid: str = Query(...),
):
    svc = ClinicalEvidenceService(session)
    return await svc.fetch_pubmed_metadata(pmid)


@router.get("/doi/lookup")
async def lookup_doi(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    doi: str = Query(...),
):
    svc = ClinicalEvidenceService(session)
    return await svc.fetch_doi_metadata(doi)
