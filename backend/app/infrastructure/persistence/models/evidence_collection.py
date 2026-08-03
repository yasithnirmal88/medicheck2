from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class EvidenceCollectionModel(BaseModel):
    __tablename__ = "evidence_collections"

    body_system_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    disease_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    methodology: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_ids: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_grade: Mapped[str | None] = mapped_column(String(5), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
