"""Advanced Entity Extraction & Classification Subsystem.

Combines deterministic canonical alias resolution with dynamic CTI heuristic pattern
recognition for threat actors, emerging threat clusters, malware families, tools,
campaigns, and target sectors.
"""

import re
import uuid
from typing import List, Dict, Any, Set, Tuple
from backend.app.normalization.entity_resolution import (
    entity_resolver,
    KNOWN_THREAT_ACTORS,
    KNOWN_MALWARE_FAMILIES,
    CanonicalEntity,
)

# Standard Critical Infrastructure & Victim Industry Sectors
STANDARD_SECTORS = [
    "Defense",
    "Financial Services",
    "Energy",
    "Healthcare",
    "Government",
    "Critical Infrastructure",
    "Telecommunications",
    "Aerospace",
    "Technology",
    "Education",
    "Manufacturing",
    "Transportation",
    "Legal",
    "Media",
    "Automotive",
]

# Dynamic Regex Heuristics for Unseen / Emerging Threat Actors
RE_ACTOR_DESIGNATIONS = re.compile(
    r"\b(?:APT-?\d+|UNC\d+|TA\d+|DEV-\d+|Storm-\d+|UAC-\d+|FIN\d+|TAG-\d+)\b",
    re.IGNORECASE,
)

# Dynamic Microsoft / CrowdStrike / Vendor Animal/Weather Naming Schemes
RE_VENDOR_ACTOR_NAMES = re.compile(
    r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(?:Blizzard|Typhoon|Panda|Bear|Kitten|Sandstorm|Sleet|Tempest|Chollima|Spider|Jackal|Falcon|Dragon|Scorpion|Ounce))\b"
)

# Dynamic Malware Naming Patterns
RE_DYNAMIC_MALWARE = re.compile(
    r"\b(?:[A-Z][a-zA-Z0-9_\-]{2,20}(?:RAT|Stealer|Locker|Wiper|Loader|Backdoor|Ransomware|Beacon|Bot)|(?:Backdoor|Trojan|Ransomware|Worm)\.[A-Z][a-zA-Z0-9_\-]+)\b"
)

# Target Campaign Patterns (e.g. "Operation Ghost", "SolarWinds Intrusion", "MOVEit Exploitation")
RE_CAMPAIGN_PATTERNS = re.compile(
    r"\b(?:Operation\s+[A-Z][a-zA-Z0-9_\-]+|(?:SolarWinds|MOVEit|NotPetya|WannaCry|SolarMarker|DarkSide|PaperCut|Log4j|CitrixBleed)\s+(?:Campaign|Attack|Exploitation|Incident|Intrusion|Heist))\b",
    re.IGNORECASE,
)


