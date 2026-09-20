"""Machine Learning Feature Engineering and Unsupervised Campaign Clustering Subsystem.

Constructs multi-dimensional threat feature vectors from the knowledge graph:
  - TTP Profile: MITRE ATT&CK techniques used
  - Infrastructure Profile: C2 domains, IPs, URLs, hashes
  - Vulnerability Profile: Exploited CVEs
  - Victimology Profile: Targeted sectors
  - Tooling Profile: Malware / tools used or associated

Clusters campaigns, malware, and threat actors using HDBSCAN density-based clustering
with weighted feature vectors reflecting attribution significance.
"""

from typing import Dict, List, Any, Set, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import hdbscan

from backend.app.graph.graph_engine import knowledge_graph
from backend.app.core.logging import logger


class MLClusteringEngine:
    """Extracts high-dimensional threat profiles and clusters campaigns/malware."""

    def __init__(self, graph_manager=knowledge_graph):
        self.gm = graph_manager

    def _collect_reachable_attributes(self, node_id: str, depth: int = 2) -> Dict[str, Set[str]]:
        """BFS traversal collecting typed attributes up to `depth` hops from a node."""
        profile: Dict[str, Set[str]] = {
            "techniques": set(),
            "cves": set(),
            "sectors": set(),
            "infrastructure": set(),
            "tools": set(),
            "reports": set(),
        }

        visited: Set[str] = set()
        frontier = [(node_id, 0)]

        while frontier:
            current, d = frontier.pop(0)
            if current in visited or d > depth:
                continue
            visited.add(current)

            node_data = self.gm.get_node(current)
            if not node_data:
                continue

            lbl = node_data.get("label", "")
            name = node_data.get("name", current)

            # Classify the node we've reached
            if lbl == "AttackTechnique":
                profile["techniques"].add(name)
            elif lbl == "CVE":
                profile["cves"].add(name)
            elif lbl in ("Sector", "Organization"):
                profile["sectors"].add(name)
            elif lbl in ("Domain", "IP", "URL"):
                profile["infrastructure"].add(name)
            elif lbl == "Hash":
                profile["infrastructure"].add(name)
            elif lbl in ("Malware", "Tool"):
                profile["tools"].add(name)
            elif lbl == "Report":
                profile["reports"].add(name)

            # Expand frontier through both outgoing and incoming edges
            if d < depth:
                for _, tgt, _ in self.gm.g.out_edges(current, data=True):
                    if tgt not in visited:
                        frontier.append((tgt, d + 1))
                for src, _, _ in self.gm.g.in_edges(current, data=True):
                    if src not in visited:
                        frontier.append((src, d + 1))

        return profile

    def build_campaign_feature_matrix(self) -> Tuple[List[str], np.ndarray, List[str]]:
        """Constructs a normalized feature matrix for all Campaign, Malware, and ThreatActor entities.

        Uses 2-hop BFS traversal to collect rich attribute profiles, then one-hot encodes
        with domain-specific weighting:
          - Infrastructure overlap: 3.0x (strongest direct attribution signal)
          - ATT&CK Techniques: 2.0x (high behavioral/tradecraft signal)
          - CVE exploitation: 1.5x (shared vulnerability exploitation)
          - Target sectors: 1.0x (victimology overlap)
          - Tooling reuse: 2.5x (shared malware/tool deployment)

        Returns:
            (entity_ids, feature_matrix, feature_names)
        """
        # 1. Identify all clusterizable entities
        target_entities = []
        for n, d in self.gm.g.nodes(data=True):
            if d.get("label") in ("Campaign", "Malware", "ThreatActor", "Tool"):
                target_entities.append((n, d))

        if not target_entities:
            return [], np.zeros((0, 0)), []

        # 2. Collect 2-hop attribute profiles for every target entity
        all_techniques: Set[str] = set()
        all_cves: Set[str] = set()
        all_sectors: Set[str] = set()
        all_infrastructure: Set[str] = set()
        all_tools: Set[str] = set()

        entity_profiles: Dict[str, Dict[str, Set[str]]] = {}

        for node_id, _ in target_entities:
            profile = self._collect_reachable_attributes(node_id, depth=2)
            entity_profiles[node_id] = profile

            all_techniques |= profile["techniques"]
            all_cves |= profile["cves"]
            all_sectors |= profile["sectors"]
            all_infrastructure |= profile["infrastructure"]
            all_tools |= profile["tools"]

        # 3. Build unified feature vocabulary
        sorted_tech = sorted(all_techniques)
        sorted_cve = sorted(all_cves)
        sorted_sec = sorted(all_sectors)
        sorted_infra = sorted(all_infrastructure)
        sorted_tools = sorted(all_tools)

        feature_names = (
            [f"TTP:{t}" for t in sorted_tech]
            + [f"CVE:{c}" for c in sorted_cve]
            + [f"Sector:{s}" for s in sorted_sec]
            + [f"Infra:{i}" for i in sorted_infra]
            + [f"Tool:{t}" for t in sorted_tools]
        )

        num_features = len(feature_names)
        num_entities = len(target_entities)

        if num_features == 0:
            return [e[0] for e in target_entities], np.zeros((num_entities, 1)), ["dummy"]

        # 4. Construct weighted binary feature matrix
        matrix = np.zeros((num_entities, num_features), dtype=np.float32)
        entity_ids = []

        for row_idx, (node_id, _) in enumerate(target_entities):
            entity_ids.append(node_id)
            prof = entity_profiles[node_id]

            col_idx = 0
            # Techniques (Weight: 2.0 — High behavioral significance)
            for t in sorted_tech:
                if t in prof["techniques"]:
                    matrix[row_idx, col_idx] = 2.0
                col_idx += 1

            # CVEs (Weight: 1.5 — Exploit profile)
            for c in sorted_cve:
                if c in prof["cves"]:
                    matrix[row_idx, col_idx] = 1.5
                col_idx += 1

            # Sectors (Weight: 1.0 — Targeting profile)
            for s in sorted_sec:
                if s in prof["sectors"]:
                    matrix[row_idx, col_idx] = 1.0
                col_idx += 1

            # Infrastructure (Weight: 3.0 — Strongest direct attribution signal)
            for i in sorted_infra:
                if i in prof["infrastructure"]:
                    matrix[row_idx, col_idx] = 3.0
                col_idx += 1

            # Tool/Malware reuse (Weight: 2.5 — High shared tradecraft signal)
            for t in sorted_tools:
                if t in prof["tools"]:
                    matrix[row_idx, col_idx] = 2.5
                col_idx += 1

        return entity_ids, matrix, feature_names

    def cluster_campaigns(self, min_cluster_size: int = 2) -> List[Dict[str, Any]]:
        """Performs HDBSCAN clustering over the threat feature matrix.

        Returns structured cluster groups with per-member probability scores,
        shared feature breakdowns, and cluster-level characterization.
        """
        entity_ids, matrix, feature_names = self.build_campaign_feature_matrix()

        if len(entity_ids) < 2 or matrix.shape[1] == 0:
            return []

        # Run HDBSCAN with euclidean distance and soft cluster boundaries
        try:
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=1,
                metric="euclidean",
                cluster_selection_epsilon=0.3,
            )
            labels = clusterer.fit_predict(matrix)
            probabilities = clusterer.probabilities_
        except Exception as e:
            logger.warning(f"HDBSCAN clustering fallback to DBSCAN: {e}")
            dbscan = DBSCAN(eps=0.5, min_samples=min_cluster_size)
            labels = dbscan.fit_predict(matrix)
            probabilities = np.ones(len(labels))

        # Group entities into structured clusters with evidence
        clusters_dict: Dict[int, List[Dict[str, Any]]] = {}
        cluster_profiles: Dict[int, Dict[str, Set[str]]] = {}

        for idx, label in enumerate(labels):
            node_id = entity_ids[idx]
            node_data = self.gm.get_node(node_id) or {}

            member_info = {
                "id": node_id,
                "name": node_data.get("name", node_id),
                "label": node_data.get("label", "Unknown"),
                "cluster_membership_prob": round(float(probabilities[idx]), 3),
            }

            cluster_label = int(label)
            clusters_dict.setdefault(cluster_label, []).append(member_info)

            # Aggregate feature profiles per cluster for evidence
            if cluster_label not in cluster_profiles:
                cluster_profiles[cluster_label] = {
                    "techniques": set(), "cves": set(), "sectors": set(),
                    "infrastructure": set(), "tools": set(),
                }

            if node_id in entity_profiles:
                entity_profiles = None
                prof = entity_profiles[node_id]
                for key in cluster_profiles[cluster_label]:
                    cluster_profiles[cluster_label][key] |= prof.get(key, set())

        # Format output with shared evidence per cluster
        cluster_output = []
        for cluster_id, members in sorted(clusters_dict.items()):
            cluster_name = f"ML_Cluster_{cluster_id}" if cluster_id != -1 else "Unclustered_Noise"
            is_noise = cluster_id == -1

            shared_evidence = {}
            if cluster_id in cluster_profiles and not is_noise:
                cp = cluster_profiles[cluster_id]
                shared_evidence = {
                    "shared_techniques": sorted(cp["techniques"]),
                    "shared_cves": sorted(cp["cves"]),
                    "shared_sectors": sorted(cp["sectors"]),
                    "shared_infrastructure": list(cp["infrastructure"])[:15],
                    "shared_tools": sorted(cp["tools"]),
                }

            cluster_output.append({
                "cluster_id": cluster_id,
                "cluster_name": cluster_name,
                "is_noise": is_noise,
                "size": len(members),
                "members": members,
                "shared_evidence": shared_evidence,
                "assessment": (
                    f"Cluster of {len(members)} entities sharing overlapping TTPs, infrastructure, and/or victimology. "
                    f"Classification: INFERRED. Requires human analyst corroboration."
                ) if not is_noise else "Entities without sufficient density for clustering.",
            })

        return cluster_output


