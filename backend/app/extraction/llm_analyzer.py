"""LLM-Powered Threat Intelligence Analyzer.

Uses Google Gemini to perform deep contextual analysis of unstructured threat
reports — extracting entities, relationships, TTPs, and generating structured
threat intelligence that deterministic regex cannot capture.

The LLM layer supplements (not replaces) the deterministic extraction engine:
  1. Deterministic Engine: High-precision, zero-hallucination IoC extraction
  2. LLM Engine: Deep contextual understanding, relationship inference, narrative analysis
  3. Merger: Combines both, deduplicates, and validates

Falls back gracefully to deterministic-only mode if no API key is configured.
"""

import json
import re
import os
from typing import Dict, List, Any, Optional, Tuple
from backend.app.core.logging import logger

# Lazy import to avoid hard dependency
_genai = None
_model = None


def _get_model():
    """Lazily initialize the Gemini model."""
    global _genai, _model
    if _model is not None:
        return _model

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set. LLM analysis will be skipped; deterministic extraction only.")
        return None

    try:
        import google.generativeai as genai
        _genai = genai
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-2.0-flash")
        logger.info("Gemini LLM Analyzer initialized successfully.")
        return _model
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model: {e}")
        return None


# Structured extraction prompt designed for CTI analysis
EXTRACTION_SYSTEM_PROMPT = """You are an expert Cyber Threat Intelligence (CTI) analyst. 
Your task is to analyze the given threat report and extract ALL structured intelligence from it.

You MUST return a valid JSON object (no markdown fences, no explanation text) with exactly this schema:

{
  "report_summary": "A 2-3 sentence executive summary of the threat report",
  "threat_actors": [
    {
      "name": "Canonical name (e.g. APT29)",
      "aliases": ["Alternative names mentioned"],
      "country": "Two-letter ISO country code or null",
      "motivation": "Espionage/Financial/Sabotage/Unknown",
      "description": "Brief description of this actor's role in the report"
    }
  ],
  "malware": [
    {
      "name": "Malware family name",
      "type": "backdoor/trojan/ransomware/wiper/loader/stealer/rat/tool",
      "description": "What this malware does in the context of the report"
    }
  ],
  "tools": [
    {
      "name": "Tool name (e.g. Cobalt Strike, Mimikatz)",
      "purpose": "What the tool is used for"
    }
  ],
  "campaigns": [
    {
      "name": "Campaign name if mentioned (e.g. Operation CloudStorm)",
      "description": "Brief description"
    }
  ],
  "iocs": {
    "domains": ["list of domains mentioned"],
    "ips": ["list of IP addresses"],
    "urls": ["list of URLs"],
    "hashes": [{"value": "hash_value", "type": "SHA256/SHA1/MD5"}],
    "emails": ["list of email addresses"]
  },
  "cves": ["CVE-YYYY-NNNNN format"],
  "attack_techniques": [
    {
      "technique_id": "T1059",
      "technique_name": "Command and Scripting Interpreter",
      "how_used": "Brief description of how this technique was used"
    }
  ],
  "target_sectors": ["Government", "Financial Services", etc.],
  "relationships": [
    {
      "source": "Entity name (actor/malware/campaign)",
      "source_type": "threat_actor/malware/tool/campaign",
      "relationship": "USES/DEPLOYS/TARGETS/EXPLOITS/CONTACTS/ATTRIBUTED_TO/CONDUCTS",
      "target": "Entity name",
      "target_type": "malware/tool/sector/cve/domain/ip/technique",
      "confidence": "high/medium/low",
      "evidence": "Brief quote or context from the report supporting this relationship"
    }
  ],
  "key_findings": ["List of 3-5 critical intelligence findings from the report"]
}

CRITICAL RULES:
- Extract EVERYTHING mentioned in the report. Do not skip any entities, IoCs, or relationships.
- Defanged indicators (e.g. hxxp://, [.], (@)) should be returned in their ORIGINAL form as written.
- For relationships, extract explicit AND implicit relationships. If the report says "APT29 deployed SUNBURST which contacted avsvmcloud.com", extract:
  - APT29 USES SUNBURST
  - SUNBURST CONTACTS avsvmcloud.com
- Return ONLY the JSON object. No markdown code fences. No explanatory text before or after.
"""


