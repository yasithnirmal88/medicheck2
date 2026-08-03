from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
)
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.disease import DiseaseModel
from app.infrastructure.persistence.models.evidence_reference import (
    EvidenceReferenceModel,
)
from app.infrastructure.persistence.models.imaging_test import ImagingTestModel
from app.infrastructure.persistence.models.laboratory_test import LaboratoryTestModel
from app.infrastructure.persistence.models.lifestyle_advice import LifestyleAdviceModel
from app.infrastructure.persistence.models.nutrition_advice import NutritionAdviceModel
from app.infrastructure.persistence.models.question import QuestionModel
from app.infrastructure.persistence.models.recommendation import RecommendationModel
from app.infrastructure.persistence.models.symptom import SymptomModel
from app.infrastructure.persistence.repositories.sql_cms_knowledge_graph_repository import (
    SQLCMSKnowledgeGraphRepository,
)


class KnowledgeGraphEditorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SQLCMSKnowledgeGraphRepository(session)

    # --- Graph CRUD ---

    async def create_graph(
        self, name: str, body_system_id: str, description: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        graph = KnowledgeGraph.create(
            name=name,
            body_system_id=body_system_id,
            description=description,
            created_by=created_by,
        )
        created = await self._repo.create(graph)
        return created.to_dict()

    async def get_graph(self, graph_id: str) -> dict[str, Any] | None:
        graph = await self._repo.find_by_id(graph_id)
        if graph is None:
            return None

        nodes = await self._repo.get_nodes(graph_id)
        edges = await self._repo.get_edges(graph_id)

        result = graph.to_dict()
        result["nodes"] = [n.to_dict() for n in nodes]
        result["edges"] = [e.to_dict() for e in edges]
        return result

    async def list_graphs(self, body_system_id: str | None = None) -> list[dict[str, Any]]:
        if body_system_id:
            graphs = await self._repo.find_by_body_system(body_system_id)
        else:
            graphs = await self._repo.find_all_active()
        return [g.to_dict() for g in graphs]

    async def update_graph(
        self, graph_id: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        graph = await self._repo.find_by_id(graph_id)
        if graph is None:
            raise ValueError(f"Graph {graph_id} not found")

        for field, value in data.items():
            if hasattr(graph, field) and value is not None:
                setattr(graph, field, value)
        graph.updated_by = user_id
        graph.updated_at = datetime.now(UTC)

        updated = await self._repo.update(graph)
        return updated.to_dict()

    async def delete_graph(self, graph_id: str) -> None:
        graph = await self._repo.find_by_id(graph_id)
        if graph:
            graph.soft_delete()
            await self._repo.update(graph)

    # --- Node management ---

    async def add_node(
        self,
        graph_id: str,
        entity_type: str,
        entity_id: str,
        label: str,
        x_position: float = 0,
        y_position: float = 0,
        color: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        node = KnowledgeGraphNode.create(
            graph_id=graph_id,
            entity_type=entity_type,
            entity_id=entity_id,
            label=label,
            x_position=x_position,
            y_position=y_position,
            color=color,
            metadata=metadata,
        )
        created = await self._repo.add_node(node)
        return created.to_dict()

    async def update_node(
        self, node_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        node = await self._repo.get_node_by_id(node_id)
        if node is None:
            raise ValueError(f"Node {node_id} not found")

        for field in ("label", "x_position", "y_position", "color", "metadata"):
            if field in data and data[field] is not None:
                setattr(node, field, data[field])
        node.updated_at = datetime.now(UTC)

        updated = await self._repo.update_node(node)
        return updated.to_dict()

    async def remove_node(self, node_id: str) -> None:
        await self._repo.remove_node(node_id)

    # --- Edge management ---

    async def add_edge(
        self,
        graph_id: str,
        source_node_id: str,
        target_node_id: str,
        relationship_type: str,
        label: str | None = None,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        edge = KnowledgeGraphEdge.create(
            graph_id=graph_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship_type=relationship_type,
            label=label,
            weight=weight,
            metadata=metadata,
        )
        created = await self._repo.add_edge(edge)
        return created.to_dict()

    async def remove_edge(self, edge_id: str) -> None:
        await self._repo.remove_edge(edge_id)

    # --- Bulk linking ---

    async def bulk_link(
        self,
        entity_type: str,
        source_ids: list[str],
        target_type: str,
        target_ids: list[str],
        relationship_type: str,
        graph_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if graph_id is None:
            graph_id = uuid.uuid4().hex

        created = []
        for sid in source_ids:
            for tid in target_ids:
                edge = KnowledgeGraphEdge.create(
                    graph_id=graph_id,
                    source_node_id=sid,
                    target_node_id=tid,
                    relationship_type=relationship_type,
                    label=f"{entity_type}->{target_type}",
                )
                result = await self._repo.add_edge(edge)
                created.append(result.to_dict())
        return created

    # --- Graph validation ---

    async def validate_graph(self, graph_id: str) -> dict[str, Any]:
        nodes = await self._repo.get_nodes(graph_id)
        edges = await self._repo.get_edges(graph_id)

        issues = []
        orphan_nodes = []
        entity_map: dict[str, int] = {}
        for node in nodes:
            entity_type = node.entity_type
            entity_map[entity_type] = entity_map.get(entity_type, 0) + 1

        node_ids = {n.id for n in nodes}
        for edge in edges:
            if edge.source_node_id not in node_ids:
                issues.append(f"Edge {edge.id}: source node {edge.source_node_id} not found")
            if edge.target_node_id not in node_ids:
                issues.append(f"Edge {edge.id}: target node {edge.target_node_id} not found")

        connected_nodes: set[str] = set()
        for edge in edges:
            connected_nodes.add(edge.source_node_id)
            connected_nodes.add(edge.target_node_id)
        for node in nodes:
            if node.id not in connected_nodes:
                orphan_nodes.append(node.id)

        cycles = self._detect_cycles(nodes, edges)

        return {
            "graph_id": graph_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "entity_distribution": entity_map,
            "orphan_nodes": orphan_nodes,
            "orphan_count": len(orphan_nodes),
            "cycles": cycles,
            "cycle_count": len(cycles),
            "issues": issues,
            "is_valid": len(issues) == 0 and len(cycles) == 0,
        }

    def _detect_cycles(
        self,
        nodes: list[KnowledgeGraphNode],
        edges: list[KnowledgeGraphEdge],
    ) -> list[list[str]]:
        graph: dict[str, list[str]] = {n.id: [] for n in nodes}
        for edge in edges:
            if edge.source_node_id in graph:
                graph[edge.source_node_id].append(edge.target_node_id)

        cycles = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node_id: str) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
            path.pop()
            rec_stack.discard(node_id)

        for node_id in graph:
            if node_id not in visited:
                dfs(node_id)

        return cycles

    # --- Impact analysis ---

    async def analyze_impact(
        self, entity_type: str, entity_id: str
    ) -> dict[str, Any]:

        entity_model_map = {
            "question": QuestionModel,
            "indicator": ClinicalIndicatorModel,
            "disease": DiseaseModel,
            "symptom": SymptomModel,
            "recommendation": RecommendationModel,
            "lab_test": LaboratoryTestModel,
            "imaging": ImagingTestModel,
            "lifestyle": LifestyleAdviceModel,
            "nutrition": NutritionAdviceModel,
            "evidence": EvidenceReferenceModel,
        }

        model_cls = entity_model_map.get(entity_type)
        downstream: list[dict[str, Any]] = []
        upstream: list[dict[str, Any]] = []

        if entity_type == "question":
            from app.infrastructure.persistence.models.links import (
                QuestionIndicatorLinkModel,
            )

            stmt = select(QuestionIndicatorLinkModel).where(
                QuestionIndicatorLinkModel.question_id == entity_id
            )
            result = await self._session.execute(stmt)
            for link in result.scalars().all():
                downstream.append(
                    {
                        "entity_type": "indicator",
                        "entity_id": link.indicator_id,
                        "relationship": "maps_to",
                    }
                )
        elif entity_type == "indicator":
            from app.infrastructure.persistence.models.links import (
                IndicatorConditionLinkModel,
                QuestionIndicatorLinkModel,
            )

            q_stmt = select(QuestionIndicatorLinkModel).where(
                QuestionIndicatorLinkModel.indicator_id == entity_id
            )
            for link in (await self._session.execute(q_stmt)).scalars().all():
                upstream.append(
                    {
                        "entity_type": "question",
                        "entity_id": link.question_id,
                        "relationship": "sourced_from",
                    }
                )

            c_stmt = select(IndicatorConditionLinkModel).where(
                IndicatorConditionLinkModel.indicator_id == entity_id
            )
            for link in (await self._session.execute(c_stmt)).scalars().all():
                downstream.append(
                    {
                        "entity_type": "disease",
                        "entity_id": link.condition_id,
                        "relationship": "indicates",
                    }
                )

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "upstream_count": len(upstream),
            "upstream": upstream,
            "downstream_count": len(downstream),
            "downstream": downstream,
        }

    async def search_entities(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        results = []
        models_to_search = [
            ("question", QuestionModel, "text"),
            ("disease", DiseaseModel, "name"),
            ("symptom", SymptomModel, "name"),
            ("indicator", ClinicalIndicatorModel, "name"),
            ("recommendation", RecommendationModel, "title"),
        ]

        for etype, model_cls, text_col in models_to_search:
            col = getattr(model_cls, text_col, None)
            if col is None:
                continue
            stmt = (
                select(model_cls)
                .where(col.ilike(f"%{query}%"), model_cls.deleted_at.is_(None))
                .limit(limit // len(models_to_search) + 1)
            )
            result = await self._session.execute(stmt)
            for row in result.scalars().all():
                results.append(
                    {
                        "entity_type": etype,
                        "id": row.id,
                        "label": getattr(row, text_col, ""),
                    }
                )
        return results[:limit]
