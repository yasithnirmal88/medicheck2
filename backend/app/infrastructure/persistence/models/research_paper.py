from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class ResearchPaperModel(BaseModel):
    __tablename__ = "research_papers"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    authors: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    journal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    pmid: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    mesh_terms: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    evidence_level: Mapped[str | None] = mapped_column(String(5), nullable=True)
    sample_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    methodology: Mapped[str | None] = mapped_column(String(255), nullable=True)
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    conflict_of_interest: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
