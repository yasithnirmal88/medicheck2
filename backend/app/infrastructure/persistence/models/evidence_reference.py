from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class EvidenceReferenceModel(BaseModel):
    __tablename__ = "evidence_references"

    question_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_level: Mapped[str] = mapped_column(String(5), nullable=False, default="C")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
