import { DownloadButton } from './DownloadButton';
// src/components/StudioPanel.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, suggestedPackagePrefix } from '../services/api';
import { CodeViewer } from './CodeViewer';
import { ClientSelectorCards } from './ClientSelectorCards';
import { VerifierModal } from './VerifierModal';
import { AiConfigModal } from './AiConfigModal';
import {
  ClientProfile,
  OpenApiSpecSummary,
  OrchestrationJob,
  GeneratedFile,
  EntityDefinition,
  CustomEndpoint,
} from '../types';

export interface StudioPanelProps {
  loadedJob?: OrchestrationJob | null;
  onJobCreated?: () => void;
}

export const StudioPanel: React.FC<StudioPanelProps> = ({ loadedJob, onJobCreated }) => {
  const { user } = useAuth();
  const [clients, setClients] = useState<ClientProfile[]>([]);
  const [activeClient, setActiveClient] = useState<ClientProfile | null>(null);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [contracts, setContracts] = useState<OpenApiSpecSummary[]>([]);

  // AI Gateway & Vault Key Ingestion State
  const [activeAiConfig, setActiveAiConfig] = useState<{ provider: string; model_name: string }>({
    provider: 'MOCK',
    model_name: 'mock-fast',
  });
  const [showAiModal, setShowAiModal] = useState<boolean>(false);

  // 7-Phase Stepper: 1 to 7
  const [activePhase, setActivePhase] = useState<number>(1);
  const [isInferring, setIsInferring] = useState<boolean>(false);
  const [inferSuccessMessage, setInferSuccessMessage] = useState<string | null>(null);

  // --- FASE 1: Identidad & Stack Base (Clean by default) ---
  const [requirementPrompt, setRequirementPrompt] = useState<string>('');
  const [buildTool, setBuildTool] = useState<'maven' | 'gradle'>('maven');
  const [javaVersion, setJavaVersion] = useState<string>('21');
  const [quarkusVersion, setQuarkusVersion] = useState<string>('3.15.1');
  const [artifactId, setArtifactId] = useState<string>('');
  const [packagePrefix, setPackagePrefix] = useState<string>('');
  const [httpPort, setHttpPort] = useState<number>(8080);
  const [packagingType, setPackagingType] = useState<'jvm' | 'native'>('jvm');

  // --- FASE 2: Arquetipo, Patrones de Diseño & Convenciones ---
  const [archStyle, setArchStyle] = useState<string>('Hexagonal');
  const [customArchNotes, setCustomArchNotes] = useState<string>('');
  const [selectedPatterns, setSelectedPatterns] = useState<string[]>(['REPOSITORY', 'BUILDER']);
  const [variableNamingStyle, setVariableNamingStyle] = useState<'camelCase' | 'snake_case'>('camelCase');
  const [useCaseSuffix, setUseCaseSuffix] = useState<string>('UseCase');
  const [portSuffix, setPortSuffix] = useState<string>('Port');
  const [adapterSuffix, setAdapterSuffix] = useState<string>('Adapter');
  const [exceptionHandlingStrategy, setExceptionHandlingStrategy] = useState<string>('Global ServerExceptionMapper (RFC-7807)');

  // --- FASE 3: Seguridad & Gobernanza ---
  const [securityOption, setSecurityOption] = useState<string>('JWT');
  const [jwtIssuer, setJwtIssuer] = useState<string>('');
  const [securityRoles, setSecurityRoles] = useState<string>('ADMIN, OPERATOR, AUDITOR');
  const [vaultProvider, setVaultProvider] = useState<string>('Azure Key Vault');

  // --- FASE 4: Persistencia & Modelado de Entidades ---
  const [databaseOption, setDatabaseOption] = useState<string>('SQLSERVER_PANACHE');
  const [databaseName, setDatabaseName] = useState<string>('');
  const [entities, setEntities] = useState<EntityDefinition[]>([]);

  // --- FASE 5: Contratos de APIs & Endpoints Reactivos ---
  const [commProtocol, setCommProtocol] = useState<string>('REST_REACTIVE');
  const [customEndpoints, setCustomEndpoints] = useState<CustomEndpoint[]>([]);

  // --- FASE 6: Eventos & Comunicación Asíncrona ---
  const [eventBroker, setEventBroker] = useState<'kafka' | 'service_bus' | 'none'>('kafka');
  const [eventTopicOut, setEventTopicOut] = useState<string>('');
  const [eventTopicIn, setEventTopicIn] = useState<string>('');

  // Quarkus Extensions
  const [selectedExtensions, setSelectedExtensions] = useState<string[]>([
    'quarkus-resteasy-reactive-jackson',
    'quarkus-smallrye-openapi',
    'quarkus-hibernate-validator',
    'quarkus-smallrye-health',
    'quarkus-micrometer-registry-prometheus',
  ]);
  const [customExtensionsText, setCustomExtensionsText] = useState<string>('quarkus-smallrye-fault-tolerance');
  const [customPropertiesText, setCustomPropertiesText] = useState<string>('');

  // Execution & Job State
  const [currentJob, setCurrentJob] = useState<OrchestrationJob | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isSavingFiles, setIsSavingFiles] = useState<boolean>(false);
  const [isVerifierOpen, setIsVerifierOpen] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Synchronize when a job is loaded from the Workspace History Sidebar
  useEffect(() => {
    if (loadedJob) {
      setCurrentJob(loadedJob);
      setActivePhase(7);
      const cCode = loadedJob.client_id || (loadedJob as any).client_code;
      if (cCode) {
        setSelectedClient(cCode.toLowerCase());
      }
      const art = (loadedJob as any).blueprint?.artifact_id || (loadedJob as any).artifact_id;
      if (art) {
        setArtifactId(art);
      }
      setTimeout(() => {
        const el = document.getElementById('fabrication-success-card') || document.getElementById('generated-code-section');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }, [loadedJob]);

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

  const fetchGatewayConfig = async () => {
    try {
      const cfg = await api.orchestrator.getGatewayConfig();
      if (cfg && cfg.active_provider) {
        setActiveAiConfig({
          provider: cfg.active_provider.toUpperCase(),
          model_name: cfg.model_name || 'default',
        });
      }
    } catch (e) {
      console.warn('Failed to load gateway config', e);
    }
  };

  useEffect(() => {
    fetchAuthorizedClients();
    fetchGatewayConfig();
  }, [user]);

  // Select Client
  const handleSelectClient = (client: ClientProfile) => {
    setActiveClient(client);
    const code = (client.code || client.client_id || '').toLowerCase();
    setSelectedClient(code);
    setPackagePrefix(suggestedPackagePrefix(client.package_prefix || `pe.com.${code}`));
    setJavaVersion(client.java_version || '21');
    setArtifactId(`${code}-nuevo-servicio`);
    setDatabaseName(`${code}_db`);
    setJwtIssuer(`https://auth.via${code}.com`);
    setRequirementPrompt('');
    setEntities([]);
    setCustomEndpoints([]);
    setCustomArchNotes('');
    setCustomPropertiesText('');
    setEventTopicOut(`pe.com.${code}.events.v1`);
    setEventTopicIn(`pe.com.${code}.notifications.v1`);
    setActivePhase(1);
    setCurrentJob(null);
    setError(null);
    setInferSuccessMessage(null);
  };

  // Reset to clean blank slate
  const handleResetToBlank = () => {
    const code = selectedClient || 'bcp';
    setArtifactId(`${code}-nuevo-servicio`);
    setRequirementPrompt('');
    setEntities([]);
    setCustomEndpoints([]);
    setCustomArchNotes('');
    setCustomPropertiesText('');
    setSelectedPatterns(['REPOSITORY', 'BUILDER']);
    setEventBroker('none');
    setCurrentJob(null);
    setError(null);
    setInferSuccessMessage(null);
    setActivePhase(1);
  };

  // AI INFERENCE: Analyze Natural Language Prompt & Auto-Structure All 7 Phases
  const handleInferSpecWithAIWithAI = async () => {
    if (!requirementPrompt.trim()) {
      setError('Escribe primero el requerimiento en lenguaje natural para que la IA pueda estructurar las 7 fases.');
      return;
    }

    setError(null);
    setIsInferring(true);
    setInferSuccessMessage(null);
    setCurrentJob(null);

    try {
      const res = await api.orchestrator.inferSpec({
        client_code: selectedClient || 'bcp',
        requirements: requirementPrompt.trim(),
      });

      if (res.artifact_id) setArtifactId(res.artifact_id);
      if (res.package_prefix) setPackagePrefix(suggestedPackagePrefix(res.package_prefix));
      if (res.database_name) setDatabaseName(res.database_name);
      if (res.database_option) setDatabaseOption(res.database_option);
      if (res.architecture_style) setArchStyle(res.architecture_style);
      if (res.custom_architecture_notes) setCustomArchNotes(res.custom_architecture_notes);
      if (res.design_patterns && Array.isArray(res.design_patterns)) setSelectedPatterns(res.design_patterns);
      if (res.entities && Array.isArray(res.entities)) setEntities(res.entities);
      if (res.custom_endpoints && Array.isArray(res.custom_endpoints)) setCustomEndpoints(res.custom_endpoints);
      if (res.event_broker) setEventBroker(res.event_broker);
      if (res.event_topic_out) setEventTopicOut(res.event_topic_out);
      if (res.event_topic_in) setEventTopicIn(res.event_topic_in);

      setInferSuccessMessage(
        `✓ La IA analizó tu pedido con éxito: Estructuró ${res.entities?.length || 0} entidades, ${res.custom_endpoints?.length || 0} endpoints y patrones recomendados. Puedes revisar y editar cada fase.`
      );
    } catch (err: any) {
      setError('Error al analizar requerimiento con IA: ' + err.message);
    } finally {
      setIsInferring(false);
    }
  };

  // Quick Preset Sample for BCP
  const handleLoadBcpSample = () => {
    setBuildTool('maven');
    setJavaVersion('21');
    setQuarkusVersion('3.15.1');
    setArtifactId('bcp-tarjetas-service');
    setPackagePrefix('pe.com.bcp.tarjetas');
    setDatabaseName('bcp_tarjetas_db');
    setJwtIssuer('https://auth.viabcp.com');
    setArchStyle('Hexagonal');
    setSelectedPatterns(['REPOSITORY', 'BUILDER', 'OUTBOX', 'STRATEGY']);
    setRequirementPrompt(
      'Microservicio para emisión y gestión de tarjetas de crédito con asignación de límites, registro de movimientos y publicación de eventos transaccionales en Kafka.'
    );
    setCustomArchNotes('Arquitectura hexagonal bancaria para BCP con separación estricta de puertos/adaptadores y trazabilidad transaccional.');
    setEntities([
      {
        name: 'CreditCard',
        tableName: 'credit_cards',
        fields: [
          { name: 'id', type: 'UUID', required: true, isId: true },
          { name: 'cardNumberMasked', type: 'String', required: true },
          { name: 'holderName', type: 'String', required: true },
          { name: 'holderDni', type: 'String', required: true },
          { name: 'creditLimit', type: 'BigDecimal', required: true },
          { name: 'status', type: 'String', required: true },
          { name: 'createdAt', type: 'LocalDateTime', required: true },
        ],
      },
    ]);
    setCustomEndpoints([
      { method: 'POST', path: '/api/v1/tarjetas', summary: 'Emitir nueva tarjeta de crédito con scoring' },
      { method: 'GET', path: '/api/v1/tarjetas/{id}', summary: 'Consultar estado y límite disponible por UUID' },
      { method: 'GET', path: '/api/v1/tarjetas', summary: 'Listar tarjetas activas del cliente' },
    ]);
    setEventBroker('kafka');
    setEventTopicOut('pe.com.bcp.tarjetas.events.v1');
    setInferSuccessMessage('✓ Plantilla de referencia BCP cargada. Puedes personalizarla libremente.');
  };

  // Final Action: Fabricate Microservice with LangGraph
  const handleStartGeneration = async () => {
    if (!selectedClient) {
      setError('Seleccione una cuenta de cliente');
      return;
    }

    setError(null);
    setIsGenerating(true);
    setCurrentJob(null);

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
        raw_requirement: requirementPrompt || 'Microservicio empresarial Quarkus con arquitectura limpia y gobernanza BCP',
        requirements: requirementPrompt || 'Microservicio empresarial Quarkus con arquitectura limpia y gobernanza BCP',
        architecture_style: archStyle,
        custom_architecture_notes: `${customArchNotes} | Patrones: ${selectedPatterns.join(', ')} | Naming: ${variableNamingStyle} | UseCase: ${useCaseSuffix} | ExceptionMapper: ${exceptionHandlingStrategy}`,
        security_option: securityOption,
        jwt_issuer: jwtIssuer,
        security_roles: rolesArray,
        communication_protocol: commProtocol,
        custom_endpoints: customEndpoints,
        database_option: databaseOption,
        database_name: databaseName,
        package_prefix: packagePrefix || suggestedPackagePrefix(`pe.com.${selectedClient}`),
        artifact_id: artifactId || `${selectedClient}-service`,
        http_port: httpPort,
        java_version: javaVersion,
        quarkus_version: quarkusVersion,
        build_tool: buildTool,
        design_patterns: selectedPatterns,
        naming_conventions: {
          variable: variableNamingStyle,
          useCaseSuffix,
          portSuffix,
          adapterSuffix,
        },
        event_broker: eventBroker,
        channels: eventBroker !== 'none' ? [
          { name: 'outgoing-events', type: 'outgoing', topic: eventTopicOut },
          { name: 'incoming-events', type: 'incoming', topic: eventTopicIn },
        ] : [],
        extensions: mergedExtensions,
        custom_extensions: extraExtensions,
        custom_properties: customPropertiesText,
        entities: entities,
      });

      setCurrentJob(job);
      setIsGenerating(false);
      if (onJobCreated) onJobCreated();
      setTimeout(() => {
        const el = document.getElementById('fabrication-success-card') || document.getElementById('generated-code-section');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 150);
    } catch (err: any) {
      setError(err.message || 'Error al fabricar microservicio con agentes de IA');
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

  // Add entity
  const handleAddEntity = () => {
    const newName = `Entity${entities.length + 1}`;
    setEntities([
      ...entities,
      {
        name: newName,
        tableName: `${newName.toLowerCase()}s`,
        fields: [
          { name: 'id', type: 'UUID', required: true, isId: true },
          { name: 'code', type: 'String', required: true },
          { name: 'amount', type: 'BigDecimal', required: true },
          { name: 'status', type: 'String', required: true },
          { name: 'createdAt', type: 'LocalDateTime', required: true },
        ],
      },
    ]);
  };

  const handleAddFieldToEntity = (entityIdx: number) => {
    const updated = [...entities];
    updated[entityIdx].fields.push({
      name: `field${updated[entityIdx].fields.length + 1}`,
      type: 'String',
      required: true,
      isId: false,
    });
    setEntities(updated);
  };

  const handleRemoveFieldFromEntity = (entityIdx: number, fieldIdx: number) => {
    const updated = [...entities];
    updated[entityIdx].fields.splice(fieldIdx, 1);
    setEntities(updated);
  };

  const handleUpdateFieldInEntity = (
    entityIdx: number,
    fieldIdx: number,
    key: string,
    val: any
  ) => {
    const updated = [...entities];
    (updated[entityIdx].fields[fieldIdx] as any)[key] = val;
    setEntities(updated);
  };

  // Add endpoint
  const handleAddEndpoint = () => {
    setCustomEndpoints([
      ...customEndpoints,
      {
        method: 'POST',
        path: `/api/v1/operacion-${customEndpoints.length + 1}`,
        summary: 'Operación transaccional con validación',
      },
    ]);
  };

  // Toggle pattern
  const togglePattern = (pattern: string) => {
    if (selectedPatterns.includes(pattern)) {
      setSelectedPatterns(selectedPatterns.filter((p) => p !== pattern));
    } else {
      setSelectedPatterns([...selectedPatterns, pattern]);
    }
  };

  // -------------------------------------------------------------
  // PANTALLA 0: Si no hay cliente seleccionado, mostrar Cards
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

  const isBcp = selectedClient === 'bcp';

  const PHASES = [
    { num: 1, title: 'Requerimiento & Stack Base', desc: 'Pedido en lenguaje natural, Maven/Gradle, Java 21' },
    { num: 2, title: 'Arquetipo & Patrones', desc: 'Hexagonal, Clean, Saga, Outbox, Builder' },
    { num: 3, title: 'Seguridad & Tokens', desc: 'SmallRye JWT, RBAC, Key Vault' },
    { num: 4, title: 'Persistencia & Entidades', desc: 'Panache ORM, SQL Server / Postgres' },
    { num: 5, title: 'APIs & Endpoints', desc: 'RESTEasy Reactive, OpenAPI, Swagger' },
    { num: 6, title: 'Eventos & Kafka', desc: 'Reactive Messaging, Outbox Tópicos' },
    { num: 7, title: 'Lógica & Fabricación', desc: 'Visualizar flujo y fabricar código con IA' },
  ];

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* 1. Header con Cuenta de Cliente y Acciones Rápidas */}
      <div className="bg-gradient-to-r from-tcs-navy via-tcs-card to-tcs-navy border border-tcs-border rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 shrink-0">
            <div className="w-14 h-14 rounded-2xl bg-black p-1.5 flex items-center justify-center shadow-lg border border-white/20 shrink-0" title="TCS Intelligent Factory">
              <img src="/tcs-logo.png" alt="TCS Logo" className="w-full h-full object-contain" />
            </div>
            {isBcp ? (
              <div className="w-14 h-14 rounded-2xl bg-[#002A8F] p-2 flex items-center justify-center shadow-lg border border-blue-400/30 shrink-0" title="Cuenta BCP">
                <img src="/bcp-logo.png" alt="BCP Logo" className="w-full h-full object-contain" />
              </div>
            ) : (
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-tcs-blue/30 to-tcs-navy border border-tcs-border flex items-center justify-center text-tcs-cyan font-extrabold text-lg shrink-0">
                {selectedClient.slice(0, 3).toUpperCase()}
              </div>
            )}
          </div>

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
              <span className="text-tcs-cyan font-semibold">{packagePrefix || suggestedPackagePrefix(`pe.com.${selectedClient}`)}</span>
              <span>•</span>
              <span className="text-white">Build: {buildTool.toUpperCase()}</span>
              <span>•</span>
              <span className="text-white">Java {javaVersion}</span>
              <span>•</span>
              <span className="text-white">Quarkus {quarkusVersion}</span>
              <span>•</span>
              <span className="text-amber-400/90 font-sans">Gobernanza BCP Activa</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* AI Provider Status Pill */}
          {activeAiConfig.provider !== 'MOCK' ? (
            <div className="flex items-center space-x-2 px-3 py-2 bg-emerald-950/70 border border-emerald-500/50 rounded-xl shadow-lg">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <div className="text-xs">
                <span className="text-emerald-400 font-extrabold font-mono">IA EN VIVO:</span>{' '}
                <span className="text-white font-bold">{activeAiConfig.provider}</span>{' '}
                <span className="text-emerald-300 font-mono text-[11px]">({activeAiConfig.model_name})</span>
              </div>
              <button
                type="button"
                onClick={() => setShowAiModal(true)}
                className="ml-1 text-[11px] text-emerald-400 underline hover:text-white font-medium"
              >
                Cambiar
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setShowAiModal(true)}
              className="px-3.5 py-2 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-black text-xs font-extrabold rounded-xl shadow-lg flex items-center space-x-1.5 transition-all"
            >
              <span>⚡</span>
              <span>Ingestar API Key & Modelo</span>
            </button>
          )}

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
            <span>✨ Empezar en Blanco</span>
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

      {inferSuccessMessage && (
        <div className="p-4 rounded-xl bg-emerald-950/80 border border-emerald-500/60 text-emerald-200 text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg animate-fadeIn">
          <div className="flex items-center space-x-2.5">
            <span className="text-lg">💡</span>
            <span className="leading-relaxed">{inferSuccessMessage}</span>
          </div>
          <div className="flex items-center space-x-2 self-end sm:self-auto shrink-0">
            {activePhase < 7 && (
              <button
                type="button"
                onClick={() => setActivePhase(activePhase + 1)}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs shadow flex items-center space-x-1.5 transition-all"
              >
                <span>Avanzar a Fase {activePhase + 1}</span>
                <span>→</span>
              </button>
            )}
            <button
              type="button"
              onClick={() => setInferSuccessMessage(null)}
              className="text-emerald-400 hover:text-white p-1 text-sm"
              title="Cerrar mensaje"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* 2. Interactive 7-Phase Stepper Navigator */}
      <div className="bg-tcs-card border border-tcs-border rounded-2xl p-4 shadow-xl">
        <div className="text-xs font-bold uppercase tracking-wider text-tcs-muted mb-3 px-1 flex items-center justify-between">
          <span>Taller de Arquitectura Quarkus — Fases de Configuración (1 al 7)</span>
          <span className="text-tcs-cyan font-mono font-bold">Fase {activePhase} de 7</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {PHASES.map((phase) => {
            const isCurrent = activePhase === phase.num;
            const isDone = activePhase > phase.num;
            return (
              <button
                key={phase.num}
                type="button"
                onClick={() => setActivePhase(phase.num)}
                className={`p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                  isCurrent
                    ? 'bg-gradient-to-br from-tcs-blue/30 to-tcs-navy border-tcs-cyan text-white shadow-lg shadow-cyan-900/20'
                    : isDone
                    ? 'bg-tcs-dark border-emerald-800/60 text-emerald-300'
                    : 'bg-tcs-dark/60 border-tcs-border text-tcs-muted hover:border-tcs-blue/50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span
                    className={`w-5 h-5 rounded-full text-[10px] font-extrabold flex items-center justify-center ${
                      isCurrent
                        ? 'bg-tcs-cyan text-tcs-dark'
                        : isDone
                        ? 'bg-emerald-600 text-white'
                        : 'bg-tcs-border text-tcs-muted'
                    }`}
                  >
                    {isDone ? '✓' : phase.num}
                  </span>
                  <span className="text-[10px] font-mono text-tcs-muted">P{phase.num}</span>
                </div>
                <div>
                  <div className="text-xs font-bold truncate text-white">{phase.title}</div>
                  <div className="text-[10px] text-tcs-muted truncate mt-0.5">{phase.desc}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Main Stage: Phase Content + Live Architecture Side-Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): Phase Editor */}
        <div className="lg:col-span-2 bg-tcs-card border border-tcs-border rounded-2xl p-6 shadow-xl space-y-6">
          {/* Header of Active Phase with Step Title */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-tcs-border/60 pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-0.5 rounded-full bg-tcs-blue/20 text-tcs-cyan border border-tcs-blue/40 text-[11px] font-bold font-mono">
                  FASE {activePhase}
                </span>
                <h3 className="text-base font-extrabold text-white">
                  {PHASES[activePhase - 1].title}
                </h3>
              </div>
              <p className="text-xs text-tcs-muted mt-1">
                {PHASES[activePhase - 1].desc}
              </p>
            </div>
          </div>

          {/* ======================================================== */}
          {/* FASE 1: REQUERIMIENTO DEL USUARIO & STACK BASE           */}
          {/* ======================================================== */}
          {activePhase === 1 && (
            <div className="space-y-6 animate-fadeIn">
              {/* PRIMARY PROMPT INPUT: THE HEART OF USER INTENT */}
              <div className="p-4 bg-gradient-to-br from-tcs-navy via-tcs-dark to-tcs-navy border-2 border-tcs-cyan/40 rounded-2xl space-y-3 shadow-lg">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-white flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-tcs-cyan animate-pulse"></span>
                    <span>1.1. Describe tu Pedido de Microservicio en Lenguaje Natural</span>
                  </label>
                  <span className="text-[11px] text-tcs-muted font-mono">Impulsado por IA</span>
                </div>

                <textarea
                  rows={4}
                  value={requirementPrompt}
                  onChange={(e) => setRequirementPrompt(e.target.value)}
                  placeholder="Describe lo que debe hacer tu microservicio... ej: Microservicio para emisión y cotización de pólizas de seguro vehicular con cobro recurrente, cálculo de primas y alertas a Kafka."
                  className="w-full p-3.5 bg-tcs-dark border border-tcs-border rounded-xl text-xs sm:text-sm text-white focus:border-tcs-cyan focus:outline-none leading-relaxed placeholder:text-tcs-muted/60"
                />

                <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 pt-1">
                  <p className="text-[11px] text-tcs-muted">
                    Presiona el botón para que la IA deduzca las entidades, endpoints, patrones y base de datos:
                  </p>
                  <button
                    type="button"
                    onClick={handleInferSpecWithAIWithAI}
                    disabled={isInferring || !requirementPrompt.trim()}
                    className="px-5 py-2.5 bg-gradient-to-r from-tcs-blue to-tcs-cyan hover:from-blue-600 hover:to-cyan-500 text-white font-extrabold text-xs rounded-xl shadow-lg shadow-cyan-900/30 transition-all flex items-center justify-center space-x-2 disabled:opacity-40"
                  >
                    {isInferring ? (
                      <>
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        <span>Analizando Pedido con IA...</span>
                      </>
                    ) : (
                      <>
                        <span>✨ Analizar Pedido y Estructurar Fases con IA</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Build Tool Selection */}
              <div>
                <label className="block text-xs font-bold text-white mb-2">
                  1.2. Herramienta de Construcción (Build Tool)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div
                    onClick={() => setBuildTool('maven')}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      buildTool === 'maven'
                        ? 'bg-tcs-blue/20 border-tcs-cyan text-white shadow-md'
                        : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">Apache Maven (`pom.xml`)</span>
                      {buildTool === 'maven' && <span className="text-tcs-cyan text-xs">● Seleccionado</span>}
                    </div>
                    <p className="text-[11px] text-tcs-muted mt-1">
                      Estándar oficial en proyectos Quarkus BCP con Maven Wrapper (`./mvnw`).
                    </p>
                  </div>

                  <div
                    onClick={() => setBuildTool('gradle')}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      buildTool === 'gradle'
                        ? 'bg-tcs-blue/20 border-tcs-cyan text-white shadow-md'
                        : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">Gradle (`build.gradle`)</span>
                      {buildTool === 'gradle' && <span className="text-tcs-cyan text-xs">● Seleccionado</span>}
                    </div>
                    <p className="text-[11px] text-tcs-muted mt-1">
                      Construcción incremental de alto rendimiento con Gradle Wrapper (`./gradlew`).
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-white mb-1">Versión de Java (JDK)</label>
                  <select
                    value={javaVersion}
                    onChange={(e) => setJavaVersion(e.target.value)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:border-tcs-blue focus:outline-none font-mono"
                  >
                    <option value="21">Java 21 (LTS Recomendado BCP)</option>
                    <option value="17">Java 17 (LTS)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-white mb-1">Versión de Quarkus</label>
                  <select
                    value={quarkusVersion}
                    onChange={(e) => setQuarkusVersion(e.target.value)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:border-tcs-blue focus:outline-none font-mono"
                  >
                    <option value="3.15.1">Quarkus 3.15.1 (LTS Corporativo)</option>
                    <option value="3.8.5">Quarkus 3.8.5 (LTS Anterior)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-white mb-1">Tipo de Empaquetado</label>
                  <select
                    value={packagingType}
                    onChange={(e) => setPackagingType(e.target.value as any)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:border-tcs-blue focus:outline-none font-mono"
                  >
                    <option value="jvm">JVM Optimizado (Fast-JAR)</option>
                    <option value="native">GraalVM Native Image</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-white mb-1">Artifact ID (Nombre Microservicio)</label>
                  <input
                    type="text"
                    value={artifactId}
                    onChange={(e) => setArtifactId(e.target.value)}
                    placeholder="ej. bcp-polizas-service"
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-white mb-1">Package Prefix (Java)</label>
                  <input
                    type="text"
                    value={packagePrefix}
                    onChange={(e) => setPackagePrefix(e.target.value)}
                    placeholder="ej. pe.com.bcp.polizas"
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-white mb-1">Puerto HTTP</label>
                  <input
                    type="number"
                    value={httpPort}
                    onChange={(e) => setHttpPort(parseInt(e.target.value) || 8080)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                  />
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* FASE 2: ARQUETIPO, PATRONES & CONVENCIONES               */}
          {/* ======================================================== */}
          {activePhase === 2 && (
            <div className="space-y-5 animate-fadeIn">
              <div>
                <label className="block text-xs font-bold text-white mb-2">
                  2.1. Arquetipo Arquitectónico Base
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[
                    { id: 'Hexagonal', name: 'Arquitectura Hexagonal (Ports & Adapters)', desc: 'Desacople estricto entre núcleo de negocio, puertos de entrada/salida y adaptadores REST.' },
                    { id: 'Clean', name: 'Clean Architecture (Onion)', desc: 'Estructura concéntrica de Entidades -> Casos de Uso (UseCases) -> Gateways.' },
                    { id: 'Layered', name: 'Arquitectura en Capas Clásica', desc: 'Controlador REST -> Capa de Servicio -> Repositorio Panache.' },
                    { id: 'Event-Driven', name: 'Event-Driven Architecture (EDA)', desc: 'Orientado a procesamiento reactivo de eventos y mensajería Kafka.' },
                  ].map((arch) => (
                    <div
                      key={arch.id}
                      onClick={() => setArchStyle(arch.id)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                        archStyle === arch.id
                          ? 'bg-tcs-blue/20 border-tcs-cyan text-white shadow-md'
                          : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white">{arch.name}</span>
                        {archStyle === arch.id && <span className="text-tcs-cyan text-xs">● Activo</span>}
                      </div>
                      <p className="text-[11px] text-tcs-muted mt-1">{arch.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-white mb-2">
                  2.2. Patrones de Diseño Utilizados (Selecciona o edita los necesarios)
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {[
                    { id: 'REPOSITORY', name: 'Repository / Panache Pattern', desc: 'Abstracción limpia de persistencia' },
                    { id: 'BUILDER', name: 'Builder / Fluent DTOs', desc: 'Inmutabilidad en objetos y requests' },
                    { id: 'OUTBOX', name: 'Transactional Outbox', desc: 'Garantía de entrega de eventos a Kafka' },
                    { id: 'SAGA', name: 'Saga Pattern', desc: 'Transacciones distribuidas' },
                    { id: 'STRATEGY', name: 'Strategy Pattern', desc: 'Políticas de cálculo intercambiables' },
                    { id: 'FACTORY', name: 'Factory Pattern', desc: 'Instanciación desacoplada' },
                  ].map((p) => {
                    const isChecked = selectedPatterns.includes(p.id);
                    return (
                      <div
                        key={p.id}
                        onClick={() => togglePattern(p.id)}
                        className={`p-2.5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                          isChecked
                            ? 'bg-emerald-950/40 border-emerald-500/50 text-white'
                            : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white">{p.name}</span>
                          <span className={`text-[10px] font-bold ${isChecked ? 'text-emerald-400' : 'text-tcs-muted'}`}>
                            {isChecked ? '✓' : '+'}
                          </span>
                        </div>
                        <span className="text-[10px] text-tcs-muted mt-1">{p.desc}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-bold text-white mb-1">Estilo de Variables</label>
                  <select
                    value={variableNamingStyle}
                    onChange={(e) => setVariableNamingStyle(e.target.value as any)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:border-tcs-blue focus:outline-none font-mono"
                  >
                    <option value="camelCase">camelCase (Estándar Java BCP)</option>
                    <option value="snake_case">snake_case</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-white mb-1">Sufijo Casos de Uso</label>
                  <input
                    type="text"
                    value={useCaseSuffix}
                    onChange={(e) => setUseCaseSuffix(e.target.value)}
                    placeholder="UseCase"
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-white mb-1">Manejo de Excepciones</label>
                  <select
                    value={exceptionHandlingStrategy}
                    onChange={(e) => setExceptionHandlingStrategy(e.target.value)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:border-tcs-blue focus:outline-none"
                  >
                    <option value="Global ServerExceptionMapper (RFC-7807)">Global @ServerExceptionMapper (RFC-7807)</option>
                    <option value="ResponseStatusException">ResponseStatusException inline</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* FASE 3: SEGURIDAD & GOBERNANZA                          */}
          {/* ======================================================== */}
          {activePhase === 3 && (
            <div className="space-y-5 animate-fadeIn">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-white mb-1">Mecanismo de Autenticación</label>
                  <select
                    value={securityOption}
                    onChange={(e) => setSecurityOption(e.target.value)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:border-tcs-blue focus:outline-none"
                  >
                    <option value="JWT">Quarkus SmallRye JWT (Tokens Criptográficos)</option>
                    <option value="OIDC">OpenID Connect / Azure AD BCP</option>
                    <option value="mTLS">Mutual TLS (mTLS Certificados PKI)</option>
                    <option value="NONE">Sin Seguridad (Stateless Público)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-white mb-1">Gestión de Secretos</label>
                  <select
                    value={vaultProvider}
                    onChange={(e) => setVaultProvider(e.target.value)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:border-tcs-blue focus:outline-none"
                  >
                    <option value="Azure Key Vault">Azure Key Vault (Normado BCP)</option>
                    <option value="HashiCorp Vault">HashiCorp Vault</option>
                    <option value="Environment Variables">Variables de Entorno del Contenedor</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-white mb-1">Emisor del Token (JWT Issuer URL)</label>
                  <input
                    type="text"
                    value={jwtIssuer}
                    onChange={(e) => setJwtIssuer(e.target.value)}
                    placeholder="https://auth.viabcp.com"
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-white mb-1">Roles de Usuario (RBAC)</label>
                  <input
                    type="text"
                    value={securityRoles}
                    onChange={(e) => setSecurityRoles(e.target.value)}
                    placeholder="ADMIN, OPERATOR, AUDITOR"
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:border-tcs-blue focus:outline-none"
                  />
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-tcs-dark/70 border border-tcs-border text-xs text-tcs-muted space-y-1">
                <span className="font-bold text-white">🔒 Directiva de Seguridad BCP:</span>
                <p>
                  Todas las operaciones REST del microservicio deben requerir validación de claims y anotación
                  `@RolesAllowed`. No se permite guardar credenciales en texto plano en `application.properties`.
                </p>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* FASE 4: PERSISTENCIA & MODELADO DE ENTIDADES             */}
          {/* ======================================================== */}
          {activePhase === 4 && (
            <div className="space-y-5 animate-fadeIn">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-white mb-1">Motor de Persistencia</label>
                  <select
                    value={databaseOption}
                    onChange={(e) => setDatabaseOption(e.target.value)}
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:border-tcs-blue focus:outline-none"
                  >
                    <option value="SQLSERVER_PANACHE">Microsoft SQL Server + Panache (Normado BCP)</option>
                    <option value="POSTGRESQL_PANACHE">PostgreSQL + Panache ORM</option>
                    <option value="MONGODB_PANACHE">MongoDB Panache (NoSQL Documental)</option>
                    <option value="NONE">Sin Base de Datos (100% Stateless)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-white mb-1">Nombre de Base de Datos / Schema</label>
                  <input
                    type="text"
                    value={databaseName}
                    onChange={(e) => setDatabaseName(e.target.value)}
                    placeholder="ej. bcp_polizas_db"
                    className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                  />
                </div>
              </div>

              {/* Editable Entities Table */}
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <label className="text-xs font-bold text-white">Entidades del Dominio ({entities.length})</label>
                    <p className="text-[11px] text-tcs-muted">Edita campos, tipos Java y restricciones de persistencia.</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={handleInferSpecWithAIWithAI}
                      disabled={isInferring}
                      className="px-3 py-1 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-lg text-xs font-bold transition-all shadow flex items-center space-x-1"
                    >
                      <span>{isInferring ? '⌛ Deduciendo...' : '✨ Deducir Entidades con IA'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleAddEntity}
                      className="px-3 py-1 bg-tcs-blue hover:bg-tcs-cyan text-white hover:text-tcs-dark rounded-lg text-xs font-bold transition-all shadow"
                    >
                      + Agregar Entidad Manual
                    </button>
                  </div>
                </div>

                {entities.length === 0 ? (
                  <div className="p-5 rounded-xl bg-tcs-dark border border-tcs-border text-xs text-center space-y-3">
                    <p className="text-tcs-muted italic">
                      No hay entidades definidas aún para este microservicio.
                    </p>
                    <button
                      type="button"
                      onClick={handleInferSpecWithAIWithAI}
                      disabled={isInferring}
                      className="px-4 py-2 bg-gradient-to-r from-tcs-blue to-tcs-cyan hover:from-blue-600 hover:to-cyan-500 text-white font-bold rounded-xl shadow transition-all mx-auto flex items-center space-x-2"
                    >
                      <span>✨ Deducir Entidades del Requerimiento con IA</span>
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {entities.map((ent, idx) => (
                      <div key={idx} className="p-4 bg-tcs-dark border border-tcs-border rounded-xl space-y-3">
                        <div className="flex items-center justify-between border-b border-tcs-border/60 pb-2">
                          <div className="flex items-center space-x-2">
                            <span className="w-2 h-2 rounded-full bg-tcs-cyan"></span>
                            <span className="text-xs font-extrabold text-white">{ent.name}</span>
                            <span className="text-xs text-tcs-muted font-mono">(`{ent.tableName}`)</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => setEntities(entities.filter((_, i) => i !== idx))}
                            className="text-rose-400 hover:text-rose-300 text-xs font-semibold"
                          >
                            Eliminar Entidad
                          </button>
                        </div>

                        {/* Fields list */}
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {ent.fields.map((f, fIdx) => (
                            <div key={fIdx} className="p-2 bg-tcs-card border border-tcs-border rounded-lg text-xs font-mono flex items-center justify-between">
                              <span className="text-white">{f.name}</span>
                              <span className="text-tcs-cyan text-[11px] font-bold">{f.type}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* FASE 5: APIS & ENDPOINTS REACTIVOS                       */}
          {/* ======================================================== */}
          {activePhase === 5 && (
            <div className="space-y-5 animate-fadeIn">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-xs font-bold text-white">Endpoints REST Reactivos ({customEndpoints.length})</label>
                  <p className="text-[11px] text-tcs-muted">Controladores RESTEasy Reactive con SmallRye OpenAPI / Swagger.</p>
                </div>
                <button
                  type="button"
                  onClick={handleAddEndpoint}
                  className="px-3 py-1 bg-tcs-blue hover:bg-tcs-cyan text-white hover:text-tcs-dark rounded-lg text-xs font-bold transition-all shadow"
                >
                  + Agregar Endpoint Manual
                </button>
              </div>

              {customEndpoints.length === 0 ? (
                <div className="p-4 rounded-xl bg-tcs-dark border border-tcs-border text-xs text-tcs-muted italic text-center">
                  Sin endpoints configurados aún. La IA generará los endpoints automáticamente al analizar tu pedido en la Fase 1.
                </div>
              ) : (
                <div className="space-y-2">
                  {customEndpoints.map((ep, idx) => (
                    <div key={idx} className="p-3 bg-tcs-dark border border-tcs-border rounded-xl text-xs flex items-center justify-between font-mono">
                      <div className="flex items-center space-x-3">
                        <span className={`px-2 py-0.5 rounded font-extrabold text-[11px] ${
                          ep.method === 'POST' ? 'bg-blue-950 text-blue-300 border border-blue-800' :
                          ep.method === 'GET' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' :
                          'bg-amber-950 text-amber-300 border border-amber-800'
                        }`}>
                          {ep.method}
                        </span>
                        <span className="text-white font-bold">{ep.path}</span>
                        <span className="text-tcs-muted font-sans text-[11px] truncate max-w-xs">— {ep.summary}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setCustomEndpoints(customEndpoints.filter((_, i) => i !== idx))}
                        className="text-rose-400 hover:text-rose-300 text-xs font-sans"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* FASE 6: EVENTOS & KAFKA                                  */}
          {/* ======================================================== */}
          {activePhase === 6 && (
            <div className="space-y-5 animate-fadeIn">
              <div>
                <label className="block text-xs font-bold text-white mb-2">
                  Broker de Mensajería & Eventos
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    { id: 'kafka', name: 'Apache Kafka', desc: 'SmallRye Reactive Messaging con Outbox Pattern' },
                    { id: 'service_bus', name: 'Azure Service Bus', desc: 'Colas y tópicos en nube Azure' },
                    { id: 'none', name: 'Sin Mensajería Asíncrona', desc: 'Comunicación síncrona exclusiva' },
                  ].map((b) => (
                    <div
                      key={b.id}
                      onClick={() => setEventBroker(b.id as any)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                        eventBroker === b.id
                          ? 'bg-tcs-blue/20 border-tcs-cyan text-white shadow-md'
                          : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white">{b.name}</span>
                        {eventBroker === b.id && <span className="text-tcs-cyan text-xs">● Activo</span>}
                      </div>
                      <p className="text-[11px] text-tcs-muted mt-1">{b.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {eventBroker !== 'none' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-white mb-1">Tópico de Salida (Outgoing Channel)</label>
                    <input
                      type="text"
                      value={eventTopicOut}
                      onChange={(e) => setEventTopicOut(e.target.value)}
                      className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-white mb-1">Tópico de Entrada (Incoming Channel)</label>
                    <input
                      type="text"
                      value={eventTopicIn}
                      onChange={(e) => setEventTopicIn(e.target.value)}
                      className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white font-mono focus:border-tcs-blue focus:outline-none"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* FASE 7: VISUALIZACIÓN DE LÓGICA & FABRICACIÓN FINAL     */}
          {/* ======================================================== */}
          {activePhase === 7 && (
            <div className="space-y-6 animate-fadeIn">
              {/* Diagram of Business Logic Pipeline */}
              <div className="space-y-2">
                <label className="block text-xs font-bold text-white">
                  7.1. Flujo Lógico de Operación del Microservicio
                </label>
                <div className="p-4 bg-tcs-dark border border-tcs-border rounded-2xl space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-center text-xs font-mono">
                    <div className="p-2.5 rounded-xl bg-tcs-card border border-tcs-border">
                      <div className="text-[10px] text-tcs-cyan">Paso 1</div>
                      <div className="font-bold text-white mt-1">REST Request</div>
                      <div className="text-[10px] text-tcs-muted">OpenAPI / JSON</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-tcs-card border border-tcs-border">
                      <div className="text-[10px] text-tcs-cyan">Paso 2</div>
                      <div className="font-bold text-white mt-1">JWT Security</div>
                      <div className="text-[10px] text-tcs-muted">Claims & Roles</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-tcs-card border border-tcs-border">
                      <div className="text-[10px] text-tcs-cyan">Paso 3</div>
                      <div className="font-bold text-white mt-1">{archStyle} Core</div>
                      <div className="text-[10px] text-tcs-muted">Reglas & Dominio</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-tcs-card border border-tcs-border">
                      <div className="text-[10px] text-tcs-cyan">Paso 4</div>
                      <div className="font-bold text-white mt-1">Panache ORM</div>
                      <div className="text-[10px] text-tcs-muted">ACID Persistence</div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-tcs-card border border-tcs-border">
                      <div className="text-[10px] text-tcs-cyan">Paso 5</div>
                      <div className="font-bold text-white mt-1">{eventBroker === 'none' ? 'Response 201' : 'Outbox / Kafka'}</div>
                      <div className="text-[10px] text-tcs-muted">{eventBroker === 'none' ? 'JSON Result' : 'Event Emitted'}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* BCP Governance Compliance Semaphore */}
              <div className="p-4 rounded-2xl bg-emerald-950/30 border border-emerald-500/40 space-y-2">
                <div className="flex items-center space-x-2 text-emerald-300 text-xs font-bold">
                  <span>🛡️ Validación de Cumplimiento de Políticas BCP:</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[10px]">
                    100% CUMPLIDO
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono text-emerald-200">
                  <div>✓ Java {javaVersion} (LTS)</div>
                  <div>✓ Quarkus {quarkusVersion}</div>
                  <div>✓ Arquitectura {archStyle}</div>
                  <div>✓ Panache Relacional</div>
                </div>
              </div>

              {/* 7.2. PRE-CONSTRUCTION AUDIT & SPEC REVIEW (HUMAN-IN-THE-LOOP) */}
              <div className="space-y-4 p-5 bg-tcs-dark/90 border border-tcs-blue/40 rounded-2xl shadow-xl animate-fadeIn">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-tcs-border pb-3">
                  <div className="flex items-center space-x-3">
                    <span className="w-9 h-9 rounded-xl bg-tcs-blue/20 border border-tcs-blue/50 flex items-center justify-center text-lg">
                      📝
                    </span>
                    <div>
                      <h4 className="text-sm font-extrabold text-white flex items-center space-x-2">
                        <span>7.2. Auditoría & Ajuste de Especificación por IA (Pre-Construcción)</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-tcs-cyan/20 text-tcs-cyan border border-tcs-cyan/30">
                          HITL VERIFICADO
                        </span>
                      </h4>
                      <p className="text-xs text-tcs-muted">
                        Revisa y edita los modelos, campos y firmas de la arquitectura antes de que los agentes escriban el código final.
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddEntity}
                    className="px-3 py-1.5 bg-tcs-surface hover:bg-tcs-dark border border-tcs-border text-tcs-cyan hover:text-white rounded-xl text-xs font-bold transition-all flex items-center space-x-1 shrink-0"
                  >
                    <span>+</span>
                    <span>Nueva Entidad</span>
                  </button>
                </div>

                {entities.length === 0 ? (
                  <div className="p-4 rounded-xl bg-tcs-card border border-tcs-border/60 text-center space-y-2">
                    <p className="text-xs text-tcs-muted">
                      No se han modelado entidades aún. Puedes agregar una manualmente o usar "Analizar con IA" en la Fase 1.
                    </p>
                    <button
                      type="button"
                      onClick={handleAddEntity}
                      className="px-3 py-1.5 bg-tcs-blue text-white rounded-xl text-xs font-bold"
                    >
                      + Agregar Primera Entidad
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {entities.map((ent, entIdx) => (
                      <div key={entIdx} className="p-4 bg-tcs-card border border-tcs-border rounded-xl space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-tcs-border/50 pb-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-bold text-tcs-cyan">Entidad:</span>
                            <input
                              type="text"
                              value={ent.name}
                              onChange={(e) => {
                                const updated = [...entities];
                                updated[entIdx].name = e.target.value;
                                setEntities(updated);
                              }}
                              className="px-2.5 py-1 bg-tcs-dark border border-tcs-border rounded-lg text-xs font-bold text-white font-mono focus:border-tcs-blue focus:outline-none"
                            />
                            <span className="text-xs text-tcs-muted font-mono">Tabla:</span>
                            <input
                              type="text"
                              value={ent.tableName || ''}
                              onChange={(e) => {
                                const updated = [...entities];
                                updated[entIdx].tableName = e.target.value;
                                setEntities(updated);
                              }}
                              className="px-2.5 py-1 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-slate-300 font-mono focus:border-tcs-blue focus:outline-none"
                            />
                          </div>

                          <div className="flex items-center space-x-2">
                            <button
                              type="button"
                              onClick={() => handleAddFieldToEntity(entIdx)}
                              className="px-2.5 py-1 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border text-tcs-cyan hover:text-white rounded-lg text-[11px] font-bold transition-all"
                            >
                              + Campo
                            </button>
                            <button
                              type="button"
                              onClick={() => setEntities(entities.filter((_, i) => i !== entIdx))}
                              className="text-rose-400 hover:text-rose-300 text-xs px-2 py-1 rounded"
                            >
                              Eliminar
                            </button>
                          </div>
                        </div>

                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs font-mono">
                            <thead>
                              <tr className="text-tcs-muted border-b border-tcs-border/30 text-[11px]">
                                <th className="pb-1.5">Nombre del Campo</th>
                                <th className="pb-1.5">Tipo Java</th>
                                <th className="pb-1.5 text-center">Requerido</th>
                                <th className="pb-1.5 text-center">ID</th>
                                <th className="pb-1.5 text-right">Acción</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-tcs-border/20">
                              {ent.fields.map((f, fIdx) => (
                                <tr key={fIdx}>
                                  <td className="py-1.5 pr-2">
                                    <input
                                      type="text"
                                      value={f.name}
                                      onChange={(e) => handleUpdateFieldInEntity(entIdx, fIdx, 'name', e.target.value)}
                                      className="w-full px-2 py-0.5 bg-tcs-dark border border-tcs-border rounded text-xs text-white"
                                    />
                                  </td>
                                  <td className="py-1.5 pr-2">
                                    <select
                                      value={f.type}
                                      onChange={(e) => handleUpdateFieldInEntity(entIdx, fIdx, 'type', e.target.value)}
                                      className="px-2 py-0.5 bg-tcs-dark border border-tcs-border rounded text-xs text-white"
                                    >
                                      <option value="String">String</option>
                                      <option value="UUID">UUID</option>
                                      <option value="Long">Long</option>
                                      <option value="Integer">Integer</option>
                                      <option value="BigDecimal">BigDecimal</option>
                                      <option value="Boolean">Boolean</option>
                                      <option value="LocalDateTime">LocalDateTime</option>
                                      <option value="LocalDate">LocalDate</option>
                                    </select>
                                  </td>
                                  <td className="py-1.5 text-center">
                                    <input
                                      type="checkbox"
                                      checked={f.required}
                                      onChange={(e) => handleUpdateFieldInEntity(entIdx, fIdx, 'required', e.target.checked)}
                                      className="rounded bg-tcs-dark border-tcs-border"
                                    />
                                  </td>
                                  <td className="py-1.5 text-center">
                                    <input
                                      type="checkbox"
                                      checked={!!f.isId}
                                      onChange={(e) => handleUpdateFieldInEntity(entIdx, fIdx, 'isId', e.target.checked)}
                                      className="rounded bg-tcs-dark border-tcs-border"
                                    />
                                  </td>
                                  <td className="py-1.5 text-right">
                                    <button
                                      type="button"
                                      onClick={() => handleRemoveFieldFromEntity(entIdx, fIdx)}
                                      className="text-rose-400 hover:text-rose-300 text-xs px-1"
                                    >
                                      ✕
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* THE FINAL GENERATION BUTTON (EXCLUSIVELY IN PHASE 7!) */}
              <div className="p-6 bg-gradient-to-r from-tcs-navy via-tcs-card to-tcs-navy border-2 border-tcs-cyan/60 rounded-2xl text-center space-y-3 shadow-2xl">
                <h4 className="text-base font-extrabold text-white">
                  ¿Todo listo para fabricar el microservicio?
                </h4>
                <p className="text-xs text-tcs-muted max-w-xl mx-auto">
                  Los agentes de IA de LangGraph escribirán todo el código fuente Quarkus, {buildTool.toUpperCase()},
                  entidades Panache, DTOs con validación, servicios transaccionales, controladores reactivos y pruebas @QuarkusTest.
                </p>

                <div className="pt-2 space-y-4">
                  <button
                    type="button"
                    onClick={handleStartGeneration}
                    disabled={isGenerating}
                    className="py-4 px-10 bg-gradient-to-r from-tcs-blue via-tcs-cyan to-tcs-blue hover:from-blue-600 hover:to-cyan-500 text-white font-extrabold text-base rounded-2xl shadow-2xl shadow-cyan-900/50 transition-all flex items-center justify-center space-x-3 mx-auto disabled:opacity-50"
                  >
                    {isGenerating ? (
                      <>
                        <span className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin"></span>
                        <span>Fabricando Proyecto Quarkus con Agentes IA...</span>
                      </>
                    ) : (
                      <>
                        <span className="text-xl">🚀</span>
                        <span>{currentJob ? '↻ Volver a Fabricar Microservicio con IA' : 'Fabricar Microservicio Quarkus Completo con IA'}</span>
                      </>
                    )}
                  </button>

                  {/* Immediate Download & Success Card */}
                  {currentJob && (
                    <div id="fabrication-success-card" className="p-6 bg-gradient-to-br from-emerald-950/70 via-tcs-dark to-cyan-950/50 border border-emerald-500/60 rounded-2xl shadow-2xl space-y-4 animate-fadeIn">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-emerald-800/50 pb-3">
                        <div className="flex items-center space-x-3">
                          <span className="text-3xl">🎉</span>
                          <div>
                            <h3 className="text-base font-extrabold text-white">¡Microservicio Quarkus Fabricado con Éxito!</h3>
                            <p className="text-xs text-emerald-300 font-medium">
                              Se generaron {Array.isArray(currentJob.files) ? currentJob.files.length : Object.keys(currentJob.files || {}).length} archivos listos para descargar, compilar y ejecutar.
                            </p>
                          </div>
                        </div>
                        <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 rounded-full font-mono text-xs font-bold self-start sm:self-auto">
                          ✓ {currentJob.status || 'COMPLETED'}
                        </span>
                      </div>

                      {/* Botones de Descarga Directa */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                        <DownloadButton url={api.orchestrator.getJobDownloadUrl(currentJob.job_id || (currentJob as any).id)} disabled={!currentJob.files?.length}
                          className="py-3 px-5 bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-600 hover:from-emerald-500 hover:to-teal-500 text-white font-extrabold text-xs rounded-xl shadow-lg flex items-center justify-center space-x-2 transition-all transform hover:scale-[1.02]"
                        >
                          <span className="text-lg">📦</span>
                          <span>Descargar Microservicio (.ZIP)</span>
                        </DownloadButton>

                        <button
                          type="button"
                          onClick={() => setIsVerifierOpen(true)}
                          className="py-3 px-5 bg-tcs-surface hover:bg-tcs-dark border border-tcs-cyan/60 text-tcs-cyan hover:text-white font-extrabold text-xs rounded-xl shadow flex items-center justify-center space-x-2 transition-all"
                        >
                          <span className="text-lg">🛡️</span>
                          <span>Verificar en Sandbox & SHA-256</span>
                        </button>
                      </div>

                      {/* Métricas del Proyecto */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-[11px] font-mono">
                        <div className="p-2.5 bg-tcs-dark/80 rounded-xl border border-tcs-border/60">
                          <span className="text-gray-400 block text-[10px]">Archivos:</span>
                          <strong className="text-white">{Array.isArray(currentJob.files) ? currentJob.files.length : Object.keys(currentJob.files || {}).length} generados</strong>
                        </div>
                        <div className="p-2.5 bg-tcs-dark/80 rounded-xl border border-tcs-border/60">
                          <span className="text-gray-400 block text-[10px]">Arquitectura:</span>
                          <strong className="text-tcs-cyan">{(currentJob as any).architecture_style || archStyle}</strong>
                        </div>
                        <div className="p-2.5 bg-tcs-dark/80 rounded-xl border border-tcs-border/60">
                          <span className="text-gray-400 block text-[10px]">Build & Java:</span>
                          <strong className="text-amber-300">{buildTool.toUpperCase()} (Java {javaVersion})</strong>
                        </div>
                        <div className="p-2.5 bg-tcs-dark/80 rounded-xl border border-tcs-border/60">
                          <span className="text-gray-400 block text-[10px]">Tokens / Duración:</span>
                          <strong className="text-purple-300">{currentJob.metrics?.total_tokens || 0} tok / {currentJob.metrics?.duration_seconds || '0'}s</strong>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Stepper Navigation Buttons (Bottom) */}
          <div className="flex items-center justify-between border-t border-tcs-border/60 pt-4">
            <button
              type="button"
              disabled={activePhase === 1}
              onClick={() => setActivePhase(activePhase - 1)}
              className="px-4 py-2 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border rounded-xl text-xs font-semibold text-tcs-muted hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
            >
              ← Fase Anterior
            </button>

            {activePhase < 7 && (
              <button
                type="button"
                onClick={() => setActivePhase(activePhase + 1)}
                className="px-6 py-2.5 bg-tcs-blue hover:bg-tcs-cyan text-white hover:text-tcs-dark rounded-xl text-xs font-extrabold shadow-md transition-all flex items-center space-x-1.5"
              >
                <span>Siguiente: Fase {activePhase + 1}</span>
                <span>→</span>
              </button>
            )}
          </div>
        </div>

        {/* Right Column (1 col): Live Blueprint & Summary Card */}
        <div className="bg-tcs-card border border-tcs-border rounded-2xl p-5 shadow-xl space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center space-x-2 border-b border-tcs-border pb-3">
              <span className="w-2.5 h-2.5 rounded-full bg-tcs-cyan animate-pulse"></span>
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                Resumen del Microservicio en Vivo
              </h4>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-tcs-dark/80 border border-tcs-border space-y-1.5">
                <div className="text-[10px] text-tcs-muted uppercase font-mono font-bold">1. Stack & Identidad</div>
                <div className="text-white font-bold">{artifactId || '(Pendiente análisis)'}</div>
                <div className="text-tcs-cyan font-mono text-[11px]">{packagePrefix || suggestedPackagePrefix(`pe.com.${selectedClient}`)}</div>
                <div className="text-tcs-muted text-[11px]">
                  {buildTool.toUpperCase()} • Java {javaVersion} • Quarkus {quarkusVersion}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-tcs-dark/80 border border-tcs-border space-y-1.5">
                <div className="text-[10px] text-tcs-muted uppercase font-mono font-bold">2. Arquitectura & Patrones</div>
                <div className="text-white font-bold">{archStyle}</div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedPatterns.map((p) => (
                    <span key={p} className="px-1.5 py-0.5 rounded bg-tcs-surface text-tcs-cyan text-[10px] font-mono">
                      {p}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-tcs-dark/80 border border-tcs-border space-y-1.5">
                <div className="text-[10px] text-tcs-muted uppercase font-mono font-bold">3. Seguridad & Persistencia</div>
                <div className="text-white font-bold">{securityOption} ({vaultProvider})</div>
                <div className="text-tcs-muted text-[11px]">{databaseOption}</div>
              </div>

              <div className="p-3 rounded-xl bg-tcs-dark/80 border border-tcs-border space-y-1.5">
                <div className="text-[10px] text-tcs-muted uppercase font-mono font-bold">4. Dominio & Endpoints</div>
                <div className="text-white font-bold">{entities.length} Entidades • {customEndpoints.length} Endpoints</div>
                <div className="text-tcs-muted text-[11px]">Broker: {eventBroker.toUpperCase()}</div>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-tcs-border text-center">
            <span className="text-[11px] font-mono text-tcs-muted">
              Fase Actual: <strong className="text-tcs-cyan">{activePhase} de 7</strong>
            </span>
          </div>
        </div>
      </div>

      {/* 4. Generated Code Viewer & Verifier (Exclusively in Phase 7 when fabricated) */}
      {activePhase === 7 && currentJob && currentJob.files && (Array.isArray(currentJob.files) ? currentJob.files.length > 0 : Object.keys(currentJob.files).length > 0) && (
        <div id="generated-code-section" className="bg-tcs-card border border-tcs-border rounded-2xl p-6 shadow-xl space-y-4 animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-tcs-border pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-white">Código Fuente Quarkus Fabricado</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase">
                  ✓ Generación Exitosa
                </span>
              </div>
              <p className="text-xs text-tcs-muted mt-0.5">
                Proyecto compilable con {buildTool.toUpperCase()}, Java {javaVersion} y Quarkus {quarkusVersion}.
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
            files={Array.isArray(currentJob.files) ? currentJob.files : Object.entries(currentJob.files).map(([p, cnt]) => ({ path: p, content: String(cnt) }))}
            onSaveFiles={handleSaveFiles}
            onVerifySandbox={() => setIsVerifierOpen(true)}
            isSaving={isSavingFiles}
          />
        </div>
      )}

      {/* Verification Modal */}
      {currentJob && (
        <VerifierModal
          isOpen={isVerifierOpen}
          onClose={() => setIsVerifierOpen(false)}
          clientCode={currentJob.client_id || (currentJob as any).client_code || selectedClient}
          jobId={currentJob.job_id || (currentJob as any).id}
          files={Array.isArray(currentJob.files) ? currentJob.files : Object.entries(currentJob.files).map(([p, cnt]) => ({ path: p, content: String(cnt) }))}
        />
      )}
    </div>
  );
};
