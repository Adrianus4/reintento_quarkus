// src/components/StudioPanel.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { CodeViewer } from './CodeViewer';
import { VerifierModal } from './VerifierModal';
import { ClientProfile, OpenApiSpecSummary, OrchestrationJob, GeneratedFile } from '../types';

export const StudioPanel: React.FC = () => {
  const { user } = useAuth();
  const [clients, setClients] = useState<ClientProfile[]>([]);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [contracts, setContracts] = useState<OpenApiSpecSummary[]>([]);
  const [selectedContractId, setSelectedContractId] = useState<string>('');
  const [archStyle, setArchStyle] = useState<string>('HEXAGONAL');
  const [requirementPrompt, setRequirementPrompt] = useState<string>(
    'Implementar microservicio de transferencias inmediatas interbancarias con validación de saldo, registro de auditoría y soporte de idempotencia.'
  );

  const [currentJob, setCurrentJob] = useState<OrchestrationJob | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isSavingFiles, setIsSavingFiles] = useState<boolean>(false);
  const [isVerifierOpen, setIsVerifierOpen] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load clients accessible to current user
  useEffect(() => {
    const fetchAuthorizedClients = async () => {
      try {
        const allClients = await api.governance.listClients(true);
        if (user?.role === 'ADMIN') {
          setClients(allClients);
          if (allClients.length > 0) {
            setSelectedClient((prev) => prev || allClients[0].code || (allClients[0] as any).client_id);
          }
        } else {
          // DEVELOPER: filter strictly by user.assigned_clients (Principio XV)
          const assigned = (user?.assigned_clients || []).map((c) => c.toLowerCase());
          const filtered = allClients.filter((c: any) => {
            const code = (c.code || c.client_id || '').toLowerCase();
            return assigned.includes(code) || assigned.includes('*');
          });
          setClients(filtered);
          if (filtered.length > 0) {
            setSelectedClient((prev) => prev || filtered[0].code || (filtered[0] as any).client_id);
          }
        }
      } catch (err: any) {
        console.error('Failed to load clients', err);
      }
    };

    fetchAuthorizedClients();
  }, [user]);

  // Load OpenAPI contracts for the selected client
  useEffect(() => {
    const fetchContracts = async () => {
      if (!selectedClient) {
        setContracts([]);
        return;
      }
      try {
        const cts = await api.governance.listContracts(selectedClient);
        setContracts(cts);
        if (cts.length > 0) {
          setSelectedContractId(cts[0].id);
        } else {
          setSelectedContractId('');
        }
      } catch (err) {
        console.warn('Could not load contracts for client', err);
        setContracts([]);
      }
    };

    fetchContracts();
  }, [selectedClient]);

  // Poll for job updates if running in background
  useEffect(() => {
    let timer: any = null;
    if (currentJob && (currentJob.status === 'RUNNING' || currentJob.status === 'PENDING' || currentJob.status === 'IN_PROGRESS')) {
      timer = setInterval(async () => {
        try {
          const updated = await api.orchestrator.getJob(currentJob.job_id || (currentJob as any).id);
          setCurrentJob(updated);
          if (
            updated.status === 'COMPLETED' ||
            updated.status === 'AWAITING_REVIEW' ||
            updated.status === 'FAILED'
          ) {
            setIsGenerating(false);
          }
        } catch (err) {
          console.error('Polling error', err);
        }
      }, 1500);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [currentJob]);

  const handleStartGeneration = async () => {
    if (!selectedClient) {
      setError('Seleccione una cuenta corporativa de cliente (ej. bcp)');
      return;
    }
    if (!requirementPrompt.trim()) {
      setError('Ingrese una especificación o requerimiento para el microservicio');
      return;
    }

    setError(null);
    setIsGenerating(true);
    setCurrentJob(null);

    try {
      const job = await api.orchestrator.createJob({
        client_code: selectedClient,
        raw_requirement: requirementPrompt,
        requirements: requirementPrompt,
        architecture_style: archStyle,
        contract_id: selectedContractId || undefined,
      });

      setCurrentJob(job);
      setIsGenerating(false);
    } catch (err: any) {
      setError(err.message || 'Error al iniciar la generación multi-agente');
      setIsGenerating(false);
    }
  };

  const handleSaveFiles = async (updatedFiles: GeneratedFile[]) => {
    if (!currentJob) return;
    setIsSavingFiles(true);
    try {
      const jobId = currentJob.job_id || (currentJob as any).id;
      const res = await api.orchestrator.patchJobFiles(jobId, updatedFiles);
      setCurrentJob(res);
    } catch (err: any) {
      setError('Error al guardar cambios de código (HITL): ' + err.message);
    } finally {
      setIsSavingFiles(false);
    }
  };

  const stages = [
    { key: 'INGESTION', label: '1. Ingestión Directivas' },
    { key: 'ARCHITECTURE', label: '2. Arquitectura & Stack' },
    { key: 'GENERATION', label: '3. Generación Quarkus' },
    { key: 'COMPILATION_TEST', label: '4. Verificación y Pruebas' },
    { key: 'COMPLETED', label: '5. Completado' },
  ];

  const currentStageIndex = currentJob
    ? currentJob.status === 'COMPLETED' || currentJob.status === 'AWAITING_REVIEW'
      ? 5
      : stages.findIndex((s) => s.key === currentJob.current_stage)
    : -1;

  return (
    <div className="space-y-6">
      {/* Configuration & Requirements Card */}
      <div className="bg-tcs-card border border-tcs-border rounded-xl p-5 shadow">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-tcs-cyan"></span>
              <span>Workspace Studio: Generador Multi-Agente de Microservicios</span>
            </h2>
            <p className="text-xs text-tcs-muted">
              Orquestación autónoma LangGraph con gobernanza técnica y calidad verificable en Quarkus
            </p>
          </div>

          {currentJob && (
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="text-tcs-muted">Job ID: {currentJob.job_id || (currentJob as any).id}</span>
              <span
                className={`px-2 py-0.5 rounded font-bold ${
                  currentJob.status === 'COMPLETED'
                    ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-700'
                    : currentJob.status === 'FAILED'
                    ? 'bg-rose-950/80 text-rose-300 border border-rose-700'
                    : 'bg-amber-950/80 text-amber-300 border border-amber-700 animate-pulse'
                }`}
              >
                {currentJob.status}
              </span>
            </div>
          )}
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
            {error}
          </div>
        )}

        {currentJob?.error_message && currentJob.status === 'FAILED' && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 text-xs font-mono">
            <strong>Fallo en la generación:</strong> {currentJob.error_message}
          </div>
        )}

        {clients.length === 0 && (
          <div className="mb-4 p-3 rounded-lg bg-amber-950/60 border border-amber-800 text-amber-300 text-xs">
            ⚠️ No se encontraron clientes asignados. Si eres Administrador, ingresa a la pestaña <strong>Admin Governance</strong> para registrar cuentas de clientes. Si eres Desarrollador, solicita a un Administrador que te asigne la cuenta <code>bcp</code>.
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Client Selector */}
          <div>
            <label className="block text-xs font-medium text-tcs-muted mb-1">
              Cuenta de Cliente ({user?.role === 'DEVELOPER' ? 'Asignada' : 'Global'})
            </label>
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              disabled={isGenerating}
              className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
            >
              {clients.map((c: any) => (
                <option key={c.code || c.client_id} value={c.code || c.client_id}>
                  {c.name} ({c.code || c.client_id})
                </option>
              ))}
              {clients.length === 0 && <option value="">No tiene clientes asignados</option>}
            </select>
          </div>

          {/* Architecture Selector */}
          <div>
            <label className="block text-xs font-medium text-tcs-muted mb-1">
              Patrón Arquitectónico (Principio II)
            </label>
            <select
              value={archStyle}
              onChange={(e) => setArchStyle(e.target.value)}
              disabled={isGenerating}
              className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue"
            >
              <option value="HEXAGONAL">Arquitectura Hexagonal (Ports & Adapters)</option>
              <option value="LAYERED">Arquitectura por Capas (Clean Layered)</option>
              <option value="EVENT_DRIVEN">Event-Driven (Reactivo / SmallRye Messaging)</option>
              <option value="BFF">Backend-for-Frontend (BFF Agregador)</option>
              <option value="GRPC">Microservicio gRPC de Alto Rendimiento</option>
            </select>
          </div>

          {/* OpenAPI Contract Selector */}
          <div>
            <label className="block text-xs font-medium text-tcs-muted mb-1">
              Contrato OpenAPI 3.x (Opcional)
            </label>
            <select
              value={selectedContractId}
              onChange={(e) => setSelectedContractId(e.target.value)}
              disabled={isGenerating}
              className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
            >
              <option value="">Ninguno (Generación por Requerimientos)</option>
              {contracts.map((c: any) => (
                <option key={c.id} value={c.id}>
                  {c.title} (v{c.version})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Requirements Prompt */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-tcs-muted mb-1">
            Instrucciones y Requerimientos Funcionales
          </label>
          <textarea
            rows={3}
            value={requirementPrompt}
            onChange={(e) => setRequirementPrompt(e.target.value)}
            disabled={isGenerating}
            placeholder="Describa el dominio, endpoints, lógica de negocio y reglas que debe contener el microservicio..."
            className="w-full p-3 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:outline-none focus:border-tcs-blue leading-relaxed font-mono"
          />
        </div>

        {/* Action Button & LangGraph Progression Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2 border-t border-tcs-border/60">
          <button
            onClick={handleStartGeneration}
            disabled={isGenerating || clients.length === 0}
            className="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-tcs-blue to-tcs-cyan hover:from-tcs-accent hover:to-tcs-blue text-white font-bold text-xs rounded-lg shadow-lg transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                <span>Orquestando Pipeline LangGraph...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Generar Microservicio Quarkus</span>
              </>
            )}
          </button>

          {/* LangGraph Pipeline Stages */}
          <div className="flex items-center space-x-1 overflow-x-auto w-full sm:w-auto text-[11px] font-mono">
            {stages.map((stage, idx) => {
              const isPast = currentStageIndex > idx;
              const isCurrent = currentStageIndex === idx;
              return (
                <div
                  key={stage.key}
                  className={`px-2 py-1 rounded border flex items-center space-x-1 whitespace-nowrap ${
                    isCurrent
                      ? 'bg-tcs-blue/30 border-tcs-cyan text-tcs-cyan font-bold shadow'
                      : isPast
                      ? 'bg-emerald-950/60 border-emerald-800 text-emerald-400'
                      : 'bg-tcs-dark border-tcs-border text-tcs-muted'
                  }`}
                >
                  <span>{isPast ? '✓' : isCurrent ? '●' : '○'}</span>
                  <span>{stage.label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Telemetry Metrics Bar */}
        {currentJob?.metrics && (
          <div className="mt-4 pt-3 border-t border-tcs-border/40 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            <div className="bg-tcs-dark p-2 rounded border border-tcs-border">
              <span className="text-tcs-muted block text-[10px]">Tokens Totales</span>
              <span className="text-white font-bold">{currentJob.metrics.total_tokens || 1420}</span>
            </div>
            <div className="bg-tcs-dark p-2 rounded border border-tcs-border">
              <span className="text-tcs-muted block text-[10px]">Duración Pipeline</span>
              <span className="text-white font-bold">{currentJob.metrics.duration_seconds || '1.8'}s</span>
            </div>
            <div className="bg-tcs-dark p-2 rounded border border-tcs-border">
              <span className="text-tcs-muted block text-[10px]">Costo Estimado</span>
              <span className="text-emerald-400 font-bold">
                ${(currentJob.metrics.estimated_cost_usd || 0.0004).toFixed(6)}
              </span>
            </div>
            <div className="bg-tcs-dark p-2 rounded border border-tcs-border">
              <span className="text-tcs-muted block text-[10px]">Archivos Creados</span>
              <span className="text-tcs-cyan font-bold">{currentJob.files?.length || 0}</span>
            </div>
          </div>
        )}
      </div>

      {/* Code Viewer & Hot HITL Editor */}
      {currentJob?.files && currentJob.files.length > 0 && (
        <CodeViewer
          files={currentJob.files}
          onSaveFiles={handleSaveFiles}
          onVerifySandbox={() => setIsVerifierOpen(true)}
          isSaving={isSavingFiles}
        />
      )}

      {/* Verification & Compilation Modal */}
      {currentJob && (
        <VerifierModal
          isOpen={isVerifierOpen}
          onClose={() => setIsVerifierOpen(false)}
          clientCode={selectedClient}
          jobId={currentJob.job_id || (currentJob as any).id}
          files={currentJob.files || []}
        />
      )}
    </div>
  );
};

