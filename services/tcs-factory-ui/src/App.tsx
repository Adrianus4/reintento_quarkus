// src/App.tsx
import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { LoginModal } from './components/LoginModal';
import { StudioPanel } from './components/StudioPanel';
import { AdminPanel } from './components/AdminPanel';

export const App: React.FC = () => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const [currentTab, setCurrentTab] = useState<'studio' | 'admin'>('studio');

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

  // Fallback: If user is developer, always lock to studio
  const activeTab = user?.role === 'ADMIN' ? currentTab : 'studio';

  return (
    <div className="min-h-screen bg-tcs-dark flex flex-col text-tcs-light">
      <Navbar
        currentTab={activeTab}
        setCurrentTab={setCurrentTab}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {activeTab === 'studio' ? <StudioPanel /> : <AdminPanel />}
      </main>

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

