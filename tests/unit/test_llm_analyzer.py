"""Tests for LLM Analyzer, fallback, and merging logic."""

import pytest
from backend.app.extraction.llm_analyzer import llm_analyzer


class TestLLMAnalyzer:
    """Validates LLM-powered extraction, merging, and deterministic fallbacks."""

    def test_merge_with_deterministic_empty(self):
        """Should return deterministic results unchanged if LLM result is None."""
        det_iocs = [{"original_value": "192[.]168[.]1[.]1", "normalized_value": "192.168.1.1", "ioc_type": "ipv4", "is_defanged": True, "confidence": 0.9}]
        det_entities = [{"id": "threat-actor--apt29", "canonical_name": "APT29", "entity_type": "threat_actor", "confidence": 1.0}]
        
        merged_iocs, merged_entities, rels = llm_analyzer.merge_with_deterministic(
            llm_result=None,
            deterministic_iocs=det_iocs,
            deterministic_entities=det_entities
        )
        
        assert merged_iocs == det_iocs
        assert merged_entities == det_entities
        assert rels == []

    def test_merge_with_deterministic_llm_data(self):
        """Should append new entities from LLM and extract relationships."""
        det_iocs = [{"original_value": "54.193.127.211", "normalized_value": "54.193.127.211", "ioc_type": "ipv4", "is_defanged": False, "confidence": 0.9}]
        det_entities = [{"id": "threat-actor--apt29", "canonical_name": "APT29", "entity_type": "threat_actor", "confidence": 1.0}]
        
        llm_result = {
            "report_summary": "Test Summary",
            "threat_actors": [
                {"name": "APT29", "aliases": ["Cozy Bear"], "country": "RU", "motivation": "Espionage", "description": "APT29 described"}
            ],
            "malware": [
                {"name": "SUNBURST", "type": "backdoor", "description": "SUNBURST malware description"}
            ],
            "relationships": [
                {"source": "APT29", "source_type": "threat_actor", "relationship": "USES", "target": "SUNBURST", "target_type": "malware", "confidence": "high", "evidence": "APT29 deployed SUNBURST"}
            ],
            "key_findings": ["Finding 1"]
        }
        
        merged_iocs, merged_entities, rels = llm_analyzer.merge_with_deterministic(
            llm_result=llm_result,
            deterministic_iocs=det_iocs,
            deterministic_entities=det_entities
        )
        
        # APT29 is already in det_entities, so it shouldn't be duplicated
        apt29_entries = [e for e in merged_entities if e["canonical_name"] == "APT29"]
        assert len(apt29_entries) == 1
        
        # SUNBURST is new from LLM, so it should be added
        sunburst_entries = [e for e in merged_entities if e["canonical_name"] == "SUNBURST"]
        assert len(sunburst_entries) == 1
        assert sunburst_entries[0]["entity_type"] == "malware"
        assert sunburst_entries[0]["classification_basis"] == "LLM Contextual Analysis"
        
        # Relationship should be extracted
        assert len(rels) == 1
        assert rels[0]["source_name"] == "APT29"
        assert rels[0]["target_name"] == "SUNBURST"
        assert rels[0]["relationship"] == "USES"
        assert rels[0]["confidence"] == 0.90
