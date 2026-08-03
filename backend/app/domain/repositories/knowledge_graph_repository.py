from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
)


class KnowledgeGraphRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> KnowledgeGraph | None:
        pass

    @abstractmethod
    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[KnowledgeGraph]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[KnowledgeGraph]:
        pass

    @abstractmethod
    async def create(self, graph: KnowledgeGraph) -> KnowledgeGraph:
        pass

    @abstractmethod
    async def update(self, graph: KnowledgeGraph) -> KnowledgeGraph:
        pass

    @abstractmethod
    async def get_nodes(
        self, graph_id: str
    ) -> list[KnowledgeGraphNode]:
        pass

    @abstractmethod
    async def get_edges(
        self, graph_id: str
    ) -> list[KnowledgeGraphEdge]:
        pass

    @abstractmethod
    async def add_node(
        self, node: KnowledgeGraphNode
    ) -> KnowledgeGraphNode:
        pass

    @abstractmethod
    async def update_node(
        self, node: KnowledgeGraphNode
    ) -> KnowledgeGraphNode:
        pass

    @abstractmethod
    async def remove_node(
        self, node_id: str
    ) -> None:
        pass

    @abstractmethod
    async def add_edge(
        self, edge: KnowledgeGraphEdge
    ) -> KnowledgeGraphEdge:
        pass

    @abstractmethod
    async def remove_edge(
        self, edge_id: str
    ) -> None:
        pass
