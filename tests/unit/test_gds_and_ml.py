"""Tests for Graph Data Science, ML Clustering, Link Prediction, and Explainability."""

import pytest
from backend.app.graph.graph_engine import ThreatKnowledgeGraph
from backend.app.analytics.gds import GraphDataScienceEngine
from backend.app.analytics.clustering import _MLClusteringEngineWithEvidence
from backend.app.analytics.link_prediction import LinkPredictionEngine
from backend.app.explainability.engine import ExplainabilityEngine
from backend.app.graph.provenance import ProvenanceRecord, EvidenceType, SourceTier


def _build_test_graph():
    """Builds a realistic test threat knowledge graph with known overlaps."""
    g = ThreatKnowledgeGraph()

    prov = ProvenanceRecord(
        source_report_id="report--test-1",
        source_title="Test Report",
        evidence_type=EvidenceType.REPORTED,
        confidence=0.95,
    )

    # Report nodes
    g.add_node("report--r1", "Report", "APT29 Advisory")
    g.add_node("report--r2", "Report", "Sandworm Advisory")
    g.add_node("report--r3", "Report", "CloudStorm Investigation")

    # Threat Actors
    g.add_node("ta-apt29", "ThreatActor", "APT29", {"country": "RU"})
    g.add_node("ta-sandworm", "ThreatActor", "Sandworm", {"country": "RU"})
    g.add_node("ta-cloudstorm", "Campaign", "Operation CloudStorm")

    # Malware
    g.add_node("mal-sunburst", "Malware", "SUNBURST")
    g.add_node("mal-industroyer", "Malware", "Industroyer")
    g.add_node("tool-cobaltstrike", "Tool", "Cobalt Strike")
    g.add_node("tool-mimikatz", "Tool", "Mimikatz")

    # Infrastructure — shared between APT29 and CloudStorm
    g.add_node("infra-ip1", "IP", "54.193.127.211")
    g.add_node("infra-domain1", "Domain", "deftsecurity.com")
    g.add_node("infra-domain2", "Domain", "avsvmcloud.com")
    g.add_node("infra-domain3", "Domain", "energy-grid-telemetry.net")

    # Techniques — shared across groups
    g.add_node("tech-t1059", "AttackTechnique", "T1059")
    g.add_node("tech-t1078", "AttackTechnique", "T1078")
    g.add_node("tech-t1003", "AttackTechnique", "T1003")
    g.add_node("tech-t1485", "AttackTechnique", "T1485")

    # CVEs
    g.add_node("cve-2020-10148", "CVE", "CVE-2020-10148")

    # Sectors
    g.add_node("sec-gov", "Sector", "Government")
    g.add_node("sec-tech", "Sector", "Technology")
    g.add_node("sec-energy", "Sector", "Energy")

    # --- APT29 relationships ---
    g.add_relationship("report--r1", "ta-apt29", "MENTIONS", prov)
    g.add_relationship("ta-apt29", "mal-sunburst", "USES", prov)
    g.add_relationship("ta-apt29", "tool-cobaltstrike", "USES", prov)
    g.add_relationship("ta-apt29", "tool-mimikatz", "USES", prov)
    g.add_relationship("mal-sunburst", "infra-ip1", "CONTACTS", prov)
    g.add_relationship("mal-sunburst", "infra-domain1", "CONTACTS", prov)
    g.add_relationship("mal-sunburst", "infra-domain2", "CONTACTS", prov)
    # Direct actor→infra links (as extracted from the report)
    g.add_relationship("ta-apt29", "infra-ip1", "CONTACTS", prov)
    g.add_relationship("ta-apt29", "infra-domain1", "CONTACTS", prov)
    g.add_relationship("ta-apt29", "tech-t1059", "USES_TECHNIQUE", prov)
    g.add_relationship("ta-apt29", "tech-t1078", "USES_TECHNIQUE", prov)
    g.add_relationship("ta-apt29", "tech-t1003", "USES_TECHNIQUE", prov)
    g.add_relationship("ta-apt29", "cve-2020-10148", "EXPLOITS", prov)
    g.add_relationship("ta-apt29", "sec-gov", "TARGETS", prov)
    g.add_relationship("ta-apt29", "sec-tech", "TARGETS", prov)

    # --- Sandworm relationships ---
    g.add_relationship("report--r2", "ta-sandworm", "MENTIONS", prov)
    g.add_relationship("ta-sandworm", "mal-industroyer", "USES", prov)
    g.add_relationship("mal-industroyer", "infra-domain3", "CONTACTS", prov)
    g.add_relationship("ta-sandworm", "tech-t1059", "USES_TECHNIQUE", prov)
    g.add_relationship("ta-sandworm", "tech-t1078", "USES_TECHNIQUE", prov)
    g.add_relationship("ta-sandworm", "tech-t1485", "USES_TECHNIQUE", prov)
    g.add_relationship("ta-sandworm", "sec-gov", "TARGETS", prov)
    g.add_relationship("ta-sandworm", "sec-energy", "TARGETS", prov)

    # --- Operation CloudStorm — overlaps with APT29 infrastructure ---
    g.add_relationship("report--r3", "ta-cloudstorm", "MENTIONS", prov)
    g.add_relationship("ta-cloudstorm", "tool-cobaltstrike", "USES", prov)
    g.add_relationship("ta-cloudstorm", "tool-mimikatz", "USES", prov)
    g.add_relationship("ta-cloudstorm", "infra-ip1", "CONTACTS", prov)    # SHARED with APT29
    g.add_relationship("ta-cloudstorm", "infra-domain1", "CONTACTS", prov) # SHARED with APT29
    g.add_relationship("ta-cloudstorm", "tech-t1059", "USES_TECHNIQUE", prov)
    g.add_relationship("ta-cloudstorm", "tech-t1078", "USES_TECHNIQUE", prov)
    g.add_relationship("ta-cloudstorm", "tech-t1003", "USES_TECHNIQUE", prov)
    g.add_relationship("ta-cloudstorm", "cve-2020-10148", "EXPLOITS", prov)  # SHARED with APT29
    g.add_relationship("ta-cloudstorm", "sec-gov", "TARGETS", prov)
    g.add_relationship("ta-cloudstorm", "sec-tech", "TARGETS", prov)

    return g


