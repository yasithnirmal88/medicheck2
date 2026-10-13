from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.evidence_reference import EvidenceReferenceModel
from app.infrastructure.persistence.repositories.sql_generic_cms_repository import (
    SQLGenericCMSRepository,
)

logger = logging.getLogger(__name__)


class ClinicalEvidenceService:
    """
    Service for managing clinical evidence, validating PubMed PMIDs / DOIs,
    and fetching scientific literature metadata via E-Utilities & Europe PMC.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._evidence_repo = SQLGenericCMSRepository(session, EvidenceReferenceModel)

    async def fetch_pubmed_metadata(self, pmid: str) -> dict[str, Any]:
        """Fetch article metadata from NCBI PubMed E-utilities API."""
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    result = data.get("result", {}).get(pmid, {})
                    if result:
                        authors = [a.get("name") for a in result.get("authors", [])]
                        return {
                            "pmid": pmid,
                            "title": result.get("title", ""),
                            "journal": result.get("fulljournalname", ""),
                            "pub_date": result.get("pubdate", ""),
                            "authors": authors,
                            "doi": next(
                                (
                                    id_obj.get("value")
                                    for id_obj in result.get("articleids", [])
                                    if id_obj.get("idtype") == "doi"
                                ),
                                None,
                            ),
                            "source": "PubMed",
                        }
        except Exception as e:
            logger.warning("Failed to fetch PubMed metadata for PMID %s: %s", pmid, e)

        return {"pmid": pmid, "source": "Manual"}

    async def fetch_doi_metadata(self, doi: str) -> dict[str, Any]:
        """Fetch paper metadata from CrossRef / Europe PMC via DOI."""
        url = f"https://api.crossref.org/works/{doi}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, headers={"User-Agent": "MedicheckPlatform/1.0"})
                if res.status_code == 200:
                    data = res.json().get("message", {})
                    title = data.get("title", [""])[0] if data.get("title") else ""
                    journal = data.get("container-title", [""])[0] if data.get("container-title") else ""
                    return {
                        "doi": doi,
                        "title": title,
                        "journal": journal,
                        "publisher": data.get("publisher", ""),
                        "source": "CrossRef",
                    }
        except Exception as e:
            logger.warning("Failed to fetch DOI metadata for %s: %s", doi, e)

        return {"doi": doi, "source": "Manual"}

    async def add_evidence_reference(
        self,
        title: str,
        url: str | None = None,
        source: str | None = None,
        evidence_level: str = "C",
        summary: str | None = None,
        question_id: str | None = None,
    ) -> dict[str, Any]:
        ref = EvidenceReferenceModel(
            title=title,
            url=url,
            source=source,
            evidence_level=evidence_level,
            summary=summary,
            question_id=question_id,
        )
        created = await self._evidence_repo.create(ref)
        await self._session.commit()
        return {
            "id": created.id,
            "title": created.title,
            "url": created.url,
            "source": created.source,
            "evidence_level": created.evidence_level,
            "summary": created.summary,
            "question_id": created.question_id,
            "created_at": created.created_at.isoformat() if created.created_at else None,
        }

    async def list_evidence_references(
        self,
        *,
        title: str | None = None,
        source: str | None = None,
        evidence_level: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        stmt = select(EvidenceReferenceModel).where(
            EvidenceReferenceModel.deleted_at.is_(None)
        )
        if title:
            stmt = stmt.where(EvidenceReferenceModel.title.ilike(f"%{title}%"))
        if source:
            stmt = stmt.where(EvidenceReferenceModel.source.ilike(f"%{source}%"))
        if evidence_level:
            stmt = stmt.where(EvidenceReferenceModel.evidence_level == evidence_level)
        stmt = stmt.order_by(EvidenceReferenceModel.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        refs = result.scalars().all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "url": r.url,
                "source": r.source,
                "evidence_level": r.evidence_level,
                "summary": r.summary,
                "question_id": r.question_id,
            }
            for r in refs
        ]
