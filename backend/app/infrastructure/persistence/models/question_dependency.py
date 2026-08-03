from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import BaseModel


class QuestionDependencyModel(BaseModel):
    __tablename__ = "question_dependencies"

    question_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    depends_on_question_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    condition_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="equals"
    )
    condition_value: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    logic_operator: Mapped[str] = mapped_column(
        String(10), nullable=False, default="AND"
    )
    group_id: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question = relationship(
        "QuestionModel",
        back_populates="dependencies",
        foreign_keys="QuestionDependencyModel.question_id",
    )
