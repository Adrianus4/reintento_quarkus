// src/components/ConsumptionPanel.tsx
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ConsumptionSummary, ConsumptionRecord } from '../types';

export const ConsumptionPanel: React.FC = () => {
  const [telemetry, setTelemetry] = useState<ConsumptionSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProviderFilter, setSelectedProviderFilter] = useState<string>('ALL');

  const fetchTelemetry = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.orchestrator.getConsumptionTelemetry();
      setTelemetry(data);
    } catch (err: any) {
      setError(err.message || 'Error al cargar telemetría de consumo');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, []);

  const rawRecords: ConsumptionRecord[] = telemetry?.recent_records || telemetry?.records || [];
  const filteredRecords = rawRecords.filter((rec: ConsumptionRecord) => {
    if (selectedProviderFilter === 'ALL') return true;
    return (rec.provider || '').toUpperCase() === selectedProviderFilter.toUpperCase();
  });

  const totalTokens = rawRecords.reduce((acc: number, r: ConsumptionRecord) => acc + (r.total_tokens || 0), 0);
  const promptTokens = rawRecords.reduce((acc: number, r: ConsumptionRecord) => acc + (r.prompt_tokens || 0), 0);
  const completionTokens = rawRecords.reduce((acc: number, r: ConsumptionRecord) => acc + (r.completion_tokens || 0), 0);
  const totalCost = rawRecords.reduce((acc: number, r: ConsumptionRecord) => acc + (r.cost_usd || 0), 0);
  const totalJobs = rawRecords.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-tcs-border gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-tcs-cyan animate-pulse"></span>
            <h2 className="text-xl font-bold text-white tracking-wide">Telemetría de Consumo de Tokens</h2>
          </div>
          <p className="text-xs text-tcs-muted mt-1">
            Registro en tiempo real de tokens consumidos por proyecto, costos y distribución analítica por proveedor LLM.
          </p>
        </div>
        <button
          onClick={fetchTelemetry}
          disabled={loading}
          className="px-3.5 py-1.5 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border rounded-lg text-xs font-semibold text-tcs-cyan transition-colors disabled:opacity-50 flex items-center space-x-1.5"
        >
          <span>{loading ? 'Sincronizando...' : 'Actualizar Registros'}</span>
        </button>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/40 border border-rose-800 rounded-lg text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Global Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-tcs-card border border-tcs-border rounded-xl p-4 shadow">
          <div className="text-[11px] font-bold text-tcs-muted uppercase tracking-wider">Total Tokens Consumidos</div>
          <div className="text-2xl font-black text-white mt-2 font-mono">
            {totalTokens.toLocaleString()}
          </div>
          <div className="text-[10px] text-tcs-muted mt-1">Acumulado en todos los proyectos</div>
        </div>

        <div className="bg-tcs-card border border-tcs-border rounded-xl p-4 shadow">
          <div className="text-[11px] font-bold text-tcs-muted uppercase tracking-wider">Tokens Entrada (Prompt)</div>
          <div className="text-2xl font-black text-tcs-cyan mt-2 font-mono">
            {promptTokens.toLocaleString()}
          </div>
          <div className="text-[10px] text-tcs-muted mt-1">Contexto & directivas de gobierno</div>
        </div>

        <div className="bg-tcs-card border border-tcs-border rounded-xl p-4 shadow">
          <div className="text-[11px] font-bold text-tcs-muted uppercase tracking-wider">Tokens Generados (Output)</div>
          <div className="text-2xl font-black text-emerald-400 mt-2 font-mono">
            {completionTokens.toLocaleString()}
          </div>
          <div className="text-[10px] text-tcs-muted mt-1">Microservicios y artefactos Quarkus</div>
        </div>

        <div className="bg-tcs-card border border-tcs-border rounded-xl p-4 shadow">
          <div className="text-[11px] font-bold text-tcs-muted uppercase tracking-wider">Costo Estimado USD</div>
          <div className="text-2xl font-black text-amber-400 mt-2 font-mono">
            ${totalCost.toFixed(4)}
          </div>
          <div className="text-[10px] text-tcs-muted mt-1">
            {totalJobs} trabajos procesados
          </div>
        </div>
      </div>

      {/* Telemetry Breakdown by Model Provider */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-white flex items-center space-x-2">
          <span>Consumo por Proveedor de Modelo</span>
          <span className="text-[10px] font-mono px-2 py-0.5 bg-tcs-surface border border-tcs-border rounded text-tcs-cyan">
            Multi-Provider Gateway
          </span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {['GEMINI', 'OPENAI', 'ANTHROPIC', 'DEEPSEEK', 'GROK', 'GROQ', 'MOCK'].map((prov) => {
            const data = telemetry?.by_provider?.[prov] || telemetry?.by_provider?.[prov.toLowerCase()];
            const tokens = data?.total_tokens || 0;
            const prompt = data?.prompt_tokens || 0;
            const completion = data?.completion_tokens || 0;
            const cost = data?.total_cost_usd || data?.cost_usd || 0;
            const count = data?.job_count || data?.jobs_count || 0;

            const providerColor =
              prov === 'GEMINI'
                ? 'border-blue-500/40 bg-blue-950/10'
                : prov === 'DEEPSEEK'
                ? 'border-indigo-500/40 bg-indigo-950/10'
                : prov === 'GROK'
                ? 'border-purple-500/40 bg-purple-950/10'
                : prov === 'GROQ'
                ? 'border-emerald-500/40 bg-emerald-950/10'
                : prov === 'MOCK'
                ? 'border-amber-500/40 bg-amber-950/10'
                : 'border-slate-600/40 bg-slate-900/20';

            return (
              <div key={prov} className={`border rounded-xl p-4 shadow ${providerColor}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white tracking-wider">{prov}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-tcs-surface border border-tcs-border text-tcs-muted">
                    {count} jobs
                  </span>
                </div>

                <div className="mt-3">
                  <div className="text-lg font-bold text-white font-mono">{tokens.toLocaleString()}</div>
                  <div className="text-[10px] text-tcs-muted">tokens totales</div>
                </div>

                <div className="mt-3 pt-3 border-t border-tcs-border/50 grid grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <span className="text-tcs-muted block">Prompt:</span>
                    <span className="font-mono text-tcs-cyan">{prompt.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-tcs-muted block">Output:</span>
                    <span className="font-mono text-emerald-400">{completion.toLocaleString()}</span>
                  </div>
                </div>

                <div className="mt-2 text-[11px] font-mono text-amber-300">
                  Costo: ${cost.toFixed(4)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Projects / Jobs Consumption Table */}
      <div className="bg-tcs-card border border-tcs-border rounded-xl p-5 shadow space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-white">Registro Detallado por Proyecto & Microservicio</h3>
            <p className="text-xs text-tcs-muted">Historial de tokens consumidos en cada orquestación Quarkus.</p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-tcs-muted">Filtrar Proveedor:</span>
            <select
              value={selectedProviderFilter}
              onChange={(e) => setSelectedProviderFilter(e.target.value)}
              className="px-2.5 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue"
            >
              <option value="ALL">Todos los Proveedores</option>
              <option value="GEMINI">Gemini</option>
              <option value="OPENAI">OpenAI</option>
              <option value="ANTHROPIC">Anthropic</option>
              <option value="DEEPSEEK">DeepSeek</option>
              <option value="GROK">Grok</option>
              <option value="GROQ">Groq</option>
              <option value="MOCK">Mock</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-tcs-dark/70 text-tcs-muted border-b border-tcs-border font-mono text-[11px]">
              <tr>
                <th className="py-2.5 px-3">Job ID</th>
                <th className="py-2.5 px-3">Cliente / Proyecto</th>
                <th className="py-2.5 px-3">Proveedor / Modelo</th>
                <th className="py-2.5 px-3">Estado</th>
                <th className="py-2.5 px-3 text-right">Tokens Prompt</th>
                <th className="py-2.5 px-3 text-right">Tokens Output</th>
                <th className="py-2.5 px-3 text-right">Total Tokens</th>
                <th className="py-2.5 px-3 text-right">Costo USD</th>
                <th className="py-2.5 px-3">Fecha</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-tcs-border font-mono text-[11px]">
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-tcs-muted font-sans">
                    No hay registros de consumo registrados para este criterio.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((rec: ConsumptionRecord) => (
                  <tr key={rec.job_id} className="hover:bg-tcs-surface/40 transition-colors">
                    <td className="py-2 px-3 text-white font-bold">{rec.job_id}</td>
                    <td className="py-2 px-3">
                      <span className="px-2 py-0.5 rounded bg-tcs-surface border border-tcs-border text-white uppercase text-[10px] font-bold">
                        {rec.client_code}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <span className="text-white font-semibold">{rec.provider}</span>
                      <span className="text-tcs-muted text-[10px] ml-1">({rec.model || 'default'})</span>
                    </td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          rec.status === 'COMPLETED'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : rec.status === 'FAILED'
                            ? 'bg-rose-950 text-rose-400 border border-rose-800'
                            : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}
                      >
                        {rec.status}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right text-tcs-cyan">
                      {(rec.prompt_tokens || 0).toLocaleString()}
                    </td>
                    <td className="py-2 px-3 text-right text-emerald-400">
                      {(rec.completion_tokens || 0).toLocaleString()}
                    </td>
                    <td className="py-2 px-3 text-right text-white font-bold">
                      {(rec.total_tokens || 0).toLocaleString()}
                    </td>
                    <td className="py-2 px-3 text-right text-amber-300">
                      ${(rec.cost_usd || 0).toFixed(4)}
                    </td>
                    <td className="py-2 px-3 text-tcs-muted text-[10px] font-sans">
                      {rec.created_at ? new Date(rec.created_at).toLocaleString() : 'Reciente'}
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

