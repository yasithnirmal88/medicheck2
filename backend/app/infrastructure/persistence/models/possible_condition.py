from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class PossibleConditionModel(BaseModel):
    __tablename__ = "possible_conditions"

    code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_system_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    icd10: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships (backrefs will be configured via linking tables)
    # indicators = relationship('ClinicalIndicatorModel', secondary='indicator_condition_links', backref='conditions')