class LLMAnalyzer:
    """LLM-powered deep analysis engine for threat intelligence reports."""

    def __init__(self):
        self._model = None
        self._initialized = False

    def _ensure_model(self) -> bool:
        """Lazy initialization of the LLM model."""
        if self._initialized:
            return self._model is not None
        self._model = _get_model()
        self._initialized = True
        return self._model is not None

    @property
    def is_available(self) -> bool:
        """Returns True if the LLM analyzer has a valid API key and model."""
        return self._ensure_model()

    def analyze_report(self, text: str, title: str = "") -> Optional[Dict[str, Any]]:
        """Sends a threat report to the LLM for deep contextual analysis.

        Returns structured extraction result or None if LLM is unavailable.
        """
        if not self._ensure_model():
            return None

        # Truncate very long reports to stay within token limits
        max_chars = 28000
        truncated = text[:max_chars] if len(text) > max_chars else text

        prompt = f"""{EXTRACTION_SYSTEM_PROMPT}

--- THREAT REPORT ---
Title: {title}

{truncated}
--- END REPORT ---

Extract all structured threat intelligence from the above report. Return ONLY the JSON object."""

        try:
            response = self._model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                },
            )

            raw_text = response.text.strip()

            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)

            result = json.loads(raw_text)
            logger.info(f"LLM analysis completed for report: {title}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return None

    def merge_with_deterministic(
        self,
        llm_result: Optional[Dict[str, Any]],
        deterministic_iocs: List[Dict[str, Any]],
        deterministic_entities: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Merges LLM extraction results with deterministic regex results.

        Priority: Deterministic IoCs are authoritative for exact indicators.
        LLM adds: contextual relationships, deeper entity classification, campaign inference.

        Returns: (merged_iocs, merged_entities, llm_relationships)
        """
        if llm_result is None:
            return deterministic_iocs, deterministic_entities, []

        merged_entities = list(deterministic_entities)
        merged_iocs = list(deterministic_iocs)
        llm_relationships = []

        seen_entity_names = {e.get("canonical_name", "").lower() for e in deterministic_entities}
        seen_ioc_values = {i.get("normalized_value", "").lower() for i in deterministic_iocs}

        # 1. Merge LLM-discovered threat actors
        for actor in llm_result.get("threat_actors", []):
            name = actor.get("name", "").strip()
            if name and name.lower() not in seen_entity_names:
                seen_entity_names.add(name.lower())
                merged_entities.append({
                    "id": f"threat-actor--llm-{_safe_id(name)}",
                    "matched_text": name,
                    "canonical_name": name,
                    "entity_type": "threat_actor",
                    "aliases": actor.get("aliases", []),
                    "confidence": 0.85,
                    "country": actor.get("country"),
                    "description": actor.get("description"),
                    "classification_basis": "LLM Contextual Analysis",
                })

        # 2. Merge LLM-discovered malware
        for mal in llm_result.get("malware", []):
            name = mal.get("name", "").strip()
            if name and name.lower() not in seen_entity_names:
                seen_entity_names.add(name.lower())
                merged_entities.append({
                    "id": f"malware--llm-{_safe_id(name)}",
                    "matched_text": name,
                    "canonical_name": name,
                    "entity_type": "malware",
                    "aliases": [],
                    "confidence": 0.82,
                    "country": None,
                    "description": mal.get("description"),
                    "classification_basis": "LLM Contextual Analysis",
                })

        # 3. Merge LLM-discovered tools
        for tool in llm_result.get("tools", []):
            name = tool.get("name", "").strip()
            if name and name.lower() not in seen_entity_names:
                seen_entity_names.add(name.lower())
                merged_entities.append({
                    "id": f"tool--llm-{_safe_id(name)}",
                    "matched_text": name,
                    "canonical_name": name,
                    "entity_type": "tool",
                    "aliases": [],
                    "confidence": 0.80,
                    "country": None,
                    "description": tool.get("purpose"),
                    "classification_basis": "LLM Contextual Analysis",
                })

        # 4. Merge LLM-discovered campaigns
        for camp in llm_result.get("campaigns", []):
            name = camp.get("name", "").strip()
            if name and name.lower() not in seen_entity_names:
                seen_entity_names.add(name.lower())
                merged_entities.append({
                    "id": f"campaign--llm-{_safe_id(name)}",
                    "matched_text": name,
                    "canonical_name": name,
                    "entity_type": "campaign",
                    "aliases": [],
                    "confidence": 0.85,
                    "country": None,
                    "description": camp.get("description"),
                    "classification_basis": "LLM Contextual Analysis",
                })

        # 5. Merge LLM-discovered sectors
        for sector in llm_result.get("target_sectors", []):
            sector = sector.strip()
            if sector and sector.lower() not in seen_entity_names:
                seen_entity_names.add(sector.lower())
                merged_entities.append({
                    "id": f"identity--sector-llm-{_safe_id(sector)}",
                    "matched_text": sector,
                    "canonical_name": sector,
                    "entity_type": "sector",
                    "aliases": [],
                    "confidence": 0.90,
                    "country": None,
                    "description": f"Target Sector: {sector}",
                    "classification_basis": "LLM Contextual Analysis",
                })

        # 6. Extract LLM relationships (these are the key value-add)
        for rel in llm_result.get("relationships", []):
            confidence_map = {"high": 0.90, "medium": 0.75, "low": 0.60}
            llm_relationships.append({
                "source_name": rel.get("source", ""),
                "source_type": rel.get("source_type", ""),
                "relationship": rel.get("relationship", "RELATED_TO"),
                "target_name": rel.get("target", ""),
                "target_type": rel.get("target_type", ""),
                "confidence": confidence_map.get(rel.get("confidence", "medium"), 0.75),
                "evidence": rel.get("evidence", ""),
                "classification_basis": "LLM Relationship Extraction",
            })

        return merged_iocs, merged_entities, llm_relationships


def _safe_id(name: str) -> str:
    """Creates a filesystem/URL-safe identifier from a name."""
    return re.sub(r"[^a-zA-Z0-9-]", "-", name.lower()).strip("-")[:60]


# Global singleton
llm_analyzer = LLMAnalyzer()
