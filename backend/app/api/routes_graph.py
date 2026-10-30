"""Graph Exploration and Query API Endpoints."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
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


class CypherQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Cypher query to execute")


@router.post("/cypher")
async def execute_custom_cypher(payload: CypherQueryRequest):
    """Executes a custom Cypher query against Neo4j or in-memory fallback and returns Cytoscape-formatted graph elements."""
    from backend.app.graph.neo4j import neo4j_manager
    from backend.app.core.logging import logger

    if neo4j_manager.is_available:
        try:
            return neo4j_manager.execute_cypher_to_graph(payload.query)
        except Exception as e:
            logger.warning(f"Neo4j Cypher failed, attempting in-memory fallback: {e}")

    try:
        result = knowledge_graph.execute_cypher(payload.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cypher execution failed: {str(e)}")

