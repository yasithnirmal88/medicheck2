from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
)
from app.domain.repositories.knowledge_graph_repository import (
    KnowledgeGraphRepository,
)
from app.infrastructure.persistence.models.knowledge_graph import (
    KnowledgeGraphEdgeModel,
    KnowledgeGraphModel,
    KnowledgeGraphNodeModel,
)


class SQLCMSKnowledgeGraphRepository(KnowledgeGraphRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> KnowledgeGraph | None:
        stmt = select(KnowledgeGraphModel).where(
            KnowledgeGraphModel.id == id,
            KnowledgeGraphModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[KnowledgeGraph]:
        stmt = (
            select(KnowledgeGraphModel)
            .where(
                KnowledgeGraphModel.body_system_id == body_system_id,
                KnowledgeGraphModel.deleted_at.is_(None),
            )
            .order_by(KnowledgeGraphModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_all_active(self) -> list[KnowledgeGraph]:
        stmt = (
            select(KnowledgeGraphModel)
            .where(
                KnowledgeGraphModel.is_active.is_(True),
                KnowledgeGraphModel.deleted_at.is_(None),
            )
            .order_by(KnowledgeGraphModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, graph: KnowledgeGraph) -> KnowledgeGraph:
        model = KnowledgeGraphModel(
            id=graph.id,
            name=graph.name,
            description=graph.description,
            body_system_id=graph.body_system_id,
            is_active=graph.is_active,
            version=graph.version,
            status=graph.status,
            created_by=graph.created_by,
            updated_by=graph.updated_by,
            created_at=graph.created_at,
            updated_at=graph.updated_at,
            deleted_at=graph.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return graph

    async def update(self, graph: KnowledgeGraph) -> KnowledgeGraph:
        stmt = select(KnowledgeGraphModel).where(
            KnowledgeGraphModel.id == graph.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"KnowledgeGraph with id {graph.id} not found")

        model.name = graph.name
        model.description = graph.description
        model.body_system_id = graph.body_system_id
        model.is_active = graph.is_active
        model.version = graph.version
        model.status = graph.status
        model.updated_by = graph.updated_by
        model.updated_at = graph.updated_at
        model.deleted_at = graph.deleted_at

        await self._session.flush()
        return graph

    async def get_nodes(self, graph_id: str) -> list[KnowledgeGraphNode]:
        stmt = (
            select(KnowledgeGraphNodeModel)
            .where(KnowledgeGraphNodeModel.graph_id == graph_id)
            .order_by(KnowledgeGraphNodeModel.label)
        )
        result = await self._session.execute(stmt)
        return [self._node_to_entity(m) for m in result.scalars().all()]

    async def get_edges(self, graph_id: str) -> list[KnowledgeGraphEdge]:
        stmt = (
            select(KnowledgeGraphEdgeModel)
            .where(KnowledgeGraphEdgeModel.graph_id == graph_id)
            .order_by(KnowledgeGraphEdgeModel.relationship_type)
        )
        result = await self._session.execute(stmt)
        return [self._edge_to_entity(m) for m in result.scalars().all()]

    async def add_node(self, node: KnowledgeGraphNode) -> KnowledgeGraphNode:
        model = KnowledgeGraphNodeModel(
            id=node.id,
            graph_id=node.graph_id,
            entity_type=node.entity_type,
            entity_id=node.entity_id,
            label=node.label,
            x_position=node.x_position,
            y_position=node.y_position,
            color=node.color,
            metadata=node.metadata,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return node

    async def get_node_by_id(self, node_id: str) -> KnowledgeGraphNode | None:
        stmt = select(KnowledgeGraphNodeModel).where(
            KnowledgeGraphNodeModel.id == node_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._node_to_entity(model) if model else None

    async def update_node(self, node: KnowledgeGraphNode) -> KnowledgeGraphNode:
        stmt = select(KnowledgeGraphNodeModel).where(
            KnowledgeGraphNodeModel.id == node.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"KnowledgeGraphNode with id {node.id} not found")

        model.label = node.label
        model.x_position = node.x_position
        model.y_position = node.y_position
        model.color = node.color
        model.metadata = node.metadata
        model.updated_at = node.updated_at

        await self._session.flush()
        return node

    async def remove_node(self, node_id: str) -> None:
        stmt = select(KnowledgeGraphNodeModel).where(
            KnowledgeGraphNodeModel.id == node_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def add_edge(self, edge: KnowledgeGraphEdge) -> KnowledgeGraphEdge:
        model = KnowledgeGraphEdgeModel(
            id=edge.id,
            graph_id=edge.graph_id,
            source_node_id=edge.source_node_id,
            target_node_id=edge.target_node_id,
            relationship_type=edge.relationship_type,
            label=edge.label,
            weight=edge.weight,
            metadata=edge.metadata,
            created_at=edge.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return edge

    async def remove_edge(self, edge_id: str) -> None:
        stmt = select(KnowledgeGraphEdgeModel).where(
            KnowledgeGraphEdgeModel.id == edge_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()

    def _to_entity(self, model: KnowledgeGraphModel) -> KnowledgeGraph:
        return KnowledgeGraph(
            id=model.id,
            name=model.name,
            description=model.description,
            body_system_id=model.body_system_id,
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    def _node_to_entity(
        self, model: KnowledgeGraphNodeModel
    ) -> KnowledgeGraphNode:
        return KnowledgeGraphNode(
            id=model.id,
            graph_id=model.graph_id,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            label=model.label,
            x_position=model.x_position,
            y_position=model.y_position,
            color=model.color,
            metadata=model.metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _edge_to_entity(
        self, model: KnowledgeGraphEdgeModel
    ) -> KnowledgeGraphEdge:
        return KnowledgeGraphEdge(
            id=model.id,
            graph_id=model.graph_id,
            source_node_id=model.source_node_id,
            target_node_id=model.target_node_id,
            relationship_type=model.relationship_type,
            label=model.label,
            weight=model.weight,
            metadata=model.metadata or {},
            created_at=model.created_at,
        )
