from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class MedicalEvidenceModel(BaseModel):
    __tablename__ = "medical_evidence"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="journal")
    doi: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    pmid: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    authors: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_level: Mapped[str] = mapped_column(String(5), default="C", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_system_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    disease_ids: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    indicator_ids: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False, index=True
    )
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
