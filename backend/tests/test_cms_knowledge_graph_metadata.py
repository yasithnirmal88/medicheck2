from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
)
from app.infrastructure.persistence.models.knowledge_graph import (
    KnowledgeGraphEdgeModel,
    KnowledgeGraphNodeModel,
)
from app.infrastructure.persistence.repositories.sql_cms_knowledge_graph_repository import (
    SQLCMSKnowledgeGraphRepository,
)


@pytest.mark.asyncio
async def test_node_and_edge_metadata_round_trip_and_node_update(
    db_session: AsyncSession,
) -> None:
    repository = SQLCMSKnowledgeGraphRepository(db_session)
    graph = KnowledgeGraph.create(name="Metadata graph", body_system_id="body-system")
    await repository.create(graph)

    node_metadata = {
        "display": {"color": "#123456", "tags": ["clinical", "review"]},
        "enabled": True,
        "threshold": 0,
    }
    node = KnowledgeGraphNode.create(
        graph_id=graph.id,
        entity_type="indicator",
        entity_id=uuid.uuid4().hex,
        label="Indicator",
        metadata=node_metadata,
    )
    empty_node = KnowledgeGraphNode.create(
        graph_id=graph.id,
        entity_type="indicator",
        entity_id=uuid.uuid4().hex,
        label="Empty metadata",
        metadata=None,
    )
    edge_metadata = {
        "provenance": {"source": "cms", "reviewers": ["user-1", "user-2"]},
        "weighting": {"factor": 1.25, "active": False},
    }
    edge = KnowledgeGraphEdge.create(
        graph_id=graph.id,
        source_node_id=node.id,
        target_node_id=empty_node.id,
        relationship_type="supports",
        metadata=edge_metadata,
    )

    await repository.add_node(node)
    await repository.add_node(empty_node)
    await repository.add_edge(edge)
    await db_session.commit()
    db_session.expunge_all()

    stored_node = await repository.get_node_by_id(node.id)
    stored_edge = (await repository.get_edges(graph.id))[0]
    assert stored_node is not None
    assert stored_node.metadata == node_metadata
    assert stored_node.to_dict()["metadata"] == node_metadata
    assert stored_edge.metadata == edge_metadata
    assert stored_edge.to_dict()["metadata"] == edge_metadata

    stored_node.metadata = {
        "display": {"color": "#abcdef", "tags": []},
        "updated": {"by": "reviewer", "count": 2},
    }
    await repository.update_node(stored_node)
    await db_session.commit()
    db_session.expunge_all()

    updated_node = await repository.get_node_by_id(node.id)
    assert updated_node is not None
    assert updated_node.metadata == stored_node.metadata
    assert updated_node.to_dict()["metadata"] == stored_node.metadata

    db_node = await db_session.get(KnowledgeGraphNodeModel, node.id)
    db_edge = await db_session.get(KnowledgeGraphEdgeModel, edge.id)
    assert db_node is not None and db_node.extra_metadata == stored_node.metadata
    assert db_edge is not None and db_edge.extra_metadata == edge_metadata


@pytest.mark.asyncio
async def test_nodes_and_edges_with_null_or_empty_metadata_remain_readable(
    db_session: AsyncSession,
) -> None:
    graph_id = uuid.uuid4().hex
    null_node_id = uuid.uuid4().hex
    empty_node_id = uuid.uuid4().hex
    null_edge_id = uuid.uuid4().hex
    empty_edge_id = uuid.uuid4().hex

    db_session.add_all(
        [
            KnowledgeGraphNodeModel(
                id=null_node_id,
                graph_id=graph_id,
                entity_type="indicator",
                entity_id=uuid.uuid4().hex,
                label="Legacy null metadata",
                extra_metadata=None,
            ),
            KnowledgeGraphNodeModel(
                id=empty_node_id,
                graph_id=graph_id,
                entity_type="indicator",
                entity_id=uuid.uuid4().hex,
                label="Empty metadata",
                extra_metadata={},
            ),
            KnowledgeGraphEdgeModel(
                id=null_edge_id,
                graph_id=graph_id,
                source_node_id=uuid.uuid4().hex,
                target_node_id=uuid.uuid4().hex,
                relationship_type="supports",
                extra_metadata=None,
            ),
            KnowledgeGraphEdgeModel(
                id=empty_edge_id,
                graph_id=graph_id,
                source_node_id=uuid.uuid4().hex,
                target_node_id=uuid.uuid4().hex,
                relationship_type="supports",
                extra_metadata={},
            ),
        ]
    )
    await db_session.commit()
    db_session.expunge_all()

    repository = SQLCMSKnowledgeGraphRepository(db_session)
    nodes = await repository.get_nodes(graph_id)
    edges = await repository.get_edges(graph_id)

    assert {node.id: node.metadata for node in nodes} == {
        null_node_id: {},
        empty_node_id: {},
    }
    assert {edge.id: edge.metadata for edge in edges} == {
        null_edge_id: {},
        empty_edge_id: {},
    }

    empty_node_row = await db_session.scalar(
        select(KnowledgeGraphNodeModel).where(
            KnowledgeGraphNodeModel.id == empty_node_id
        )
    )
    empty_edge_row = await db_session.scalar(
        select(KnowledgeGraphEdgeModel).where(
            KnowledgeGraphEdgeModel.id == empty_edge_id
        )
    )
    assert empty_node_row is not None and empty_node_row.extra_metadata == {}
    assert empty_edge_row is not None and empty_edge_row.extra_metadata == {}
