import { DownloadButton } from './DownloadButton';
// src/components/WorkspaceHistorySidebar.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { OrchestrationJob } from '../types';

interface WorkspaceHistorySidebarProps {
  onSelectJob: (job: OrchestrationJob) => void;
  selectedJobId?: string | null;
  refreshTrigger?: number;
}

export const WorkspaceHistorySidebar: React.FC<WorkspaceHistorySidebarProps> = ({
  onSelectJob,
  selectedJobId,
  refreshTrigger = 0,
}) => {
  const [jobs, setJobs] = useState<OrchestrationJob[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [clientFilter, setClientFilter] = useState<string>('ALL');
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  const fetchJobs = useCallback(async () => {
    setIsLoading(true);
    try {
      const list = await api.orchestrator.listJobs();
      setJobs(list);
    } catch (err) {
      console.error('Error fetching workspace jobs:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs, refreshTrigger]);

  const getClientBadgeColor = (code: string) => {
    const c = (code || '').toUpperCase();
    if (c.includes('BCP')) return 'bg-blue-600/20 text-blue-400 border-blue-500/30';
    if (c.includes('INTERBANK')) return 'bg-emerald-600/20 text-emerald-400 border-emerald-500/30';
    if (c.includes('BBVA')) return 'bg-indigo-600/20 text-indigo-400 border-indigo-500/30';
    if (c.includes('SCOTIABANK')) return 'bg-rose-600/20 text-rose-400 border-rose-500/30';
    return 'bg-purple-600/20 text-purple-400 border-purple-500/30';
  };

  const getStatusBadge = (status: string) => {
    const s = (status || '').toUpperCase();
    if (s.includes('VERIFIED') || s.includes('APPROVED') || s === 'COMPLETED') {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1 animate-pulse"></span>
          Generado
        </span>
      );
    }
    if (s.includes('REVIEW') || s.includes('WAITING') || s.includes('IN_PROGRESS') || s === 'RUNNING') {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1 animate-pulse"></span>
          {s === 'RUNNING' ? 'Procesando' : 'Revisión'}
        </span>
      );
    }
    if (s.includes('FAIL') || s.includes('REJECT')) {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mr-1"></span>
          Fallido
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-tcs-muted/20 text-tcs-muted border border-tcs-border">
        {status}
      </span>
    );
  };

  const formatJobDate = (dateStr?: string) => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 1) return 'Hace un momento';
      if (diffMins < 60) return `Hace ${diffMins} min`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `Hace ${diffHours} h`;
      return d.toLocaleDateString(undefined, { day: '2-digit', month: 'short' });
    } catch {
      return dateStr;
    }
  };

  const filteredJobs = jobs.filter((job) => {
    const clientCode = (job.client_id || (job as any).client_code || '').toLowerCase();
    const artifact = ((job as any).blueprint?.artifact_id || (job as any).artifact_id || '').toLowerCase();
    const req = (job.requirements || '').toLowerCase();
    const query = searchTerm.toLowerCase();

    const matchesSearch = !query || clientCode.includes(query) || artifact.includes(query) || req.includes(query);
    const matchesClient = clientFilter === 'ALL' || clientCode.toUpperCase() === clientFilter;

    return matchesSearch && matchesClient;
  });

  const uniqueClients = Array.from(
    new Set(jobs.map((j) => (j.client_id || (j as any).client_code || '').toUpperCase()).filter(Boolean))
  );

  return (
    <div className="flex flex-col border-t border-tcs-border/60 pt-4 mt-2">
      {/* Header with Title, Count, Refresh, and Collapse Toggle */}
      <div className="flex items-center justify-between mb-2 px-1">
        <div className="flex items-center space-x-2">
          <svg className="w-4 h-4 text-tcs-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <span className="text-[11px] font-bold uppercase tracking-wider text-tcs-light">
            Microservicios Generados
          </span>
          <span className="text-[10px] font-mono bg-tcs-card px-1.5 py-0.5 rounded-full border border-tcs-border text-tcs-muted">
            {jobs.length}
          </span>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={fetchJobs}
            title="Actualizar historial"
            className="p-1 rounded text-tcs-muted hover:text-white hover:bg-tcs-card transition-all"
          >
            <svg
              className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-tcs-cyan' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            title={isCollapsed ? 'Expandir registros' : 'Minimizar registros'}
            className="p-1 rounded text-tcs-muted hover:text-white hover:bg-tcs-card transition-all"
          >
            <svg
              className={`w-3.5 h-3.5 transform transition-transform ${isCollapsed ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <>
          {/* Search Box */}
          <div className="mb-2 px-1">
            <div className="relative">
              <input
                type="text"
                placeholder="Buscar en workspace..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-tcs-card/80 border border-tcs-border/80 rounded-md py-1.5 pl-7 pr-2 text-[11px] text-white placeholder-tcs-muted focus:outline-none focus:border-tcs-cyan"
              />
              <svg className="w-3.5 h-3.5 text-tcs-muted absolute left-2 top-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-2 top-2 text-tcs-muted hover:text-white"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Client Filter Tags (if more than 1 client) */}
          {uniqueClients.length > 1 && (
            <div className="flex items-center space-x-1 overflow-x-auto pb-1 mb-2 px-1 no-scrollbar text-[10px]">
              <button
                onClick={() => setClientFilter('ALL')}
                className={`px-2 py-0.5 rounded transition-all shrink-0 ${
                  clientFilter === 'ALL'
                    ? 'bg-tcs-blue text-white font-semibold'
                    : 'bg-tcs-card text-tcs-muted hover:text-white'
                }`}
              >
                Todos ({jobs.length})
              </button>
              {uniqueClients.map((c) => (
                <button
                  key={c}
                  onClick={() => setClientFilter(c)}
                  className={`px-2 py-0.5 rounded transition-all shrink-0 uppercase ${
                    clientFilter === c
                      ? 'bg-tcs-blue text-white font-semibold'
                      : 'bg-tcs-card text-tcs-muted hover:text-white'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          )}

          {/* Microservices List Container */}
          <div className="space-y-2 overflow-y-auto max-h-[420px] pr-1 custom-scrollbar">
            {isLoading && jobs.length === 0 ? (
              <div className="text-center py-6 text-tcs-muted text-xs flex flex-col items-center space-y-2">
                <div className="w-5 h-5 border-2 border-tcs-cyan border-t-transparent rounded-full animate-spin"></div>
                <span>Cargando registros...</span>
              </div>
            ) : filteredJobs.length === 0 ? (
              <div className="text-center py-6 px-3 bg-tcs-card/40 rounded-lg border border-dashed border-tcs-border text-xs text-tcs-muted">
                {searchTerm ? (
                  <span>No se encontraron microservicios con ese filtro.</span>
                ) : (
                  <div className="space-y-1">
                    <p className="font-semibold text-tcs-light">Sin microservicios generados</p>
                    <p className="text-[11px]">Genera tu primer servicio desde el Studio para verlo aquí.</p>
                  </div>
                )}
              </div>
            ) : (
              filteredJobs.map((job) => {
                const jobId = job.job_id || (job as any).id;
                const isSelected = selectedJobId === jobId;
                const clientCode = (job.client_id || (job as any).client_code || 'GEN').toUpperCase();
                const artifact =
                  (job as any).blueprint?.artifact_id ||
                  (job as any).artifact_id ||
                  `${clientCode.toLowerCase()}-microservice`;
                const filesCount = Array.isArray(job.files)
                  ? job.files.length
                  : Object.keys(job.files || {}).length;
                const dateText = formatJobDate(job.created_at);

                return (
                  <div
                    key={jobId}
                    className={`group relative p-2.5 rounded-lg border transition-all text-xs ${
                      isSelected
                        ? 'bg-tcs-card border-tcs-cyan/70 shadow-md shadow-tcs-cyan/10'
                        : 'bg-tcs-navy/60 hover:bg-tcs-card/90 border-tcs-border/80 hover:border-tcs-border'
                    }`}
                  >
                    {/* Header Row: Client & Status */}
                    <div className="flex items-center justify-between mb-1.5">
                      <span
                        className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase ${getClientBadgeColor(
                          clientCode
                        )}`}
                      >
                        {clientCode}
                      </span>
                      <div className="flex items-center space-x-1.5">
                        {getStatusBadge(job.status)}
                        {dateText && (
                          <span className="text-[10px] text-tcs-muted">{dateText}</span>
                        )}
                      </div>
                    </div>

                    {/* Artifact Title */}
                    <div
                      onClick={() => onSelectJob(job)}
                      className="font-mono font-semibold text-white truncate cursor-pointer hover:text-tcs-cyan transition-colors text-[11px]"
                      title={artifact}
                    >
                      {artifact}
                    </div>

                    {/* Snippet / Requirement overview */}
                    {job.requirements && (
                      <p className="text-[10px] text-tcs-muted line-clamp-1 mt-0.5 font-sans" title={job.requirements}>
                        {job.requirements}
                      </p>
                    )}

                    {job.error_message && <p role="alert" className="text-xs text-rose-300 mt-1">{job.error_message}</p>}
                    {/* Metadata Pill Row */}
                    <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-tcs-border/40 text-[10px] text-tcs-muted">
                      <div className="flex items-center space-x-2">
                        <span className="flex items-center space-x-1">
                          <svg className="w-3 h-3 text-tcs-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <span>{filesCount} archivos</span>
                        </span>
                        {((job as any).architecture_style || (job as any).blueprint?.architecture_style) && (
                          <span className="bg-tcs-dark/60 px-1 rounded text-[9px] text-tcs-cyan border border-tcs-border/50">
                            {(job as any).architecture_style || (job as any).blueprint?.architecture_style}
                          </span>
                        )}
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => onSelectJob(job)}
                          title="Cargar y ver código en Studio"
                          className="px-2 py-0.5 rounded bg-tcs-blue/20 hover:bg-tcs-blue text-tcs-cyan hover:text-white font-medium text-[10px] transition-all flex items-center space-x-1 border border-tcs-blue/40"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                          </svg>
                          <span>Studio</span>
                        </button>

                        <DownloadButton url={api.orchestrator.getJobDownloadUrl(jobId)} disabled={filesCount === 0}
                          title={filesCount === 0 ? "No hay archivos generados; revisa el error del trabajo" : "Descargar paquete .ZIP completo"}
                          className="p-1 rounded bg-tcs-card hover:bg-emerald-600/30 text-tcs-muted hover:text-emerald-400 border border-tcs-border hover:border-emerald-500/40 transition-all flex items-center justify-center"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                        </DownloadButton>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </>
      )}
    </div>
  );
};

