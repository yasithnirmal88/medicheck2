from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class KnowledgeGraphNode:
    id: str
    graph_id: str
    entity_type: str
    entity_id: str
    label: str
    x_position: float
    y_position: float
    color: str | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        graph_id: str,
        entity_type: str,
        entity_id: str,
        label: str,
        x_position: float = 0.0,
        y_position: float = 0.0,
        color: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeGraphNode:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            graph_id=graph_id,
            entity_type=entity_type,
            entity_id=entity_id,
            label=label.strip(),
            x_position=x_position,
            y_position=y_position,
            color=color,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "graph_id": self.graph_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "label": self.label,
            "x_position": self.x_position,
            "y_position": self.y_position,
            "color": self.color,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class KnowledgeGraphEdge:
    id: str
    graph_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    label: str | None
    weight: float
    metadata: dict[str, Any]
    created_at: datetime

    @classmethod
    def create(
        cls,
        graph_id: str,
        source_node_id: str,
        target_node_id: str,
        relationship_type: str,
        label: str | None = None,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeGraphEdge:
        return cls(
            id=uuid.uuid4().hex,
            graph_id=graph_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship_type=relationship_type,
            label=label,
            weight=weight,
            metadata=metadata or {},
            created_at=datetime.now(UTC),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "graph_id": self.graph_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "relationship_type": self.relationship_type,
            "label": self.label,
            "weight": self.weight,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class KnowledgeGraph:
    id: str
    name: str
    description: str | None
    body_system_id: str
    is_active: bool
    version: int
    status: str
    created_by: str | None
    updated_by: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        name: str,
        body_system_id: str,
        description: str | None = None,
        is_active: bool = True,
        created_by: str | None = None,
    ) -> KnowledgeGraph:
        now = datetime.now(UTC)
        return cls(
            id=uuid.uuid4().hex,
            name=name.strip(),
            description=description,
            body_system_id=body_system_id,
            is_active=is_active,
            version=1,
            status="draft",
            created_by=created_by,
            updated_by=created_by,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "body_system_id": self.body_system_id,
            "is_active": self.is_active,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
