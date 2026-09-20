"""Integration Tests for FastAPI Endpoints and Ingestion Pipeline."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.graph.graph_engine import knowledge_graph


@pytest.mark.asyncio
async def test_health_and_readiness():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_ingest_report_and_query_graph():
    knowledge_graph.clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "title": "Threat Alert: Emotet Campaign Resurgence",
            "content": "Emotet loaders communicating with 185.220.101[.]5 and c2-gate[.]org exploiting CVE-2022-30190.",
            "source_name": "Integration Test Advisory",
        }
        res_ingest = await ac.post("/api/v1/ingestion/report", json=payload)
        assert res_ingest.status_code == 200
        res_data = res_ingest.json()
        assert res_data["metrics"]["nodes_added"] > 1

        # Query Graph
        res_graph = await ac.get("/api/v1/graph")
        assert res_graph.status_code == 200
        graph_data = res_graph.json()
        assert graph_data["stats"]["total_nodes"] > 0
        assert graph_data["stats"]["total_edges"] > 0

        # Query Analytics
        res_analytics = await ac.get("/api/v1/analytics/communities")
        assert res_analytics.status_code == 200

        # Query Link Prediction
        res_lp = await ac.get("/api/v1/analytics/link-prediction")
        assert res_lp.status_code == 200