class TestGraphDataScience:
    """Validates GDS analytics on the threat knowledge graph."""

    def test_centrality_metrics(self):
        g = _build_test_graph()
        gds = GraphDataScienceEngine(graph_manager=g)
        metrics = gds.compute_centrality_metrics()
        assert "degree_centrality" in metrics
        assert "pagerank" in metrics
        assert len(metrics["degree_centrality"]) > 0
        assert len(metrics["pagerank"]) > 0

    def test_community_detection(self):
        g = _build_test_graph()
        gds = GraphDataScienceEngine(graph_manager=g)
        communities = gds.detect_graph_communities()
        assert len(communities) >= 1
        # Should find at least one community with multiple members
        assert any(c["size"] >= 3 for c in communities)

    def test_jaccard_similarity_shared_infra(self):
        g = _build_test_graph()
        gds = GraphDataScienceEngine(graph_manager=g)
        # APT29 and CloudStorm share significant infrastructure
        similarity = gds.compute_jaccard_similarity("ta-apt29", "ta-cloudstorm")
        assert similarity > 0.1

    def test_jaccard_similarity_unrelated(self):
        g = _build_test_graph()
        gds = GraphDataScienceEngine(graph_manager=g)
        # APT29 and Sandworm share fewer neighbors (some techniques overlap)
        sim = gds.compute_jaccard_similarity("ta-apt29", "ta-sandworm")
        assert isinstance(sim, float)


class TestMLClustering:
    """Validates HDBSCAN campaign clustering."""

    def test_builds_feature_matrix(self):
        g = _build_test_graph()
        clustering = _MLClusteringEngineWithEvidence(graph_manager=g)
        entity_ids, matrix, feature_names = clustering.build_campaign_feature_matrix()
        assert len(entity_ids) >= 3
        assert matrix.shape[0] >= 3
        assert matrix.shape[1] > 0
        assert len(feature_names) > 0

    def test_cluster_campaigns(self):
        g = _build_test_graph()
        clustering = _MLClusteringEngineWithEvidence(graph_manager=g)
        clusters = clustering.cluster_campaigns()
        assert isinstance(clusters, list)
        # Should produce at least one cluster
        assert len(clusters) >= 1
        for cl in clusters:
            assert "cluster_id" in cl
            assert "members" in cl
            assert "size" in cl
            assert cl["size"] > 0

    def test_cluster_contains_shared_evidence(self):
        g = _build_test_graph()
        clustering = _MLClusteringEngineWithEvidence(graph_manager=g)
        clusters = clustering.cluster_campaigns()
        non_noise = [c for c in clusters if not c["is_noise"]]
        if non_noise:
            cl = non_noise[0]
            assert "shared_evidence" in cl
            assert "assessment" in cl


