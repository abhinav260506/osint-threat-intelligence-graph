"""Threat Report Ingestion and Graph Assembly Pipeline.

Transforms raw unstructured threat advisories (PDF, TXT, Markdown) and STIX 2.1 JSON
into fully articulated STIX 2.1 Threat Knowledge Graph subgraphs with complete provenance.

Pipeline Flow:
  1. Document Processing (PDF→Text, Clean/Chunk)
  2. LLM Deep Analysis (Entity/Relationship/Context Extraction via Gemini)
  3. Deterministic IoC Extraction (Regex, Defanging, Validation)
  4. Entity Resolution & Normalization (Alias Canonicalization)
  5. Merge LLM + Deterministic Results
  6. STIX 2.1 Knowledge Graph Assembly (Nodes + Provenance Edges)
  7. GDS & ML Analytics (Louvain + HDBSCAN + Link Prediction)
"""

from typing import Dict, Any, List, Optional, Set
import uuid
import json
import re
import io
from datetime import datetime, timezone

from pypdf import PdfReader

from backend.app.ingestion.interfaces import RawThreatDocument
from backend.app.core.security import sanitize_input_text
from backend.app.extraction.ioc_extractor import IoCExtractor
from backend.app.extraction.entity_extractor import EntityExtractor
from backend.app.extraction.llm_analyzer import llm_analyzer
from backend.app.graph.graph_engine import knowledge_graph
from backend.app.graph.provenance import ProvenanceRecord, EvidenceType, SourceTier
from backend.app.analytics.gds import gds_engine
from backend.app.analytics.clustering import ml_clustering_engine
from backend.app.analytics.link_prediction import link_prediction_engine
from backend.app.core.logging import logger


