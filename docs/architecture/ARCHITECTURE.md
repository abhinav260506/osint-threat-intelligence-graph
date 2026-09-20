# System Architecture Specification

## 1. System Overview & Data Flow

The platform transforms unstructured and semi-structured OSINT cyber threat intelligence into an explainable STIX 2.1-aligned Neo4j Threat Knowledge Graph, subsequently employing Graph Data Science (GDS) and Machine Learning (HDBSCAN / Link Prediction) to identify candidate campaign relationships and shared malicious infrastructure.

```
+-----------------------------------------------------------------------------------+
| 1. Ingestion Layer                                                                |
| - Pluggable ThreatIntelSource (RSS, CISA Alerts, MITRE ATT&CK STIX, Raw Reports) |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 2. Extraction & Normalization Layer                                               |
| - Deterministic Regex IoC Extraction (IPv4, IPv6, Domain, URL, Hash, CVE)         |
| - Defanging Normalization (e.g. hxxp://, [.] -> standard forms, preserving raw)  |
| - Strict RFC/Format Validation (IPv4, Domain regex, SHA256 length, CVE format)    |
| - Rule-based / spaCy Entity Extraction (Threat Actors, Malware, Tools, Sectors)   |
| - Entity Resolution & Alias Canonicalization (e.g., APT29 == Cozy Bear == NOBELIUM|
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 3. Canonical STIX 2.1 & Neo4j Knowledge Graph                                     |
| - STIX 2.1 Domain & Relationship Object Mapper                                    |
| - Neo4j Enterprise / Community Knowledge Graph with Schema Constraints & Indexes  |
| - Mandatory Provenance Subsystem on all nodes & edges                             |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 4. Graph Data Science & Machine Learning Engine                                   |
| - GDS Community Detection (Louvain / Leiden)                                      |
| - GDS Node Centrality & PageRank                                                  |
| - Heterogeneous Feature Engineering (Shared Infra, ATT&CK TTP vector, Temporal)   |
| - Unsupervised ML Clustering (HDBSCAN)                                            |
| - Link Prediction & Potential Relationship Discovery                              |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 5. Explainability & Correlation Subsystem                                         |
| - Synthesized Evidence Aggregator (GDS Community overlap + ML Cluster overlap)    |
| - Transparent, non-fabricated evidence breakdown & confidence scoring             |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 6. REST API & Analyst SOC/TIP Dashboard                                           |
| - FastAPI RESTful Backend with Swagger / OpenAPI                                  |
| - React 18 / TypeScript / Vite / Tailwind CSS / Cytoscape.js 2D Graph Explorer    |
| - Interactive Ingestion Workbench, IoC Search, Cluster & Provenance Inspector     |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

1. **Separation of Concerns**:
   - `ingestion`: Source adapters and raw text extraction only.
   - `extraction`: Deterministic parsing, defanging, and syntax validation.
   - `normalization`: Entity resolution, deduplication, confidence assignment.
   - `stix`: Canonical representation mappings.
   - `graph`: Neo4j interaction, Cypher queries, provenance tracking.
   - `analytics`: Graph Data Science, ML feature vectors, HDBSCAN clustering.
   - `explainability`: Deterministic evidence chain generation.
   - `api`: FastAPI route handlers performing contract validation.

2. **Zero Unjustified LLM / AI Hallucination**:
   - Extraction is deterministic first (Regex, MITRE lookup, Rule-based NER).
   - Relationship explanations are constructed exclusively from graph topology and verified co-occurrences.

3. **Strict Epistemic Classification**:
   - `OBSERVED`: Direct telemetry / honeypot observation.
   - `REPORTED`: Explicitly stated in an external CTI advisory.
   - `EXTRACTED`: Parsed via automated NLP/Regex from an unstructured document.
   - `CORROBORATED`: Independently verified across 2+ distinct reputable sources.
   - `INFERRED`: Derived via deterministic graph rules (e.g. transitivity).
   - `PREDICTED`: Machine-learning or link-prediction candidate connection.
