"""Link Prediction and Potential Relationship Discovery Engine.

Computes multi-dimensional similarity to discover unobserved candidate relationships:

  1. Feature Space Cosine Similarity — TTP + Infra + CVE + Sector + Tooling profile vectors
  2. Graph Topological Jaccard Similarity — Shared 1-hop neighbor overlap
  3. Adamic-Adar Index — Weighted neighbor overlap penalizing high-degree hub nodes
  4. Provenance Co-occurrence — Entities mentioned in the same reports

Combines signals into a weighted composite link prediction score with epistemic
classification following strict CTI ontology:
  - OBSERVED / REPORTED / EXTRACTED / CORROBORATED / INFERRED / PREDICTED
"""

from typing import List, Dict, Any, Set, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.graph.graph_engine import knowledge_graph
from backend.app.analytics.clustering import ml_clustering_engine
from backend.app.analytics.gds import gds_engine
from backend.app.core.logging import logger


class LinkPredictionEngine:
    """Discovers candidate hidden relationships across threat entities."""

    def __init__(self, graph_manager=knowledge_graph, clustering_engine=None, gds=None):
        self.gm = graph_manager
        self._clustering_engine = clustering_engine
        self._gds = gds

    @property
    def clustering(self):
        if self._clustering_engine is not None:
            return self._clustering_engine
        return ml_clustering_engine

    @property
    def gds(self):
        if self._gds is not None:
            return self._gds
        return gds_engine

    def _compute_adamic_adar(self, node_a: str, node_b: str) -> float:
        """Adamic-Adar index: weighted neighbor overlap penalizing high-degree hubs."""
        if not self.gm.g.has_node(node_a) or not self.gm.g.has_node(node_b):
            return 0.0

        undirected = self.gm.g.to_undirected(as_view=True)
        neighbors_a = set(undirected.neighbors(node_a))
        neighbors_b = set(undirected.neighbors(node_b))
        common = neighbors_a & neighbors_b

        if not common:
            return 0.0

        score = 0.0
        for cn in common:
            degree = undirected.degree(cn)
            if degree > 1:
                score += 1.0 / np.log(degree)
            else:
                score += 1.0

        # Normalize to [0,1] range
        max_possible = min(len(neighbors_a), len(neighbors_b))
        if max_possible > 0:
            return min(score / max_possible, 1.0)
        return 0.0

    def _compute_report_cooccurrence(self, node_a: str, node_b: str) -> float:
        """Measures how often two entities are mentioned in the same intelligence reports."""
        reports_a: Set[str] = set()
        reports_b: Set[str] = set()

        # Collect reports mentioning entity A
        for src, _, data in self.gm.g.in_edges(node_a, data=True):
            src_data = self.gm.get_node(src)
            if src_data and src_data.get("label") == "Report":
                reports_a.add(src)
        for _, tgt, data in self.gm.g.out_edges(node_a, data=True):
            tgt_data = self.gm.get_node(tgt)
            if tgt_data and tgt_data.get("label") == "Report":
                reports_a.add(tgt)

        # Collect reports mentioning entity B
        for src, _, data in self.gm.g.in_edges(node_b, data=True):
            src_data = self.gm.get_node(src)
            if src_data and src_data.get("label") == "Report":
                reports_b.add(src)
        for _, tgt, data in self.gm.g.out_edges(node_b, data=True):
            tgt_data = self.gm.get_node(tgt)
            if tgt_data and tgt_data.get("label") == "Report":
                reports_b.add(tgt)

        union = reports_a | reports_b
        if not union:
            return 0.0

        intersection = reports_a & reports_b
        return len(intersection) / len(union)

    def _classify_relationship(
        self,
        combined_score: float,
        has_direct_edge: bool,
        report_cooccurrence: float,
        feature_sim: float,
    ) -> Tuple[str, str]:
        """Determines epistemic classification and human-readable status.

        Returns (classification, status):
          - CORROBORATED: Multiple independent sources confirm the link
          - INFERRED: Graph topology + ML features strongly suggest the relationship
          - PREDICTED: ML model predicts the link, weaker confidence
        """
        if has_direct_edge and report_cooccurrence > 0.3:
            return "CORROBORATED", "Relationship confirmed by multiple intelligence sources"
        elif has_direct_edge:
            return "REPORTED", "Relationship documented in at least one intelligence source"
        elif combined_score >= 0.75 and report_cooccurrence > 0:
            return "INFERRED", "Strong structural and behavioral overlap with co-occurring reports"
        elif combined_score >= 0.55:
            return "INFERRED", "Significant TTP/infrastructure overlap suggests shared origin or coordination"
        elif combined_score >= 0.40:
            return "PREDICTED", "ML model predicts potential relationship based on feature similarity"
        else:
            return "PREDICTED", "Weak candidate relationship requiring further investigation"

    def discover_candidate_relationships(
        self,
        min_combined_score: float = 0.35,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """Identifies top-K candidate relationships between campaigns/malware/actors.

        Combines four signals:
          1. Feature Cosine Similarity (TTP + Infra + CVE + Sector + Tools) — 40%
          2. Graph Topological Jaccard Similarity — 25%
          3. Adamic-Adar Index — 15%
          4. Report Co-occurrence — 20%
        """
        entity_ids, matrix, feature_names = self.clustering.build_campaign_feature_matrix()

        if len(entity_ids) < 2 or matrix.shape[0] < 2:
            return []

        # 1. Compute pairwise Cosine Similarity matrix
        cos_sim = cosine_similarity(matrix)

        candidates: List[Dict[str, Any]] = []
        n = len(entity_ids)

        for i in range(n):
            for j in range(i + 1, n):
                node_a = entity_ids[i]
                node_b = entity_ids[j]

                node_a_data = self.gm.get_node(node_a) or {}
                node_b_data = self.gm.get_node(node_b) or {}

                # Skip self-referential pairs (same canonical entity reached via alias)
                if node_a_data.get("name") == node_b_data.get("name"):
                    continue

                # Check if direct relationship already exists
                has_direct_edge = (
                    self.gm.g.has_edge(node_a, node_b) or self.gm.g.has_edge(node_b, node_a)
                )

                # Compute individual similarity signals
                feature_sim = float(cos_sim[i, j])
                graph_jaccard = self.gds.compute_jaccard_similarity(node_a, node_b)
                adamic_adar = self._compute_adamic_adar(node_a, node_b)
                report_cooc = self._compute_report_cooccurrence(node_a, node_b)

                # Weighted composite score
                combined_score = round(
                    0.40 * feature_sim
                    + 0.25 * graph_jaccard
                    + 0.15 * adamic_adar
                    + 0.20 * report_cooc,
                    4,
                )

                if combined_score >= min_combined_score:
                    classification, status = self._classify_relationship(
                        combined_score, has_direct_edge, report_cooc, feature_sim,
                    )

                    # Build human-readable evidence summary
                    evidence_factors = []
                    if feature_sim > 0.3:
                        evidence_factors.append(f"Feature similarity: {feature_sim:.0%}")
                    if graph_jaccard > 0.1:
                        evidence_factors.append(f"Neighbor overlap: {graph_jaccard:.0%}")
                    if adamic_adar > 0.1:
                        evidence_factors.append(f"Adamic-Adar: {adamic_adar:.2f}")
                    if report_cooc > 0:
                        evidence_factors.append(f"Report co-occurrence: {report_cooc:.0%}")

                    candidates.append({
                        "source_id": node_a,
                        "source_name": node_a_data.get("name", node_a),
                        "source_label": node_a_data.get("label", "Unknown"),
                        "target_id": node_b,
                        "target_name": node_b_data.get("name", node_b),
                        "target_label": node_b_data.get("label", "Unknown"),
                        "relationship_score": combined_score,
                        "feature_similarity": round(feature_sim, 4),
                        "graph_jaccard_similarity": round(graph_jaccard, 4),
                        "adamic_adar_index": round(adamic_adar, 4),
                        "report_cooccurrence": round(report_cooc, 4),
                        "is_already_connected": has_direct_edge,
                        "classification": classification,
                        "status": status,
                        "evidence_factors": evidence_factors,
                    })

        # Sort by composite score descending
        candidates.sort(key=lambda x: x["relationship_score"], reverse=True)
        return candidates[:top_k]


link_prediction_engine = LinkPredictionEngine()
