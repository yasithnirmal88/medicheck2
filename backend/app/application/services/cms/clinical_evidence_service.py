from __future__ import annotations

import logging
from typing import Any

import httpx
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
                            "doi": next((id_obj.get("value") for id_obj in result.get("articleids", []) if id_obj.get("idtype") == "doi"), None),
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
        citation: str,
        pmid: str | None = None,
        doi: str | None = None,
        evidence_level: str = "Level I",
        confidence_score: float = 0.90,
        summary: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        ref = EvidenceReferenceModel(
            title=title,
            citation=citation,
            pmid=pmid,
            doi=doi,
            evidence_level=evidence_level,
            confidence_score=confidence_score,
            summary=summary,
            is_active=True,
            created_by=created_by,
            updated_by=created_by,
        )
        created = await self._evidence_repo.create(ref)
        return {
            "id": created.id,
            "title": created.title,
            "citation": created.citation,
            "pmid": created.pmid,
            "doi": created.doi,
            "evidence_level": created.evidence_level,
            "confidence_score": created.confidence_score,
            "summary": created.summary,
            "created_at": created.created_at.isoformat() if created.created_at else None,
        }

    async def list_evidence_references(self) -> list[dict[str, Any]]:
        refs = await self._evidence_repo.find_all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "citation": r.citation,
                "pmid": r.pmid,
                "doi": r.doi,
                "evidence_level": r.evidence_level,
                "confidence_score": r.confidence_score,
                "summary": r.summary,
            }
            for r in refs
        ]
