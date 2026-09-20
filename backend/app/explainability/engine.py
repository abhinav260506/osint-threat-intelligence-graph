"""Explainability Engine for Threat Intelligence Evidence & Correlation.

Generates rigorous, non-hallucinated evidence breakdowns and structured explanations
for discovered candidate relationships between threat entities.

Synthesizes evidence across five vectors:
  1. Shared Infrastructure (C2 domains, IPs, URLs, hashes)
  2. Shared ATT&CK Techniques (behavioral tradecraft overlap)
  3. Shared Tooling (malware and offensive tools)
  4. Shared Vulnerability Exploitation (CVEs)
  5. Shared Victimology (targeted sectors and organizations)
  6. Intelligence Provenance (co-occurrence in reports, source tiers)
  7. Graph Path Analysis (shortest connecting paths through the graph)
"""

from typing import Dict, List, Any, Set
from backend.app.graph.graph_engine import knowledge_graph
from backend.app.graph.provenance import EvidenceType
from backend.app.core.logging import logger


class ExplainabilityEngine:
    """Provides transparent, fact-based evidence reasoning for graph correlations."""

    def __init__(self, graph_manager=knowledge_graph):
        self.gm = graph_manager

    def _collect_typed_neighbors(self, node_id: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Collects and categorizes all 1-hop neighbors by label type."""
        categories: Dict[str, Dict[str, Dict[str, Any]]] = {
            "infrastructure": {},
            "techniques": {},
            "tools": {},
            "cves": {},
            "sectors": {},
            "reports": {},
            "actors": {},
            "campaigns": {},
        }

        if not self.gm.g.has_node(node_id):
            return categories

        # Outgoing edges
        for _, tgt, data in self.gm.g.out_edges(node_id, data=True):
            tgt_data = self.gm.get_node(tgt)
            if not tgt_data:
                continue
            self._classify_neighbor(tgt, tgt_data, data, categories)

        # Incoming edges
        for src, _, data in self.gm.g.in_edges(node_id, data=True):
            src_data = self.gm.get_node(src)
            if not src_data:
                continue
            self._classify_neighbor(src, src_data, data, categories)

        return categories

    def _classify_neighbor(
        self,
        neighbor_id: str,
        neighbor_data: Dict[str, Any],
        edge_data: Dict[str, Any],
        categories: Dict[str, Dict[str, Dict[str, Any]]],
    ):
        """Classifies a neighbor node into the appropriate evidence category."""
        lbl = neighbor_data.get("label", "")
        name = neighbor_data.get("name", neighbor_id)
        rel_type = edge_data.get("rel_type", "RELATED")
        confidence = edge_data.get("confidence", 0.0)
        evidence_type = edge_data.get("evidence_type", "REPORTED")

        entry = {
            "id": neighbor_id,
            "name": name,
            "label": lbl,
            "relationship": rel_type,
            "confidence": confidence,
            "evidence_type": evidence_type,
            "source_title": edge_data.get("source_title"),
        }

        if lbl in ("Domain", "IP", "URL", "Hash"):
            categories["infrastructure"][neighbor_id] = entry
        elif lbl == "AttackTechnique":
            categories["techniques"][neighbor_id] = entry
        elif lbl in ("Malware", "Tool"):
            categories["tools"][neighbor_id] = entry
        elif lbl == "CVE":
            categories["cves"][neighbor_id] = entry
        elif lbl in ("Sector", "Organization"):
            categories["sectors"][neighbor_id] = entry
        elif lbl == "Report":
            categories["reports"][neighbor_id] = entry
        elif lbl == "ThreatActor":
            categories["actors"][neighbor_id] = entry
        elif lbl == "Campaign":
            categories["campaigns"][neighbor_id] = entry

    def explain_relationship(self, entity_a_id: str, entity_b_id: str) -> Dict[str, Any]:
        """Generates an exhaustive, multi-vector evidence report comparing two entities.

        Returns structured evidence with:
          - Per-category shared indicators
          - Confidence-weighted evidence scoring
          - Graph path traces
          - Human-readable evidence bullets
          - Epistemic classification (never claims definitive attribution from inference)
        """
        node_a = self.gm.get_node(entity_a_id)
        node_b = self.gm.get_node(entity_b_id)

        if not node_a or not node_b:
            return {"error": "One or both entities not found in knowledge graph"}

        name_a = node_a.get("name", entity_a_id)
        name_b = node_b.get("name", entity_b_id)
        label_a = node_a.get("label", "Entity")
        label_b = node_b.get("label", "Entity")

        # 1. Collect typed neighbors for both entities
        cats_a = self._collect_typed_neighbors(entity_a_id)
        cats_b = self._collect_typed_neighbors(entity_b_id)

        # 2. Compute per-category overlaps
        shared_infra = self._compute_overlap(cats_a["infrastructure"], cats_b["infrastructure"])
        shared_techniques = self._compute_overlap(cats_a["techniques"], cats_b["techniques"])
        shared_tools = self._compute_overlap(cats_a["tools"], cats_b["tools"])
        shared_cves = self._compute_overlap(cats_a["cves"], cats_b["cves"])
        shared_sectors = self._compute_overlap(cats_a["sectors"], cats_b["sectors"])
        shared_reports = self._compute_overlap(cats_a["reports"], cats_b["reports"])

        # 3. Compute evidence strength score (0.0 - 1.0)
        evidence_score = self._compute_evidence_score(
            shared_infra, shared_techniques, shared_tools,
            shared_cves, shared_sectors, shared_reports,
        )

        # 4. Path tracing between entities
        connecting_paths = self.gm.find_paths(entity_a_id, entity_b_id, max_depth=4)
        annotated_paths = self._annotate_paths(connecting_paths[:5])

        # 5. Synthesize human-readable evidence bullets
        evidence_bullets = self._synthesize_bullets(
            name_a, name_b,
            shared_infra, shared_techniques, shared_tools,
            shared_cves, shared_sectors, shared_reports,
            connecting_paths,
        )

        # 6. Determine epistemic classification
        classification = self._determine_classification(
            evidence_score, shared_infra, shared_reports, connecting_paths,
        )

        # 7. Generate assessment narrative
        assessment = self._generate_assessment(
            name_a, name_b, label_a, label_b, evidence_score, classification,
            shared_infra, shared_techniques, shared_tools,
        )

        return {
            "entity_a": {"id": entity_a_id, "name": name_a, "label": label_a},
            "entity_b": {"id": entity_b_id, "name": name_b, "label": label_b},
            "evidence_score": round(evidence_score, 3),
            "classification": classification,
            "evidence_summary": evidence_bullets,
            "shared_infrastructure": [
                {"name": v["name"], "type": v["label"], "confidence": v["confidence"]}
                for v in shared_infra.values()
            ],
            "shared_techniques": [
                {"name": v["name"], "confidence": v["confidence"]}
                for v in shared_techniques.values()
            ],
            "shared_tools": [
                {"name": v["name"], "type": v["label"], "confidence": v["confidence"]}
                for v in shared_tools.values()
            ],
            "shared_cves": [
                {"name": v["name"], "confidence": v["confidence"]}
                for v in shared_cves.values()
            ],
            "shared_sectors": [
                {"name": v["name"]}
                for v in shared_sectors.values()
            ],
            "common_reports": [
                {"name": v["name"], "source_title": v.get("source_title")}
                for v in shared_reports.values()
            ],
            "connecting_paths": annotated_paths,
            "assessment": assessment,
        }

    def _compute_overlap(
        self,
        dict_a: Dict[str, Dict[str, Any]],
        dict_b: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """Returns the intersection of two neighbor dictionaries."""
        common_ids = set(dict_a.keys()) & set(dict_b.keys())
        return {k: dict_a[k] for k in common_ids}

    def _compute_evidence_score(
        self,
        shared_infra: Dict, shared_techniques: Dict, shared_tools: Dict,
        shared_cves: Dict, shared_sectors: Dict, shared_reports: Dict,
    ) -> float:
        """Computes a weighted evidence strength score across all vectors."""
        score = 0.0
        # Infrastructure overlap is the strongest signal (weight 0.35)
        score += min(len(shared_infra) * 0.12, 0.35)
        # Technique overlap (weight 0.25)
        score += min(len(shared_techniques) * 0.06, 0.25)
        # Tool/malware overlap (weight 0.20)
        score += min(len(shared_tools) * 0.10, 0.20)
        # CVE overlap (weight 0.10)
        score += min(len(shared_cves) * 0.05, 0.10)
        # Sector overlap (weight 0.05)
        score += min(len(shared_sectors) * 0.02, 0.05)
        # Report co-occurrence (weight 0.05)
        score += min(len(shared_reports) * 0.03, 0.05)
        return min(score, 1.0)

    def _determine_classification(
        self,
        evidence_score: float,
        shared_infra: Dict,
        shared_reports: Dict,
        paths: List,
    ) -> str:
        """Determines epistemic classification per CTI ontology.

        Never claims definitive attribution solely from ML inference.
        """
        if evidence_score >= 0.6 and len(shared_reports) >= 2:
            return "CORROBORATED"
        elif evidence_score >= 0.4 and (len(shared_infra) >= 1 or len(shared_reports) >= 1):
            return "INFERRED"
        elif evidence_score >= 0.2:
            return "PREDICTED"
        elif len(paths) > 0:
            return "PREDICTED"
        else:
            return "INSUFFICIENT_EVIDENCE"

    def _synthesize_bullets(
        self, name_a: str, name_b: str,
        shared_infra: Dict, shared_techniques: Dict, shared_tools: Dict,
        shared_cves: Dict, shared_sectors: Dict, shared_reports: Dict,
        paths: List,
    ) -> List[str]:
        """Generates human-readable evidence summary bullets."""
        bullets = []

        if shared_infra:
            infra_names = [v["name"] for v in list(shared_infra.values())[:4]]
            bullets.append(
                f"✓ {len(shared_infra)} shared infrastructure indicator(s): {', '.join(infra_names)}"
            )

        if shared_techniques:
            tech_names = [v["name"] for v in list(shared_techniques.values())[:4]]
            bullets.append(
                f"✓ {len(shared_techniques)} shared ATT&CK technique(s): {', '.join(tech_names)}"
            )

        if shared_tools:
            tool_names = [v["name"] for v in list(shared_tools.values())[:3]]
            bullets.append(
                f"✓ {len(shared_tools)} overlapping malware/tool(s): {', '.join(tool_names)}"
            )

        if shared_cves:
            cve_names = [v["name"] for v in list(shared_cves.values())]
            bullets.append(
                f"✓ {len(shared_cves)} exploited vulnerability overlap(s): {', '.join(cve_names)}"
            )

        if shared_sectors:
            sec_names = [v["name"] for v in list(shared_sectors.values())]
            bullets.append(
                f"✓ {len(shared_sectors)} common victim sector(s): {', '.join(sec_names)}"
            )

        if shared_reports:
            report_names = [v["name"] for v in list(shared_reports.values())[:3]]
            bullets.append(
                f"✓ Co-mentioned in {len(shared_reports)} intelligence report(s): {', '.join(report_names)}"
            )

        if paths:
            shortest = min(len(p) for p in paths)
            bullets.append(
                f"✓ {len(paths)} connecting path(s) found in graph (shortest: {shortest - 1} hops)"
            )

        if not bullets:
            bullets.append(
                f"✗ No direct 1-hop infrastructure, TTP, or report overlap identified between {name_a} and {name_b}."
            )

        return bullets

    def _annotate_paths(self, paths: List[List[str]]) -> List[List[Dict[str, str]]]:
        """Annotates raw node ID paths with human-readable names and labels."""
        annotated = []
        for path in paths:
            annotated_path = []
            for node_id in path:
                nd = self.gm.get_node(node_id) or {}
                annotated_path.append({
                    "id": node_id,
                    "name": nd.get("name", node_id),
                    "label": nd.get("label", "Unknown"),
                })
            annotated.append(annotated_path)
        return annotated

    def _generate_assessment(
        self, name_a: str, name_b: str, label_a: str, label_b: str,
        evidence_score: float, classification: str,
        shared_infra: Dict, shared_techniques: Dict, shared_tools: Dict,
    ) -> str:
        """Generates a structured assessment narrative."""
        strength = "strong" if evidence_score >= 0.5 else "moderate" if evidence_score >= 0.25 else "limited"

        vectors = []
        if shared_infra:
            vectors.append(f"{len(shared_infra)} shared C2/infrastructure indicators")
        if shared_techniques:
            vectors.append(f"{len(shared_techniques)} overlapping ATT&CK techniques")
        if shared_tools:
            vectors.append(f"{len(shared_tools)} reused malware/tool components")

        vector_text = (
            f", evidenced by {', '.join(vectors)}" if vectors else ""
        )

        epistemic_note = {
            "CORROBORATED": "This relationship is corroborated by multiple independent intelligence sources.",
            "INFERRED": "This relationship is inferred from structural and behavioral graph overlap. It requires human analyst validation before definitive attribution.",
            "PREDICTED": "This is a machine learning prediction based on feature similarity. Confidence is limited and requires additional corroboration.",
            "INSUFFICIENT_EVIDENCE": "Insufficient evidence exists to establish a meaningful relationship at this time.",
        }.get(classification, "Classification pending.")

        return (
            f"{name_a} ({label_a}) and {name_b} ({label_b}) exhibit {strength} structural and behavioral overlap "
            f"(evidence score: {evidence_score:.1%}){vector_text}. "
            f"Classification: {classification}. {epistemic_note}"
        )


explainability_engine = ExplainabilityEngine()
