// src/App.tsx
import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { LoginModal } from './components/LoginModal';
import { StudioPanel } from './components/StudioPanel';
import { AdminPanel } from './components/AdminPanel';
import { ConsumptionPanel } from './components/ConsumptionPanel';
import { WorkspaceHistorySidebar } from './components/WorkspaceHistorySidebar';
import { OrchestrationJob } from './types';

export const App: React.FC = () => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const [currentTab, setCurrentTab] = useState<'studio' | 'consumption' | 'admin'>('studio');
  const [loadedJob, setLoadedJob] = useState<OrchestrationJob | null>(null);
  const [historyRefreshTrigger, setHistoryRefreshTrigger] = useState<number>(0);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-tcs-dark flex flex-col items-center justify-center text-white space-y-4">
        <div className="w-12 h-12 rounded-lg bg-gradient-to-tr from-tcs-blue to-tcs-cyan flex items-center justify-center shadow-lg animate-pulse">
          <span className="text-white font-extrabold text-xl">TCS</span>
        </div>
        <div className="text-xs text-tcs-muted font-mono tracking-wider">
          Iniciando TCS Intelligent Microservice Factory...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-tcs-dark relative overflow-hidden flex flex-col items-center justify-center">
        {/* Ambient background decoration */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-tcs-blue/10 rounded-full blur-3xl pointer-events-none"></div>
        <LoginModal />
      </div>
    );
  }

  // Developer can access studio & consumption, Admin can access all three
  const activeTab = (currentTab === 'admin' && user?.role !== 'ADMIN') ? 'studio' : currentTab;

  return (
    <div className="min-h-screen bg-tcs-dark flex flex-col text-tcs-light">
      <Navbar
        currentTab={activeTab}
        setCurrentTab={setCurrentTab}
      />

      <div className="flex-1 max-w-7xl w-full mx-auto flex flex-col md:flex-row">
        {/* Left Sidebar Navigation & Workspace History */}
        <aside className="w-full md:w-80 border-b md:border-b-0 md:border-r border-tcs-border p-4 bg-tcs-navy/40 shrink-0 flex flex-col">
          <div className="text-[10px] font-bold uppercase tracking-wider text-tcs-muted mb-3 px-2">
            Módulos de Fábrica
          </div>
          <nav className="space-y-1">
            <button
              onClick={() => setCurrentTab('studio')}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'studio'
                  ? 'bg-tcs-blue text-white shadow-md'
                  : 'text-tcs-muted hover:text-white hover:bg-tcs-card'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              <span>Workspace Studio</span>
            </button>

            <button
              onClick={() => setCurrentTab('consumption')}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'consumption'
                  ? 'bg-tcs-blue text-white shadow-md'
                  : 'text-tcs-muted hover:text-white hover:bg-tcs-card'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Consumo & Tokens</span>
            </button>

            {user?.role === 'ADMIN' && (
              <button
                onClick={() => setCurrentTab('admin')}
                className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'admin'
                    ? 'bg-tcs-blue text-white shadow-md'
                    : 'text-tcs-muted hover:text-white hover:bg-tcs-card'
                }`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
                <span>Gobernanza Admin</span>
              </button>
            )}
          </nav>

          {/* Módulo de Registros del Workspace y Microservicios Generados */}
          <WorkspaceHistorySidebar
            onSelectJob={(job) => {
              setLoadedJob(job);
              setCurrentTab('studio');
            }}
            selectedJobId={loadedJob?.job_id || (loadedJob as any)?.id}
            refreshTrigger={historyRefreshTrigger}
          />
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-6 overflow-x-hidden min-w-0">
          {activeTab === 'studio' && (
            <StudioPanel
              loadedJob={loadedJob}
              onJobCreated={() => setHistoryRefreshTrigger((prev) => prev + 1)}
            />
          )}
          {activeTab === 'consumption' && <ConsumptionPanel />}
          {activeTab === 'admin' && <AdminPanel />}
        </main>
      </div>

      <footer className="border-t border-tcs-border/60 bg-tcs-navy py-4 text-center text-xs text-tcs-muted">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Tata Consultancy Services © 2026. All Rights Reserved.</span>
          <span className="font-mono text-[11px]">
            TCS Intelligent Microservice Factory • Quarkus Multi-Agent Engine
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
