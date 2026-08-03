from __future__ import annotations

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class QuestionnaireVersionModel(BaseModel):
    __tablename__ = "questionnaire_versions"

    questionnaire_template_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    change_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
