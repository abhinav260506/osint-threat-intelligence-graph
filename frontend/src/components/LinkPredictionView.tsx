import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { CandidateRelationship, EvidenceExplanation } from '../types';
import { Sparkles, ArrowRight, ShieldCheck, FileCheck, CheckCircle2, AlertTriangle, X } from 'lucide-react';

export const LinkPredictionView: React.FC = () => {
  const [candidates, setCandidates] = useState<CandidateRelationship[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateRelationship | null>(null);
  const [explanation, setExplanation] = useState<EvidenceExplanation | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState<boolean>(false);

  useEffect(() => {
    loadPredictions();
  }, []);

  const loadPredictions = async () => {
    setLoading(true);
    try {
      const res = await api.getLinkPredictions(0.35);
      setCandidates(res.candidate_relationships || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleInspect = async (cand: CandidateRelationship) => {
    setSelectedCandidate(cand);
    setLoadingExplanation(true);
    try {
      const exp = await api.getExplanation(cand.source_id, cand.target_id);
      setExplanation(exp);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingExplanation(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-cyan-400" />
          Potential Relationship Discovery & Link Prediction
        </h2>
        <p className="text-sm text-slate-400">
          Uncovering hidden, unobserved correlations between malware, campaigns, and infrastructure using Cosine Similarity on high-dimensional threat profiles and Graph Topology.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 font-mono animate-pulse">
          Computing graph topological neighbor overlap and multi-dimensional feature similarity...
        </div>
      ) : candidates.length === 0 ? (
        <div className="cyber-card p-12 text-center text-slate-400 font-mono">
          No candidate links found above threshold. Try loading benchmark datasets in the header.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Candidate List */}
          <div className="lg:col-span-2 space-y-3">
            {candidates.map((cand, idx) => (
              <div
                key={idx}
                className={`cyber-card p-4 border transition-all cursor-pointer ${
                  selectedCandidate?.source_id === cand.source_id && selectedCandidate?.target_id === cand.target_id
                    ? 'border-cyan-500 bg-cyan-950/20 shadow-lg shadow-cyan-500/10'
                    : 'border-cyber-border hover:border-slate-700'
                }`}
                onClick={() => handleInspect(cand)}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="cyber-badge bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    {cand.classification}
                  </span>
                  <div className="flex items-center gap-2 font-mono text-xs">
                    <span className="text-slate-400">Relationship Score:</span>
                    <span className="text-cyan-300 font-bold text-sm">
                      {Math.round(cand.relationship_score * 100)}%
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between py-2">
                  <div className="space-y-0.5">
                    <div className="text-sm font-bold text-slate-200">{cand.source_name}</div>
                    <div className="text-[10px] font-mono text-slate-400">{cand.source_label}</div>
                  </div>

                  <div className="px-3 py-1 bg-slate-900/80 rounded-full border border-cyber-border text-cyan-400 flex items-center gap-1 text-xs font-mono">
                    <ArrowRight className="w-3.5 h-3.5" />
                    <span>Candidate Link</span>
                  </div>

                  <div className="space-y-0.5 text-right">
                    <div className="text-sm font-bold text-slate-200">{cand.target_name}</div>
                    <div className="text-[10px] font-mono text-slate-400">{cand.target_label}</div>
                  </div>
                </div>

                <div className="flex items-center gap-4 mt-2 pt-2 border-t border-cyber-border/60 text-[11px] font-mono text-slate-400">
                  <div>TTP/Feature Similarity: <span className="text-slate-200 font-semibold">{Math.round(cand.feature_similarity * 100)}%</span></div>
                  <div>Graph Jaccard: <span className="text-slate-200 font-semibold">{Math.round(cand.graph_jaccard_similarity * 100)}%</span></div>
                </div>
              </div>
            ))}
          </div>

          {/* Explainability Engine Drawer */}
          <div className="cyber-card p-5 border border-cyber-border space-y-4 h-fit sticky top-24">
            <div className="flex items-center justify-between pb-3 border-b border-cyber-border">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
                <h3 className="font-bold text-slate-200">Explainability Engine</h3>
              </div>
              {selectedCandidate && (
                <button
                  onClick={() => {
                    setSelectedCandidate(null);
                    setExplanation(null);
                  }}
                  className="text-slate-400 hover:text-slate-200"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {!selectedCandidate ? (
              <div className="p-8 text-center text-slate-500 text-xs font-mono">
                Select any candidate relationship on the left to inspect verifiable evidence, shared infrastructure, and TTP overlap.
              </div>
            ) : loadingExplanation ? (
              <div className="p-8 text-center text-slate-400 text-xs font-mono animate-pulse">
                Synthesizing multi-vector evidence chain...
              </div>
            ) : explanation ? (
              <div className="space-y-4 text-xs font-mono">
                {/* Evidence Checklist */}
                <div>
                  <span className="text-slate-400 uppercase font-semibold block mb-2 text-[11px]">
                    Supporting Verifiable Evidence:
                  </span>
                  <div className="space-y-1.5">
                    {explanation.evidence_summary.map((bullet, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 p-2 rounded bg-slate-900/80 border border-cyber-border text-slate-300"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{bullet}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Shared Infra */}
                {explanation.shared_infrastructure.length > 0 && (
                  <div>
                    <span className="text-slate-400 uppercase font-semibold block mb-1 text-[11px]">
                      Overlapping Infrastructure:
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {explanation.shared_infrastructure.map((infra, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 text-[10px]"
                        >
                          {infra}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Shared TTPs */}
                {explanation.shared_techniques.length > 0 && (
                  <div>
                    <span className="text-slate-400 uppercase font-semibold block mb-1 text-[11px]">
                      Overlapping ATT&CK Techniques:
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {explanation.shared_techniques.map((tech, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px]"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Analytical Caveat Assessment */}
                <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-800/40 text-amber-300 text-[11px] leading-relaxed">
                  <div className="flex items-center gap-1.5 font-bold mb-1">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Epistemic Assessment
                  </div>
                  {explanation.assessment}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
