import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Search, ShieldAlert, CheckCircle, Database } from 'lucide-react';

export const IocSearch: React.FC = () => {
  const [iocs, setIocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('');

  const types = ['IP', 'Domain', 'URL', 'Hash', 'CVE', 'AttackTechnique'];

  useEffect(() => {
    fetchIocs();
  }, [selectedType]);

  const fetchIocs = async () => {
    setLoading(true);
    try {
      const res = await api.listIoCs(selectedType || undefined, searchTerm || undefined);
      setIocs(res.iocs || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchIocs();
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Database className="w-6 h-6 text-cyan-400" />
          Extracted Indicators of Compromise (IoC) Registry
        </h2>
        <p className="text-sm text-slate-400">
          Search, filter, and inspect normalized network observables, hashes, vulnerabilities, and ATT&CK techniques with defanging provenance.
        </p>
      </div>

      {/* Search & Filter Bar */}
      <div className="cyber-card p-4 border border-cyber-border flex flex-col md:flex-row items-center gap-4">
        <form onSubmit={handleSearchSubmit} className="flex-1 relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search IP, domain, hash, CVE (e.g. 54.193.127.211 or panprocess[.]com)..."
            className="w-full pl-9 pr-4 py-2 bg-slate-900/80 border border-cyber-border rounded-lg text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </form>

        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
          <button
            onClick={() => setSelectedType('')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
              selectedType === ''
                ? 'bg-blue-600 text-white font-semibold'
                : 'bg-slate-900/80 border border-cyber-border text-slate-400 hover:text-slate-200'
            }`}
          >
            All Types
          </button>
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                selectedType === t
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'bg-slate-900/80 border border-cyber-border text-slate-400 hover:text-slate-200'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="cyber-card border border-cyber-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 border-b border-cyber-border text-slate-400 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="p-3.5">Type</th>
                <th className="p-3.5">Normalized Indicator Value</th>
                <th className="p-3.5">Original / Defanged</th>
                <th className="p-3.5">Graph Connectivity</th>
                <th className="p-3.5">Security Classification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyber-border/60">
              {loading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-400 animate-pulse">
                    Querying Knowledge Graph IoCs...
                  </td>
                </tr>
              ) : iocs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500">
                    No matching IoCs found in the knowledge graph.
                  </td>
                </tr>
              ) : (
                iocs.map((ioc) => (
                  <tr key={ioc.id} className="hover:bg-slate-800/40 transition-all">
                    <td className="p-3.5">
                      <span className="cyber-badge bg-blue-500/15 text-blue-300 border border-blue-500/25">
                        {ioc.label}
                      </span>
                    </td>
                    <td className="p-3.5 font-bold text-slate-200">{ioc.value}</td>
                    <td className="p-3.5 text-slate-400">
                      {ioc.properties?.original_value || ioc.value}
                      {ioc.properties?.is_defanged && (
                        <span className="ml-2 text-[10px] text-cyan-400 font-semibold">(Defanged)</span>
                      )}
                    </td>
                    <td className="p-3.5 text-slate-300">
                      {ioc.degree} edge(s)
                    </td>
                    <td className="p-3.5">
                      {ioc.is_sinkhole ? (
                        <span className="cyber-badge bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          Shared / Sinkhole
                        </span>
                      ) : (
                        <span className="cyber-badge bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          Active Malicious IoC
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
