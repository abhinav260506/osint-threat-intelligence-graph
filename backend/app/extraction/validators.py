"""Strict Indicator Validation and Sanity Checking Module.

Ensures no syntactically invalid or malformed IoCs silently pollute the Threat Knowledge Graph.
"""

import ipaddress
import re
from urllib.parse import urlparse
from typing import Optional, Tuple


# Regex patterns for strict format verification
RE_CVE = re.compile(r"^CVE-\d{4}-\d{4,8}$", re.IGNORECASE)
RE_MD5 = re.compile(r"^[a-fA-F0-9]{32}$")
RE_SHA1 = re.compile(r"^[a-fA-F0-9]{40}$")
RE_SHA256 = re.compile(r"^[a-fA-F0-9]{64}$")
RE_EMAIL = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
RE_DOMAIN = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)
RE_MITRE_TECHNIQUE = re.compile(r"^T\d{4}(?:\.\d{3})?$", re.IGNORECASE)


def validate_ipv4(ip_str: str) -> bool:
    """Validates if string is a valid IPv4 address."""
    try:
        ip = ipaddress.IPv4Address(ip_str)
        return not ip.is_unspecified
    except ValueError:
        return False


def validate_ipv6(ip_str: str) -> bool:
    """Validates if string is a valid IPv6 address."""
    try:
        ip = ipaddress.IPv6Address(ip_str)
        return not ip.is_unspecified
    except ValueError:
        return False


def validate_domain(domain_str: str) -> bool:
    """Validates RFC-compliant domain name format."""
    if not domain_str or len(domain_str) > 253:
        return False
    # Avoid IP addresses masquerading as domains
    if validate_ipv4(domain_str) or validate_ipv6(domain_str):
        return False
    return bool(RE_DOMAIN.match(domain_str))


def validate_url(url_str: str) -> bool:
    """Validates URL syntax and ensures hostname exists."""
    try:
        result = urlparse(url_str)
        return all([result.scheme in ("http", "https", "ftp"), result.netloc])
    except Exception:
        return False


def validate_hash(hash_str: str) -> Optional[str]:
    """Validates hash fingerprint and returns hash algorithm type ('MD5', 'SHA1', 'SHA256') or None."""
    h = hash_str.strip()
    if RE_SHA256.match(h):
        return "SHA256"
    if RE_SHA1.match(h):
        return "SHA1"
    if RE_MD5.match(h):
        return "MD5"
    return None


def validate_cve(cve_str: str) -> bool:
    """Validates CVE standard identifier format (e.g., CVE-2023-34362)."""
    return bool(RE_CVE.match(cve_str.strip()))


def validate_email(email_str: str) -> bool:
    """Validates email format."""
    return bool(RE_EMAIL.match(email_str.strip()))


def validate_mitre_id(technique_id: str) -> bool:
    """Validates MITRE ATT&CK technique format (e.g., T1059 or T1059.001)."""
    return bool(RE_MITRE_TECHNIQUE.match(technique_id.strip()))


def validate_ioc(ioc_type: str, value: str) -> Tuple[bool, Optional[str]]:
    """Validates any indicator by its stated type.
    
    Returns:
        (is_valid: bool, error_reason: Optional[str])
    """
    val = value.strip()
    if not val:
        return False, "Empty indicator value"

    match ioc_type.lower():
        case "ipv4" | "ip":
            if validate_ipv4(val):
                return True, None
            return False, f"Invalid IPv4 syntax: {val}"
        case "ipv6":
            if validate_ipv6(val):
                return True, None
            return False, f"Invalid IPv6 syntax: {val}"
        case "domain":
            if validate_domain(val):
                return True, None
            return False, f"Invalid domain syntax or invalid TLD: {val}"
        case "url":
            if validate_url(val):
                return True, None
            return False, f"Invalid URL structure: {val}"
        case "hash" | "sha256" | "sha1" | "md5":
            algo = validate_hash(val)
            if algo:
                return True, None
            return False, f"Invalid cryptographic hash length/hex: {val}"
        case "cve":
            if validate_cve(val):
                return True, None
            return False, f"Invalid CVE format: {val}"
        case "email":
            if validate_email(val):
                return True, None
            return False, f"Invalid email format: {val}"
        case "attack_technique" | "technique":
            if validate_mitre_id(val):
                return True, None
            return False, f"Invalid ATT&CK technique format: {val}"
        case _:
            # Unknown type defaults to length sanity check
            return len(val) < 500, None
