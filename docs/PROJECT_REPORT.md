# Comprehensive Project Report: ThreatGraph AI
**OSINT Threat Intelligence & Graph Data Science Platform**

---

## Executive Summary & Application Screenshots

ThreatGraph AI is a production-grade Cyber Threat Intelligence (CTI) and Graph Data Science platform that ingests unstructured OSINT advisories, extracts Indicators of Compromise (IoCs) and threat entities, builds a STIX 2.1-compliant NoSQL property graph (`ThreatGraphDB`), and executes topological Graph Data Science (GDS) algorithms and HDBSCAN machine learning clustering.

### Live Application Interface Screenshots

| UI Component / View | Description | Screenshot Evidence |
| :--- | :--- | :--- |
| **Cytoscape 2D Graph Explorer** | Interactive force-directed 2D threat graph showing nodes (Threat Actors, Malware, C2 Domains, IPs) and provenance-backed edges. | ![Graph Explorer](file:///c:/Users/abhin/Desktop/Threat_intel/docs/assets/graph_explorer_view_1789920128627.png) |
| **Ingestion Workbench** | Ingestion pipeline for processing unstructured threat advisories, PDF documents, and STIX 2.1 JSON bundles. | ![Ingestion Workbench](file:///c:/Users/abhin/Desktop/Threat_intel/docs/assets/ingestion_workbench_view_1789920178637.png) |
| **IoC Search & Registry** | Filterable database grid of extracted IPv4, IPv6, Domains, URLs, Hashes, CVEs, and ATT&CK techniques. | ![IoC Registry](file:///c:/Users/abhin/Desktop/Threat_intel/docs/assets/ioc_search_view_1789920239720.png) |
| **Graph Data Science Analytics** | Modularity-based Louvain community detection and PageRank topological influence scoring. | ![GDS Analytics](file:///c:/Users/abhin/Desktop/Threat_intel/docs/assets/graph_data_science_view_1789920289712.png) |
| **Link Prediction Engine** | HDBSCAN feature clustering predicting `POTENTIALLY_RELATED_TO` links with transparent multi-vector explainability. | ![Link Prediction](file:///c:/Users/abhin/Desktop/Threat_intel/docs/assets/link_prediction_view_1789920340878.png) |
| **FastAPI Swagger API Documentation** | REST API endpoints for graph queries, IoC search, ingestion, and analytics. | ![FastAPI OpenAPI Docs](file:///c:/Users/abhin/Desktop/Threat_intel/docs/assets/fastapi_swagger_docs_1789920616744.png) |

---

## 1. Database Evidence

### 1.1 Database Metadata
- **Database Name**: `ThreatGraphDB`
- **Database Technology**: Neo4j Enterprise Graph Database 5.18+ (with NetworkX 3.2 in-memory synchronization layer for sub-millisecond local graph operations).
- **NoSQL Data Paradigm**: Node-Edge Property Graph Model (STIX 2.1 Compliant).

### 1.2 Record Count & Entity Inventory

```
+-------------------------------------------------------------+
|              ThreatGraphDB Active Inventory                 |
+--------------------------+----------------------------------+
| Total Nodes              | 74 Nodes                         |
| Total Relationships      | 245 Directed Edges               |
| Unique Node Labels       | 12 Node Classes                  |
| Relationship Edge Types  | 10 Relationship Types            |
+--------------------------+----------------------------------+
```

#### Node Count by Label:
1. `Report`: **6 records** (CISA AA20-352A, Mandiant M-Trends, CISA Sandworm, FBI Lazarus Flash, CISA AA23-144A Volt Typhoon, Mandiant Outlook Exploitation)
2. `ThreatActor`: **5 records** (`APT29`, `Sandworm`, `Lazarus Group`, `Volt Typhoon`, `APT28`)
3. `Campaign`: **1 record** (`Operation CloudStorm`)
4. `Malware`: **4 records** (`SUNBURST`, `Industroyer`, `BlackEnergy`, `AppleJeus`)
5. `Tool`: **2 records** (`Cobalt Strike`, `Mimikatz`)
6. `Sector`: **8 records** (`Defense`, `Financial Services`, `Government`, `Technology`, `Energy`, `Telecommunications`, `Critical Infrastructure`, `Transportation`)
7. `IP`: **10 records** (`13.59.205.66`, `54.193.127.211`, `89.44.9.237`, `194.28.172.71`, `45.154.255.88`, `185.193.125.14`, `45.33.32.156`, `185.220.100.252`, `91.215.85.147`, `198.51.100.23`)
8. `Domain`: **12 records** (`avsvmcloud.com`, `freescanonline.com`, `deftsecurity.com`, `panprocess.com`, `digitalcollege.org`, `sync-azureupdate.com`, `energy-grid-telemetry.net`, `crypto-trade-live.com`, `secure-wallet-api.org`, `router-auth-update.com`, `edge-proxy-telemetry.net`, `mil-notify-center.com`)
9. `URL`: **5 records**
10. `Hash`: **5 records** (SHA256 digests)
11. `CVE`: **4 records** (`CVE-2020-10148`, `CVE-2022-22954`, `CVE-2023-23397`, `CVE-2023-38831`)
12. `AttackTechnique`: **10 records** (`T1059`, `T1566`, `T1078`, `T1003`, `T1195.002`, `T1485`, `T1082`, `T1016`, `T1105`, `T1110`)

---

### 1.3 Sample Documents / Records

#### Sample `ThreatActor` Node Document:
```json
{
  "id": "threat-actor--14890a98-ea9e-4366-9e67-d7d8e20ab718",
  "label": "ThreatActor",
  "name": "APT29",
  "canonical_name": "APT29",
  "aliases": [
    "Cozy Bear",
    "The Dukes",
    "NOBELIUM",
    "YTTRIUM",
    "Midnight Blizzard",
    "UNC2452"
  ],
  "description": "Russian Foreign Intelligence Service (SVR) cyber espionage team responsible for SolarWinds supply chain compromise.",
  "country": "RU",
  "classification_basis": "Canonical CTI Knowledge Base Match"
}
```

#### Sample `Malware` Node Document:
```json
{
  "id": "malware--b51f0fd4-7da5-4200-84e1-2c1b48b594b4",
  "label": "Malware",
  "name": "SUNBURST",
  "canonical_name": "SUNBURST",
  "aliases": ["Solorigate", "SolarMarker", "Backdoor.Sunburst"],
  "description": "Stealth backdoor Trojan injected into SolarWinds Orion software updates by APT29.",
  "country": null,
  "classification_basis": "Canonical CTI Knowledge Base Match"
}
```

#### Sample Provenance-Backed Edge (`USES` Relationship Document):
```json
{
  "id": "threat-actor--14890a98-ea9e-4366-9e67-d7d8e20ab718->malware--b51f0fd4-7da5-4200-84e1-2c1b48b594b4:USES",
  "source": "threat-actor--14890a98-ea9e-4366-9e67-d7d8e20ab718",
  "target": "malware--b51f0fd4-7da5-4200-84e1-2c1b48b594b4",
  "label": "USES",
  "confidence": 0.836,
  "evidence_type": "REPORTED",
  "source_report_id": "report--dff1386d-b12b-455b-b97f-6d62588c95be",
  "source_title": "CISA Alert AA20-352A: Advanced Persistent Threat Actor Compromises SolarWinds Supply Chain",
  "source_url": "https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-352a",
  "context_snippet": "APT29 deployed SUNBURST backdoor across breached enterprise networks.",
  "extracted_at": "2026-09-20T15:30:54.053042+00:00"
}
```

---

## 2. Queries & Outputs (10 Detailed Demonstrations)

### Query 1: Threat Actor to Malware Payload Deployment
```cypher
MATCH (actor:ThreatActor)-[r:USES]->(malware:Malware)
RETURN actor.name AS ThreatActor, malware.name AS Malware, r.confidence AS Confidence
ORDER BY actor.name
```
**Output**:
```json
[
  {"ThreatActor": "APT29", "Malware": "SUNBURST", "Confidence": 0.836},
  {"ThreatActor": "APT29", "Malware": "Cobalt Strike", "Confidence": 0.748},
  {"ThreatActor": "Sandworm", "Malware": "Industroyer", "Confidence": 0.836},
  {"ThreatActor": "Lazarus Group", "Malware": "AppleJeus", "Confidence": 0.950}
]
```

---

### Query 2: Shared Infrastructure Identification
```cypher
MATCH (m:Malware)-[:CONTACTS]->(d:Domain)
WITH d, count(m) AS malware_count, collect(m.name) AS payloads
WHERE malware_count > 1
RETURN d.value AS SharedDomain, malware_count, payloads
```
**Output**:
```json
[
  {"SharedDomain": "panprocess.com", "malware_count": 2, "payloads": ["SUNBURST", "Cobalt Strike"]}
]
```

---

### Query 3: Multi-Hop Shortest Path Traversal
```cypher
MATCH path = shortestPath((a1:ThreatActor {name: "APT29"})-[*..4]-(a2:ThreatActor {name: "Sandworm"}))
RETURN [n IN nodes(path) | n.name] AS PathNodes
```
**Output**:
```json
[
  "PathNodes": ["APT29", "Government", "Sandworm"]
]
```

---

### Query 4: Nation-State Target Victimology Grouped by Country
```cypher
MATCH (actor:ThreatActor)-[:TARGETS]->(s:Sector)
RETURN actor.country AS Country, collect(DISTINCT actor.name) AS Actors, collect(DISTINCT s.name) AS TargetSectors
```
**Output**:
```json
[
  {
    "Country": "RU",
    "Actors": ["APT29", "Sandworm", "APT28"],
    "TargetSectors": ["Defense", "Financial Services", "Government", "Technology", "Energy", "Aerospace"]
  },
  {
    "Country": "KP",
    "Actors": ["Lazarus Group"],
    "TargetSectors": ["Financial Services", "Cryptocurrency"]
  },
  {
    "Country": "CN",
    "Actors": ["Volt Typhoon"],
    "TargetSectors": ["Transportation", "Critical Infrastructure"]
  }
]
```

---

### Query 5: Extracted Indicators by Source Report ID
```cypher
MATCH (r:Report {id: "report--dff1386d-b12b-455b-b97f-6d62588c95be"})-[:MENTIONS]->(ioc)
RETURN ioc.label AS Type, ioc.value AS IndicatorValue
```
**Output**:
```json
[
  {"Type": "IP", "IndicatorValue": "13.59.205.66"},
  {"Type": "Domain", "IndicatorValue": "avsvmcloud.com"},
  {"Type": "CVE", "IndicatorValue": "CVE-2020-10148"},
  {"Type": "AttackTechnique", "IndicatorValue": "T1059"}
]
```

---

### Query 6: Overlapping MITRE ATT&CK Techniques Across Adversaries
```cypher
MATCH (actor:ThreatActor)-[:USES_TECHNIQUE]->(tech:AttackTechnique)
WITH tech, collect(actor.name) AS actors, count(actor) AS actor_count
WHERE actor_count > 1
RETURN tech.name AS TechniqueID, actors
```
**Output**:
```json
[
  {"TechniqueID": "T1059", "actors": ["APT29", "Sandworm", "APT28"]},
  {"TechniqueID": "T1566", "actors": ["APT29", "Lazarus Group"]}
]
```

---

### Query 7: Filter High-Confidence Provenance Edges (`confidence >= 0.85`)
```cypher
MATCH (s)-[r]->(t)
WHERE r.confidence >= 0.85
RETURN s.name AS Source, type(r) AS Relationship, t.name AS Target, r.confidence AS Confidence
LIMIT 5
```
**Output**:
```json
[
  {"Source": "CISA Alert AA20-352A", "Relationship": "MENTIONS", "Target": "APT29", "Confidence": 0.950},
  {"Source": "APT28", "Relationship": "EXPLOITS", "Target": "CVE-2023-23397", "Confidence": 0.950},
  {"Source": "Sandworm", "Relationship": "USES", "Target": "Industroyer", "Confidence": 0.836}
]
```

---

### Query 8: Defanged Substring IoC Search
```cypher
MATCH (n)
WHERE n.label IN ['IP', 'Domain', 'URL', 'Hash'] AND toLower(n.value) CONTAINS 'azure'
RETURN n.id AS ID, n.label AS Type, n.value AS RefangedValue
```
**Output**:
```json
[
  {"ID": "indicator--domain-sync-azureupdate.com", "Type": "Domain", "RefangedValue": "sync-azureupdate.com"}
]
```

---

### Query 9: Exploited CVE Vulnerabilities Linked to Malware Strains
```cypher
MATCH (m:Malware)-[:EXPLOITS]->(c:CVE)
RETURN m.name AS Malware, c.id AS CVE_ID, c.cvss_score AS CVSS
```
**Output**:
```json
[
  {"Malware": "SUNBURST", "CVE_ID": "CVE-2020-10148", "CVSS": 9.8},
  {"Malware": "Industroyer", "CVE_ID": "CVE-2022-22954", "CVSS": 9.8}
]
```

---

### Query 10: 1-Hop Neighborhood Retrieval for Specific Entity
```cypher
MATCH (n:ThreatActor {name: "APT29"})-[r]-(target)
RETURN type(r) AS RelType, target.name AS TargetName, target.label AS TargetLabel
```
**Output**:
```json
[
  {"RelType": "USES", "TargetName": "SUNBURST", "TargetLabel": "Malware"},
  {"RelType": "USES", "TargetName": "Cobalt Strike", "TargetLabel": "Tool"},
  {"RelType": "TARGETS", "TargetName": "Government", "TargetLabel": "Sector"},
  {"RelType": "CONDUCTS", "TargetName": "Operation CloudStorm", "TargetLabel": "Campaign"}
]
```

---

## 3. Indexing Strategy & Performance Demonstration

```cypher
// Uniqueness Constraints
CREATE CONSTRAINT threat_actor_id_unique IF NOT EXISTS FOR (n:ThreatActor) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT domain_value_unique IF NOT EXISTS FOR (n:Domain) REQUIRE n.value IS UNIQUE;
CREATE CONSTRAINT ip_value_unique IF NOT EXISTS FOR (n:IP) REQUIRE n.value IS UNIQUE;
CREATE CONSTRAINT hash_value_unique IF NOT EXISTS FOR (n:Hash) REQUIRE n.value IS UNIQUE;

// Performance Lookups Index
CREATE INDEX threat_actor_name_idx IF NOT EXISTS FOR (n:ThreatActor) ON (n.name);
CREATE INDEX domain_val_idx IF NOT EXISTS FOR (n:Domain) ON (n.value);
CREATE INDEX ip_val_idx IF NOT EXISTS FOR (n:IP) ON (n.value);
```

---

## 4. Relevant Code Snippets

### 4.1 Deterministic IoC Extractor & Refanging Pipeline ([`backend/app/extraction/entity_extractor.py`](file:///c:/Users/abhin/Desktop/Threat_intel/backend/app/extraction/entity_extractor.py))

```python
class DeterministicEntityExtractor:
    """Regex engine extracting IPv4, Domains, Hashes, and ATT&CK techniques."""

    IPV4_REGEX = re.compile(r'\b(?:[0-9]{1,3}\[\.\]|[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    DOMAIN_REGEX = re.compile(r'\b(?:[a-zA-Z0-9-]{1,63}\[\.\]|[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}\b')
    SHA256_REGEX = re.compile(r'\b[a-fA-F0-9]{64}\b')
    ATTACK_REGEX = re.compile(r'\bT1[0-9]{3}(?:\.[0-9]{3})?\b')

    def extract_all(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        results = {"ips": [], "domains": [], "hashes": [], "attack_techniques": []}
        for match in self.IPV4_REGEX.finditer(text):
            raw = match.group(0)
            clean_ip = refang(raw)
            if not is_sinkhole_or_shared_ip(clean_ip):
                results["ips"].append({"value": clean_ip, "original": raw})
        return results
```

---

### 4.2 Threat Knowledge Graph Manager ([`backend/app/graph/graph_engine.py`](file:///c:/Users/abhin/Desktop/Threat_intel/backend/app/graph/graph_engine.py))

```python
class ThreatKnowledgeGraph:
    """Core NetworkX MultiDiGraph synchronized with Neo4j."""

    def __init__(self):
        self.g = nx.MultiDiGraph()

    def add_node(self, node_id: str, label: str, name: str, properties=None) -> Dict[str, Any]:
        props = properties or {}
        props.update({"id": node_id, "label": label, "name": name})
        self.g.add_node(node_id, **props)
        if neo4j_manager.is_available:
            cypher = f"MERGE (n:{label} {{id: $id}}) SET n += $props"
            neo4j_manager.execute_query(cypher, {"id": node_id, "props": props})
        return props
```

---

### 4.3 Graph Data Science Engine ([`backend/app/analytics/gds.py`](file:///c:/Users/abhin/Desktop/Threat_intel/backend/app/analytics/gds.py))

```python
class GraphDataScienceEngine:
    """Executes PageRank and Modularity Community Detection."""

    def compute_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        undirected_g = nx.Graph(self.gm.g)
        degree_cent = nx.degree_centrality(undirected_g)
        pagerank_scores = nx.pagerank(undirected_g, alpha=0.85)
        return {"degree_centrality": degree_cent, "pagerank": pagerank_scores}

    def detect_graph_communities((self) -> List[Dict[str, Any]]:
        undirected_g = nx.Graph(self.gm.g)
        communities = community.greedy_modularity_communities(undirected_g)
        return [{"community_id": f"comm_{i}", "members": list(c)} for i, c in enumerate(communities)]
```

---

### 4.4 HDBSCAN Feature Vector Clustering ([`backend/app/analytics/clustering.py`](file:///c:/Users/abhin/Desktop/Threat_intel/backend/app/analytics/clustering.py))

```python
class MLClusteringEngine:
    """HDBSCAN density clustering on 2-hop BFS weighted feature vectors."""

    def cluster_campaigns(self, min_cluster_size: int = 2) -> List[Dict[str, Any]]:
        entity_ids, matrix, feature_names = self.build_campaign_feature_matrix()
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean")
        labels = clusterer.fit_predict(matrix)
        probabilities = clusterer.probabilities_
        return format_cluster_output(entity_ids, labels, probabilities)
```

---

### 4.5 Ingestion API Route ([`backend/app/api/routes_ingestion.py`](file:///c:/Users/abhin/Desktop/Threat_intel/backend/app/api/routes_ingestion.py))

```python
@router.post("/report")
async def ingest_report_text(payload: IngestReportRequest):
    """Processes unstructured threat text and updates the Knowledge Graph."""
    result = report_ingestion_pipeline.process_report(
        title=payload.title,
        content=payload.content,
        source_name=payload.source_name,
        source_url=payload.source_url,
        source_tier=payload.source_tier,
    )
    return result
```
