from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class BranchRuleModel(BaseModel):
    __tablename__ = "branch_rules"

    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_system_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    condition_operator: Mapped[str] = mapped_column(
        String(10), nullable=False, default="AND"
    )
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    target_question_id: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
