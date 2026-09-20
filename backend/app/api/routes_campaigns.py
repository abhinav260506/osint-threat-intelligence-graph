"""Campaign and Threat Actor Investigation API Endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.graph.graph_engine import knowledge_graph

router = APIRouter(prefix="/campaigns", tags=["Campaigns & Threat Actors"])


@router.get("")
async def list_campaigns_and_actors():
    """Lists all Threat Actors and Campaigns present in the Threat Knowledge Graph."""
    actors = []
    campaigns = []

    for n, d in knowledge_graph.g.nodes(data=True):
        lbl = d.get("label")
        if lbl == "ThreatActor":
            actors.append({
                "id": n,
                "name": d.get("name", n),
                "aliases": d.get("aliases", []),
                "country": d.get("country"),
                "description": d.get("description"),
                "degree": knowledge_graph.g.degree(n),
            })
        elif lbl == "Campaign":
            campaigns.append({
                "id": n,
                "name": d.get("name", n),
                "degree": knowledge_graph.g.degree(n),
                "description": d.get("description"),
            })

    return {
        "threat_actors_count": len(actors),
        "campaigns_count": len(campaigns),
        "threat_actors": actors,
        "campaigns": campaigns,
    }


@router.get("/{entity_id:path}")
async def get_campaign_detail(entity_id: str):
    """Retrieves full campaign profile, associated infrastructure, and tactics."""
    node = knowledge_graph.get_node(entity_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Campaign/Actor '{entity_id}' not found")

    neighbors = knowledge_graph.get_neighbors(entity_id)
    return {
        "profile": node,
        "connections": neighbors,
    }
