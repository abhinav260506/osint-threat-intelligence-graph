import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { GraphCommunity, MLCluster } from '../types';
import { Layers, Cpu, Shield, Network, ArrowRight } from 'lucide-react';

export const ClusterView: React.FC = () => {
  const [communities, setCommunities] = useState<GraphCommunity[]>([]);
  const [mlClusters, setMlClusters] = useState<MLCluster[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCommunity, setSelectedCommunity] = useState<GraphCommunity | null>(null);
  const [selectedMlCluster, setSelectedMlCluster] = useState<MLCluster | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [commRes, clusterRes] = await Promise.all([
        api.getCommunities(),
        api.getClusters(),
      ]);
      setCommunities(commRes.communities || []);
      setMlClusters(clusterRes.clusters || []);
      if (commRes.communities && commRes.communities.length > 0) {
        setSelectedCommunity(commRes.communities[0]);
      }
      if (clusterRes.clusters && clusterRes.clusters.length > 0) {
        setSelectedMlCluster(clusterRes.clusters[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* View Header */}
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Layers className="w-6 h-6 text-cyan-400" />
          Hybrid Campaign & Threat Community Clustering
        </h2>
        <p className="text-sm text-slate-400">
          Comparing topological Graph Data Science (GDS Modularity) communities against Unsupervised Machine Learning (HDBSCAN feature embeddings) clusters.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 font-mono animate-pulse">
          Computing graph modularity and ML feature embeddings...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 1. Graph Data Science Communities */}
          <div className="cyber-card p-5 border border-cyber-border space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-cyber-border">
              <div className="flex items-center gap-2">
                <Network className="w-5 h-5 text-blue-400" />
                <h3 className="font-bold text-slate-200">GDS Graph Communities (Modularity)</h3>
              </div>
              <span className="cyber-badge bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {communities.length} Communities
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {communities.map((comm) => (
                <button
                  key={comm.community_id}
                  onClick={() => setSelectedCommunity(comm)}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    selectedCommunity?.community_id === comm.community_id
                      ? 'bg-blue-600/20 border-blue-500 shadow-lg shadow-blue-500/10'
                      : 'bg-slate-900/60 border-cyber-border hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between font-mono text-xs mb-1">
                    <span className="font-semibold text-slate-200">{comm.community_id}</span>
                    <span className="text-cyan-400">{comm.size} nodes</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {Object.entries(comm.composition).slice(0, 3).map(([lbl, count]) => (
                      <span
                        key={lbl}
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400"
                      >
                        {lbl}: {count}
                      </span>
                    ))}
                  </div>
                </button>
              ))}
            </div>

            {selectedCommunity && (
              <div className="mt-4 p-4 rounded-xl bg-slate-900/80 border border-cyber-border space-y-3">
                <span className="text-xs font-mono font-semibold uppercase text-slate-400">
                  {selectedCommunity.community_id} Member Breakdown:
                </span>
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {selectedCommunity.members.map((m) => (
                    <div
                      key={m.id}
                      className="flex items-center justify-between p-2 rounded bg-slate-800/50 text-xs font-mono"
                    >
                      <span className="font-medium text-slate-200 truncate">{m.name}</span>
                      <span className="text-[10px] text-cyan-300 px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800">
                        {m.label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 2. HDBSCAN Machine Learning Clusters */}
          <div className="cyber-card p-5 border border-cyber-border space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-cyber-border">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-purple-400" />
                <h3 className="font-bold text-slate-200">ML Threat Profile Clusters (HDBSCAN)</h3>
              </div>
              <span className="cyber-badge bg-purple-500/20 text-purple-300 border border-purple-500/30">
                {mlClusters.length} Clusters
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {mlClusters.map((cluster) => (
                <button
                  key={cluster.cluster_id}
                  onClick={() => setSelectedMlCluster(cluster)}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    selectedMlCluster?.cluster_id === cluster.cluster_id
                      ? 'bg-purple-600/20 border-purple-500 shadow-lg shadow-purple-500/10'
                      : 'bg-slate-900/60 border-cyber-border hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between font-mono text-xs mb-1">
                    <span className="font-semibold text-slate-200">{cluster.cluster_name}</span>
                    <span className="text-purple-400">{cluster.size} entities</span>
                  </div>
                  <span className={`text-[10px] font-mono ${cluster.is_noise ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {cluster.is_noise ? 'Isolated (Noise)' : 'Dense Cluster'}
                  </span>
                </button>
              ))}
            </div>

            {selectedMlCluster && (
              <div className="mt-4 p-4 rounded-xl bg-slate-900/80 border border-cyber-border space-y-3">
                <span className="text-xs font-mono font-semibold uppercase text-slate-400">
                  {selectedMlCluster.cluster_name} Entities:
                </span>
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {selectedMlCluster.members.map((m) => (
                    <div
                      key={m.id}
                      className="flex items-center justify-between p-2 rounded bg-slate-800/50 text-xs font-mono"
                    >
                      <span className="font-medium text-slate-200 truncate">{m.name}</span>
                      <span className="text-[10px] text-purple-300 px-1.5 py-0.5 rounded bg-purple-950 border border-purple-800">
                        Prob: {Math.round(m.cluster_membership_prob * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
