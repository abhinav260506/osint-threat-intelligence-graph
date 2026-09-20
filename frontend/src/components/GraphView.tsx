import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { GraphData, GraphNode, EntityLabel } from '../types';
import { api } from '../services/api';
import { 
  Filter, 
  Maximize2, 
  Route, 
  Info, 
  X, 
  ExternalLink, 
  Shield, 
  Activity,
  Layers,
  ZoomIn,
  ZoomOut,
  RotateCcw
} from 'lucide-react';

interface GraphViewProps {
  graphData: GraphData;
  onRefresh: () => void;
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

export const GraphView: React.FC<GraphViewProps> = ({ graphData, onRefresh }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [nodeNeighbors, setNodeNeighbors] = useState<any[]>([]);
  const [isLoadingNeighbors, setIsLoadingNeighbors] = useState(false);

  // Pathfinding state
  const [pathSource, setPathSource] = useState<string>('');
  const [pathTarget, setPathTarget] = useState<string>('');
  const [discoveredPaths, setDiscoveredPaths] = useState<string[][]>([]);

  // Filter state
  const [activeLayout, setActiveLayout] = useState<string>('cose');
  const [selectedTypes, setSelectedTypes] = useState<Record<string, boolean>>({
    ThreatActor: true,
    Campaign: true,
    Malware: true,
    Tool: true,
    Domain: true,
    IP: true,
    URL: true,
    Hash: true,
    CVE: true,
    AttackTechnique: true,
    Sector: true,
    Report: true,
  });

  // Initialize and update Cytoscape instance
  useEffect(() => {
    if (!containerRef.current) return;

    // Filter elements based on type selections
    const filteredNodes = graphData.nodes.filter(
      (n) => selectedTypes[n.data.label] !== false
    );
    const validNodeIds = new Set(filteredNodes.map((n) => n.data.id));
    const filteredEdges = graphData.edges.filter(
      (e) => validNodeIds.has(e.data.source) && validNodeIds.has(e.data.target)
    );

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...filteredNodes, ...filteredEdges],
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(name)',
            'color': '#f8fafc',
            'font-size': '10px',
            'font-family': 'Inter, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'background-color': (ele: any) => LABEL_COLORS[ele.data('label')] || '#64748b',
            'width': (ele: any) => {
              const lbl = ele.data('label');
              if (lbl === 'ThreatActor' || lbl === 'Campaign') return 32;
              if (lbl === 'Malware') return 26;
              return 20;
            },
            'height': (ele: any) => {
              const lbl = ele.data('label');
              if (lbl === 'ThreatActor' || lbl === 'Campaign') return 32;
              if (lbl === 'Malware') return 26;
              return 20;
            },
            'border-width': 2,
            'border-color': '#1e293b',
            'border-opacity': 0.8,
          } as any,
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#38bdf8',
            'border-width': 4,
          } as any,
        },
        {
          selector: 'edge',
          style: {
            'label': 'data(label)',
            'font-size': '8px',
            'color': '#64748b',
            'text-rotation': 'autorotate',
            'text-margin-y': -6,
            'width': 1.5,
            'line-color': '#334155',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.8,
            'opacity': 0.7,
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#38bdf8',
            'target-arrow-color': '#38bdf8',
            'width': 2.5,
            'opacity': 1.0,
          },
        },
        {
          selector: '.highlighted',
          style: {
            'background-color': '#38bdf8',
            'line-color': '#38bdf8',
            'target-arrow-color': '#38bdf8',
            'border-color': '#ffffff',
            'border-width': 3,
            'width': 3,
            'opacity': 1.0,
            'z-index': 999,
          },
        },
      ],
      layout: {
        name: activeLayout,
        animate: true,
        animationDuration: 500,
        padding: 50,
      } as any,
    });

    // Node click handler
    cy.on('tap', 'node', async (evt) => {
      const node = evt.target;
      const data = node.data();
      setSelectedNode(data);
      setIsLoadingNeighbors(true);
      try {
        const details = await api.getEntity(data.id);
        setNodeNeighbors(details.neighbors || []);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoadingNeighbors(false);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graphData, selectedTypes, activeLayout]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit(undefined, 40);

  const toggleType = (type: string) => {
    setSelectedTypes((prev) => ({ ...prev, [type]: !prev[type] }));
  };

  const handleFindPath = async () => {
    if (!pathSource || !pathTarget) return;
    try {
      const res = await api.findPath(pathSource, pathTarget);
      setDiscoveredPaths(res.paths || []);

      if (cyRef.current && res.paths && res.paths.length > 0) {
        cyRef.current.elements().removeClass('highlighted');
        const firstPath = res.paths[0];
        firstPath.forEach((id: string) => {
          cyRef.current?.$id(id).addClass('highlighted');
        });
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="relative w-full h-[calc(100vh-4.5rem)] flex overflow-hidden">
      {/* Cytoscape Canvas */}
      <div ref={containerRef} className="flex-1 w-full h-full bg-[#080c14]" />

      {/* Floating Control Toolbar */}
      <div className="absolute top-4 left-4 flex flex-col gap-2 z-10">
        {/* Layout Switcher */}
        <div className="cyber-glass p-2 rounded-xl border border-cyber-border flex items-center gap-1.5 shadow-xl">
          <Layers className="w-4 h-4 text-slate-400 ml-1" />
          {['cose', 'concentric', 'circle', 'breadthfirst'].map((layout) => (
            <button
              key={layout}
              onClick={() => setActiveLayout(layout)}
              className={`px-2.5 py-1 rounded-md text-xs font-mono capitalize transition-all ${
                activeLayout === layout
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              {layout}
            </button>
          ))}
        </div>

        {/* Zoom & Reset Controls */}
        <div className="cyber-glass p-1.5 rounded-xl border border-cyber-border flex items-center gap-1 w-fit shadow-xl">
          <button
            onClick={handleZoomIn}
            title="Zoom In"
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 rounded-lg"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            title="Zoom Out"
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 rounded-lg"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleFit}
            title="Fit to Screen"
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 rounded-lg"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Type Legend & Filter Overlay */}
      <div className="absolute bottom-4 left-4 cyber-glass p-3 rounded-xl border border-cyber-border shadow-2xl max-w-md z-10">
        <div className="flex items-center justify-between mb-2 pb-1 border-b border-cyber-border/60">
          <span className="text-xs font-semibold uppercase font-mono tracking-wider text-slate-300 flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-cyan-400" />
            Entity Filters
          </span>
          <span className="text-[10px] text-slate-400">Click to toggle</span>
        </div>
        <div className="grid grid-cols-3 gap-1.5">
          {Object.entries(LABEL_COLORS).map(([label, color]) => {
            const isEnabled = selectedTypes[label] !== false;
            return (
              <button
                key={label}
                onClick={() => toggleType(label)}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-mono transition-all border ${
                  isEnabled
                    ? 'bg-slate-800/70 border-slate-700 text-slate-200'
                    : 'opacity-40 border-transparent text-slate-500 line-through'
                }`}
              >
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: color }}
                />
                <span className="truncate">{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Entity Inspector Side Drawer */}
      {selectedNode && (
        <aside className="w-96 cyber-glass border-l border-cyber-border h-full overflow-y-auto p-5 z-20 flex flex-col justify-between shadow-2xl">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-cyber-border mb-4">
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: LABEL_COLORS[selectedNode.label] || '#64748b' }}
                />
                <span className="font-mono text-xs font-semibold uppercase text-slate-400">
                  {selectedNode.label}
                </span>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <h3 className="font-bold text-lg text-slate-100 mb-2">{selectedNode.name}</h3>

            {selectedNode.aliases && selectedNode.aliases.length > 0 && (
              <div className="mb-4">
                <span className="text-xs text-slate-400 font-mono block mb-1">Known Aliases:</span>
                <div className="flex flex-wrap gap-1">
                  {selectedNode.aliases.map((alias: string) => (
                    <span
                      key={alias}
                      className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20"
                    >
                      {alias}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {selectedNode.description && (
              <div className="mb-4 text-xs text-slate-300 bg-slate-900/60 p-3 rounded-lg border border-cyber-border">
                {selectedNode.description}
              </div>
            )}

            {/* Pathfinding Shortcuts */}
            <div className="mb-4 pt-3 border-t border-cyber-border/60">
              <span className="text-xs font-mono text-slate-400 block mb-2">Graph Pathfinding</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPathSource(selectedNode.id)}
                  className={`flex-1 py-1.5 px-2 rounded text-xs font-mono border transition-all ${
                    pathSource === selectedNode.id
                      ? 'bg-blue-600 border-blue-500 text-white'
                      : 'bg-slate-800/60 border-slate-700 text-slate-300 hover:bg-slate-700/60'
                  }`}
                >
                  Set Source
                </button>
                <button
                  onClick={() => setPathTarget(selectedNode.id)}
                  className={`flex-1 py-1.5 px-2 rounded text-xs font-mono border transition-all ${
                    pathTarget === selectedNode.id
                      ? 'bg-purple-600 border-purple-500 text-white'
                      : 'bg-slate-800/60 border-slate-700 text-slate-300 hover:bg-slate-700/60'
                  }`}
                >
                  Set Target
                </button>
              </div>
            </div>

            {/* Connected Relationships */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-semibold uppercase text-slate-400">
                  Connected Entities ({nodeNeighbors.length})
                </span>
                {isLoadingNeighbors && <span className="text-[10px] text-cyan-400 animate-pulse">Loading...</span>}
              </div>
              <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                {nodeNeighbors.map((n, idx) => {
                  const target = n.target_node;
                  const rel = n.relationship;
                  return (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-slate-900/70 border border-cyber-border hover:border-slate-700 transition-all text-xs"
                    >
                      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1">
                        <span className="text-cyan-400">{rel.rel_type}</span>
                        <span>Conf: {Math.round(rel.confidence * 100)}%</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: LABEL_COLORS[target.label] || '#64748b' }}
                        />
                        <span className="font-semibold text-slate-200 truncate">{target.name}</span>
                        <span className="text-[10px] font-mono text-slate-500 ml-auto">
                          {target.label}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-cyber-border text-[10px] font-mono text-slate-500 break-all">
            STIX ID: {selectedNode.id}
          </div>
        </aside>
      )}

      {/* Path Discovery Modal/Drawer */}
      {pathSource && pathTarget && (
        <div className="absolute top-4 right-4 cyber-glass p-4 rounded-xl border border-cyber-border shadow-2xl w-96 z-10">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-cyber-border">
            <span className="text-xs font-mono font-semibold uppercase text-cyan-400 flex items-center gap-1.5">
              <Route className="w-4 h-4" />
              Path Investigation
            </span>
            <button
              onClick={() => {
                setPathSource('');
                setPathTarget('');
                setDiscoveredPaths([]);
                cyRef.current?.elements().removeClass('highlighted');
              }}
              className="text-slate-400 hover:text-slate-200"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-2 text-xs font-mono mb-3">
            <div className="truncate text-slate-300">
              <span className="text-blue-400">Src:</span> {pathSource}
            </div>
            <div className="truncate text-slate-300">
              <span className="text-purple-400">Tgt:</span> {pathTarget}
            </div>
          </div>

          <button
            onClick={handleFindPath}
            className="w-full py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white text-xs font-semibold rounded-lg shadow-lg hover:from-blue-500 hover:to-cyan-500 transition-all mb-3"
          >
            Trace Shortest Path
          </button>

          {discoveredPaths.length > 0 && (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              <span className="text-[11px] font-mono text-slate-400">Paths Found ({discoveredPaths.length}):</span>
              {discoveredPaths.map((path, idx) => (
                <div
                  key={idx}
                  className="p-2 rounded bg-slate-900/80 border border-cyber-border text-[10px] font-mono text-slate-300"
                >
                  {path.join(' ➔ ')}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
