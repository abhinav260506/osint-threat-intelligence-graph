# STIX 2.1 Canonical Intelligence Mapping

## 1. STIX 2.1 Domain Objects (SDOs) Mapping

| Extraction / Domain Entity | STIX 2.1 Type | Key STIX Attributes | Neo4j Node Equivalent |
| :--- | :--- | :--- | :--- |
| Threat Group / APT | `threat-actor` | `id`, `name`, `aliases`, `roles`, `sophistication` | `(:ThreatActor)` |
| Cyber Campaign | `campaign` | `id`, `name`, `aliases`, `first_seen`, `objective` | `(:Campaign)` |
| Malware / Ransomware / RAT | `malware` | `id`, `name`, `is_family`, `malware_types` | `(:Malware)` |
| Dual-use Attacker Tool | `tool` | `id`, `name`, `tool_types`, `tool_version` | `(:Tool)` |
| MITRE ATT&CK Technique | `attack-pattern` | `id`, `name`, `external_references` (MITRE ID) | `(:AttackTechnique)` |
| Vulnerability | `vulnerability` | `id`, `name` (CVE ID), `external_references` | `(:CVE)` |
| Infrastructure (C2, Staging) | `infrastructure` | `id`, `name`, `infrastructure_types` | `(:Infrastructure)` |
| Observable Indicator (IP/Domain/Hash) | `indicator` | `id`, `pattern` (STIX Pattern), `valid_from` | `(:IP)`, `(:Domain)`, `(:Hash)` |
| Target Victim / Sector | `identity` | `id`, `name`, `identity_class`, `sectors` | `(:Organization)` |
| Source Document / Advisory | `report` | `id`, `name`, `published`, `object_refs` | `(:Report)` |

---

## 2. STIX 2.1 Relationship Objects (SROs) Mapping

| Relational Meaning | STIX SRO `relationship_type` | Neo4j Graph Edge | Source -> Target |
| :--- | :--- | :--- | :--- |
| Group orchestrates campaign | `attributed-to` | `(:ThreatActor)-[:CONDUCTS]->(:Campaign)` | Actor -> Campaign |
| Group utilizes malware/tool | `uses` | `(:ThreatActor)-[:USES]->(:Malware)` | Actor -> Malware |
| Campaign employs payload | `uses` | `(:Campaign)-[:USES]->(:Malware)` | Campaign -> Malware |
| Malware connects to C2 domain | `communicates-with` | `(:Malware)-[:CONTACTS]->(:Domain)` | Malware -> Domain |
| Domain resolves to IP | `consists-of` / `resolves-to` | `(:Domain)-[:RESOLVES_TO]->(:IP)` | Domain -> IP |
| Malware has cryptographic hash | `has-sample` | `(:Malware)-[:HAS_HASH]->(:Hash)` | Malware -> Hash |
| Malware exploits vulnerability | `exploits` | `(:Malware)-[:EXPLOITS]->(:CVE)` | Malware -> CVE |
| Malware executes TTP technique | `uses` | `(:Malware)-[:USES_TECHNIQUE]->(:AttackTechnique)` | Malware -> Technique |
| Group/Campaign targets sector | `targets` | `(:Campaign)-[:TARGETS]->(:Organization)` | Campaign -> Organization |
| Report contains objects | `object_refs` | `(:Report)-[:MENTIONS]->(...)` | Report -> Node |
