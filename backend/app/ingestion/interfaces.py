"""Abstract Base Interfaces for Pluggable CTI Sources."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class RawThreatDocument(BaseModel):
    """Container for unstructured/semi-structured ingested content."""
    document_id: str
    title: str
    source_name: str
    source_url: Optional[str] = None
    source_tier: str = "TIER_2"
    published_at: str
    raw_content: str
    content_type: str = "text/plain"  # text/plain, text/markdown, application/pdf, application/json


class ThreatIntelSource(ABC):
    """Abstract interface for all pluggable threat intelligence adapters."""

    @abstractmethod
    def fetch(self) -> List[RawThreatDocument]:
        """Fetches raw documents from the external or local feed source."""
        pass

    @abstractmethod
    def parse(self, raw_doc: RawThreatDocument) -> Dict[str, Any]:
        """Parses raw content into structured extracted indicators and entities."""
        pass

    @abstractmethod
    def validate(self, parsed_data: Dict[str, Any]) -> bool:
        """Validates syntactic integrity and schema constraints."""
        pass

    @abstractmethod
    def normalize(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes entities and maps them to canonical STIX representations."""
        pass
