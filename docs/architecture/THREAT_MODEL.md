# Threat Model & Intelligence Poisoning Defense

## 1. System Threat Landscape & STRIDE Analysis

| STRIDE Category | Threat Description | Attack Vector / Scenario | Platform Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Fabricated CTI Reports & Fake Threat Actors | Attacker publishes malicious RSS feeds or fake advisories attributing attacks to legitimate entities | Multi-source corroboration required before high confidence; strict source reputation tiers; provenance tracked per relation. |
| **Tampering** | Graph Poisoning & False Link Injection | Malicious actor feeds IoCs sharing legitimate IP (e.g. Cloudflare / 8.8.8.8) to link unrelated campaigns | Whitelist / sinkhole filtering for popular CDNs and public DNS; strict entity resolution algorithms; community confidence decay. |
| **Repudiation** | Intelligence Provenance Loss | Analyst cannot trace why a critical malware node is linked to an APT group | Immutable provenance records (`source_report_id`, `published_at`, `extracted_at`, `evidence_type`) stored directly on every graph relationship. |
| **Information Disclosure** | API / Secret Leakage | Exposing database credentials or raw ingestion tokens | Environment-based configuration, no hardcoded secrets, strict CORS and security headers, API token auth. |
| **Denial of Service** | Malformed / ReDoS / Deep Graph Query DoS | Uploading adversarial regex strings, recursive payloads, or triggering full-graph traversal queries | Pre-compiled linear regex engine; document size limits (max 10MB); depth-limited Cypher queries (`LIMIT`, max path depth 4). |
| **Elevation of Privilege** | Sandboxed Document Exploitation | Uploading weaponized PDF / Office documents with active macros or shellcode | Headless, non-executing text extraction parsers; no script/macro execution; file type MIME validation; privilege isolation. |

---

## 2. Threat Intelligence Poisoning Defenses

1. **Source Reliability Weighting**:
   - `TIER_1` (Official advisories: CISA, NCSC, CERT, MITRE): Base reliability `0.95`.
   - `TIER_2` (Established security vendors: Mandiant, CrowdStrike, Kaspersky): Base reliability `0.85`.
   - `TIER_3` (Public community feeds, AlienVault OTX, URLhaus): Base reliability `0.65`.
   - `TIER_4` (Unverified / Anonymous blogs / Social feeds): Base reliability `0.40`.

2. **Sinkhole & Cloud CDN Whitelist Filtering**:
   - Exclude known shared infrastructure (e.g., `8.8.8.8`, `1.1.1.1`, major AWS/Cloudflare shared gateways) from single-point-of-contact attribution links to prevent false massive graph clusters.

3. **Epistemic Label Separation**:
   - The graph strictly separates `OBSERVED`/`REPORTED` from `PREDICTED` edges. ML clustering never alters ground-truth relationships.