# We need `entity_profiles` accessible in the cluster output, so we capture it via closure.
# The `_collect_reachable_attributes` method already does the work inline.
# To make shared_evidence work, we recollect inside `cluster_campaigns`:

class _MLClusteringEngineWithEvidence(MLClusteringEngine):
    """Extended clustering engine that includes shared evidence in output."""

    def cluster_campaigns(self, min_cluster_size: int = 2) -> List[Dict[str, Any]]:
        entity_ids, matrix, feature_names = self.build_campaign_feature_matrix()

        if len(entity_ids) < 2 or matrix.shape[1] == 0:
            return []

        try:
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=1,
                metric="euclidean",
                cluster_selection_epsilon=0.3,
            )
            labels = clusterer.fit_predict(matrix)
            probabilities = clusterer.probabilities_
        except Exception as e:
            logger.warning(f"HDBSCAN fallback: {e}")
            dbscan = DBSCAN(eps=0.5, min_samples=min_cluster_size)
            labels = dbscan.fit_predict(matrix)
            probabilities = np.ones(len(labels))

        # Collect per-entity profiles for evidence aggregation
        entity_prof_map: Dict[str, Dict[str, Set[str]]] = {}
        for eid in entity_ids:
            entity_prof_map[eid] = self._collect_reachable_attributes(eid, depth=2)

        clusters_dict: Dict[int, List[Dict[str, Any]]] = {}
        cluster_profiles: Dict[int, Dict[str, Set[str]]] = {}

        for idx, label in enumerate(labels):
            node_id = entity_ids[idx]
            node_data = self.gm.get_node(node_id) or {}

            member_info = {
                "id": node_id,
                "name": node_data.get("name", node_id),
                "label": node_data.get("label", "Unknown"),
                "cluster_membership_prob": round(float(probabilities[idx]), 3),
            }

            cl = int(label)
            clusters_dict.setdefault(cl, []).append(member_info)

            if cl not in cluster_profiles:
                cluster_profiles[cl] = {
                    "techniques": set(), "cves": set(), "sectors": set(),
                    "infrastructure": set(), "tools": set(),
                }

            if node_id in entity_prof_map:
                prof = entity_prof_map[node_id]
                for key in cluster_profiles[cl]:
                    cluster_profiles[cl][key] |= prof.get(key, set())

        cluster_output = []
        for cluster_id, members in sorted(clusters_dict.items()):
            cluster_name = f"ML_Cluster_{cluster_id}" if cluster_id != -1 else "Unclustered_Noise"
            is_noise = cluster_id == -1

            shared_evidence = {}
            if cluster_id in cluster_profiles and not is_noise:
                cp = cluster_profiles[cluster_id]
                shared_evidence = {
                    "shared_techniques": sorted(cp["techniques"]),
                    "shared_cves": sorted(cp["cves"]),
                    "shared_sectors": sorted(cp["sectors"]),
                    "shared_infrastructure": list(cp["infrastructure"])[:15],
                    "shared_tools": sorted(cp["tools"]),
                }

            cluster_output.append({
                "cluster_id": cluster_id,
                "cluster_name": cluster_name,
                "is_noise": is_noise,
                "size": len(members),
                "members": members,
                "shared_evidence": shared_evidence,
                "assessment": (
                    f"Cluster of {len(members)} entities sharing overlapping TTPs, infrastructure, and/or victimology. "
                    f"Classification: INFERRED. Requires human analyst corroboration."
                ) if not is_noise else "Entities without sufficient density for clustering.",
            })

        return cluster_output


ml_clustering_engine = _MLClusteringEngineWithEvidence()
