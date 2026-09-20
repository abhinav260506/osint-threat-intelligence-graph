import React from 'react';
import { ShieldAlert, Network, Layers, Sparkles, Search, FileText, RefreshCw } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  stats: { total_nodes: number; total_edges: number };
  onRefresh: () => void;
  onSeed: () => void;
  isSeeding: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  stats,
  onRefresh,
  onSeed,
  isSeeding,
}) => {
  const tabs = [
    { id: 'graph', label: 'Threat Graph', icon: Network },
    { id: 'clusters', label: 'Campaign Clusters', icon: Layers },
    { id: 'prediction', label: 'Link Prediction', icon: Sparkles },
    { id: 'iocs', label: 'IoC Registry', icon: Search },
    { id: 'ingestion', label: 'Ingestion Workbench', icon: FileText },
  ];

  return (
    <header className="cyber-glass sticky top-0 z-50 border-b border-cyber-border/80 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/10 border border-blue-500/30 rounded-lg text-blue-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-blue-400 via-cyan-300 to-indigo-400 bg-clip-text text-transparent">
                ThreatGraph AI
              </span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                STIX 2.1
              </span>
            </div>
            <p className="text-xs text-slate-400">Automated Threat Intelligence & Graph Data Science</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-cyber-border">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Quick Stats & Actions */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-3 text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-900/80 border border-cyber-border">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              <span className="text-slate-400">Nodes:</span>
              <span className="text-cyan-300 font-semibold">{stats.total_nodes}</span>
            </div>
            <span className="text-slate-600">|</span>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400">Edges:</span>
              <span className="text-purple-300 font-semibold">{stats.total_edges}</span>
            </div>
          </div>

          <button
            onClick={onRefresh}
            title="Refresh Graph"
            className="p-2 text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-700/60 border border-cyber-border rounded-lg transition-all"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={onSeed}
            disabled={isSeeding}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg bg-gradient-to-r from-cyan-500/20 to-blue-600/20 hover:from-cyan-500/30 hover:to-blue-600/30 text-cyan-300 border border-cyan-500/30 transition-all disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {isSeeding ? 'Seeding...' : 'Load Benchmarks'}
          </button>
        </div>
      </div>
    </header>
  );
};
