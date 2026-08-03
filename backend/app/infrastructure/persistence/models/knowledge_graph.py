from __future__ import annotations

from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import BaseModel


class KnowledgeGraphModel(BaseModel):
    __tablename__ = "knowledge_graphs"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_system_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False, index=True
    )
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(32), nullable=True)


class KnowledgeGraphNodeModel(BaseModel):
    __tablename__ = "knowledge_graph_nodes"

    graph_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    x_position: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    y_position: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)


class KnowledgeGraphEdgeModel(BaseModel):
    __tablename__ = "knowledge_graph_edges"

    graph_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_node_id: Mapped[str] = mapped_column(String(32), nullable=False)
    target_node_id: Mapped[str] = mapped_column(String(32), nullable=False)
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
