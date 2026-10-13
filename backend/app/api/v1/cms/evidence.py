from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.application.services.cms.clinical_evidence_service import ClinicalEvidenceService
from app.identity import (
    Permission,
    User,
    check_permission,
    get_cms_user,
    get_user_permissions,
)

router = APIRouter(prefix="/cms/evidence", tags=["CMS Clinical Evidence"])


class EvidenceReferenceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    url: str | None = Field(
        None, max_length=1000, pattern=r"(?i)^https?://"
    )
    source: str | None = Field(None, max_length=255)
    evidence_level: str = Field("C", min_length=1, max_length=5)
    summary: str | None = None
    question_id: str | None = Field(None, max_length=32)


@router.get("")
async def list_evidence(
    _user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    title: str | None = Query(None, max_length=255),
    source: str | None = Query(None, max_length=255),
    evidence_level: str | None = Query(None, max_length=5),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    svc = ClinicalEvidenceService(session)
    return await svc.list_evidence_references(
        title=title,
        source=source,
        evidence_level=evidence_level,
        skip=skip,
        limit=limit,
    )


@router.post("")
async def create_evidence(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: EvidenceReferenceCreate,
):
    permissions = await get_user_permissions(session, user.id)
    if not check_permission(permissions, Permission.CMS_WRITE_EVIDENCE):
        raise HTTPException(403, "Insufficient permissions")

    svc = ClinicalEvidenceService(session)
    return await svc.add_evidence_reference(
        title=payload.title,
        url=payload.url,
        source=payload.source,
        evidence_level=payload.evidence_level,
        summary=payload.summary,
        question_id=payload.question_id,
    )


@router.get("/pubmed/lookup")
async def lookup_pubmed(
    _user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    pmid: str = Query(...),
):
    svc = ClinicalEvidenceService(session)
    return await svc.fetch_pubmed_metadata(pmid)


@router.get("/doi/lookup")
async def lookup_doi(
    __user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    doi: str = Query(...),
):
    svc = ClinicalEvidenceService(session)
    return await svc.fetch_doi_metadata(doi)