class EntityExtractor:
    """Extracts and classifies Threat Actors, Malware, Tools, Campaigns, and Sectors."""

    def __init__(self):
        # Index all known terms for instant high-precision keyword scanning
        all_terms = set()
        for e in KNOWN_THREAT_ACTORS + KNOWN_MALWARE_FAMILIES:
            all_terms.add(e.canonical_name)
            all_terms.update(e.aliases)

        # Sort longest terms first to handle multi-word matches greedily
        sorted_terms = sorted(all_terms, key=len, reverse=True)
        escaped_terms = [re.escape(t) for t in sorted_terms]
        self.re_known_entities = re.compile(r"\b(" + "|".join(escaped_terms) + r")\b", re.IGNORECASE)

    def extract_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extracts, resolves, and classifies all threat entities from text."""
        if not text:
            return []

        extracted: List[Dict[str, Any]] = []
        seen_keys: Set[str] = set()

        # 1. High-Precision Canonical Matches
        for match in self.re_known_entities.finditer(text):
            raw_mention = match.group(0)
            canonical, confidence = entity_resolver.resolve(raw_mention)

            if canonical and canonical.id not in seen_keys:
                seen_keys.add(canonical.id)
                extracted.append({
                    "id": canonical.id,
                    "matched_text": raw_mention,
                    "canonical_name": canonical.canonical_name,
                    "entity_type": canonical.entity_type,
                    "aliases": canonical.aliases,
                    "confidence": confidence,
                    "country": canonical.attribution_country,
                    "description": canonical.description,
                    "classification_basis": "Canonical CTI Knowledge Base Match",
                })

        # 2. Dynamic Threat Actor Designations (e.g. UNC3944, APT-41, Storm-0811)
        for match in RE_ACTOR_DESIGNATIONS.finditer(text):
            mention = match.group(0).upper()
            canonical, conf = entity_resolver.resolve(mention)
            if canonical:
                if canonical.id not in seen_keys:
                    seen_keys.add(canonical.id)
                    extracted.append({
                        "id": canonical.id,
                        "matched_text": mention,
                        "canonical_name": canonical.canonical_name,
                        "entity_type": canonical.entity_type,
                        "aliases": canonical.aliases,
                        "confidence": conf,
                        "country": canonical.attribution_country,
                        "description": canonical.description,
                        "classification_basis": "Resolved Designation",
                    })
            else:
                actor_id = f"threat-actor--dynamic-{uuid.uuid5(uuid.NAMESPACE_DNS, mention)}"
                if actor_id not in seen_keys:
                    seen_keys.add(actor_id)
                    extracted.append({
                        "id": actor_id,
                        "matched_text": mention,
                        "canonical_name": mention,
                        "entity_type": "threat_actor",
                        "aliases": [],
                        "confidence": 0.85,
                        "country": None,
                        "description": f"Unclassified Threat Actor cluster: {mention}",
                        "classification_basis": "Regex Threat Actor Designation",
                    })

        # 3. Dynamic Vendor Actor Schemes (e.g. "Volt Typhoon", "Mint Sandstorm", "Scatter Swine")
        for match in RE_VENDOR_ACTOR_NAMES.finditer(text):
            mention = match.group(0)
            canonical, conf = entity_resolver.resolve(mention)
            if canonical:
                if canonical.id not in seen_keys:
                    seen_keys.add(canonical.id)
                    extracted.append({
                        "id": canonical.id,
                        "matched_text": mention,
                        "canonical_name": canonical.canonical_name,
                        "entity_type": canonical.entity_type,
                        "aliases": canonical.aliases,
                        "confidence": conf,
                        "country": canonical.attribution_country,
                        "description": canonical.description,
                        "classification_basis": "Resolved Vendor Alias",
                    })
            else:
                actor_id = f"threat-actor--dynamic-{uuid.uuid5(uuid.NAMESPACE_DNS, mention)}"
                if actor_id not in seen_keys:
                    seen_keys.add(actor_id)
                    extracted.append({
                        "id": actor_id,
                        "matched_text": mention,
                        "canonical_name": mention,
                        "entity_type": "threat_actor",
                        "aliases": [],
                        "confidence": 0.88,
                        "country": None,
                        "description": f"Identified Adversary Group: {mention}",
                        "classification_basis": "Vendor Naming Pattern Heuristic",
                    })

        # 4. Dynamic Malware Patterns (e.g. "RedLine Stealer", "AsyncRAT", "HermeticWiper")
        for match in RE_DYNAMIC_MALWARE.finditer(text):
            mention = match.group(0)
            canonical, conf = entity_resolver.resolve(mention)
            if canonical:
                if canonical.id not in seen_keys:
                    seen_keys.add(canonical.id)
                    extracted.append({
                        "id": canonical.id,
                        "matched_text": mention,
                        "canonical_name": canonical.canonical_name,
                        "entity_type": canonical.entity_type,
                        "aliases": canonical.aliases,
                        "confidence": conf,
                        "country": None,
                        "description": canonical.description,
                        "classification_basis": "Resolved Malware Family",
                    })
            else:
                mal_id = f"malware--dynamic-{uuid.uuid5(uuid.NAMESPACE_DNS, mention)}"
                if mal_id not in seen_keys:
                    seen_keys.add(mal_id)
                    extracted.append({
                        "id": mal_id,
                        "matched_text": mention,
                        "canonical_name": mention,
                        "entity_type": "malware",
                        "aliases": [],
                        "confidence": 0.82,
                        "country": None,
                        "description": f"Identified Malware/Tool Component: {mention}",
                        "classification_basis": "Malware Suffix Heuristic",
                    })

        # 5. Cyber Campaign Extraction
        for match in RE_CAMPAIGN_PATTERNS.finditer(text):
            camp_name = match.group(0)
            camp_id = f"campaign--dynamic-{uuid.uuid5(uuid.NAMESPACE_DNS, camp_name)}"
            if camp_id not in seen_keys:
                seen_keys.add(camp_id)
                extracted.append({
                    "id": camp_id,
                    "matched_text": camp_name,
                    "canonical_name": camp_name,
                    "entity_type": "campaign",
                    "aliases": [],
                    "confidence": 0.90,
                    "country": None,
                    "description": f"Identified Cyber Campaign: {camp_name}",
                    "classification_basis": "Campaign Pattern Match",
                })

        # 6. Target Industry Sector Extraction
        for sector in STANDARD_SECTORS:
            if re.search(r"\b" + re.escape(sector) + r"\b", text, re.IGNORECASE):
                sec_id = f"identity--sector-{sector.lower().replace(' ', '-')}"
                if sec_id not in seen_keys:
                    seen_keys.add(sec_id)
                    extracted.append({
                        "id": sec_id,
                        "matched_text": sector,
                        "canonical_name": sector,
                        "entity_type": "sector",
                        "aliases": [],
                        "confidence": 0.92,
                        "country": None,
                        "description": f"Target Industry Sector: {sector}",
                        "classification_basis": "Critical Infrastructure Taxonomy",
                    })

        return extracted


entity_extractor = EntityExtractor()
