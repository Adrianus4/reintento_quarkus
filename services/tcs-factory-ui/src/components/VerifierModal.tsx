// src/components/VerifierModal.tsx
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { GeneratedFile, VerificationResult } from '../types';

interface VerifierModalProps {
  isOpen: boolean;
  onClose: () => void;
  clientCode: string;
  jobId?: string;
  files: GeneratedFile[];
}

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
  const [activeTab, setActiveTab] = useState<'logs' | 'manifest'>('logs');

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
      if (res.status === 'SUCCESS') {
        setActiveTab('manifest');
      }
    } catch (err: any) {
      setError(err.message || 'Error en la verificación');
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-tcs-dark/85 backdrop-blur-md p-4">
      <div className="w-full max-w-4xl bg-tcs-navy border border-tcs-border rounded-xl shadow-2xl flex flex-col h-[750px] overflow-hidden animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="p-4 bg-gradient-to-r from-tcs-navy to-tcs-dark border-b border-tcs-border flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center">
              <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center space-x-2">
                <span>Sandbox Verifier Service (:8004)</span>
                {result && (
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                      result.status === 'SUCCESS'
                        ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-700'
                        : 'bg-rose-950/80 text-rose-300 border border-rose-700'
                    }`}
                  >
                    {result.status}
                  </span>
                )}
              </h2>
              <p className="text-xs text-tcs-muted">
                Compilación Determinista & Manifiesto Criptográfico SHA-256 (Principio XIV)
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {result?.status === 'SUCCESS' && (
              <a
                href={api.verifier.getDownloadUrl(result.run_id || (result as any).id)}
                download
                className="px-4 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded-lg shadow transition-all flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Descargar Microservicio (.ZIP)</span>
              </a>
            )}

            <button
              onClick={onClose}
              className="p-1.5 text-tcs-muted hover:text-white rounded-lg hover:bg-tcs-surface"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-tcs-dark px-4 py-2 border-b border-tcs-border flex items-center justify-between text-xs">
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab('logs')}
              className={`px-3 py-1 rounded font-medium transition-colors ${
                activeTab === 'logs' ? 'bg-tcs-blue text-white' : 'text-tcs-muted hover:text-white'
              }`}
            >
              Consola del Compilador
            </button>
            <button
              onClick={() => setActiveTab('manifest')}
              className={`px-3 py-1 rounded font-medium transition-colors ${
                activeTab === 'manifest' ? 'bg-tcs-blue text-white' : 'text-tcs-muted hover:text-white'
              }`}
            >
              Manifiesto Criptográfico (SHA-256)
            </button>
          </div>

          <button
            onClick={executeVerification}
            disabled={loading}
            className="text-[11px] px-2 py-0.5 rounded border border-tcs-border text-tcs-muted hover:text-white disabled:opacity-40"
          >
            {loading ? 'Compilando...' : 'Re-ejecutar Verificación'}
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden p-4 bg-[#050b14]">
          {loading && (
            <div className="h-full flex flex-col items-center justify-center space-y-3">
              <span className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin"></span>
              <p className="text-xs text-emerald-400 font-mono">
                Materializando en sandbox efímero y ejecutando comprobación determinista...
              </p>
            </div>
          )}

          {error && !loading && (
            <div className="p-4 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs font-mono">
              <strong>Error en la verificación:</strong>
              <pre className="mt-2 whitespace-pre-wrap">{error}</pre>
            </div>
          )}

          {!loading && result && activeTab === 'logs' && (
            <div className="h-full overflow-auto font-mono text-xs text-slate-300 leading-relaxed p-3 bg-black/40 rounded border border-tcs-border/40">
              <pre className="whitespace-pre-wrap">{result.compiler_logs || (result as any).compilation_output}</pre>
            </div>
          )}

          {!loading && result && activeTab === 'manifest' && (
            <div className="h-full overflow-auto space-y-4">
              <div className="bg-tcs-card border border-tcs-border p-3 rounded-lg text-xs space-y-1">
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
                  <span className="font-mono text-emerald-400">SHA-256 Determinista</span>
                </div>
              </div>

              <div className="border border-tcs-border rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-tcs-navy text-tcs-muted border-b border-tcs-border">
                    <tr>
                      <th className="p-2.5">Ruta de Archivo</th>
                      <th className="p-2.5">Hash SHA-256</th>
                      <th className="p-2.5 text-right">Tamaño</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-tcs-border/40 bg-tcs-dark/50">
                    {(result.manifest?.files || []).map((entry: any) => (
                      <tr key={entry.path} className="hover:bg-tcs-surface/40">
                        <td className="p-2.5 text-white truncate max-w-xs">{entry.path}</td>
                        <td className="p-2.5 text-tcs-cyan text-[11px] truncate max-w-sm">
                          {entry.sha256}
                        </td>
                        <td className="p-2.5 text-right text-tcs-muted">
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

