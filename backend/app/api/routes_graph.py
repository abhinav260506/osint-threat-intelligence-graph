"""Graph Exploration and Query API Endpoints."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from backend.app.graph.graph_engine import knowledge_graph

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


@router.get("")
async def get_entire_graph(limit: int = Query(default=600, ge=10, le=2000)):
    """Fetches the active Threat Knowledge Graph in Cytoscape-compatible JSON format."""
    return knowledge_graph.get_graph_data(limit=limit)


@router.get("/entity/{node_id:path}")
async def get_entity_subgraph(node_id: str):
    """Fetches entity metadata, attributes, and 1-hop connected neighbors."""
    node = knowledge_graph.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Entity node '{node_id}' not found")

    neighbors = knowledge_graph.get_neighbors(node_id)
    return {
        "entity": node,
        "neighbor_count": len(neighbors),
        "neighbors": neighbors,
    }


@router.get("/path")
async def find_entity_path(
    source_id: str = Query(..., description="Starting entity ID"),
    target_id: str = Query(..., description="Destination entity ID"),
    max_depth: int = Query(default=4, ge=1, le=6),
):
    """Finds simple graph paths between two threat entities up to max_depth."""
    paths = knowledge_graph.find_paths(source_id=source_id, target_id=target_id, max_depth=max_depth)
    return {
        "source_id": source_id,
        "target_id": target_id,
        "paths_found": len(paths),
        "paths": paths,
    }


@router.post("/clear")
async def clear_graph():
    """Resets all nodes and edges in the graph."""
    knowledge_graph.clear()
    return {"status": "success", "message": "Knowledge graph cleared"}
