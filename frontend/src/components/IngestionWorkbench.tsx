import React, { useState, useRef, useEffect } from 'react';
import cytoscape from 'cytoscape';
import { api } from '../services/api';
import { IngestionResult, EntityLabel } from '../types';
import { 
  FileText, 
  Upload, 
  Send, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles, 
  BookOpen, 
  FileUp, 
  Cpu, 
  Network, 
  Layers, 
  ArrowRight, 
  ShieldCheck,
  Check,
  ChevronRight,
  RefreshCw,
  ExternalLink,
  Maximize2,
  ZoomIn,
  ZoomOut
} from 'lucide-react';

interface IngestionWorkbenchProps {
  onIngested: () => void;
  onNavigateToGraph?: () => void;
}

const LABEL_COLORS: Record<EntityLabel | string, string> = {
  ThreatActor: '#ef4444',      // Red
  Campaign: '#f97316',         // Orange
  Malware: '#a855f7',          // Purple
  Tool: '#8b5cf6',             // Violet
  Domain: '#3b82f6',           // Blue
  IP: '#06b6d4',               // Cyan
  URL: '#0284c7',              // Sky Blue
  Hash: '#94a3b8',             // Gray
  CVE: '#eab308',              // Yellow
  AttackTechnique: '#10b981',  // Emerald
  Sector: '#ec4899',           // Pink
  Report: '#6366f1',           // Indigo
};

