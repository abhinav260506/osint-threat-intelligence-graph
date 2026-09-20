"""ThreatGraph-AI - Master FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.graph.neo4j import neo4j_manager
from backend.app.api.routes_ingestion import router as ingestion_router
from backend.app.api.routes_graph import router as graph_router
from backend.app.api.routes_iocs import router as iocs_router
from backend.app.api.routes_campaigns import router as campaigns_router
from backend.app.api.routes_analytics import router as analytics_router
from data.reports.sample_advisories import SAMPLE_CTI_REPORTS
from backend.app.ingestion.reports import report_ingestion_pipeline
from backend.app.graph.provenance import SourceTier


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle event handler."""
    logger.info("Initializing ThreatGraph AI Engine...")
    neo4j_manager.connect()

    # Pre-seed benchmark threat intelligence reports on startup if graph is empty
    logger.info("Pre-seeding benchmark ground-truth APT threat intelligence datasets...")
    for report_data in SAMPLE_CTI_REPORTS:
        tier_enum = getattr(SourceTier, report_data.get("source_tier", "TIER_2"), SourceTier.TIER_2)
        report_ingestion_pipeline.process_report(
            title=report_data["title"],
            content=report_data["content"],
            source_name=report_data["source_name"],
            source_url=report_data["source_url"],
            source_tier=tier_enum,
            published_at=report_data["published_at"],
        )
    logger.info("ThreatGraph AI operational and ready for intelligence queries.")
    yield
    logger.info("Shutting down ThreatGraph AI Engine...")
    neo4j_manager.close()


app = FastAPI(
    title="OSINT Threat Intelligence & Graph Data Science Platform (ThreatGraph AI)",
    description=(
        "Production-grade CTI platform that transforms unstructured OSINT data into a STIX 2.1 "
        "Threat Knowledge Graph and applies Graph Data Science and Machine Learning to discover "
        "hidden relationships and cluster cyber-espionage campaigns."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS + ["*"],  # Permissive for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Applies secure HTTP headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Mount API V1 Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(ingestion_router, prefix=api_v1_prefix)
app.include_router(graph_router, prefix=api_v1_prefix)
app.include_router(iocs_router, prefix=api_v1_prefix)
app.include_router(campaigns_router, prefix=api_v1_prefix)
app.include_router(analytics_router, prefix=api_v1_prefix)


@app.get("/health", tags=["Observability"])
async def health_check():
    """Liveness probe for orchestration and monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "neo4j_connected": neo4j_manager.is_available,
    }


@app.get("/ready", tags=["Observability"])
async def readiness_check():
    """Readiness probe."""
    return {"status": "ready"}
