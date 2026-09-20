"""Graph Data Science, Machine Learning, and Explainability Analytics API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from backend.app.analytics.gds import gds_engine
from backend.app.analytics.clustering import ml_clustering_engine
from backend.app.analytics.link_prediction import link_prediction_engine
from backend.app.explainability.engine import explainability_engine

router = APIRouter(prefix="/analytics", tags=["Graph Data Science & ML Analytics"])


@router.get("/centrality")
async def get_centrality_and_pagerank():
    """Computes Degree Centrality (hubs) and PageRank (influence) across the Threat Graph."""
    return gds_engine.compute_centrality_metrics()


@router.get("/communities")
async def get_graph_communities():
    """Executes Modularity Community Detection to discover topological threat clusters."""
    communities = gds_engine.detect_graph_communities()
    return {
        "community_count": len(communities),
        "communities": communities,
    }


@router.get("/clusters")
async def get_ml_campaign_clusters():
    """Runs HDBSCAN Unsupervised Clustering on multi-dimensional threat feature vectors."""
    clusters = ml_clustering_engine.cluster_campaigns()
    return {
        "cluster_count": len(clusters),
        "clusters": clusters,
    }


@router.get("/link-prediction")
async def discover_candidate_relationships(
    min_score: float = Query(default=0.40, ge=0.0, le=1.0),
    top_k: int = Query(default=15, ge=1, le=50),
):
    """Discovers hidden candidate relationships between campaigns and malware families."""
    candidates = link_prediction_engine.discover_candidate_relationships(
        min_combined_score=min_score,
        top_k=top_k,
    )
    return {
        "candidate_count": len(candidates),
        "candidate_relationships": candidates,
    }


@router.get("/explain")
async def explain_relationship(
    entity_a: str = Query(..., description="First Entity ID"),
    entity_b: str = Query(..., description="Second Entity ID"),
):
    """Generates a structured, evidence-backed explainability report comparing two entities."""
    explanation = explainability_engine.explain_relationship(entity_a, entity_b)
    if "error" in explanation:
        raise HTTPException(status_code=404, detail=explanation["error"])
    return explanation
