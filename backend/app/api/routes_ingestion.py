"""Ingestion API Endpoints."""

from typing import Optional, List
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from backend.app.ingestion.reports import report_ingestion_pipeline
from backend.app.graph.provenance import SourceTier
from data.reports.sample_advisories import SAMPLE_CTI_REPORTS

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


class IngestReportRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    content: str = Field(..., min_length=10)
    source_name: str = Field(default="OSINT Report")
    source_url: Optional[str] = None
    source_tier: SourceTier = SourceTier.TIER_2
    published_at: Optional[str] = None


@router.post("/report")
async def ingest_report_text(payload: IngestReportRequest):
    """Processes unstructured threat advisory text and updates the Knowledge Graph."""
    try:
        result = report_ingestion_pipeline.process_report(
            title=payload.title,
            content=payload.content,
            source_name=payload.source_name,
            source_url=payload.source_url,
            source_tier=payload.source_tier,
            published_at=payload.published_at,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report processing failed: {str(e)}")


@router.post("/upload")
async def upload_document_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    source_name: str = Form("Uploaded Document"),
    source_tier: SourceTier = Form(SourceTier.TIER_2),
):
    """Safely ingests and parses uploaded PDF, STIX JSON, Markdown, or plain text threat reports."""
    filename = file.filename or "unknown_report.txt"
    report_title = title or f"Uploaded: {filename}"

    # Read content with 10MB safety cap
    raw_bytes = await file.read(10 * 1024 * 1024)

    # 1. Handle PDF Documents
    if filename.lower().endswith(".pdf") or file.content_type == "application/pdf":
        extracted_text = report_ingestion_pipeline.extract_text_from_pdf(raw_bytes)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Could not extract readable text from PDF document.")
        result = report_ingestion_pipeline.process_report(
            title=report_title,
            content=extracted_text,
            source_name=source_name,
            source_tier=source_tier,
        )
        return result

    # 2. Handle STIX 2.1 JSON
    if filename.lower().endswith(".json") or file.content_type == "application/json":
        try:
            bundle = json.loads(raw_bytes.decode("utf-8", errors="ignore"))
            if isinstance(bundle, dict) and (bundle.get("type") == "bundle" or "objects" in bundle):
                return report_ingestion_pipeline.process_stix_bundle(bundle, source_name=source_name)
        except Exception:
            pass

    # 3. Default to text / markdown decoding
    try:
        content = raw_bytes.decode("utf-8", errors="ignore")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to decode file content as text")

    result = report_ingestion_pipeline.process_report(
        title=report_title,
        content=content,
        source_name=source_name,
        source_tier=source_tier,
    )
    return result


@router.post("/seed-benchmarks")
async def seed_benchmark_datasets():
    """Seeds the Threat Knowledge Graph with ground-truth APT campaigns (APT29, Sandworm, Lazarus, CloudStorm)."""
    results = []
    for report_data in SAMPLE_CTI_REPORTS:
        tier_enum = getattr(SourceTier, report_data.get("source_tier", "TIER_2"), SourceTier.TIER_2)
        res = report_ingestion_pipeline.process_report(
            title=report_data["title"],
            content=report_data["content"],
            source_name=report_data["source_name"],
            source_url=report_data["source_url"],
            source_tier=tier_enum,
            published_at=report_data["published_at"],
        )
        results.append({
            "report_id": res["report_id"],
            "title": res["title"],
            "metrics": res["metrics"],
        })
    return {
        "status": "success",
        "message": f"Successfully ingested {len(results)} benchmark APT advisories into the knowledge graph.",
        "seeded_reports": results,
    }
