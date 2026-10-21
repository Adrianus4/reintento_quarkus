// src/components/Navbar.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

interface NavbarProps {
  currentTab: 'studio' | 'consumption' | 'admin';
  setCurrentTab: (tab: 'studio' | 'consumption' | 'admin') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab }) => {
  const { user, logout } = useAuth();
  const [health, setHealth] = useState<{
    auth: boolean;
    governance: boolean;
    orchestrator: boolean;
    verifier: boolean;
  }>({ auth: false, governance: false, orchestrator: false, verifier: false });

  useEffect(() => {
    const checkMicroservicesHealth = async () => {
      const [hAuth, hGov, hOrch, hVer] = await Promise.allSettled([
        api.auth.checkHealth(),
        api.governance.checkHealth(),
        api.orchestrator.checkHealth(),
        api.verifier.checkHealth(),
      ]);

      setHealth({
        auth: hAuth.status === 'fulfilled',
        governance: hGov.status === 'fulfilled',
        orchestrator: hOrch.status === 'fulfilled',
        verifier: hVer.status === 'fulfilled',
      });
    };

    checkMicroservicesHealth();
    const interval = setInterval(checkMicroservicesHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-tcs-navy border-b border-tcs-border px-6 py-3 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand & Title */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-9 h-9 rounded bg-gradient-to-br from-tcs-blue to-tcs-cyan flex items-center justify-center shadow-lg shadow-tcs-blue/20">
              <span className="text-white font-extrabold text-sm tracking-wider">TCS</span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-white font-bold tracking-tight text-base">
                  Intelligent Microservice Factory
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-tcs-surface border border-tcs-border text-tcs-cyan font-mono">
                  v1.2.0
                </span>
              </div>
              <p className="text-xs text-tcs-muted">Autonomous Quarkus Engineering Studio</p>
            </div>
          </div>

          {/* Microservices Cluster Health Pills */}
          <div className="hidden lg:flex items-center space-x-2 ml-6 pl-4 border-l border-tcs-border text-[11px] font-mono">
            <span className="text-tcs-muted">Suite:</span>
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded ${health.auth ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800' : 'bg-rose-950/60 text-rose-400 border border-rose-800'}`}>
              :8001
            </span>
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded ${health.governance ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800' : 'bg-rose-950/60 text-rose-400 border border-rose-800'}`}>
              :8002
            </span>
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded ${health.orchestrator ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800' : 'bg-rose-950/60 text-rose-400 border border-rose-800'}`}>
              :8003
            </span>
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded ${health.verifier ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800' : 'bg-rose-950/60 text-rose-400 border border-rose-800'}`}>
              :8004
            </span>
          </div>
        </div>

        {/* Navigation Tabs & User Bar */}
        <div className="flex items-center space-x-4">
          <div className="bg-tcs-dark p-1 rounded-lg border border-tcs-border flex space-x-1">
            <button
              onClick={() => setCurrentTab('studio')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                currentTab === 'studio'
                  ? 'bg-tcs-blue text-white shadow-sm'
                  : 'text-tcs-muted hover:text-white'
              }`}
            >
              Workspace Studio
            </button>
            <button
              onClick={() => setCurrentTab('consumption')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center space-x-1.5 ${
                currentTab === 'consumption'
                  ? 'bg-tcs-blue text-white shadow-sm'
                  : 'text-tcs-muted hover:text-white'
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-tcs-cyan"></span>
              <span>Consumo</span>
            </button>
            {user?.role === 'ADMIN' && (
              <button
                onClick={() => setCurrentTab('admin')}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  currentTab === 'admin'
                    ? 'bg-tcs-blue text-white shadow-sm'
                    : 'text-tcs-muted hover:text-white'
                }`}
              >
                Admin Governance
              </button>
            )}
          </div>

          {/* User profile badge & logout */}
          {user && (
            <div className="flex items-center space-x-3 pl-3 border-l border-tcs-border">
              <div className="text-right">
                <div className="flex items-center justify-end space-x-2">
                  <span className="text-xs font-semibold text-white">{user.full_name}</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                      user.role === 'ADMIN'
                        ? 'bg-purple-900/40 text-purple-300 border border-purple-700/50'
                        : 'bg-cyan-900/40 text-cyan-300 border border-cyan-700/50'
                    }`}
                  >
                    {user.role}
                  </span>
                </div>
                <div className="text-[11px] text-tcs-muted">{user.email}</div>
              </div>

              <button
                onClick={logout}
                title="Cerrar Sesión"
                className="p-1.5 rounded-md text-tcs-muted hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

