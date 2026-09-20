"""Security, Input Sanitization, and Intelligence Poisoning Defense Safeguards."""

import re
from typing import Set

# Shared Public/CDN Infrastructure whitelist to avoid false-positive graph supernodes
SINKHOLE_AND_PUBLIC_INFRASTRUCTURE: Set[str] = {
    # Public DNS / Resolvers
    "8.8.8.8",
    "8.8.4.4",
    "1.1.1.1",
    "1.0.0.1",
    "9.9.9.9",
    "149.112.112.112",
    "208.67.222.222",
    "208.67.220.220",
    # Localhost / RFC 1918 / Documentation ranges
    "127.0.0.1",
    "0.0.0.0",
    "255.255.255.255",
    "localhost",
    # Common shared CDNs / Gateways
    "cloudflare.com",
    "amazonaws.com",
    "akamai.net",
    "fastly.net",
    "github.com",
    "raw.githubusercontent.com",
    "pastebin.com",
}


def is_sinkhole_or_shared_infra(indicator_value: str) -> bool:
    """Checks if an indicator is a common shared infrastructure or sinkhole.
    
    Prevents artificial graph bridging (Intelligence Poisoning).
    """
    clean_val = indicator_value.strip().lower()
    return clean_val in SINKHOLE_AND_PUBLIC_INFRASTRUCTURE


def sanitize_input_text(raw_text: str, max_chars: int = 2_000_000) -> str:
    """Sanitizes unstructured input text, preventing null-byte and buffer issues."""
    if not raw_text:
        return ""
    # Strip null bytes and non-printable control characters (keeping \n, \r, \t)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw_text)
    return cleaned[:max_chars]
