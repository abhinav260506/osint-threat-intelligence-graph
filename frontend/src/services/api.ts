import type { GraphData, GraphCommunity, MLCluster, CandidateRelationship, EvidenceExplanation, IngestionResult } from '../types';

const API_BASE = '/api/v1';

export const api = {
  async getHealth() {
    const res = await fetch('/health');
    return res.json();
  },

  async getGraph(limit: number = 600): Promise<GraphData> {
    const res = await fetch(`${API_BASE}/graph?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch graph data');
    return res.json();
  },

  async getEntity(nodeId: string) {
    const res = await fetch(`${API_BASE}/graph/entity/${encodeURIComponent(nodeId)}`);
    if (!res.ok) throw new Error('Failed to fetch entity details');
    return res.json();
  },

  async findPath(sourceId: string, targetId: string) {
    const res = await fetch(`${API_BASE}/graph/path?source_id=${encodeURIComponent(sourceId)}&target_id=${encodeURIComponent(targetId)}`);
    if (!res.ok) throw new Error('Failed to find paths');
    return res.json();
  },

  async getCommunities(): Promise<{ community_count: number; communities: GraphCommunity[] }> {
    const res = await fetch(`${API_BASE}/analytics/communities`);
    if (!res.ok) throw new Error('Failed to fetch communities');
    return res.json();
  },

  async getClusters(): Promise<{ cluster_count: number; clusters: MLCluster[] }> {
    const res = await fetch(`${API_BASE}/analytics/clusters`);
    if (!res.ok) throw new Error('Failed to fetch ML clusters');
    return res.json();
  },

  async getLinkPredictions(minScore: number = 0.35): Promise<{ candidate_count: number; candidate_relationships: CandidateRelationship[] }> {
    const res = await fetch(`${API_BASE}/analytics/link-prediction?min_score=${minScore}`);
    if (!res.ok) throw new Error('Failed to fetch link predictions');
    return res.json();
  },

  async getExplanation(entityA: string, entityB: string): Promise<EvidenceExplanation> {
    const res = await fetch(`${API_BASE}/analytics/explain?entity_a=${encodeURIComponent(entityA)}&entity_b=${encodeURIComponent(entityB)}`);
    if (!res.ok) throw new Error('Failed to fetch explanation');
    return res.json();
  },

  async listIoCs(iocType?: string, search?: string) {
    const params = new URLSearchParams();
    if (iocType) params.append('ioc_type', iocType);
    if (search) params.append('search', search);
    const res = await fetch(`${API_BASE}/iocs?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to list IoCs');
    return res.json();
  },

  async ingestReport(payload: { title: string; content: string; source_name?: string; source_url?: string }): Promise<IngestionResult> {
    const res = await fetch(`${API_BASE}/ingestion/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to ingest report');
    return res.json();
  },

  async uploadReportFile(formData: FormData): Promise<IngestionResult> {
    const res = await fetch(`${API_BASE}/ingestion/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to upload and process document');
    return res.json();
  },

  async seedBenchmarks() {
    const res = await fetch(`${API_BASE}/ingestion/seed-benchmarks`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to seed benchmarks');
    return res.json();
  },

  async clearGraph() {
    const res = await fetch(`${API_BASE}/graph/clear`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to clear graph');
    return res.json();
  },
};
