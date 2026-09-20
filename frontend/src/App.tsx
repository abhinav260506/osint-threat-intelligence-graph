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

  useEffect(() => {
    loadGraphData();
  }, []);

  const loadGraphData = async () => {
    try {
      const data = await api.getGraph();
      setGraphData(data);
    } catch (e) {
      console.error('Failed to load graph:', e);
    }
  };

  const handleSeed = async () => {
    setIsSeeding(true);
    try {
      await api.seedBenchmarks();
      await loadGraphData();
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
        onRefresh={loadGraphData}
        onSeed={handleSeed}
        isSeeding={isSeeding}
      />

      <main className="flex-1 w-full overflow-hidden">
        {activeTab === 'graph' && (
          <GraphView graphData={graphData} onRefresh={loadGraphData} />
        )}
        {activeTab === 'clusters' && <ClusterView />}
        {activeTab === 'prediction' && <LinkPredictionView />}
        {activeTab === 'iocs' && <IocSearch />}
        {activeTab === 'ingestion' && (
          <IngestionWorkbench
            onIngested={loadGraphData}
            onNavigateToGraph={() => {
              loadGraphData();
              setActiveTab('graph');
            }}
          />
        )}
      </main>
    </div>
  );
};

export default App;
