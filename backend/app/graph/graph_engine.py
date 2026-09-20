"""Unified Threat Knowledge Graph Engine.

Maintains an in-memory NetworkX directed multigraph synchronized with Neo4j,
providing subgraphs, path analysis, and graph statistics.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx
from backend.app.graph.provenance import ProvenanceRecord, EvidenceType
from backend.app.graph.neo4j import neo4j_manager
from backend.app.core.logging import logger


class ThreatKnowledgeGraph:
    """Core Threat Knowledge Graph storing entities and evidence-backed relationships."""

    def __init__(self):
        self.g = nx.MultiDiGraph()

    def add_node(
        self,
        node_id: str,
        label: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Adds or updates a node in the threat knowledge graph."""
        props = properties or {}
        props.update({
            "id": node_id,
            "label": label,
            "name": name,
        })
        self.g.add_node(node_id, **props)

        # Sync to Neo4j if online
        if neo4j_manager.is_available:
            cypher = f"""
            MERGE (n:{label} {{id: $id}})
            SET n += $props
            """
            neo4j_manager.execute_query(cypher, {"id": node_id, "props": props})

        return props

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        provenance: ProvenanceRecord,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Adds a directed relationship between two nodes with mandatory provenance."""
        if not self.g.has_node(source_id) or not self.g.has_node(target_id):
            logger.warning(f"Cannot link {source_id} -> {target_id}: Missing node(s)")
            return {}

        edge_props = properties or {}
        edge_props.update({
            "rel_type": rel_type,
            "source_id": source_id,
            "target_id": target_id,
            "evidence_type": provenance.evidence_type.value,
            "confidence": provenance.calculate_effective_confidence(),
            "source_report_id": provenance.source_report_id,
            "source_title": provenance.source_title,
            "source_url": provenance.source_url,
            "context_snippet": provenance.context_snippet,
            "extracted_at": provenance.extracted_at,
        })

        # Add edge with unique key (source, target, rel_type)
        self.g.add_edge(source_id, target_id, key=rel_type, **edge_props)

        # Sync to Neo4j if online
        if neo4j_manager.is_available:
            src_label = self.g.nodes[source_id].get("label", "Entity")
            tgt_label = self.g.nodes[target_id].get("label", "Entity")
            cypher = f"""
            MATCH (s:{src_label} {{id: $source_id}})
            MATCH (t:{tgt_label} {{id: $target_id}})
            MERGE (s)-[r:{rel_type}]->(t)
            SET r += $edge_props
            """
            neo4j_manager.execute_query(cypher, {
                "source_id": source_id,
                "target_id": target_id,
                "edge_props": edge_props,
            })

        return edge_props

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves node attributes by ID."""
        if self.g.has_node(node_id):
            return dict(self.g.nodes[node_id])
        return None

    def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        """Retrieves all 1-hop connected nodes and edges."""
        if not self.g.has_node(node_id):
            return []

        neighbors: List[Dict[str, Any]] = []
        # Outgoing
        for _, tgt, data in self.g.out_edges(node_id, data=True):
            tgt_data = self.g.nodes[tgt]
            neighbors.append({
                "direction": "OUTGOING",
                "relationship": data,
                "target_node": tgt_data,
            })
        # Incoming
        for src, _, data in self.g.in_edges(node_id, data=True):
            src_data = self.g.nodes[src]
            neighbors.append({
                "direction": "INCOMING",
                "relationship": data,
                "target_node": src_data,
            })
        return neighbors

    def find_paths(self, source_id: str, target_id: str, max_depth: int = 4) -> List[List[str]]:
        """Discovers all simple paths between two entities up to max_depth."""
        if not self.g.has_node(source_id) or not self.g.has_node(target_id):
            return []

        undirected = self.g.to_undirected(as_view=True)
        try:
            paths = list(nx.all_simple_paths(undirected, source=source_id, target=target_id, cutoff=max_depth))
            return paths
        except nx.NetworkXNoPath:
            return []

    def get_graph_data(self, limit: int = 500) -> Dict[str, Any]:
        """Returns Cytoscape/Web-compatible graph JSON representation."""
        nodes = []
        for n, d in list(self.g.nodes(data=True))[:limit]:
            nodes.append({
                "data": {
                    "id": n,
                    "label": d.get("label", "Entity"),
                    "name": d.get("name", n),
                    **{k: v for k, v in d.items() if k not in ("id", "label", "name")},
                }
            })

        edges = []
        for u, v, k, d in list(self.g.edges(keys=True, data=True))[:limit * 2]:
            edges.append({
                "data": {
                    "id": f"{u}->{v}:{k}",
                    "source": u,
                    "target": v,
                    "label": d.get("rel_type", k),
                    "confidence": d.get("confidence", 1.0),
                    "evidence_type": d.get("evidence_type", "REPORTED"),
                    **{key: val for key, val in d.items() if key not in ("source_id", "target_id", "rel_type")},
                }
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": self.g.number_of_nodes(),
                "total_edges": self.g.number_of_edges(),
            },
        }

    def clear(self):
        """Resets the in-memory graph."""
        self.g.clear()


knowledge_graph = ThreatKnowledgeGraph()
