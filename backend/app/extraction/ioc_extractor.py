"""Deterministic IoC Extraction Engine.

Performs layered regex extraction with defanging detection, RFC validation,
context snipping, and confidence scoring.
"""

import re
from typing import List, Dict, Any, Set
from backend.app.normalization.defanging import refang
from backend.app.extraction.validators import (
    validate_ipv4,
    validate_ipv6,
    validate_domain,
    validate_url,
    validate_hash,
    validate_cve,
    validate_email,
    validate_mitre_id,
)
from backend.app.core.security import is_sinkhole_or_shared_infra

# Pre-compiled Regex Patterns for Unstructured Text Extraction (matching both fanged and defanged)
RE_DEFANGED_URL = re.compile(
    r"\b(?:h(?:xx|XX|tt)ps?://|ftp://)[^\s<>\"'{}|\\^`\[\]]+(?:\[\.\]|\(\.\)|\{\.\}|\.)[^\s<>\"'{}|\\^`]+",
    re.IGNORECASE,
)
RE_DEFANGED_IP = re.compile(
    r"\b(?:\d{1,3}(?:\[\.\]|\(\.\)|\{\.\}|\.)){3}\d{1,3}\b"
)
RE_DEFANGED_DOMAIN = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\[\.\]|\(\.\)|\{\.\}|\.))+(?:[a-zA-Z]{2,24})\b",
    re.IGNORECASE,
)
RE_HASH_SHA256 = re.compile(r"\b[a-fA-F0-9]{64}\b")
RE_HASH_SHA1 = re.compile(r"\b[a-fA-F0-9]{40}\b")
RE_HASH_MD5 = re.compile(r"\b[a-fA-F0-9]{32}\b")
RE_CVE = re.compile(r"\bCVE-\d{4}-\d{4,8}\b", re.IGNORECASE)
RE_DEFANGED_EMAIL = re.compile(
    r"\b[a-zA-Z0-9_.+-]+(?:\[@\]|\(@\)|\{@\}|@)[a-zA-Z0-9-]+(?:\[\.\]|\(\.\)|\{\.\}|\.)+[a-zA-Z0-9-.]+\b"
)
RE_ATTACK_TECHNIQUE = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")


class IoCExtractor:
    """Production-grade IoC Extractor with provenance context capturing."""

    def __init__(self):
        pass

    def extract_from_text(self, text: str, min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """Extracts, defangs, validates, and annotates all indicators from unstructured text."""
        if not text:
            return []

        results: List[Dict[str, Any]] = []
        seen_normalized: Set[str] = set()

        def _add_ioc(raw_match: str, ioc_type: str, validator_fn, confidence: float = 0.9):
            norm = refang(raw_match)
            # Remove trailing punctuation often captured in natural language
            norm = norm.rstrip(".,;!?:")
            key = f"{ioc_type}:{norm.lower()}"

            if key in seen_normalized:
                return

            is_valid = validator_fn(norm)
            if not is_valid:
                return

            is_sinkhole = is_sinkhole_or_shared_infra(norm)
            adj_confidence = 0.3 if is_sinkhole else confidence

            seen_normalized.add(key)
            results.append({
                "original_value": raw_match,
                "normalized_value": norm,
                "ioc_type": ioc_type,
                "is_defanged": raw_match != norm,
                "is_sinkhole_or_shared": is_sinkhole,
                "confidence": adj_confidence,
                "context_snippet": self._get_snippet(text, raw_match),
            })

        # 1. URLs
        for m in RE_DEFANGED_URL.finditer(text):
            _add_ioc(m.group(0), "url", validate_url, 0.95)

        # 2. IPv4
        for m in RE_DEFANGED_IP.finditer(text):
            _add_ioc(m.group(0), "ipv4", validate_ipv4, 0.95)

        # 3. Domains
        for m in RE_DEFANGED_DOMAIN.finditer(text):
            raw = m.group(0)
            norm = refang(raw)
            # Prevent pure IPs matching as domains
            if not validate_ipv4(norm):
                _add_ioc(raw, "domain", validate_domain, 0.90)

        # 4. Hashes (SHA256, SHA1, MD5)
        for m in RE_HASH_SHA256.finditer(text):
            _add_ioc(m.group(0), "sha256", lambda x: validate_hash(x) == "SHA256", 1.0)
        for m in RE_HASH_SHA1.finditer(text):
            _add_ioc(m.group(0), "sha1", lambda x: validate_hash(x) == "SHA1", 0.95)
        for m in RE_HASH_MD5.finditer(text):
            _add_ioc(m.group(0), "md5", lambda x: validate_hash(x) == "MD5", 0.90)

        # 5. CVEs
        for m in RE_CVE.finditer(text):
            _add_ioc(m.group(0).upper(), "cve", validate_cve, 1.0)

        # 6. Emails
        for m in RE_DEFANGED_EMAIL.finditer(text):
            _add_ioc(m.group(0), "email", validate_email, 0.95)

        # 7. ATT&CK Techniques
        for m in RE_ATTACK_TECHNIQUE.finditer(text):
            _add_ioc(m.group(0).upper(), "attack_technique", validate_mitre_id, 0.95)

        return [r for r in results if r["confidence"] >= min_confidence]

    def _get_snippet(self, text: str, match_str: str, window: int = 60) -> str:
        """Captures contextual surrounding text for explainability and provenance."""
        idx = text.find(match_str)
        if idx == -1:
            return ""
        start = max(0, idx - window)
        end = min(len(text), idx + len(match_str) + window)
        snippet = text[start:end].replace("\n", " ").strip()
        if start > 0:
            snippet = f"...{snippet}"
        if end < len(text):
            snippet = f"{snippet}..."
        return snippet
