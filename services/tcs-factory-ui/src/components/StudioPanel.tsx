// src/components/StudioPanel.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { CodeViewer } from './CodeViewer';
import { ClientSelectorCards } from './ClientSelectorCards';
import { VerifierModal } from './VerifierModal';
import {
  ClientProfile,
  OpenApiSpecSummary,
  OrchestrationJob,
  GeneratedFile,
  EntityDefinition,
  CustomEndpoint,
} from '../types';

export const StudioPanel: React.FC = () => {
  const { user } = useAuth();
  const [clients, setClients] = useState<ClientProfile[]>([]);
  const [activeClient, setActiveClient] = useState<ClientProfile | null>(null);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [contracts, setContracts] = useState<OpenApiSpecSummary[]>([]);
  const [selectedContractId, setSelectedContractId] = useState<string>('');

  // Primary Requirement Prompt (Clean by default)
  const [requirementPrompt, setRequirementPrompt] = useState<string>('');

  // Toggle for Advanced Technical Fine-Tuning
  const [showAdvancedSettings, setShowAdvancedSettings] = useState<boolean>(false);
  const [advancedTab, setAdvancedTab] = useState<'identity' | 'arch' | 'security' | 'database' | 'endpoints' | 'extensions'>('identity');

  // --- 1. Project Identity Inputs ---
  const [artifactId, setArtifactId] = useState<string>('');
  const [packagePrefix, setPackagePrefix] = useState<string>('');
  const [httpPort, setHttpPort] = useState<number>(8080);
  const [javaVersion, setJavaVersion] = useState<string>('21');
  const [quarkusVersion] = useState<string>('3.15.1');

  // --- 2. Architecture Inputs ---
  const [archStyle, setArchStyle] = useState<string>('Hexagonal');
  const [customArchNotes, setCustomArchNotes] = useState<string>('');

  // --- 3. Security Inputs ---
  const [securityOption, setSecurityOption] = useState<string>('JWT');
  const [jwtIssuer, setJwtIssuer] = useState<string>('');
  const [securityRoles, setSecurityRoles] = useState<string>('ADMIN, USER');

  // --- 4. Communication & Custom Endpoints Inputs ---
  const [commProtocol, setCommProtocol] = useState<string>('REST');
  const [customEndpoints, setCustomEndpoints] = useState<CustomEndpoint[]>([]);

  // --- 5. Database & Editable Entities Inputs ---
  const [databaseOption, setDatabaseOption] = useState<string>('POSTGRESQL_PANACHE');
  const [databaseName, setDatabaseName] = useState<string>('');
  const [entities, setEntities] = useState<EntityDefinition[]>([]);

  // --- 6. Quarkus Extensions & Custom Properties Inputs ---
  const [selectedExtensions, setSelectedExtensions] = useState<string[]>([
    'quarkus-resteasy-reactive-jackson',
    'quarkus-smallrye-openapi',
    'quarkus-hibernate-validator',
  ]);
  const [customExtensionsText, setCustomExtensionsText] = useState<string>('');
  const [customPropertiesText, setCustomPropertiesText] = useState<string>('');

  // Execution & Job State
  const [currentJob, setCurrentJob] = useState<OrchestrationJob | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isSavingFiles, setIsSavingFiles] = useState<boolean>(false);
  const [isVerifierOpen, setIsVerifierOpen] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load clients accessible to current user
  const fetchAuthorizedClients = async () => {
    try {
      const allClients = await api.governance.listClients(true);
      if (user?.role === 'ADMIN') {
        setClients(allClients);
      } else {
        const assigned = (user?.assigned_clients || []).map((c) => c.toLowerCase());
        const filtered = allClients.filter((c: any) => {
          const code = (c.code || c.client_id || '').toLowerCase();
          return assigned.includes(code) || assigned.includes('*');
        });
        setClients(filtered);
      }
    } catch (err: any) {
      console.error('Failed to load clients', err);
    }
  };

  useEffect(() => {
    fetchAuthorizedClients();
  }, [user]);

  // When a user selects a client card
  const handleSelectClient = (client: ClientProfile) => {
    setActiveClient(client);
    const code = (client.code || client.client_id || '').toLowerCase();
    setSelectedClient(code);
    setPackagePrefix(client.package_prefix || `pe.com.${code}`);
    setJavaVersion(client.java_version || '21');
    setArtifactId(`${code}-nuevo-servicio`);
    setDatabaseName(`${code}_db`);
    setJwtIssuer(`https://auth.${code}.com`);

    // Start with a clean, blank slate
    setRequirementPrompt('');
    setEntities([]);
    setCustomEndpoints([]);
    setCustomArchNotes('');
    setCustomPropertiesText('');
    setCurrentJob(null);
    setError(null);
  };

  const handleResetToBlank = () => {
    const code = selectedClient || 'bcp';
    setArtifactId(`${code}-nuevo-servicio`);
    setRequirementPrompt('');
    setEntities([]);
    setCustomEndpoints([]);
    setCustomArchNotes('');
    setCustomPropertiesText('');
    setCurrentJob(null);
    setError(null);
  };

  const handleLoadBcpSample = () => {
    setArtifactId('bcp-transfers-service');
    setPackagePrefix('pe.com.bcp');
    setDatabaseName('bcp_transfers_db');
    setJwtIssuer('https://auth.viabcp.com');
    setJavaVersion('21');
    setArchStyle('Hexagonal');
    setCustomArchNotes(
      'Arquitectura hexagonal bancaria para BCP con separación de puertos/adaptadores y trazabilidad transaccional.'
    );
    setRequirementPrompt(
      'Implementar microservicio de transferencias bancarias y gestión de cuentas para BCP con validación de saldos, registro de auditoría, control de idempotencia y persistencia transaccional ACID.'
    );
    setEntities([
      {
        name: 'Transfer',
        tableName: 'transfers',
        fields: [
          { name: 'id', type: 'String', required: true, isId: true },
          { name: 'sourceAccount', type: 'String', required: true },
          { name: 'destinationAccount', type: 'String', required: true },
          { name: 'destinationBankCode', type: 'String', required: true },
          { name: 'amount', type: 'BigDecimal', required: true },
          { name: 'currency', type: 'String', required: true },
          { name: 'status', type: 'String', required: true },
          { name: 'createdAt', type: 'LocalDateTime', required: true },
        ],
      },
    ]);
    setCustomEndpoints([
      {
        method: 'POST',
        path: '/api/v1/transfers',
        summary: 'Ejecutar transferencia inmediata con validación de saldo',
      },
      {
        method: 'GET',
        path: '/api/v1/transfers/{id}',
        summary: 'Consultar estado y detalle de transferencia por UUID',
      },
    ]);
  };

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
        setContracts([]);
      }
    };

    fetchContracts();
  }, [selectedClient]);

  // Main Generation Handler (Prompt-Driven)
  const handleStartGeneration = async () => {
    if (!selectedClient) {
      setError('Seleccione una cuenta corporativa de cliente (ej. BCP)');
      return;
    }
    if (!requirementPrompt.trim()) {
      setError('Por favor escribe el requerimiento o descripción del microservicio que deseas crear.');
      return;
    }

    setError(null);
    setIsGenerating(true);
    setCurrentJob(null);

    // Parse custom extensions
    const extraExtensions = customExtensionsText
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const mergedExtensions = Array.from(
      new Set([...selectedExtensions, ...extraExtensions])
    );

    const rolesArray = securityRoles
      .split(',')
      .map((r) => r.trim())
      .filter((r) => r.length > 0);

    try {
      const job = await api.orchestrator.createJob({
        client_code: selectedClient,
        raw_requirement: requirementPrompt,
        requirements: requirementPrompt,
        architecture_style: archStyle,
        custom_architecture_notes: customArchNotes,
        security_option: securityOption,
        jwt_issuer: jwtIssuer,
        security_roles: rolesArray,
        communication_protocol: commProtocol,
        custom_endpoints: customEndpoints,
        database_option: databaseOption,
        database_name: databaseName,
        package_prefix: packagePrefix || `pe.com.${selectedClient}`,
        artifact_id: artifactId || `${selectedClient}-service`,
        http_port: httpPort,
        java_version: javaVersion,
        extensions: mergedExtensions,
        custom_extensions: extraExtensions,
        custom_properties: customPropertiesText,
        entities: entities,
        contract_id: selectedContractId || undefined,
      });

      setCurrentJob(job);
      setIsGenerating(false);
    } catch (err: any) {
      setError(err.message || 'Error al iniciar la generación con agentes de IA');
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

  // Helper for adding entity
  const handleAddEntity = () => {
    const newName = `Entity${entities.length + 1}`;
    setEntities([
      ...entities,
      {
        name: newName,
        tableName: `${newName.toLowerCase()}s`,
        fields: [
          { name: 'id', type: 'String', required: true, isId: true },
          { name: 'name', type: 'String', required: true },
          { name: 'status', type: 'String', required: true },
        ],
      },
    ]);
  };

  // Helper for adding endpoint
  const handleAddEndpoint = () => {
    setCustomEndpoints([
      ...customEndpoints,
      {
        method: 'GET',
        path: `/api/v1/resource-${customEndpoints.length + 1}`,
        summary: 'Operación REST generada',
      },
    ]);
  };

  // -------------------------------------------------------------
  // STEP 0: If NO client is selected, show Client Selector Cards
  // -------------------------------------------------------------
  if (!activeClient) {
    return (
      <ClientSelectorCards
        clients={clients}
        onSelectClient={handleSelectClient}
        onRefreshClients={fetchAuthorizedClients}
        isAdmin={user?.role === 'ADMIN'}
      />
    );
  }

  // -------------------------------------------------------------
  // STEP 1: Workspace Studio with Active Client
  // -------------------------------------------------------------
  const isBcp = selectedClient === 'bcp';

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* 1. Active Client Corporate Banner & Quick Switcher */}
      <div className="bg-gradient-to-r from-tcs-navy via-tcs-card to-tcs-navy border border-tcs-border rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl relative overflow-hidden">
        <div className="flex items-center space-x-4 relative z-10">
          {isBcp ? (
            <div className="w-16 h-16 rounded-2xl bg-[#002A8F] p-2 flex items-center justify-center shadow-lg border border-blue-400/30 shrink-0">
              <img
                src="/bcp-logo.png"
                alt="BCP Logo"
                className="w-full h-full object-contain"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            </div>
          ) : (
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-tcs-blue/30 to-tcs-navy border border-tcs-border flex items-center justify-center text-tcs-cyan font-extrabold text-lg shrink-0">
              {selectedClient.slice(0, 3).toUpperCase()}
            </div>
          )}

          <div>
            <div className="flex items-center space-x-2.5">
              <h2 className="text-lg font-extrabold text-white">
                {activeClient.name}
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase">
                ● Cuenta Seleccionada
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2 mt-1.5 text-xs font-mono text-tcs-muted">
              <span className="text-tcs-cyan font-semibold">{packagePrefix}</span>
              <span>•</span>
              <span className="text-white/80">Java {javaVersion}</span>
              <span>•</span>
              <span className="text-white/80">Quarkus {quarkusVersion}</span>
              <span>•</span>
              <span className="text-amber-400/90 font-sans">Gobernanza Activa</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 relative z-10">
          <button
            type="button"
            onClick={() => setActiveClient(null)}
            className="px-3.5 py-2 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border hover:border-tcs-cyan/60 rounded-xl text-xs font-semibold text-tcs-cyan flex items-center space-x-1.5 transition-all shadow"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
            <span>Cambiar de Cuenta</span>
          </button>

          <button
            type="button"
            onClick={handleResetToBlank}
            className="px-3.5 py-2 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border hover:border-emerald-500/60 rounded-xl text-xs font-semibold text-emerald-300 flex items-center space-x-1.5 transition-all shadow"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>✨ Nuevo Pedido (En blanco)</span>
          </button>

          {isBcp && (
            <button
              type="button"
              onClick={handleLoadBcpSample}
              className="px-3.5 py-2 bg-gradient-to-r from-[#002A8F] to-tcs-blue hover:from-blue-700 hover:to-cyan-600 border border-blue-400/40 rounded-xl text-xs font-bold text-white flex items-center space-x-1.5 transition-all shadow-lg"
            >
              <span>📋 Cargar Ejemplo BCP</span>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-200 text-xs flex items-center space-x-2">
          <span className="text-base">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* 2. PROMPT-FIRST REQUIREMENT BOX (THE HEART OF THE STUDIO) */}
      <div className="bg-tcs-card border border-tcs-border rounded-2xl p-6 shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-tcs-border/60 pb-3">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-tcs-cyan animate-pulse"></span>
              <span>Especificación del Microservicio Quarkus</span>
            </h3>
            <p className="text-xs text-tcs-muted mt-0.5">
              Describe en lenguaje natural tu microservicio. Los agentes de IA de TCS diseñarán el Blueprint,
              entidades, endpoints REST, dependencias y pruebas @QuarkusTest respetando las directivas de {activeClient.name}.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
            className="text-xs text-tcs-cyan hover:underline flex items-center space-x-1 font-semibold"
          >
            <span>⚙️ {showAdvancedSettings ? 'Ocultar Ajustes Técnicos' : 'Ajustes Técnicos Avanzados (Opcional)'}</span>
          </button>
        </div>

        {/* Textarea for Natural Language Specification */}
        <div className="space-y-2">
          <textarea
            rows={4}
            value={requirementPrompt}
            onChange={(e) => setRequirementPrompt(e.target.value)}
            placeholder={`Describe lo que debe hacer tu microservicio para ${activeClient.name}... \nEjemplo: Microservicio para originación y evaluación de préstamos vehiculares con validación de scoring crediticio, cálculo de cuotas con Panache ORM y publicación asíncrona de eventos a Kafka.`}
            className="w-full p-4 bg-tcs-dark border border-tcs-border rounded-xl text-xs sm:text-sm text-white focus:outline-none focus:border-tcs-blue leading-relaxed font-sans placeholder:text-tcs-muted/60 shadow-inner"
          />
        </div>

        {/* Primary Action Button (ALWAYS VISIBLE!) */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
          <div className="text-xs text-tcs-muted flex items-center space-x-2 font-mono">
            <span>Cliente: <strong className="text-white">{selectedClient.toUpperCase()}</strong></span>
            <span>•</span>
            <span>Java: <strong className="text-tcs-cyan">{javaVersion}</strong></span>
            <span>•</span>
            <span>Quarkus: <strong className="text-white">{quarkusVersion}</strong></span>
          </div>

          <button
            type="button"
            onClick={handleStartGeneration}
            disabled={isGenerating || !requirementPrompt.trim()}
            className="py-3 px-8 bg-gradient-to-r from-tcs-blue via-tcs-cyan to-tcs-blue hover:from-blue-600 hover:to-cyan-500 text-white font-extrabold text-sm rounded-xl shadow-xl shadow-cyan-900/30 transition-all flex items-center justify-center space-x-2.5 disabled:opacity-40 disabled:cursor-not-allowed group"
          >
            {isGenerating ? (
              <>
                <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                <span>Fabricando Microservicio con Agentes IA...</span>
              </>
            ) : (
              <>
                <span className="text-lg group-hover:scale-125 transition-transform">🚀</span>
                <span>Generar Microservicio Quarkus con IA</span>
              </>
            )}
          </button>
        </div>

        {/* 3. OPTIONAL ADVANCED FINE-TUNING DRAWER */}
        {showAdvancedSettings && (
          <div className="pt-5 border-t border-tcs-border/80 space-y-4 animate-fadeIn">
            <div className="flex items-center space-x-1 border-b border-tcs-border/60 pb-2 overflow-x-auto text-xs font-semibold">
              <button
                type="button"
                onClick={() => setAdvancedTab('identity')}
                className={`px-3 py-1.5 rounded-lg transition-colors ${advancedTab === 'identity' ? 'bg-tcs-blue text-white' : 'text-tcs-muted hover:text-white'}`}
              >
                1. Identidad
              </button>
              <button
                type="button"
                onClick={() => setAdvancedTab('arch')}
                className={`px-3 py-1.5 rounded-lg transition-colors ${advancedTab === 'arch' ? 'bg-tcs-blue text-white' : 'text-tcs-muted hover:text-white'}`}
              >
                2. Arquitectura
              </button>
              <button
                type="button"
                onClick={() => setAdvancedTab('security')}
                className={`px-3 py-1.5 rounded-lg transition-colors ${advancedTab === 'security' ? 'bg-tcs-blue text-white' : 'text-tcs-muted hover:text-white'}`}
              >
                3. Seguridad
              </button>
              <button
                type="button"
                onClick={() => setAdvancedTab('database')}
                className={`px-3 py-1.5 rounded-lg transition-colors ${advancedTab === 'database' ? 'bg-tcs-blue text-white' : 'text-tcs-muted hover:text-white'}`}
              >
                4. Base de Datos & Entidades
              </button>
              <button
                type="button"
                onClick={() => setAdvancedTab('endpoints')}
                className={`px-3 py-1.5 rounded-lg transition-colors ${advancedTab === 'endpoints' ? 'bg-tcs-blue text-white' : 'text-tcs-muted hover:text-white'}`}
              >
                5. Endpoints REST
              </button>
              <button
                type="button"
                onClick={() => setAdvancedTab('extensions')}
                className={`px-3 py-1.5 rounded-lg transition-colors ${advancedTab === 'extensions' ? 'bg-tcs-blue text-white' : 'text-tcs-muted hover:text-white'}`}
              >
                6. Extensiones Quarkus
              </button>
            </div>

            {/* Tab: Identity */}
            {advancedTab === 'identity' && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-medium text-tcs-muted mb-1">Artifact ID</label>
                  <input
                    type="text"
                    value={artifactId}
                    onChange={(e) => setArtifactId(e.target.value)}
                    placeholder="ej. bcp-loans-service"
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-tcs-muted mb-1">Package Prefix</label>
                  <input
                    type="text"
                    value={packagePrefix}
                    onChange={(e) => setPackagePrefix(e.target.value)}
                    placeholder="ej. pe.com.bcp"
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-tcs-muted mb-1">Puerto HTTP</label>
                  <input
                    type="number"
                    value={httpPort}
                    onChange={(e) => setHttpPort(parseInt(e.target.value) || 8080)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                  />
                </div>
              </div>
            )}

            {/* Tab: Architecture */}
            {advancedTab === 'arch' && (
              <div className="space-y-3 pt-2">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {['Hexagonal', 'Layered', 'Event-Driven'].map((style) => (
                    <div
                      key={style}
                      onClick={() => setArchStyle(style)}
                      className={`p-3 rounded-xl border cursor-pointer transition-all ${
                        archStyle === style
                          ? 'bg-tcs-blue/20 border-tcs-cyan text-white shadow'
                          : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue'
                      }`}
                    >
                      <div className="text-xs font-bold text-white">{style}</div>
                      <div className="text-[10px] text-tcs-muted mt-1">
                        {style === 'Hexagonal' && 'Puertos y adaptadores para desacople bancario estricto.'}
                        {style === 'Layered' && 'Capas clásicas Controller -> Service -> Repository.'}
                        {style === 'Event-Driven' && 'Orientado a eventos reactivos con SmallRye y Kafka.'}
                      </div>
                    </div>
                  ))}
                </div>
                <div>
                  <label className="block text-xs font-medium text-tcs-muted mb-1">Notas de Arquitectura (Opcional)</label>
                  <input
                    type="text"
                    value={customArchNotes}
                    onChange={(e) => setCustomArchNotes(e.target.value)}
                    placeholder="ej. Inmutabilidad en modelos de dominio y validación con Hibernate Validator..."
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:border-tcs-blue focus:outline-none"
                  />
                </div>
              </div>
            )}

            {/* Tab: Security */}
            {advancedTab === 'security' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-medium text-tcs-muted mb-1">Mecanismo de Seguridad</label>
                  <select
                    value={securityOption}
                    onChange={(e) => setSecurityOption(e.target.value)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:border-tcs-blue focus:outline-none"
                  >
                    <option value="JWT">JWT (JSON Web Token - SmallRye JWT)</option>
                    <option value="OIDC">OpenID Connect / OAuth2</option>
                    <option value="NONE">Sin Seguridad (Stateless Público)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-tcs-muted mb-1">Roles de Usuario</label>
                  <input
                    type="text"
                    value={securityRoles}
                    onChange={(e) => setSecurityRoles(e.target.value)}
                    placeholder="ADMIN, OPERATOR, AUDITOR"
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:border-tcs-blue focus:outline-none"
                  />
                </div>
              </div>
            )}

            {/* Tab: Database & Entities */}
            {advancedTab === 'database' && (
              <div className="space-y-4 pt-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-tcs-muted mb-1">Persistencia / Base de Datos</label>
                    <select
                      value={databaseOption}
                      onChange={(e) => setDatabaseOption(e.target.value)}
                      className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:border-tcs-blue focus:outline-none"
                    >
                      <option value="POSTGRESQL_PANACHE">PostgreSQL + Hibernate ORM Panache (Recomendado)</option>
                      <option value="SQLSERVER_PANACHE">Microsoft SQL Server + Panache (Normado BCP)</option>
                      <option value="MONGODB_PANACHE">MongoDB Panache (NoSQL Documental)</option>
                      <option value="NONE">Sin Base de Datos (100% Stateless)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-tcs-muted mb-1">Nombre de la Base de Datos</label>
                    <input
                      type="text"
                      value={databaseName}
                      onChange={(e) => setDatabaseName(e.target.value)}
                      placeholder="ej. bcp_loans_db"
                      className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white">Entidades del Dominio ({entities.length})</span>
                    <button
                      type="button"
                      onClick={handleAddEntity}
                      className="text-xs text-tcs-cyan hover:underline font-semibold"
                    >
                      + Agregar Entidad Manual
                    </button>
                  </div>
                  {entities.length === 0 ? (
                    <div className="p-3 rounded-lg bg-tcs-dark border border-tcs-border text-xs text-tcs-muted italic">
                      No hay entidades fijas definidas. La IA diseñará las entidades automáticamente a partir de tu requerimiento.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {entities.map((ent, idx) => (
                        <div key={idx} className="p-3 bg-tcs-dark border border-tcs-border rounded-lg text-xs flex items-center justify-between">
                          <div>
                            <span className="font-bold text-white">{ent.name}</span>
                            <span className="text-tcs-muted ml-2 font-mono">Tabla: {ent.tableName}</span>
                            <span className="text-tcs-cyan ml-2">({ent.fields.length} campos)</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => setEntities(entities.filter((_, i) => i !== idx))}
                            className="text-rose-400 hover:text-rose-300 text-xs"
                          >
                            Eliminar
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Tab: Endpoints */}
            {advancedTab === 'endpoints' && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-white">Endpoints REST ({customEndpoints.length})</span>
                  <button
                    type="button"
                    onClick={handleAddEndpoint}
                    className="text-xs text-tcs-cyan hover:underline font-semibold"
                  >
                    + Agregar Endpoint
                  </button>
                </div>
                {customEndpoints.length === 0 ? (
                  <div className="p-3 rounded-lg bg-tcs-dark border border-tcs-border text-xs text-tcs-muted italic">
                    Sin endpoints fijos. La IA generará los endpoints REST reactivos óptimos para este caso de uso.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {customEndpoints.map((ep, idx) => (
                      <div key={idx} className="p-3 bg-tcs-dark border border-tcs-border rounded-lg text-xs flex items-center justify-between font-mono">
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-0.5 rounded font-bold ${ep.method === 'POST' ? 'bg-blue-950 text-blue-300' : 'bg-emerald-950 text-emerald-300'}`}>
                            {ep.method}
                          </span>
                          <span className="text-white">{ep.path}</span>
                          <span className="text-tcs-muted font-sans text-[11px]">— {ep.summary}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setCustomEndpoints(customEndpoints.filter((_, i) => i !== idx))}
                          className="text-rose-400 hover:text-rose-300 font-sans"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Tab: Extensions */}
            {advancedTab === 'extensions' && (
              <div className="space-y-3 pt-2">
                <label className="block text-xs font-medium text-tcs-muted">Extensiones Quarkus Seleccionadas</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                  {[
                    { id: 'quarkus-resteasy-reactive-jackson', name: 'RESTEasy Reactive Jackson' },
                    { id: 'quarkus-smallrye-openapi', name: 'SmallRye OpenAPI / Swagger' },
                    { id: 'quarkus-hibernate-validator', name: 'Hibernate Validator' },
                    { id: 'quarkus-smallrye-health', name: 'SmallRye Health' },
                    { id: 'quarkus-micrometer-registry-prometheus', name: 'Micrometer Prometheus' },
                    { id: 'quarkus-smallrye-reactive-messaging-kafka', name: 'Reactive Messaging Kafka' },
                  ].map((ext) => {
                    const isChecked = selectedExtensions.includes(ext.id);
                    return (
                      <label key={ext.id} className="flex items-center space-x-2 p-2 bg-tcs-dark border border-tcs-border rounded-lg cursor-pointer">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedExtensions([...selectedExtensions, ext.id]);
                            } else {
                              setSelectedExtensions(selectedExtensions.filter((x) => x !== ext.id));
                            }
                          }}
                          className="rounded border-tcs-border text-tcs-blue focus:ring-0"
                        />
                        <span className="text-white">{ext.name}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 4. LIVE MULTI-AGENT PROGRESS STEPPER */}
      {isGenerating && (
        <div className="bg-tcs-card border border-tcs-blue/40 rounded-2xl p-6 shadow-xl space-y-4 animate-pulse">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-white flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-tcs-cyan"></span>
              <span>Cadena Multi-Agente en Ejecución (LangGraph)</span>
            </h4>
            <span className="text-xs font-mono text-tcs-cyan">Procesando...</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
            {[
              { num: 1, title: 'Gobernanza BCP' },
              { num: 2, title: 'Blueprint Arquitecto' },
              { num: 3, title: 'DevSecOps Scaffolding' },
              { num: 4, title: 'Código Java Quarkus' },
              { num: 5, title: 'Pruebas & Manifest SHA-256' },
            ].map((step) => (
              <div key={step.num} className="p-3 rounded-xl bg-tcs-dark border border-tcs-border text-center space-y-1">
                <div className="text-[10px] text-tcs-cyan font-mono font-bold">Fase {step.num}</div>
                <div className="text-xs font-semibold text-white truncate">{step.title}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. GENERATED CODE VIEWER & VERIFICATION */}
      {currentJob && currentJob.files && currentJob.files.length > 0 && (
        <div className="bg-tcs-card border border-tcs-border rounded-2xl p-6 shadow-xl space-y-4 animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-tcs-border pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-white">Código Fuente Quarkus Fabricado</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase">
                  ✓ Generación Exitosa
                </span>
              </div>
              <p className="text-xs text-tcs-muted mt-0.5">
                Archivos compilables generados con Java {javaVersion} y Quarkus {quarkusVersion}. Puedes editar archivos directamente antes de empaquetar.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setIsVerifierOpen(true)}
              className="py-2.5 px-5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded-xl shadow-lg flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>🛡️ Verificar en Sandbox y Descargar ZIP</span>
            </button>
          </div>

          <CodeViewer
            files={currentJob.files}
            onSaveFiles={handleSaveFiles}
            onVerifySandbox={() => setIsVerifierOpen(true)}
            isSaving={isSavingFiles}
          />
        </div>
      )}

      {/* Verification and Packager Modal */}
      {currentJob && (
        <VerifierModal
          isOpen={isVerifierOpen}
          onClose={() => setIsVerifierOpen(false)}
          clientCode={currentJob.client_id || (currentJob as any).client_code || selectedClient}
          jobId={currentJob.job_id || (currentJob as any).id}
          files={currentJob.files}
        />
      )}
    </div>
  );
};
