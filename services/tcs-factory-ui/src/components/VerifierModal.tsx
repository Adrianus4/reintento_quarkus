import { DownloadButton } from './DownloadButton';
// src/components/VerifierModal.tsx
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { GeneratedFile, VerificationResult, PhaseResult, StructuredFailure } from '../types';

interface VerifierModalProps {
  isOpen: boolean;
  onClose: () => void;
  clientCode: string;
  jobId?: string;
  files: GeneratedFile[];
}

const DEFAULT_PHASES = [
  { phase: 'validate', label: '1. Validación de Estructura POM & BOM', icon: '📋' },
  { phase: 'test-compile', label: '2. Compilación AST & Tipos Java 21', icon: '⚙️' },
  { phase: 'verify', label: '3. Ejecución de Pruebas Unitarias & Aceptación', icon: '🧪' },
  { phase: 'runtime-test', label: '4. Arranque de Contenedor Efímero en Perfil Test', icon: '🚀' },
  { phase: 'smoke-test', label: '5. Smoke Tests de Inbounds & Outbounds', icon: '🔍' },
];

export const VerifierModal: React.FC<VerifierModalProps> = ({
  isOpen,
  onClose,
  clientCode,
  jobId,
  files,
}) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'phases' | 'logs' | 'manifest'>('phases');

  const executeVerification = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.verifier.createRun({
        client_code: clientCode,
        job_id: jobId,
        files: files.map((f) => ({ path: f.path, content: f.content })),
      });
      setResult(res);
      if (res.veto_applied || res.status === 'FAILED') {
        setActiveTab('phases');
      } else {
        setActiveTab('manifest');
      }
    } catch (err: any) {
      setError(err.message || 'Error en la verificación del sandbox');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      executeVerification();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const vetoApplied = result?.veto_applied ?? (result?.status === 'FAILED');
  const verdict = result?.verdict || (result?.status === 'SUCCESS' ? 'PASSED' : 'FAILED');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div className="w-full max-w-4xl bg-tcs-navy border border-tcs-border rounded-2xl shadow-2xl flex flex-col h-[750px] overflow-hidden animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="p-4 bg-gradient-to-r from-tcs-navy via-tcs-card to-tcs-dark border-b border-tcs-border flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center border shadow-lg ${
              vetoApplied
                ? 'bg-rose-500/20 border-rose-500/50 text-rose-400'
                : 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
            }`}>
              <span className="text-xl">{vetoApplied ? '⛔' : '🛡️'}</span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-extrabold text-white">
                  TCS Factory Ephemeral Sandbox Verifier (:8004)
                </h2>
                {result && (
                  <span
                    className={`text-[10px] px-2.5 py-0.5 rounded-full font-mono font-bold tracking-wider uppercase border ${
                      !vetoApplied
                        ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/60'
                        : 'bg-rose-950/80 text-rose-300 border-rose-500/60'
                    }`}
                  >
                    VEREDICTO: {verdict}
                  </span>
                )}
              </div>
              <p className="text-xs text-tcs-muted">
                5 Fases Estrictas con Poder de Veto & Manifiesto SHA-256 (Principio XIV)
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {result && !vetoApplied ? (
              <DownloadButton url={api.verifier.getDownloadUrl(result.run_id || (result as any).id)} disabled={false}
                className="px-4 py-2 bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-600 hover:from-emerald-500 hover:to-teal-500 text-white font-extrabold text-xs rounded-xl shadow-lg transition-all flex items-center space-x-2 transform hover:scale-[1.02]"
              >
                <span>📦</span>
                <span>Descargar Microservicio (.ZIP)</span>
              </DownloadButton>
            ) : (
              <span
                title="Descarga bloqueada: El sandbox aplicó VETO por fallos de integridad"
                className="px-4 py-2 bg-rose-950/40 border border-rose-800/60 text-rose-400 font-bold text-xs rounded-xl cursor-not-allowed flex items-center space-x-1.5 opacity-80"
              >
                <span>⛔</span>
                <span>Descarga Bloqueada por Veto</span>
              </span>
            )}

            <button
              onClick={onClose}
              className="p-2 text-tcs-muted hover:text-white rounded-xl hover:bg-tcs-surface transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Veto Warning Banner */}
        {vetoApplied && (
          <div className="bg-rose-950/80 border-b border-rose-800/80 px-4 py-2.5 text-xs text-rose-200 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-base">⚠️</span>
              <span>
                <strong>PODER DE VETO APLICADO:</strong> El proyecto contiene defectos sintácticos, de dependencias o compilación. Se bloqueó la entrega para garantizar que ningún código defectuoso llegue a producción.
              </span>
            </div>
            <span className="font-mono text-[10px] bg-rose-900/60 px-2 py-0.5 rounded border border-rose-700/50">HTTP 403 EN DOWNLOAD</span>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="bg-tcs-dark px-4 py-2 border-b border-tcs-border flex items-center justify-between text-xs">
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab('phases')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                activeTab === 'phases' ? 'bg-tcs-blue text-white shadow' : 'text-tcs-muted hover:text-white'
              }`}
            >
              5 Fases de Verificación
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                activeTab === 'logs' ? 'bg-tcs-blue text-white shadow' : 'text-tcs-muted hover:text-white'
              }`}
            >
              Consola del Sandbox
            </button>
            <button
              onClick={() => setActiveTab('manifest')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                activeTab === 'manifest' ? 'bg-tcs-blue text-white shadow' : 'text-tcs-muted hover:text-white'
              }`}
            >
              Manifiesto Criptográfico (SHA-256)
            </button>
          </div>

          <button
            onClick={executeVerification}
            disabled={loading}
            className="text-xs px-3 py-1 rounded-lg border border-tcs-border text-tcs-muted hover:text-white hover:bg-tcs-surface disabled:opacity-40 transition-colors"
          >
            {loading ? 'Verificando...' : '↻ Re-ejecutar Sandbox'}
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden p-4 bg-[#050b14]">
          {loading && (
            <div className="h-full flex flex-col items-center justify-center space-y-4">
              <div className="w-10 h-10 border-4 border-tcs-cyan border-t-transparent rounded-full animate-spin"></div>
              <p className="text-xs text-tcs-cyan font-mono animate-pulse">
                Materializando en sandbox efímero y ejecutando comprobación determinista...
              </p>
            </div>
          )}

          {error && !loading && (
            <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs font-mono">
              <strong>Error en la verificación:</strong>
              <pre className="mt-2 whitespace-pre-wrap">{error}</pre>
            </div>
          )}

          {!loading && result && activeTab === 'phases' && (
            <div className="h-full overflow-auto space-y-4 pr-1">
              {/* 5 Phases Grid */}
              <div className="space-y-2">
                {DEFAULT_PHASES.map((def) => {
                  const phaseData = result.phase_results?.find((p) => p.phase === def.phase);
                  const status = phaseData?.status || (result.status === 'SUCCESS' ? 'SUCCESS' : 'PENDING');
                  const isSuccess = status === 'SUCCESS';
                  const isFailed = status === 'FAILED';
                  const isSkipped = status === 'SKIPPED';

                  return (
                    <div
                      key={def.phase}
                      className={`p-3.5 rounded-xl border transition-all ${
                        isFailed
                          ? 'bg-rose-950/30 border-rose-600/60'
                          : isSuccess
                          ? 'bg-emerald-950/30 border-emerald-600/50'
                          : isSkipped
                          ? 'bg-tcs-dark/50 border-tcs-border/40 opacity-60'
                          : 'bg-tcs-card border-tcs-border'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className="text-lg">{def.icon}</span>
                          <div>
                            <div className="text-xs font-extrabold text-white">{def.label}</div>
                            {phaseData?.details && (
                              <div className="text-[11px] text-tcs-muted font-mono mt-0.5">
                                {phaseData.details}
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          {phaseData?.duration_ms !== undefined && (
                            <span className="text-[10px] text-tcs-muted font-mono">
                              {phaseData.duration_ms}ms
                            </span>
                          )}
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                              isSuccess
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                : isFailed
                                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                : isSkipped
                                ? 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                                : 'bg-blue-500/20 text-blue-400'
                            }`}
                          >
                            {status}
                          </span>
                        </div>
                      </div>

                      {/* Display Failures for this phase if any */}
                      {phaseData?.failures && phaseData.failures.length > 0 && (
                        <div className="mt-3 p-3 bg-black/50 border border-rose-800/60 rounded-lg space-y-1.5 text-xs font-mono text-rose-300">
                          {phaseData.failures.map((f, idx) => (
                            <div key={idx} className="flex items-start space-x-2">
                              <span className="text-rose-400">✖</span>
                              <div>
                                {f.file && <span className="text-amber-300 font-bold">{f.file}</span>}
                                {f.line && <span className="text-amber-400">:{f.line}</span>}
                                {f.test_name && <span className="text-purple-300"> ({f.test_name})</span>}
                                <p className="text-rose-200 mt-0.5 whitespace-pre-wrap">{f.message}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Overall structured failures */}
              {result.structured_failures && result.structured_failures.length > 0 && (
                <div className="p-4 bg-rose-950/40 border border-rose-600/60 rounded-xl space-y-2">
                  <h4 className="text-xs font-bold text-rose-300">
                    Defectos Críticos Detectados ({result.structured_failures.length}):
                  </h4>
                  <ul className="space-y-1.5 text-xs font-mono text-rose-200">
                    {result.structured_failures.map((sf, idx) => (
                      <li key={idx} className="p-2 bg-black/40 rounded border border-rose-800/50">
                        <span className="text-xs font-bold text-amber-300 uppercase">[{sf.phase}]</span>{' '}
                        {sf.file && <span className="text-white">{sf.file}</span>}
                        {sf.line && <span className="text-amber-400">:{sf.line}</span>}
                        <div className="text-[11px] text-rose-300 mt-1">{sf.message}</div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {!loading && result && activeTab === 'logs' && (
            <div className="h-full overflow-auto font-mono text-xs text-slate-300 leading-relaxed p-3 bg-black/50 rounded-xl border border-tcs-border/40">
              <pre className="whitespace-pre-wrap">{result.compiler_logs || (result as any).compilation_output}</pre>
            </div>
          )}

          {!loading && result && activeTab === 'manifest' && (
            <div className="h-full overflow-auto space-y-4 pr-1">
              <div className="bg-tcs-card border border-tcs-border p-3.5 rounded-xl text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-tcs-muted">Archivo de Manifiesto:</span>
                  <span className="font-mono text-white">VERIFICATION_MANIFEST.json</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-tcs-muted">Total de Archivos Auditados:</span>
                  <span className="font-mono text-white">
                    {result.manifest?.total_files || result.manifest?.files?.length || files.length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-tcs-muted">Estándar Criptográfico:</span>
                  <span className="font-mono text-emerald-400 font-bold">SHA-256 Determinista</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-tcs-muted">Veredicto del Sandbox:</span>
                  <span className={`font-mono font-bold ${!vetoApplied ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {verdict} {!vetoApplied ? '(100% Integra)' : '(VETO APLICADO)'}
                  </span>
                </div>
              </div>

              <div className="border border-tcs-border rounded-xl overflow-hidden shadow-lg">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-tcs-navy text-tcs-muted border-b border-tcs-border">
                    <tr>
                      <th className="p-3">Ruta de Archivo</th>
                      <th className="p-3">Hash SHA-256</th>
                      <th className="p-3 text-right">Tamaño</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-tcs-border/40 bg-tcs-dark/60">
                    {(result.manifest?.files || []).map((entry: any) => (
                      <tr key={entry.path} className="hover:bg-tcs-surface/40 transition-colors">
                        <td className="p-3 text-white truncate max-w-xs">{entry.path}</td>
                        <td className="p-3 text-tcs-cyan text-[11px] truncate max-w-sm">
                          {entry.sha256}
                        </td>
                        <td className="p-3 text-right text-tcs-muted">
                          {entry.size_bytes} B
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
