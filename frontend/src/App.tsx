import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { GraphView } from './components/GraphView';
import { ClusterView } from './components/ClusterView';
import { LinkPredictionView } from './components/LinkPredictionView';
import { IocSearch } from './components/IocSearch';
import { IngestionWorkbench } from './components/IngestionWorkbench';
import { api } from './services/api';
import { GraphData } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('graph');
  const [graphData, setGraphData] = useState<GraphData>({
    nodes: [],
    edges: [],
    stats: { total_nodes: 0, total_edges: 0 },
  });
  const [isSeeding, setIsSeeding] = useState<boolean>(false);
  const [dataVersion, setDataVersion] = useState<number>(0);
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null);

  const loadGraphData = async () => {
    try {
      const data = await api.getGraph();
      setGraphData(data);
    } catch (e) {
      console.error('Failed to load graph:', e);
    }
  };

  const refreshAll = async () => {
    await loadGraphData();
    setDataVersion((v) => v + 1);
  };

  const handleNavigateToGraph = (nodeId?: string) => {
    setFocusNodeId(nodeId || null);
    setActiveTab('graph');
    refreshAll();
  };

  useEffect(() => {
    loadGraphData();
  }, []);

  const handleSeed = async () => {
    setIsSeeding(true);
    try {
      await api.seedBenchmarks();
      await refreshAll();
    } catch (e) {
      console.error('Failed to seed:', e);
    } finally {
      setIsSeeding(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0f19] text-slate-100 selection:bg-blue-500 selection:text-white">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={graphData.stats}
        onRefresh={refreshAll}
        onSeed={handleSeed}
        isSeeding={isSeeding}
      />

      <main className="flex-1 w-full overflow-hidden">
        {activeTab === 'graph' && (
          <GraphView graphData={graphData} onRefresh={refreshAll} focusNodeId={focusNodeId} />
        )}
        {activeTab === 'clusters' && (
          <ClusterView dataVersion={dataVersion} onRefresh={refreshAll} />
        )}
        {activeTab === 'prediction' && (
          <LinkPredictionView dataVersion={dataVersion} onRefresh={refreshAll} />
        )}
        {activeTab === 'iocs' && (
          <IocSearch dataVersion={dataVersion} onRefresh={refreshAll} />
        )}
        {activeTab === 'ingestion' && (
          <IngestionWorkbench
            onIngested={refreshAll}
            onNavigateToGraph={handleNavigateToGraph}
          />
        )}
      </main>
    </div>
  );
};

export default App;
