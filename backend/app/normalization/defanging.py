"""Defanged IoC Normalization Subsystem.

Normalizes obfuscated indicators (e.g., 'hxxp://', 'example[.]com', '192[.]168[.]1[.]1')
while preserving the exact raw representation for forensic provenance.
"""

import re
from typing import Dict, Any


def defang(value: str) -> str:
    """Defangs a raw IoC to prevent accidental clicking or resolution."""
    val = value.replace("http://", "hxxp://").replace("https://", "hxxps://")
    val = val.replace(".", "[.]").replace("@", "[@]")
    return val


def refang(value: str) -> str:
    """Refangs/normalizes an obfuscated IoC to canonical operational syntax.
    
    Handles:
    - [.] , (.), {,} , {.} -> .
    - hxxp:// , hxxps:// , hXXp:// , hXXps:// , fxp:// -> http://, https://
    - [@] , (@) , {@} -> @
    - [:] , (:) -> :
    """
    if not value:
        return ""

    val = value.strip()

    # Protocol refanging
    val = re.sub(r"^hxxps?://", lambda m: "https://" if "s" in m.group(0).lower() else "http://", val, flags=re.IGNORECASE)
    val = re.sub(r"^h[xX]{2}ps?://", lambda m: "https://" if "s" in m.group(0).lower() else "http://", val)

    # Obfuscated dots
    val = re.sub(r"\[\.\]|\(\.\)|\{\.\}|\[dot\]|\(dot\)", ".", val, flags=re.IGNORECASE)
    val = re.sub(r"\[\,\]|\(\,\)|\{\,\}", ".", val)

    # Obfuscated at signs
    val = re.sub(r"\[@\]|\(@\)|\{@\}|\[at\]|\(at\)", "@", val, flags=re.IGNORECASE)

    # Obfuscated colons
    val = re.sub(r"\[:\]|\(:\)|\{:\}", ":", val)

    # Strip surrounding quotes or brackets
    val = val.strip("'\"<>[](){}")
    return val


def process_defanged_indicator(raw_indicator: str, ioc_type: str) -> Dict[str, Any]:
    """Wraps raw and normalized representations with indicator typing."""
    normalized = refang(raw_indicator)
    return {
        "original_value": raw_indicator,
        "normalized_value": normalized,
        "type": ioc_type,
        "is_defanged": raw_indicator != normalized,
    }
