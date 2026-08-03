from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cms_user, get_db
from app.application.services.cms.knowledge_graph_editor_service import (
    KnowledgeGraphEditorService,
)
from app.domain.entities.user import User

router = APIRouter(prefix="/cms/knowledge-graph", tags=["CMS Knowledge Graph"])


@router.get("/graphs")
async def list_graphs(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    body_system_id: str | None = Query(None),
):
    svc = KnowledgeGraphEditorService(session)
    return await svc.list_graphs(body_system_id)


@router.post("/graphs")
async def create_graph(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = KnowledgeGraphEditorService(session)
    return await svc.create_graph(
        name=payload["name"],
        body_system_id=payload["body_system_id"],
        description=payload.get("description"),
        created_by=user.id,
    )


@router.get("/graphs/{graph_id}")
async def get_graph(
    graph_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = KnowledgeGraphEditorService(session)
    graph = await svc.get_graph(graph_id)
    if graph is None:
        raise HTTPException(404, "Graph not found")
    return graph


@router.put("/graphs/{graph_id}")
async def update_graph(
    graph_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = KnowledgeGraphEditorService(session)
    try:
        return await svc.update_graph(graph_id, payload, user.id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/graphs/{graph_id}")
async def delete_graph(
    graph_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = KnowledgeGraphEditorService(session)
    await svc.delete_graph(graph_id)
    return {"message": "Graph deleted"}


@router.post("/graphs/{graph_id}/nodes")
async def add_node(
    graph_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = KnowledgeGraphEditorService(session)
    return await svc.add_node(
        graph_id=graph_id,
        entity_type=payload["entity_type"],
        entity_id=payload["entity_id"],
        label=payload.get("label", payload["entity_type"]),
        x_position=payload.get("x", 0),
        y_position=payload.get("y", 0),
        color=payload.get("color"),
        metadata=payload.get("metadata"),
    )


@router.put("/graphs/nodes/{node_id}")
async def update_node(
    node_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = KnowledgeGraphEditorService(session)
    try:
        return await svc.update_node(node_id, payload)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/graphs/nodes/{node_id}")
async def remove_node(
    node_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = KnowledgeGraphEditorService(session)
    await svc.remove_node(node_id)
    return {"message": "Node removed"}


@router.post("/graphs/{graph_id}/edges")
async def add_edge(
    graph_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = KnowledgeGraphEditorService(session)
    return await svc.add_edge(
        graph_id=graph_id,
        source_node_id=payload["source_node_id"],
        target_node_id=payload["target_node_id"],
        relationship_type=payload["relationship_type"],
        label=payload.get("label"),
        weight=payload.get("weight", 1.0),
        metadata=payload.get("metadata"),
    )


@router.delete("/graphs/edges/{edge_id}")
async def remove_edge(
    edge_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = KnowledgeGraphEditorService(session)
    await svc.remove_edge(edge_id)
    return {"message": "Edge removed"}


@router.post("/graphs/{graph_id}/validate")
async def validate_graph(
    graph_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = KnowledgeGraphEditorService(session)
    return await svc.validate_graph(graph_id)


@router.get("/impact/{entity_type}/{entity_id}")
async def analyze_impact(
    entity_type: str,
    entity_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = KnowledgeGraphEditorService(session)
    return await svc.analyze_impact(entity_type, entity_id)


@router.get("/search")
async def search_entities(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query("", alias="query"),
    limit: int = Query(20),
):
    svc = KnowledgeGraphEditorService(session)
    return await svc.search_entities(q, limit)


@router.post("/bulk-link")
async def bulk_link(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = KnowledgeGraphEditorService(session)
    return await svc.bulk_link(
        entity_type=payload["entity_type"],
        source_ids=payload["source_ids"],
        target_type=payload["target_type"],
        target_ids=payload["target_ids"],
        relationship_type=payload.get("relationship_type", "related_to"),
        graph_id=payload.get("graph_id"),
    )