export const IngestionWorkbench: React.FC<IngestionWorkbenchProps> = ({ onIngested, onNavigateToGraph }) => {
  const [inputMode, setInputMode] = useState<'paste' | 'upload'>('paste');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [sourceName, setSourceName] = useState('Analyst OSINT Report');
  const [sourceUrl, setSourceUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Analysis Flow State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeStep, setActiveStep] = useState<number>(0);
  const [result, setResult] = useState<IngestionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeResultTab, setActiveResultTab] = useState<'graph' | 'iocs' | 'entities' | 'predictions' | 'llm'>('graph');

  // Subgraph Cytoscape container ref
  const cySubRef = useRef<HTMLDivElement>(null);
  const cyInstanceRef = useRef<cytoscape.Core | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sampleSnippets = [
    {
      name: 'APT29 SolarWinds Intrusion',
      title: 'CISA Alert AA20-352A: Advanced Persistent Threat Compromises SolarWinds',
      content: `CISA and FBI identify APT29 (also known as Cozy Bear, NOBELIUM) utilizing SUNBURST malware.
The backdoor contacted C2 domains: avsvmcloud[.]com, panprocess[.]com, and deftsecurity[.]com resolving to 54.193.127[.]211 and 13.59.205[.]66.
Deploying Cobalt Strike and Mimikatz for lateral movement.
Observed MITRE ATT&CK techniques: T1059.001 (Command and Scripting Interpreter), T1078 (Valid Accounts), T1003 (OS Credential Dumping), and T1195.002 (Supply Chain Compromise).
Exploited CVE: CVE-2020-10148.
Targeted Sectors: Government, Technology, and Financial Services.`,
    },
    {
      name: 'Volt Typhoon Critical Infra',
      title: 'CISA Joint Advisory: Volt Typhoon Compromises US Critical Infrastructure',
      content: `The cyber group Volt Typhoon (Bronze Silhouette, Vanguard Panda) was observed compromising routers to establish stealth proxy networks.
The actors connected to malicious domains: router-auth-update[.]com and 45.33.32[.]156.
They utilized living-off-the-land tools such as wmic and netsh.
Observed MITRE techniques include T1078 (Valid Accounts), T1059 (Command and Scripting Interpreter), and T1016 (System Network Configuration Discovery).
Targeted sectors: Telecommunications, Energy, and Government.`,
    },
    {
      name: 'Lazarus AppleJeus Campaign',
      title: 'FBI Flash Alert: Lazarus Deploys AppleJeus Backdoors in Fintech',
      content: `Lazarus Group (HIDDEN COBRA, Zinc) created fraudulent fintech trading platforms to distribute AppleJeus payloads.
C2 traffic was routed through secure-wallet-api[.]org and 185.193.125[.]14.
SHA-256 fingerprint: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.
Targeted sectors: Financial Services and Technology.
Techniques: T1566 (Phishing) and T1059.`,
    },
  ];

  const analysisSteps = [
    { label: 'Document Processing', desc: 'PDF→Text, Clean & Chunk' },
    { label: 'LLM Deep Analysis', desc: 'Gemini Entity & Relationship Extraction' },
    { label: 'Deterministic Extraction', desc: 'Regex IoCs, Defanging, Validation' },
    { label: 'Merge & Normalize', desc: 'LLM + Regex Fusion & Resolution' },
    { label: 'Knowledge Graph Assembly', desc: 'STIX 2.1 Nodes & Provenance Edges' },
    { label: 'GDS & ML Analytics', desc: 'Clustering, Link Prediction, Evidence' },
  ];

  // Render Subgraph when analysis completes or tab changes to graph
  useEffect(() => {
    if (!result?.generated_subgraph || activeResultTab !== 'graph' || !cySubRef.current) {
      return;
    }

    const { nodes, edges } = result.generated_subgraph;

    const cy = cytoscape({
      container: cySubRef.current,
      elements: [...nodes, ...edges],
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(name)',
            'color': '#f8fafc',
            'font-size': '9px',
            'font-family': 'Inter, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'background-color': (ele: any) => LABEL_COLORS[ele.data('label')] || '#64748b',
            'width': (ele: any) => {
              const lbl = ele.data('label');
              if (lbl === 'Report') return 34;
              if (lbl === 'ThreatActor' || lbl === 'Campaign') return 28;
              if (lbl === 'Malware') return 24;
              return 18;
            },
            'height': (ele: any) => {
              const lbl = ele.data('label');
              if (lbl === 'Report') return 34;
              if (lbl === 'ThreatActor' || lbl === 'Campaign') return 28;
              if (lbl === 'Malware') return 24;
              return 18;
            },
            'border-width': 2,
            'border-color': '#1e293b',
          } as any,
        },
        {
          selector: 'node[label = "Report"]',
          style: {
            'border-color': '#818cf8',
            'border-width': 3,
          } as any,
        },
        {
          selector: 'edge',
          style: {
            'label': 'data(label)',
            'font-size': '7px',
            'color': '#64748b',
            'text-rotation': 'autorotate',
            'text-margin-y': -5,
            'width': 1.5,
            'line-color': '#334155',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.7,
            'opacity': 0.8,
          } as any,
        },
      ],
      layout: {
        name: 'concentric',
        concentric: (node: any) => {
          if (node.data('label') === 'Report') return 10;
          if (node.data('label') === 'ThreatActor' || node.data('label') === 'Campaign') return 7;
          if (node.data('label') === 'Malware') return 5;
          return 2;
        },
        levelWidth: () => 2,
        padding: 20,
        animate: true,
        animationDuration: 400,
      } as any,
    });

    cyInstanceRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [result, activeResultTab]);

  const handleApplyTemplate = (snippet: typeof sampleSnippets[0]) => {
    setInputMode('paste');
    setTitle(snippet.title);
    setContent(snippet.content);
    setSourceName('Joint Advisory');
    setSelectedFile(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (!title) {
        setTitle(`Report: ${file.name}`);
      }
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMode === 'paste' && (!title || !content)) return;
    if (inputMode === 'upload' && !selectedFile) return;

    setIsAnalyzing(true);
    setError(null);
    setResult(null);
    setActiveStep(0);

    // Step 1: Input Validation
    setActiveStep(1);
    await new Promise((r) => setTimeout(r, 300));

    // Step 2: Extraction
    setActiveStep(2);
    await new Promise((r) => setTimeout(r, 400));

    // Step 3: Normalization & Resolution
    setActiveStep(3);
    await new Promise((r) => setTimeout(r, 350));

    try {
      let res: IngestionResult;
      if (inputMode === 'upload' && selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('title', title || `Uploaded: ${selectedFile.name}`);
        formData.append('source_name', sourceName);
        res = await api.uploadReportFile(formData);
      } else {
        res = await api.ingestReport({
          title,
          content,
          source_name: sourceName,
          source_url: sourceUrl || undefined,
        });
      }

      // Step 4: STIX Graph
      setActiveStep(4);
      await new Promise((r) => setTimeout(r, 350));

      // Step 5: GDS & ML Analytics
      setActiveStep(5);
      await new Promise((r) => setTimeout(r, 350));

      // Step 6: Complete
      setActiveStep(6);
      setResult(res);
      setActiveResultTab('graph'); // Automatically show the generated graph view
      onIngested();
    } catch (err: any) {
      setError(err.message || 'Analysis pipeline failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <FileText className="w-6 h-6 text-cyan-400" />
          Threat Report Analysis & Live Graph Generation
        </h2>
        <p className="text-sm text-slate-400">
          Upload or paste unstructured threat reports (PDF, TXT, Markdown, STIX) to trigger extraction, STIX 2.1 mapping, and instantaneously generate the interactive Threat Graph.
        </p>
      </div>

      {/* Main Analysis Architecture Flow Stepper */}
      <div className="cyber-card p-5 border border-cyber-border space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-cyber-border/60">
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Automated Threat Intelligence Analysis Pipeline
          </span>
          <span className="text-[11px] font-mono text-cyan-400">
            {isAnalyzing ? `Executing Step ${activeStep} of 6...` : result ? 'Pipeline Execution Complete ➔ Graph Generated' : 'Ready for Analysis'}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-2 pt-2">
          {analysisSteps.map((step, idx) => {
            const stepNum = idx + 1;
            const isCompleted = activeStep > stepNum || (result && !isAnalyzing);
            const isCurrent = activeStep === stepNum && isAnalyzing;

            return (
              <div
                key={idx}
                className={`p-3 rounded-lg border text-left transition-all ${
                  isCurrent
                    ? 'bg-cyan-950/40 border-cyan-400 shadow-lg shadow-cyan-500/20 scale-[1.02]'
                    : isCompleted
                    ? 'bg-slate-900/80 border-emerald-500/50 text-slate-200'
                    : 'bg-slate-900/40 border-cyber-border/60 text-slate-500'
                }`}
              >
                <div className="flex items-center justify-between font-mono text-[10px] mb-1">
                  <span className="font-bold">STEP 0{stepNum}</span>
                  {isCompleted ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : isCurrent ? (
                    <RefreshCw className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-600" />
                  )}
                </div>
                <div className="font-semibold text-xs text-slate-200 leading-tight mb-1">
                  {step.label}
                </div>
                <div className="text-[10px] text-slate-400 font-mono">
                  {step.desc}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Input & Live Results Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Form (5 cols) */}
        <div className="lg:col-span-5 cyber-card p-6 border border-cyber-border space-y-4 h-fit">
          {/* Mode Switcher */}
          <div className="flex items-center justify-between pb-3 border-b border-cyber-border/60">
            <div className="flex rounded-lg bg-slate-900/80 p-1 border border-cyber-border">
              <button
                type="button"
                onClick={() => setInputMode('paste')}
                className={`px-3 py-1.5 text-xs font-mono rounded-md transition-all ${
                  inputMode === 'paste'
                    ? 'bg-blue-600 text-white font-semibold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Paste Report Text
              </button>
              <button
                type="button"
                onClick={() => setInputMode('upload')}
                className={`px-3 py-1.5 text-xs font-mono rounded-md transition-all ${
                  inputMode === 'upload'
                    ? 'bg-blue-600 text-white font-semibold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Upload Document (PDF/TXT/STIX)
              </button>
            </div>
          </div>

          {/* Preset Buttons */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
              Pre-seeded CTI Advisories:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {sampleSnippets.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleApplyTemplate(s)}
                  className="px-2 py-1 text-[10px] font-mono rounded bg-slate-800/80 text-cyan-300 hover:bg-slate-700 border border-cyber-border transition-all"
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleAnalyze} className="space-y-4 pt-2">
            <div>
              <label className="block text-xs font-mono font-semibold uppercase text-slate-300 mb-1">
                Report Title / Advisory Heading
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. CISA Alert AA24-038A: Volt Typhoon Infiltration"
                className="w-full px-3.5 py-2 bg-slate-900/80 border border-cyber-border rounded-lg text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-mono font-semibold uppercase text-slate-300 mb-1">
                  Source Author / Vendor
                </label>
                <input
                  type="text"
                  value={sourceName}
                  onChange={(e) => setSourceName(e.target.value)}
                  placeholder="e.g. CISA, Mandiant"
                  className="w-full px-3.5 py-2 bg-slate-900/80 border border-cyber-border rounded-lg text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div>
                <label className="block text-xs font-mono font-semibold uppercase text-slate-300 mb-1">
                  Source URL (Optional)
                </label>
                <input
                  type="url"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full px-3.5 py-2 bg-slate-900/80 border border-cyber-border rounded-lg text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            {inputMode === 'upload' ? (
              <div>
                <label className="block text-xs font-mono font-semibold uppercase text-slate-300 mb-1">
                  Select Threat Report File (PDF, TXT, MD, JSON/STIX)
                </label>
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-cyber-border hover:border-cyan-500/60 p-6 rounded-xl text-center cursor-pointer bg-slate-900/50 transition-all"
                >
                  <FileUp className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                  {selectedFile ? (
                    <div className="font-mono text-xs text-slate-200">
                      <span className="text-cyan-400 font-bold">{selectedFile.name}</span> ({(selectedFile.size / 1024).toFixed(1)} KB)
                    </div>
                  ) : (
                    <div className="space-y-1">
                      <div className="text-xs font-mono text-slate-300 font-semibold">
                        Click or drag document to upload
                      </div>
                      <div className="text-[10px] font-mono text-slate-500">
                        Supports PDF whitepapers, Markdown, and STIX 2.1 JSON
                      </div>
                    </div>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.txt,.md,.json"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-mono font-semibold uppercase text-slate-300 mb-1">
                  Raw Advisory Text Content (Defanged IoCs Supported)
                </label>
                <textarea
                  required
                  rows={9}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste unstructured threat advisory text containing defanged indicators (e.g. hxxp://evil[.]com, 192[.]168[.]1[.]1), threat actors, malware, and ATT&CK techniques..."
                  className="w-full px-3.5 py-2 bg-slate-900/80 border border-cyber-border rounded-lg text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={isAnalyzing}
              className="w-full py-3 bg-gradient-to-r from-blue-600 via-cyan-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-xl shadow-cyan-600/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Analyzing & Generating Threat Graph...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Analyze Report & Generate Graph</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Live Analysis Telemetry & Generated Threat Graph Output (7 cols) */}
        <div className="lg:col-span-7 cyber-card p-6 border border-cyber-border space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-cyber-border">
            <h3 className="font-bold text-slate-200 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-cyan-400" />
              Generated Intelligence & Threat Graph
            </h3>
            {result && onNavigateToGraph && (
              <button
                onClick={onNavigateToGraph}
                className="flex items-center gap-1.5 text-xs font-mono text-cyan-300 hover:text-cyan-200 px-3 py-1.5 rounded-lg bg-cyan-950 border border-cyan-800 shadow-md transition-all font-semibold"
              >
                <span>Expand Master Threat Graph</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/40 text-red-300 text-xs font-mono flex items-center gap-2">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!result && !isAnalyzing ? (
            <div className="p-16 text-center text-slate-500 space-y-2">
              <Network className="w-12 h-12 text-slate-600 mx-auto animate-pulse" />
              <div className="font-mono text-sm font-semibold text-slate-400">
                Threat Knowledge Graph Generator Ready
              </div>
              <div className="text-xs text-slate-500 font-mono">
                Submit an advisory or PDF report on the left. The system will automatically construct and render the interactive STIX 2.1 Threat Graph here in real time.
              </div>
            </div>
          ) : isAnalyzing ? (
            <div className="p-16 text-center text-slate-400 space-y-3 font-mono animate-pulse">
              <RefreshCw className="w-10 h-10 text-cyan-400 mx-auto animate-spin" />
              <div className="text-sm font-bold text-slate-200">Analyzing Threat Report</div>
              <div className="text-xs text-slate-400">Running LLM deep analysis → IoC extraction → Entity resolution → Graph assembly → ML analytics...</div>
            </div>
          ) : result ? (
            <div className="space-y-4">
              {/* Quick Metrics Bar */}
              <div className="grid grid-cols-4 gap-2 font-mono">
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-cyber-border text-center">
                  <div className="text-lg font-bold text-cyan-300">{result.metrics.iocs_extracted}</div>
                  <div className="text-[9px] text-slate-400 uppercase">IoCs Extracted</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-cyber-border text-center">
                  <div className="text-lg font-bold text-purple-300">{result.metrics.entities_identified}</div>
                  <div className="text-[9px] text-slate-400 uppercase">Entities Resolved</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-cyber-border text-center">
                  <div className="text-lg font-bold text-blue-300">{result.metrics.nodes_added}</div>
                  <div className="text-[9px] text-slate-400 uppercase">Graph Nodes</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-cyber-border text-center">
                  <div className="text-lg font-bold text-emerald-300">{result.metrics.relationships_established}</div>
                  <div className="text-[9px] text-slate-400 uppercase">Relationships</div>
                </div>
              </div>

              {/* Result Tabs */}
              <div className="flex border-b border-cyber-border/60">
                <button
                  onClick={() => setActiveResultTab('graph')}
                  className={`flex items-center gap-1.5 px-3 py-2 text-xs font-mono border-b-2 transition-all ${
                    activeResultTab === 'graph'
                      ? 'border-cyan-400 text-cyan-300 font-semibold'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Network className="w-3.5 h-3.5" />
                  Generated Report Graph ({result.metrics.nodes_added} Nodes)
                </button>
                <button
                  onClick={() => setActiveResultTab('iocs')}
                  className={`px-3 py-2 text-xs font-mono border-b-2 transition-all ${
                    activeResultTab === 'iocs'
                      ? 'border-blue-400 text-blue-300 font-semibold'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Extracted IoCs ({result.extracted_iocs.length})
                </button>
                <button
                  onClick={() => setActiveResultTab('entities')}
                  className={`px-3 py-2 text-xs font-mono border-b-2 transition-all ${
                    activeResultTab === 'entities'
                      ? 'border-purple-400 text-purple-300 font-semibold'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Entities ({result.extracted_entities.length})
                </button>
                {result.analytics_summary?.top_candidate_relationships && (
                  <button
                    onClick={() => setActiveResultTab('predictions')}
                    className={`px-3 py-2 text-xs font-mono border-b-2 transition-all ${
                      activeResultTab === 'predictions'
                        ? 'border-amber-400 text-amber-300 font-semibold'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Campaign Overlaps ({result.analytics_summary.top_candidate_relationships.length})
                  </button>
                )}
                {result.llm_analysis && (
                  <button
                    onClick={() => setActiveResultTab('llm')}
                    className={`flex items-center gap-1.5 px-3 py-2 text-xs font-mono border-b-2 transition-all ${
                      activeResultTab === 'llm'
                        ? 'border-emerald-400 text-emerald-300 font-semibold'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2a8 8 0 0 0-8 8c0 3.5 2 6 4 7.5V20a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2.5c2-1.5 4-4 4-7.5a8 8 0 0 0-8-8z"/><path d="M10 22v-1h4v1"/></svg>
                    LLM Intelligence ({result.llm_analysis.relationships_extracted} relationships)
                  </button>
                )}
              </div>

              {/* Tab 0: Interactive Generated Subgraph Canvas */}
              {activeResultTab === 'graph' && (
                <div className="relative w-full h-80 rounded-xl overflow-hidden border border-cyber-border bg-[#080c14]">
                  <div ref={cySubRef} className="w-full h-full" />
                  <div className="absolute bottom-2 left-2 px-2.5 py-1 rounded bg-slate-900/80 border border-cyber-border text-[10px] font-mono text-slate-400 z-10 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                    <span>Interactive Subgraph • Drag & Zoom nodes</span>
                  </div>
                </div>
              )}

              {/* Tab 1: Extracted IoCs */}
              {activeResultTab === 'iocs' && (
                <div className="max-h-72 overflow-y-auto pr-1 space-y-1.5">
                  {result.extracted_iocs.length === 0 ? (
                    <div className="p-4 text-center text-xs font-mono text-slate-500">
                      No standalone IoCs found in the submitted document.
                    </div>
                  ) : (
                    result.extracted_iocs.map((ioc: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-slate-900/80 border border-cyber-border text-xs font-mono flex items-center justify-between"
                      >
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-200">{ioc.normalized_value}</span>
                            {ioc.is_defanged && (
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                                Refanged from {ioc.original_value}
                              </span>
                            )}
                          </div>
                          {ioc.context_snippet && (
                            <div className="text-[10px] text-slate-500 truncate max-w-md">
                              {ioc.context_snippet}
                            </div>
                          )}
                        </div>
                        <span className="cyber-badge bg-blue-500/20 text-blue-300 border border-blue-500/30">
                          {ioc.ioc_type}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Tab 2: Resolved Entities */}
              {activeResultTab === 'entities' && (
                <div className="max-h-72 overflow-y-auto pr-1 space-y-2">
                  {result.extracted_entities.length === 0 ? (
                    <div className="p-4 text-center text-xs font-mono text-slate-500">
                      No threat actors, malware, or sector entities identified.
                    </div>
                  ) : (
                    result.extracted_entities.map((ent: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-slate-900/80 border border-cyber-border text-xs font-mono space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-100">{ent.canonical_name}</span>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                              {ent.entity_type}
                            </span>
                            {ent.classification_basis === 'LLM Contextual Analysis' && (
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                LLM
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-slate-400">
                            Confidence: {Math.round(ent.confidence * 100)}%
                          </span>
                        </div>
                        {ent.aliases && ent.aliases.length > 0 && (
                          <div className="text-[10px] text-slate-400">
                            Known Aliases: {ent.aliases.join(', ')}
                          </div>
                        )}
                        {ent.description && (
                          <div className="text-[10px] text-slate-400 italic">
                            {ent.description}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Tab 3: LLM Intelligence Analysis */}
              {activeResultTab === 'llm' && result.llm_analysis && (
                <div className="max-h-96 overflow-y-auto pr-1 space-y-3">
                  {/* Summary */}
                  <div className="p-3.5 rounded-lg bg-gradient-to-br from-emerald-950/50 to-slate-900/80 border border-emerald-500/30 text-xs font-mono space-y-2">
                    <div className="flex items-center gap-2 mb-1">
                      <svg className="w-4 h-4 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2a8 8 0 0 0-8 8c0 3.5 2 6 4 7.5V20a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2.5c2-1.5 4-4 4-7.5a8 8 0 0 0-8-8z"/></svg>
                      <span className="font-bold text-emerald-300 text-sm">Gemini LLM Analysis</span>
                    </div>
                    <p className="text-slate-300 leading-relaxed">{result.llm_analysis.report_summary}</p>
                    <div className="grid grid-cols-3 gap-2 pt-2 border-t border-emerald-800/40">
                      <div className="text-center">
                        <div className="text-emerald-300 font-bold">{result.llm_analysis.threat_actors_found}</div>
                        <div className="text-[9px] text-slate-500 uppercase">Threat Actors</div>
                      </div>
                      <div className="text-center">
                        <div className="text-emerald-300 font-bold">{result.llm_analysis.malware_found}</div>
                        <div className="text-[9px] text-slate-500 uppercase">Malware</div>
                      </div>
                      <div className="text-center">
                        <div className="text-emerald-300 font-bold">{result.llm_analysis.llm_edges_created}</div>
                        <div className="text-[9px] text-slate-500 uppercase">LLM Edges</div>
                      </div>
                    </div>
                  </div>

                  {/* Key Findings */}
                  {result.llm_analysis.key_findings.length > 0 && (
                    <div className="p-3 rounded-lg bg-slate-900/80 border border-cyber-border text-xs font-mono space-y-1.5">
                      <div className="font-bold text-amber-300 text-[11px]">⚡ Key Intelligence Findings</div>
                      {result.llm_analysis.key_findings.map((finding: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-slate-300">
                          <span className="text-amber-400 mt-0.5 shrink-0">▸</span>
                          <span>{finding}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* ATT&CK Techniques with context */}
                  {result.llm_analysis.attack_techniques.length > 0 && (
                    <div className="p-3 rounded-lg bg-slate-900/80 border border-cyber-border text-xs font-mono space-y-1.5">
                      <div className="font-bold text-red-300 text-[11px]">🎯 ATT&CK Techniques (LLM Context)</div>
                      {result.llm_analysis.attack_techniques.map((tech: any, i: number) => (
                        <div key={i} className="flex items-start gap-2">
                          <span className="text-red-400 font-bold shrink-0">{tech.technique_id}</span>
                          <div className="space-y-0.5">
                            <span className="text-slate-200">{tech.technique_name}</span>
                            {tech.how_used && (
                              <div className="text-[10px] text-slate-500 italic">{tech.how_used}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Extracted Relationships */}
                  {result.llm_analysis.relationships.length > 0 && (
                    <div className="p-3 rounded-lg bg-slate-900/80 border border-cyber-border text-xs font-mono space-y-1.5">
                      <div className="font-bold text-cyan-300 text-[11px]">🔗 LLM-Discovered Relationships</div>
                      {result.llm_analysis.relationships.map((rel: any, i: number) => (
                        <div key={i} className="p-2 rounded bg-slate-800/50 border border-slate-700/50 space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-cyan-300 font-bold">{rel.source}</span>
                            <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[10px]">
                              {rel.relationship}
                            </span>
                            <span className="text-amber-300 font-bold">{rel.target}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                              rel.confidence === 'high' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                              rel.confidence === 'medium' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30' :
                              'bg-red-500/20 text-red-300 border border-red-500/30'
                            }`}>
                              {rel.confidence}
                            </span>
                          </div>
                          {rel.evidence && (
                            <div className="text-[10px] text-slate-400 italic pl-2 border-l-2 border-slate-600">
                              {rel.evidence}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 4: Discovered Predictions */}
              {activeResultTab === 'predictions' && result.analytics_summary?.top_candidate_relationships && (
                <div className="max-h-72 overflow-y-auto pr-1 space-y-2">
                  {result.analytics_summary.top_candidate_relationships.map((cand: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-slate-900/80 border border-amber-500/30 text-xs font-mono space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-cyan-300 font-bold">{cand.source_name}</span>
                        <span className="text-amber-400 font-semibold flex items-center gap-1">
                          ➔ {Math.round(cand.relationship_score * 100)}% Match
                        </span>
                        <span className="text-purple-300 font-bold">{cand.target_name}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 flex justify-between">
                        <span>Classification: {cand.classification}</span>
                        <span>Feature Similarity: {Math.round(cand.feature_similarity * 100)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
