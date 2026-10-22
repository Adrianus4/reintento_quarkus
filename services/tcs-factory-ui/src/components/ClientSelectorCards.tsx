// src/components/ClientSelectorCards.tsx
import React, { useState } from 'react';
import { ClientProfile } from '../types';
import { api } from '../services/api';

interface ClientSelectorCardsProps {
  clients: ClientProfile[];
  onSelectClient: (client: ClientProfile) => void;
  onRefreshClients: () => Promise<void>;
  isAdmin?: boolean;
}

export const ClientSelectorCards: React.FC<ClientSelectorCardsProps> = ({
  clients,
  onSelectClient,
  onRefreshClients,
  isAdmin = false,
}) => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New Client Form State
  const [newCode, setNewCode] = useState('');
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newPackagePrefix, setNewPackagePrefix] = useState('pe.com.');
  const [newJavaVersion, setNewJavaVersion] = useState('21');
  const [newQuarkusVersion] = useState('3.15.1');

  const handleOpenModal = () => {
    setNewCode('');
    setNewName('');
    setNewDesc('');
    setNewPackagePrefix('pe.com.');
    setNewJavaVersion('21');
    setError(null);
    setIsAddModalOpen(true);
  };

  const handleCreateClient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCode.trim() || !newName.trim()) {
      setError('El código y el nombre del cliente son obligatorios.');
      return;
    }

    const cleanCode = newCode.trim().toLowerCase().replace(/[^a-z0-9-]/g, '-');
    setIsSubmitting(true);
    setError(null);

    try {
      const created = await api.governance.createClient({
        code: cleanCode,
        name: newName.trim(),
        description: newDesc.trim() || undefined,
        package_prefix: newPackagePrefix.trim() || `pe.com.${cleanCode}`,
        java_version: newJavaVersion,
        quarkus_version: newQuarkusVersion,
      });

      await onRefreshClients();
      setIsAddModalOpen(false);
      onSelectClient(created);
    } catch (err: any) {
      setError(err.message || 'Error al registrar el cliente');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-tcs-navy via-tcs-card to-tcs-navy border border-tcs-border p-6 rounded-2xl shadow-xl relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-tcs-blue/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="max-w-3xl space-y-2 relative z-10">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-tcs-blue/20 border border-tcs-blue/40 text-[11px] font-semibold text-tcs-cyan">
            <span className="w-2 h-2 rounded-full bg-tcs-cyan animate-pulse"></span>
            <span>CENTRO DE GOBERNANZA CORPORATIVA</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Cuentas y Clientes Autorizados
          </h1>
          <p className="text-xs sm:text-sm text-tcs-muted leading-relaxed">
            Selecciona la cuenta corporativa a la que tienes acceso para ingresar a su{' '}
            <strong className="text-white">Workspace Studio</strong>. Las directivas técnicas,
            normativas bancarias, versionamiento de Java y contratos OpenAPI del cliente se aplicarán
            automáticamente a los agentes de IA sin configuraciones rígidas.
          </p>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clients.map((client) => {
          const clientCode = (client.code || client.client_id || '').toLowerCase();
          const isBcp = clientCode === 'bcp';

          return (
            <div
              key={clientCode || client.id}
              className={`group relative rounded-2xl border transition-all duration-300 flex flex-col justify-between overflow-hidden shadow-lg hover:shadow-2xl hover:-translate-y-1 ${
                isBcp
                  ? 'bg-gradient-to-b from-[#002A8F]/25 via-tcs-card to-tcs-navy border-tcs-blue/40 hover:border-tcs-blue'
                  : 'bg-tcs-card/80 border-tcs-border hover:border-tcs-blue/60'
              }`}
            >
              {/* Card Top / Badge */}
              <div className="p-6 space-y-4">
                <div className="flex items-start justify-between">
                  {/* Logo or Icon */}
                  {isBcp ? (
                    <div className="w-16 h-16 rounded-xl bg-[#002A8F] p-2 flex items-center justify-center shadow-md border border-blue-400/30 overflow-hidden shrink-0">
                      <img
                        src="/bcp-logo.png"
                        alt="BCP Logo"
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          // Fallback to text if image fails
                          (e.target as HTMLElement).style.display = 'none';
                        }}
                      />
                    </div>
                  ) : (
                    <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-tcs-blue/30 to-tcs-navy border border-tcs-border flex items-center justify-center text-tcs-cyan font-extrabold text-lg shadow-inner">
                      {clientCode.slice(0, 3).toUpperCase()}
                    </div>
                  )}

                  <div className="flex flex-col items-end space-y-1">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase">
                      ● Activo
                    </span>
                    <span className="text-[10px] font-mono text-tcs-muted uppercase tracking-wider">
                      ID: {clientCode}
                    </span>
                  </div>
                </div>

                {/* Client Info */}
                <div>
                  <h3 className="text-base font-bold text-white group-hover:text-tcs-cyan transition-colors">
                    {client.name}
                  </h3>
                  <p className="text-xs text-tcs-muted mt-1.5 line-clamp-2">
                    {client.description ||
                      `Cuenta corporativa autorizada para la generación adaptativa de microservicios Quarkus.`}
                  </p>
                </div>

                {/* Technical Directive Highlights */}
                <div className="pt-2 border-t border-tcs-border/60 space-y-2">
                  <div className="flex flex-wrap gap-1.5 text-[11px] font-mono">
                    <span className="px-2 py-0.5 rounded bg-tcs-dark/80 text-tcs-cyan border border-tcs-border">
                      Java {client.java_version || '21'}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-tcs-dark/80 text-white/90 border border-tcs-border">
                      Quarkus {client.quarkus_version || '3.15.1'}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-tcs-dark/80 text-tcs-muted border border-tcs-border truncate max-w-[170px]">
                      {client.package_prefix || `pe.com.${clientCode}`}
                    </span>
                  </div>

                  {isBcp && (
                    <div className="flex flex-wrap gap-1 text-[10px] text-amber-300/90 font-medium pt-1">
                      <span className="bg-amber-400/10 px-1.5 py-0.5 rounded border border-amber-400/20">
                        Mutiny Reactive
                      </span>
                      <span className="bg-amber-400/10 px-1.5 py-0.5 rounded border border-amber-400/20">
                        Panache ORM
                      </span>
                      <span className="bg-amber-400/10 px-1.5 py-0.5 rounded border border-amber-400/20">
                        OpenAPI
                      </span>
                      <span className="bg-amber-400/10 px-1.5 py-0.5 rounded border border-amber-400/20">
                        Kafka / Outbox
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <div className="p-4 bg-tcs-dark/40 border-t border-tcs-border/60">
                <button
                  onClick={() => onSelectClient(client)}
                  className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center space-x-2 transition-all ${
                    isBcp
                      ? 'bg-gradient-to-r from-[#002A8F] to-tcs-blue hover:from-blue-700 hover:to-cyan-600 text-white shadow-lg shadow-blue-900/30'
                      : 'bg-tcs-blue hover:bg-tcs-blue/80 text-white shadow-md'
                  }`}
                >
                  <span>Entrar al Workspace {isBcp ? 'BCP' : client.name}</span>
                  <svg
                    className="w-4 h-4 transform group-hover:translate-x-1 transition-transform"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 7l5 5m0 0l-5 5m5-5H6"
                    />
                  </svg>
                </button>
              </div>
            </div>
          );
        })}

        {/* Add New Client Card */}
        <div
          onClick={handleOpenModal}
          className="group relative rounded-2xl border-2 border-dashed border-tcs-border hover:border-tcs-cyan/60 bg-tcs-navy/30 hover:bg-tcs-navy/60 p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 min-h-[300px] hover:shadow-xl"
        >
          <div className="w-14 h-14 rounded-2xl bg-tcs-card border border-tcs-border group-hover:border-tcs-cyan group-hover:bg-tcs-blue/20 flex items-center justify-center text-tcs-cyan transition-all mb-4">
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-white group-hover:text-tcs-cyan transition-colors">
            Agregar Nueva Cuenta de Cliente
          </h3>
          <p className="text-xs text-tcs-muted mt-2 max-w-xs">
            Registra una nueva cuenta institucional de TCS con sus directivas técnicas, paquete base
            y versión de Java para comenzar a generar microservicios Quarkus.
          </p>
          <div className="mt-5 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-tcs-card border border-tcs-border text-xs font-semibold text-tcs-cyan group-hover:bg-tcs-blue group-hover:text-white transition-all">
            <span>+ Configurar Cliente</span>
          </div>
        </div>
      </div>

      {/* Modal: Add New Client */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-tcs-card border border-tcs-border rounded-2xl max-w-lg w-full p-6 shadow-2xl relative space-y-5 animate-scaleUp">
            <div className="flex items-center justify-between pb-3 border-b border-tcs-border">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-tcs-blue/20 flex items-center justify-center text-tcs-cyan">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Registrar Nueva Cuenta Corporativa</h3>
                  <p className="text-xs text-tcs-muted">Configuración del perfil de gobernanza</p>
                </div>
              </div>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-tcs-muted hover:text-white text-lg p-1"
              >
                ✕
              </button>
            </div>

            {error && (
              <div className="p-3 bg-red-950/40 border border-red-500/40 rounded-lg text-xs text-red-200">
                {error}
              </div>
            )}

            <form onSubmit={handleCreateClient} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-tcs-muted mb-1">
                    Código Slug (ID Único) *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="ej. interbank, bbva, santander"
                    value={newCode}
                    onChange={(e) => {
                      const val = e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-');
                      setNewCode(val);
                      if (!newPackagePrefix || newPackagePrefix.startsWith('pe.com.')) {
                        setNewPackagePrefix(`pe.com.${val}`);
                      }
                    }}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                  />
                  <span className="text-[10px] text-tcs-muted">Solo minúsculas y guiones</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-tcs-muted mb-1">
                    Nombre Oficial de la Empresa *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="ej. Interbank Perú"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:outline-none focus:border-tcs-blue"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-tcs-muted mb-1">
                  Prefijo de Paquetes Java (Package Prefix)
                </label>
                <input
                  type="text"
                  placeholder="ej. pe.com.interbank"
                  value={newPackagePrefix}
                  onChange={(e) => setNewPackagePrefix(e.target.value)}
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-tcs-muted mb-1">
                    Versión de Java
                  </label>
                  <select
                    value={newJavaVersion}
                    onChange={(e) => setNewJavaVersion(e.target.value)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:outline-none focus:border-tcs-blue"
                  >
                    <option value="21">Java 21 (LTS Recomendado)</option>
                    <option value="17">Java 17 (LTS)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-tcs-muted mb-1">
                    Versión de Quarkus
                  </label>
                  <input
                    type="text"
                    readOnly
                    value="3.15.1"
                    className="w-full px-3 py-2 bg-tcs-dark/50 border border-tcs-border rounded-lg text-xs text-tcs-muted font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-tcs-muted mb-1">
                  Descripción o Alcance
                </label>
                <textarea
                  rows={2}
                  placeholder="Descripción de la cuenta, tipo de industria o alcance bancario/empresarial..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:outline-none focus:border-tcs-blue resize-none"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-tcs-border">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-tcs-muted hover:text-white"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-lg text-xs font-bold bg-tcs-blue hover:bg-tcs-blue/80 text-white shadow-md disabled:opacity-50"
                >
                  {isSubmitting ? 'Guardando...' : 'Crear Cuenta y Entrar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
