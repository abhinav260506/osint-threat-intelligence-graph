export type EntityLabel = 
  | 'ThreatActor' 
  | 'Campaign' 
  | 'Malware' 
  | 'Tool' 
  | 'IP' 
  | 'Domain' 
  | 'URL' 
  | 'Hash' 
  | 'CVE' 
  | 'AttackTechnique' 
  | 'Sector' 
  | 'Report';

export interface GraphNode {
  data: {
    id: string;
    label: EntityLabel;
    name: string;
    aliases?: string[];
    description?: string;
    country?: string;
    is_defanged?: boolean;
    is_sinkhole_or_shared?: boolean;
    ioc_type?: string;
    [key: string]: any;
  };
}

export interface GraphEdge {
  data: {
    id: string;
    source: string;
    target: string;
    label: string;
    confidence: number;
    evidence_type: string;
    source_title?: string;
    source_url?: string;
    context_snippet?: string;
    [key: string]: any;
  };
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: {
    total_nodes: number;
    total_edges: number;
  };
}

export interface CommunityMember {
  id: string;
  name: string;
  label: string;
}

export interface GraphCommunity {
  community_id: string;
  size: number;
  composition: Record<string, number>;
  members: CommunityMember[];
}

export interface MLClusterMember {
  id: string;
  name: string;
  label: string;
  cluster_membership_prob: number;
}

export interface MLCluster {
  cluster_id: number;
  cluster_name: string;
  is_noise: boolean;
  size: number;
  members: MLClusterMember[];
}

export interface CandidateRelationship {
  source_id: string;
  source_name: string;
  source_label: string;
  target_id: string;
  target_name: string;
  target_label: string;
  relationship_score: number;
  feature_similarity: number;
  graph_jaccard_similarity: number;
  is_already_connected: boolean;
  classification: string;
  status: string;
}

export interface EvidenceExplanation {
  entity_a: { id: string; name: string; label: string };
  entity_b: { id: string; name: string; label: string };
  evidence_summary: string[];
  shared_infrastructure: string[];
  shared_techniques: string[];
  shared_tools: string[];
  shared_cves: string[];
  shared_sectors: string[];
  common_reports: string[];
  connecting_paths: string[][];
  assessment: string;
  classification: string;
}

export interface IngestionResult {
  report_id: string;
  title: string;
  published_at: string;
  metrics: {
    iocs_extracted: number;
    entities_identified: number;
    nodes_added: number;
    relationships_established: number;
  };
  extracted_iocs: any[];
  extracted_entities: any[];
  llm_analysis?: {
    report_summary: string;
    key_findings: string[];
    threat_actors_found: number;
    malware_found: number;
    relationships_extracted: number;
    attack_techniques: any[];
    relationships: any[];
    llm_edges_created: number;
  };
  analytics_summary?: {
    communities_detected: number;
    ml_clusters_count: number;
    top_candidate_relationships: any[];
  };
  generated_subgraph?: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
}
