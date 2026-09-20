"""Threat Intelligence Provenance and Epistemic Classification Module.

Tracks full audit trails, evidence types, source reliability, and confidence scores
for every entity and relationship in the knowledge graph.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    OBSERVED = "OBSERVED"        # Direct telemetry/sensor observation
    REPORTED = "REPORTED"        # Stated in external CTI document
    EXTRACTED = "EXTRACTED"      # Automated NLP/Regex extraction
    CORROBORATED = "CORROBORATED" # Verified across multiple independent sources
    INFERRED = "INFERRED"        # Derived via deterministic graph rules
    PREDICTED = "PREDICTED"      # ML / Link prediction candidate


class SourceTier(str, Enum):
    TIER_1 = "TIER_1"  # CISA, NCSC, CERT, MITRE (Base Reliability: 0.95)
    TIER_2 = "TIER_2"  # Mandiant, CrowdStrike, Kaspersky (Base: 0.85)
    TIER_3 = "TIER_3"  # AlienVault OTX, URLhaus, vx-underground (Base: 0.65)
    TIER_4 = "TIER_4"  # Unverified blogs, paste sites, social feeds (Base: 0.40)


TIER_RELIABILITY_MAP = {
    SourceTier.TIER_1: 0.95,
    SourceTier.TIER_2: 0.85,
    SourceTier.TIER_3: 0.65,
    SourceTier.TIER_4: 0.40,
}


class ProvenanceRecord(BaseModel):
    """Immutable provenance record attached to graph nodes and relationships."""
    source_report_id: str
    source_title: Optional[str] = "OSINT Advisory"
    source_url: Optional[str] = None
    source_tier: SourceTier = SourceTier.TIER_2
    evidence_type: EvidenceType = EvidenceType.REPORTED
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    context_snippet: Optional[str] = None
    extracted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    corroboration_count: int = 1

    def calculate_effective_confidence(self) -> float:
        """Calculates final confidence accounting for source tier and corroboration."""
        base = TIER_RELIABILITY_MAP.get(self.source_tier, 0.70)
        # Corroboration boost (up to +0.20 for multiple independent sources)
        boost = min(0.20, (self.corroboration_count - 1) * 0.10)
        return min(1.0, round(self.confidence * base + boost, 3))