class ReportIngestionPipeline:
    """Orchestrates LLM analysis, extraction, entity resolution, and knowledge graph persistence."""

    def __init__(
        self,
        ioc_extractor: Optional[IoCExtractor] = None,
        entity_extractor: Optional[EntityExtractor] = None,
        graph_manager=knowledge_graph,
    ):
        self.ioc_extractor = ioc_extractor or IoCExtractor()
        self.entity_extractor = entity_extractor or EntityExtractor()
        self.gm = graph_manager

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Safely extracts text pages from PDF bytes without script execution."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_pages = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text_pages.append(t)
            return "\n".join(text_pages)
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return ""

    def process_stix_bundle(self, bundle_json: Dict[str, Any], source_name: str = "STIX Feed") -> Dict[str, Any]:
        """Ingests a structured STIX 2.1 JSON bundle directly into the knowledge graph."""
        objects = bundle_json.get("objects", [])
        if not objects and bundle_json.get("type"):
            objects = [bundle_json]

        created_nodes = 0
        created_relationships = 0
        report_id = f"report--stix-{uuid.uuid4()}"
        subgraph_nodes = []
        subgraph_edges = []

        rep_props = {
            "title": f"STIX 2.1 Ingestion ({source_name})",
            "source_name": source_name,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        self.gm.add_node(node_id=report_id, label="Report", name=f"STIX 2.1 Bundle ({source_name})", properties=rep_props)
        created_nodes += 1
        subgraph_nodes.append({"data": {"id": report_id, "label": "Report", "name": f"STIX 2.1 Bundle ({source_name})", **rep_props}})

        node_map = {}
        for obj in objects:
            stix_type = obj.get("type", "")
            stix_id = obj.get("id", f"{stix_type}--{uuid.uuid4()}")
            name = obj.get("name") or obj.get("value") or obj.get("pattern") or stix_id
            label_map = {"threat-actor": "ThreatActor", "campaign": "Campaign", "malware": "Malware", "tool": "Tool", "indicator": "Indicator", "attack-pattern": "AttackTechnique", "vulnerability": "CVE", "identity": "Sector", "infrastructure": "Domain"}
            node_label = label_map.get(stix_type, "Entity")
            props = {"stix_type": stix_type, "description": obj.get("description"), "aliases": obj.get("aliases", [])}
            self.gm.add_node(node_id=stix_id, label=node_label, name=name, properties=props)
            created_nodes += 1
            node_map[stix_id] = node_label
            subgraph_nodes.append({"data": {"id": stix_id, "label": node_label, "name": name, **props}})
            prov = ProvenanceRecord(source_report_id=report_id, source_title=f"STIX Bundle: {source_name}", evidence_type=EvidenceType.REPORTED, confidence=1.0)
            edge_props = self.gm.add_relationship(report_id, stix_id, "MENTIONS", prov)
            created_relationships += 1
            subgraph_edges.append({"data": {"id": f"{report_id}->{stix_id}:MENTIONS", "source": report_id, "target": stix_id, "label": "MENTIONS", **edge_props}})

        for obj in objects:
            if obj.get("type") == "relationship":
                src = obj.get("source_ref")
                tgt = obj.get("target_ref")
                rel = obj.get("relationship_type", "RELATED_TO").upper().replace("-", "_")
                if src and tgt and self.gm.g.has_node(src) and self.gm.g.has_node(tgt):
                    prov = ProvenanceRecord(source_report_id=report_id, source_title=f"STIX Relationship ({rel})", evidence_type=EvidenceType.REPORTED, confidence=0.95)
                    edge_props = self.gm.add_relationship(src, tgt, rel, prov)
                    created_relationships += 1
                    subgraph_edges.append({"data": {"id": f"{src}->{tgt}:{rel}", "source": src, "target": tgt, "label": rel, **edge_props}})

        return {
            "report_id": report_id,
            "title": f"STIX 2.1 Bundle: {source_name}",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {"iocs_extracted": sum(1 for o in objects if o.get("type") == "indicator"), "entities_identified": sum(1 for o in objects if o.get("type") in ("threat-actor", "malware", "campaign")), "nodes_added": created_nodes, "relationships_established": created_relationships},
            "extracted_iocs": [], "extracted_entities": [],
            "llm_analysis": None,
            "generated_subgraph": {"nodes": subgraph_nodes, "edges": subgraph_edges},
        }

    def process_report(
        self,
        title: str,
        content: str,
        source_name: str = "Advisory",
        source_url: Optional[str] = None,
        source_tier: SourceTier = SourceTier.TIER_2,
        published_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Full pipeline: LLM Analysis → Deterministic Extraction → Merge → Graph Assembly."""
        # 0. Check if input is a STIX JSON string
        content_stripped = content.strip()
        if content_stripped.startswith("{") and '"objects"' in content_stripped:
            try:
                bundle_obj = json.loads(content_stripped)
                return self.process_stix_bundle(bundle_obj, source_name=source_name)
            except Exception:
                pass

        clean_text = sanitize_input_text(content)
        report_id = f"report--{uuid.uuid4()}"
        pub_time = published_at or datetime.now(timezone.utc).isoformat()

        subgraph_nodes = []
        subgraph_edges = []

        # ═══════════════════════════════════════════════════════
        # STEP 1: LLM Deep Analysis (Gemini)
        # ═══════════════════════════════════════════════════════
        llm_result = None
        llm_relationships = []
        try:
            llm_result = llm_analyzer.analyze_report(clean_text, title=title)
            if llm_result:
                logger.info(f"LLM analysis completed: {len(llm_result.get('threat_actors', []))} actors, "
                           f"{len(llm_result.get('relationships', []))} relationships discovered")
        except Exception as e:
            logger.warning(f"LLM analysis skipped: {e}")

        # ═══════════════════════════════════════════════════════
        # STEP 2: Deterministic IoC & Entity Extraction
        # ═══════════════════════════════════════════════════════
        extracted_iocs = self.ioc_extractor.extract_from_text(clean_text)
        extracted_entities = self.entity_extractor.extract_from_text(clean_text)

        # ═══════════════════════════════════════════════════════
        # STEP 3: Merge LLM + Deterministic Results
        # ═══════════════════════════════════════════════════════
        merged_iocs, merged_entities, llm_relationships = llm_analyzer.merge_with_deterministic(
            llm_result, extracted_iocs, extracted_entities,
        )

        # ═══════════════════════════════════════════════════════
        # STEP 4: Create Report Node
        # ═══════════════════════════════════════════════════════
        rep_props = {
            "title": title,
            "source_name": source_name,
            "source_url": source_url,
            "source_tier": source_tier.value,
            "published_at": pub_time,
            "llm_summary": llm_result.get("report_summary", "") if llm_result else "",
        }
        self.gm.add_node(node_id=report_id, label="Report", name=title, properties=rep_props)
        subgraph_nodes.append({"data": {"id": report_id, "label": "Report", "name": title, **rep_props}})

        created_nodes = 1
        created_relationships = 0

        actor_nodes: List[str] = []
        malware_nodes: List[str] = []
        campaign_nodes: List[str] = []
        infrastructure_nodes: List[str] = []
        technique_nodes: List[str] = []
        cve_nodes: List[str] = []
        sector_nodes: List[str] = []

        # Map entity names → node IDs for LLM relationship resolution
        entity_name_to_id: Dict[str, str] = {}

        # ═══════════════════════════════════════════════════════
        # STEP 5: Insert Merged Threat Entities
        # ═══════════════════════════════════════════════════════
        for ent in merged_entities:
            ent_id = ent["id"]
            ent_type = ent["entity_type"]
            label_map = {"threat_actor": "ThreatActor", "malware": "Malware", "tool": "Tool", "campaign": "Campaign", "sector": "Sector"}
            node_label = label_map.get(ent_type, "Entity")

            ent_props = {
                "canonical_name": ent["canonical_name"],
                "aliases": ent.get("aliases", []),
                "description": ent.get("description"),
                "country": ent.get("country"),
                "classification_basis": ent.get("classification_basis", "Deterministic"),
            }
            self.gm.add_node(node_id=ent_id, label=node_label, name=ent["canonical_name"], properties=ent_props)
            created_nodes += 1
            subgraph_nodes.append({"data": {"id": ent_id, "label": node_label, "name": ent["canonical_name"], **ent_props}})

            # Track name → ID mapping
            entity_name_to_id[ent["canonical_name"].lower()] = ent_id
            for alias in ent.get("aliases", []):
                entity_name_to_id[alias.lower()] = ent_id

            prov_mention = ProvenanceRecord(
                source_report_id=report_id, source_title=title, source_url=source_url,
                source_tier=source_tier, evidence_type=EvidenceType.REPORTED,
                confidence=ent.get("confidence", 0.9),
                context_snippet=f"Identified entity {ent['canonical_name']} in report",
            )
            edge_props = self.gm.add_relationship(source_id=report_id, target_id=ent_id, rel_type="MENTIONS", provenance=prov_mention)
            created_relationships += 1
            subgraph_edges.append({"data": {"id": f"{report_id}->{ent_id}:MENTIONS", "source": report_id, "target": ent_id, "label": "MENTIONS", **edge_props}})

            if node_label == "ThreatActor":
                actor_nodes.append(ent_id)
            elif node_label in ("Malware", "Tool"):
                malware_nodes.append(ent_id)
            elif node_label == "Campaign":
                campaign_nodes.append(ent_id)
            elif node_label == "Sector":
                sector_nodes.append(ent_id)

        # ═══════════════════════════════════════════════════════
        # STEP 6: Insert Merged IoCs
        # ═══════════════════════════════════════════════════════
        for ioc in merged_iocs:
            ioc_type = ioc["ioc_type"]
            val = ioc["normalized_value"]
            ioc_id = f"indicator--{ioc_type}-{val}"
            label_map = {"ipv4": "IP", "ipv6": "IP", "domain": "Domain", "url": "URL", "sha256": "Hash", "sha1": "Hash", "md5": "Hash", "cve": "CVE", "attack_technique": "AttackTechnique"}
            ioc_label = label_map.get(ioc_type, "Indicator")
            ioc_props = {"value": val, "original_value": ioc["original_value"], "ioc_type": ioc_type, "is_defanged": ioc["is_defanged"], "is_sinkhole_or_shared": ioc.get("is_sinkhole_or_shared", False)}
            self.gm.add_node(node_id=ioc_id, label=ioc_label, name=val, properties=ioc_props)
            created_nodes += 1
            subgraph_nodes.append({"data": {"id": ioc_id, "label": ioc_label, "name": val, **ioc_props}})

            entity_name_to_id[val.lower()] = ioc_id

            prov_ioc = ProvenanceRecord(source_report_id=report_id, source_title=title, source_url=source_url, source_tier=source_tier, evidence_type=EvidenceType.EXTRACTED, confidence=ioc["confidence"], context_snippet=ioc.get("context_snippet"))
            edge_props = self.gm.add_relationship(source_id=report_id, target_id=ioc_id, rel_type="MENTIONS", provenance=prov_ioc)
            created_relationships += 1
            subgraph_edges.append({"data": {"id": f"{report_id}->{ioc_id}:MENTIONS", "source": report_id, "target": ioc_id, "label": "MENTIONS", **edge_props}})

            if ioc_label in ("IP", "Domain", "URL", "Hash"):
                infrastructure_nodes.append(ioc_id)
            elif ioc_label == "AttackTechnique":
                technique_nodes.append(ioc_id)
            elif ioc_label == "CVE":
                cve_nodes.append(ioc_id)

        # ═══════════════════════════════════════════════════════
        # STEP 7: LLM-Discovered Relationships (primary value-add)
        # ═══════════════════════════════════════════════════════
        llm_edges_created = 0
        for rel in llm_relationships:
            src_name = rel.get("source_name", "").lower()
            tgt_name = rel.get("target_name", "").lower()
            rel_type = rel.get("relationship", "RELATED_TO").upper().replace(" ", "_")

            src_id = entity_name_to_id.get(src_name)
            tgt_id = entity_name_to_id.get(tgt_name)

            if src_id and tgt_id and src_id != tgt_id:
                prov = ProvenanceRecord(
                    source_report_id=report_id, source_title=title, source_url=source_url,
                    source_tier=source_tier, evidence_type=EvidenceType.EXTRACTED,
                    confidence=rel.get("confidence", 0.75),
                    context_snippet=rel.get("evidence", "LLM-inferred relationship"),
                )
                edge_props = self.gm.add_relationship(src_id, tgt_id, rel_type, prov)
                created_relationships += 1
                llm_edges_created += 1
                subgraph_edges.append({"data": {"id": f"{src_id}->{tgt_id}:{rel_type}", "source": src_id, "target": tgt_id, "label": rel_type, **edge_props}})

        if llm_edges_created > 0:
            logger.info(f"LLM relationship integration: {llm_edges_created} edges created from LLM analysis")

        # ═══════════════════════════════════════════════════════
        # STEP 8: Deterministic Semantic Relationships (fallback/supplement)
        # ═══════════════════════════════════════════════════════
        # Only create heuristic relationships if LLM didn't produce any
        if llm_edges_created == 0:
            for actor_id in actor_nodes:
                for camp_id in campaign_nodes:
                    prov = ProvenanceRecord(source_report_id=report_id, source_title=title, source_url=source_url, source_tier=source_tier, evidence_type=EvidenceType.REPORTED, confidence=0.90)
                    e_p = self.gm.add_relationship(actor_id, camp_id, "CONDUCTS", prov)
                    created_relationships += 1
                    subgraph_edges.append({"data": {"id": f"{actor_id}->{camp_id}:CONDUCTS", "source": actor_id, "target": camp_id, "label": "CONDUCTS", **e_p}})

            active_owners = campaign_nodes if campaign_nodes else actor_nodes
            for owner_id in active_owners:
                for mal_id in malware_nodes:
                    prov = ProvenanceRecord(source_report_id=report_id, source_title=title, source_url=source_url, source_tier=source_tier, evidence_type=EvidenceType.REPORTED, confidence=0.88)
                    e_p = self.gm.add_relationship(owner_id, mal_id, "USES", prov)
                    created_relationships += 1
                    subgraph_edges.append({"data": {"id": f"{owner_id}->{mal_id}:USES", "source": owner_id, "target": mal_id, "label": "USES", **e_p}})

            for mal_id in (malware_nodes if malware_nodes else active_owners):
                for infra_id in infrastructure_nodes:
                    infra_node = self.gm.get_node(infra_id) or {}
                    rel_type = "HAS_HASH" if infra_node.get("label") == "Hash" else "CONTACTS"
                    prov = ProvenanceRecord(source_report_id=report_id, source_title=title, source_url=source_url, source_tier=source_tier, evidence_type=EvidenceType.EXTRACTED, confidence=0.85)
                    e_p = self.gm.add_relationship(mal_id, infra_id, rel_type, prov)
                    created_relationships += 1
                    subgraph_edges.append({"data": {"id": f"{mal_id}->{infra_id}:{rel_type}", "source": mal_id, "target": infra_id, "label": rel_type, **e_p}})

            for subject_id in (malware_nodes if malware_nodes else active_owners):
                for tech_id in technique_nodes:
                    prov = ProvenanceRecord(source_report_id=report_id, source_title=title, source_url=source_url, source_tier=source_tier, evidence_type=EvidenceType.EXTRACTED, confidence=0.92)
                    e_p = self.gm.add_relationship(subject_id, tech_id, "USES_TECHNIQUE", prov)
                    created_relationships += 1
                    subgraph_edges.append({"data": {"id": f"{subject_id}->{tech_id}:USES_TECHNIQUE", "source": subject_id, "target": tech_id, "label": "USES_TECHNIQUE", **e_p}})

            for mal_id in (malware_nodes if malware_nodes else active_owners):
                for cve_id in cve_nodes:
                    prov = ProvenanceRecord(source_report_id=report_id, source_title=title, source_url=source_url, source_tier=source_tier, evidence_type=EvidenceType.REPORTED, confidence=0.90)
                    e_p = self.gm.add_relationship(mal_id, cve_id, "EXPLOITS", prov)
                    created_relationships += 1
                    subgraph_edges.append({"data": {"id": f"{mal_id}->{cve_id}:EXPLOITS", "source": mal_id, "target": cve_id, "label": "EXPLOITS", **e_p}})

            for owner_id in active_owners:
                for sec_id in sector_nodes:
                    prov = ProvenanceRecord(source_report_id=report_id, source_title=title, source_url=source_url, source_tier=source_tier, evidence_type=EvidenceType.REPORTED, confidence=0.85)
                    e_p = self.gm.add_relationship(owner_id, sec_id, "TARGETS", prov)
                    created_relationships += 1
                    subgraph_edges.append({"data": {"id": f"{owner_id}->{sec_id}:TARGETS", "source": owner_id, "target": sec_id, "label": "TARGETS", **e_p}})

        # ═══════════════════════════════════════════════════════
        # STEP 9: Post-Ingestion Analytics
        # ═══════════════════════════════════════════════════════
        communities = gds_engine.detect_graph_communities()
        clusters = ml_clustering_engine.cluster_campaigns()
        predictions = link_prediction_engine.discover_candidate_relationships(min_combined_score=0.35, top_k=5)

        # Build LLM analysis summary for frontend
        llm_analysis_output = None
        if llm_result:
            llm_analysis_output = {
                "report_summary": llm_result.get("report_summary", ""),
                "key_findings": llm_result.get("key_findings", []),
                "threat_actors_found": len(llm_result.get("threat_actors", [])),
                "malware_found": len(llm_result.get("malware", [])),
                "relationships_extracted": len(llm_result.get("relationships", [])),
                "attack_techniques": llm_result.get("attack_techniques", []),
                "relationships": llm_result.get("relationships", []),
                "llm_edges_created": llm_edges_created,
            }

        return {
            "report_id": report_id,
            "title": title,
            "published_at": pub_time,
            "metrics": {
                "iocs_extracted": len(merged_iocs),
                "entities_identified": len(merged_entities),
                "nodes_added": created_nodes,
                "relationships_established": created_relationships,
            },
            "extracted_iocs": merged_iocs,
            "extracted_entities": merged_entities,
            "llm_analysis": llm_analysis_output,
            "analytics_summary": {
                "communities_detected": len(communities),
                "ml_clusters_count": len(clusters),
                "top_candidate_relationships": predictions,
            },
            "generated_subgraph": {
                "nodes": subgraph_nodes,
                "edges": subgraph_edges,
            },
        }


report_ingestion_pipeline = ReportIngestionPipeline()