class TestLinkPrediction:
    """Validates link prediction candidate discovery."""

    def test_discovers_candidates(self):
        g = _build_test_graph()
        clustering = _MLClusteringEngineWithEvidence(graph_manager=g)
        gds = GraphDataScienceEngine(graph_manager=g)
        lp = LinkPredictionEngine(graph_manager=g, clustering_engine=clustering, gds=gds)
        candidates = lp.discover_candidate_relationships(min_combined_score=0.2, top_k=10)
        assert isinstance(candidates, list)
        assert len(candidates) >= 1

    def test_candidate_structure(self):
        g = _build_test_graph()
        clustering = _MLClusteringEngineWithEvidence(graph_manager=g)
        gds = GraphDataScienceEngine(graph_manager=g)
        lp = LinkPredictionEngine(graph_manager=g, clustering_engine=clustering, gds=gds)
        candidates = lp.discover_candidate_relationships(min_combined_score=0.2, top_k=10)
        if candidates:
            c = candidates[0]
            assert "source_name" in c
            assert "target_name" in c
            assert "relationship_score" in c
            assert "classification" in c
            assert "evidence_factors" in c

    def test_apt29_cloudstorm_high_score(self):
        """APT29 and CloudStorm share infra, tools, techniques, and CVEs — should score highly."""
        g = _build_test_graph()
        clustering = _MLClusteringEngineWithEvidence(graph_manager=g)
        gds = GraphDataScienceEngine(graph_manager=g)
        lp = LinkPredictionEngine(graph_manager=g, clustering_engine=clustering, gds=gds)
        candidates = lp.discover_candidate_relationships(min_combined_score=0.1, top_k=20)
        # Find the APT29 ↔ CloudStorm pair
        pair = [
            c for c in candidates
            if ("APT29" in c["source_name"] and "CloudStorm" in c["target_name"])
            or ("CloudStorm" in c["source_name"] and "APT29" in c["target_name"])
        ]
        assert len(pair) >= 1, "APT29 ↔ CloudStorm relationship should be discovered"
        assert pair[0]["relationship_score"] > 0.3


class TestExplainability:
    """Validates explainability engine evidence synthesis."""

    def test_explain_relationship_basic(self):
        g = _build_test_graph()
        engine = ExplainabilityEngine(graph_manager=g)
        explanation = engine.explain_relationship("ta-apt29", "ta-cloudstorm")
        assert "error" not in explanation
        assert "evidence_summary" in explanation
        assert "classification" in explanation
        assert "assessment" in explanation

    def test_shared_infra_detected(self):
        g = _build_test_graph()
        engine = ExplainabilityEngine(graph_manager=g)
        explanation = engine.explain_relationship("ta-apt29", "ta-cloudstorm")
        # Should detect shared infrastructure (54.193.127.211, deftsecurity.com)
        assert len(explanation["shared_infrastructure"]) >= 1

    def test_shared_techniques_detected(self):
        g = _build_test_graph()
        engine = ExplainabilityEngine(graph_manager=g)
        explanation = engine.explain_relationship("ta-apt29", "ta-cloudstorm")
        # Should detect shared techniques (T1059, T1078, T1003)
        assert len(explanation["shared_techniques"]) >= 2

    def test_evidence_score_calculated(self):
        g = _build_test_graph()
        engine = ExplainabilityEngine(graph_manager=g)
        explanation = engine.explain_relationship("ta-apt29", "ta-cloudstorm")
        assert "evidence_score" in explanation
        assert explanation["evidence_score"] > 0.0

    def test_returns_error_for_unknown_entity(self):
        g = _build_test_graph()
        engine = ExplainabilityEngine(graph_manager=g)
        explanation = engine.explain_relationship("nonexistent-1", "nonexistent-2")
        assert "error" in explanation
