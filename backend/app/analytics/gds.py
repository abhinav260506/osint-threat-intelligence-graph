"""Graph Data Science (GDS) and Graph Analytics Subsystem.

Implements Centrality, PageRank, Community Detection (Louvain / Greedy Modularity),
and Node Neighborhood Similarity on the Threat Knowledge Graph.
"""

from typing import Dict, List, Any, Set, Tuple
import networkx as nx
from networkx.algorithms import community
from backend.app.graph.graph_engine import knowledge_graph
from backend.app.core.logging import logger


class GraphDataScienceEngine:
    """Performs topological analysis and graph algorithms on threat entities."""

    def __init__(self, graph_manager=knowledge_graph):
        self.gm = graph_manager

    def compute_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """Computes Degree Centrality and PageRank across all nodes.
        
        Degree Centrality: Identifies high-density hub nodes (e.g. shared C2 servers, widespread malware).
        PageRank: Identifies structurally influential entities with high strategic importance.
        """
        if self.gm.g.number_of_nodes() == 0:
            return {"degree_centrality": {}, "pagerank": {}}

        # Convert to undirected simple graph for topological analysis
        undirected_g = nx.Graph(self.gm.g)

        degree_cent = nx.degree_centrality(undirected_g)
        try:
            pagerank_scores = nx.pagerank(undirected_g, alpha=0.85, max_iter=100)
        except Exception as e:
            logger.warning(f"PageRank fallback due to convergence: {e}")
            pagerank_scores = {n: 1.0 / len(undirected_g) for n in undirected_g.nodes()}

        return {
            "degree_centrality": {k: round(v, 4) for k, v in degree_cent.items()},
            "pagerank": {k: round(v, 4) for k, v in pagerank_scores.items()},
        }

    def detect_graph_communities(self) -> List[Dict[str, Any]]:
        """Executes Modularity-based Community Detection (Louvain / Greedy Modularity).
        
        Discovers structurally cohesive clusters of ThreatActors, Campaigns, Malware,
        and Infrastructure based purely on topological graph connectivity.
        """
        if self.gm.g.number_of_nodes() < 2:
            return []

        undirected_g = nx.Graph(self.gm.g)
        try:
            # Use greedy modularity communities (pure NetworkX native, zero binary dependencies)
            communities = community.greedy_modularity_communities(undirected_g)
        except Exception as e:
            logger.error(f"Community detection error: {e}")
            return []

        cluster_results = []
        for idx, comm in enumerate(communities):
            nodes_list = list(comm)
            entity_types = {}
            entities_detail = []

            for node_id in nodes_list:
                node_data = self.gm.get_node(node_id) or {}
                lbl = node_data.get("label", "Unknown")
                entity_types[lbl] = entity_types.get(lbl, 0) + 1
                entities_detail.append({
                    "id": node_id,
                    "name": node_data.get("name", node_id),
                    "label": lbl,
                })

            cluster_results.append({
                "community_id": f"graph_community_{idx + 1}",
                "size": len(nodes_list),
                "composition": entity_types,
                "members": entities_detail,
            })

        return cluster_results

    def compute_jaccard_similarity(self, node_a: str, node_b: str) -> float:
        """Computes Jaccard neighbor similarity between two entities."""
        if not self.gm.g.has_node(node_a) or not self.gm.g.has_node(node_b):
            return 0.0

        neighbors_a = set(self.gm.g.neighbors(node_a))
        neighbors_b = set(self.gm.g.neighbors(node_b))

        union_len = len(neighbors_a.union(neighbors_b))
        if union_len == 0:
            return 0.0

        intersection_len = len(neighbors_a.intersection(neighbors_b))
        return round(intersection_len / union_len, 4)


gds_engine = GraphDataScienceEngine()
