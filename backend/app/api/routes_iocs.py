"""IoC Search and Investigation API Endpoints."""

from typing import Optional, List
from fastapi import APIRouter, Query
from backend.app.graph.graph_engine import knowledge_graph
from backend.app.normalization.defanging import refang

router = APIRouter(prefix="/iocs", tags=["Indicators of Compromise"])


@router.get("")
async def list_iocs(
    ioc_type: Optional[str] = Query(None, description="Filter by type (IP, Domain, URL, Hash, CVE)"),
    search: Optional[str] = Query(None, description="Search indicator value substring"),
    limit: int = Query(default=100, ge=1, le=500),
):
    """Lists and searches extracted Indicators of Compromise in the Threat Graph."""
    results = []
    target_labels = {"IP", "Domain", "URL", "Hash", "CVE", "AttackTechnique"}

    if ioc_type:
        target_labels = {ioc_type.strip().capitalize()}

    search_term = refang(search).lower() if search else None

    for n, d in knowledge_graph.g.nodes(data=True):
        lbl = d.get("label", "")
        if lbl in target_labels or (ioc_type is None and lbl in {"IP", "Domain", "URL", "Hash", "CVE", "AttackTechnique"}):
            val = d.get("name", n)
            if search_term and search_term not in val.lower():
                continue

            results.append({
                "id": n,
                "label": lbl,
                "value": val,
                "degree": knowledge_graph.g.degree(n),
                "is_sinkhole": d.get("is_sinkhole_or_shared", False),
                "properties": d,
            })

            if len(results) >= limit:
                break

    return {
        "count": len(results),
        "iocs": results,
    }
