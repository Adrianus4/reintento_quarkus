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

  // Mode: Wizard Steps vs All-in-One Unified View
  const [viewMode, setViewMode] = useState<'wizard' | 'unified'>('wizard');
  const [activeStep, setActiveStep] = useState<number>(1);

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

  // Business Requirement Input (Clean and free-form by default)
  const [requirementPrompt, setRequirementPrompt] = useState<string>('');

  // --- Entry Mode: Direct Requirement / Free Phase Shaping vs Ingest Blueprint JSON ---
  const [entryMode, setEntryMode] = useState<'prompt' | 'blueprint'>('prompt');
  const [blueprintJsonInput, setBlueprintJsonInput] = useState<string>('');
  const [blueprintFeedback, setBlueprintFeedback] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  // Execution & Job State
  const [currentJob, setCurrentJob] = useState<OrchestrationJob | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isSavingFiles, setIsSavingFiles] = useState<boolean>(false);
  const [isVerifierOpen, setIsVerifierOpen] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleSelectClient = (client: ClientProfile) => {
    setActiveClient(client);
    const code = (client.code || client.client_id || '').toLowerCase();
    setSelectedClient(code);
    setPackagePrefix(client.package_prefix || `pe.com.${code}`);
    setJavaVersion(client.java_version || '21');
    setArtifactId(`${code}-nuevo-servicio`);
    setDatabaseName(`${code}_db`);
    setJwtIssuer(`https://auth.${code}.com`);

    // Clean initial state for new microservice
    setRequirementPrompt('');
    setEntities([]);
    setCustomEndpoints([]);
    setCustomArchNotes('');
    setCustomPropertiesText('');
    setCurrentJob(null);
    setError(null);
    setActiveStep(1);
  };

  const handleResetToBlank = (overrideCode?: string) => {
    const code = overrideCode || selectedClient || 'bcp';
    setArtifactId(`${code}-nuevo-servicio`);
    setRequirementPrompt('');
    setEntities([]);
    setCustomEndpoints([]);
    setCustomArchNotes('');
    setCustomPropertiesText('');
    setCurrentJob(null);
    setError(null);
    setActiveStep(1);
  };

  const handleLoadBcpSample = () => {
    setArtifactId('bcp-transfers-service');
    setPackagePrefix('pe.com.bcp');
    setDatabaseName('bcp_transfers_db');
    setJwtIssuer('https://auth.viabcp.com');
    setJavaVersion('21');
    setArchStyle('Hexagonal');
    setCustomArchNotes('Arquitectura hexagonal bancaria para BCP con separación de puertos/adaptadores y trazabilidad transaccional.');
    setRequirementPrompt('Implementar microservicio de transferencias bancarias y gestión de cuentas para BCP con validación de saldos, registro de auditoría, control de idempotencia y persistencia transaccional ACID.');
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
      { method: 'POST', path: '/api/v1/transfers', summary: 'Ejecutar transferencia inmediata con validación de saldo' },
      { method: 'GET', path: '/api/v1/transfers/{id}', summary: 'Consultar estado y detalle de transferencia por UUID' },
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
        console.warn('Could not load contracts for client', err);
        setContracts([]);
      }
    };

    fetchContracts();
  }, [selectedClient]);

  // Poll for job updates if running in background
  useEffect(() => {
    let timer: any = null;
    if (
      currentJob &&
      (currentJob.status === 'RUNNING' ||
        currentJob.status === 'PENDING' ||
        currentJob.status === 'IN_PROGRESS')
    ) {
      timer = setInterval(async () => {
        try {
          const updated = await api.orchestrator.getJob(
            currentJob.job_id || (currentJob as any).id
          );
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
      setError('Seleccione una cuenta corporativa de cliente (ej. ibk o bcp)');
      return;
    }
    if (!requirementPrompt.trim()) {
      setError('Ingrese una especificación o requerimiento para el microservicio');
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

    // Parse security roles
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
        package_prefix: packagePrefix,
        artifact_id: artifactId,
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

  // Custom Endpoints Handlers
  const handleAddEndpoint = () => {
    setCustomEndpoints([
      ...customEndpoints,
      {
        method: 'GET',
        path: `/api/v1/endpoint-${customEndpoints.length + 1}`,
        summary: 'Nueva operación REST',
      },
    ]);
  };

  const handleRemoveEndpoint = (index: number) => {
    setCustomEndpoints(customEndpoints.filter((_, i) => i !== index));
  };

  const handleEndpointChange = (
    index: number,
    field: 'method' | 'path' | 'summary',
    val: string
  ) => {
    const copy = [...customEndpoints];
    copy[index] = {
      ...copy[index],
      [field]: val,
    };
    setCustomEndpoints(copy);
  };

  // Entity Editor Handlers
  const handleAddEntity = () => {
    const newEntity: EntityDefinition = {
      name: `Entity${entities.length + 1}`,
      tableName: `table_${entities.length + 1}`,
      fields: [
        { name: 'id', type: 'String', required: true, isId: true },
        { name: 'name', type: 'String', required: true },
      ],
    };
    setEntities([...entities, newEntity]);
  };

  const handleRemoveEntity = (index: number) => {
    setEntities(entities.filter((_, i) => i !== index));
  };

  const handleEntityNameChange = (index: number, newName: string) => {
    const copy = [...entities];
    copy[index].name = newName;
    copy[index].tableName = `${newName.toLowerCase()}s`;
    setEntities(copy);
  };

  const handleAddField = (entityIndex: number) => {
    const copy = [...entities];
    copy[entityIndex].fields.push({
      name: `field${copy[entityIndex].fields.length + 1}`,
      type: 'String',
      required: true,
    });
    setEntities(copy);
  };

  const handleRemoveField = (entityIndex: number, fieldIndex: number) => {
    const copy = [...entities];
    copy[entityIndex].fields = copy[entityIndex].fields.filter(
      (_, fi) => fi !== fieldIndex
    );
    setEntities(copy);
  };

  const handleFieldChange = (
    entityIndex: number,
    fieldIndex: number,
    key: 'name' | 'type' | 'required',
    val: any
  ) => {
    const copy = [...entities];
    copy[entityIndex].fields[fieldIndex] = {
      ...copy[entityIndex].fields[fieldIndex],
      [key]: val,
    };
    setEntities(copy);
  };

  // Toggle Extension Checkbox
  const toggleExtension = (extName: string) => {
    if (selectedExtensions.includes(extName)) {
      setSelectedExtensions(selectedExtensions.filter((e) => e !== extName));
    } else {
      setSelectedExtensions([...selectedExtensions, extName]);
    }
  };

  const handleApplyBlueprint = (jsonStr: string) => {
    try {
      const data = JSON.parse(jsonStr);

      if (data.client_code || data.client) {
        setSelectedClient((data.client_code || data.client).toLowerCase());
      }
      if (data.artifact_id || data.project?.artifact_id) {
        setArtifactId(data.artifact_id || data.project?.artifact_id);
      }
      if (data.package_prefix || data.project?.package_prefix) {
        setPackagePrefix(data.package_prefix || data.project?.package_prefix);
      }
      if (data.http_port || data.project?.http_port) {
        setHttpPort(Number(data.http_port || data.project?.http_port));
      }
      if (data.java_version || data.project?.java_version) {
        setJavaVersion(String(data.java_version || data.project?.java_version));
      }

      if (data.architecture_style || data.architecture?.style) {
        setArchStyle(data.architecture_style || data.architecture?.style);
      }
      if (data.custom_architecture_notes || data.architecture?.notes) {
        setCustomArchNotes(data.custom_architecture_notes || data.architecture?.notes);
      }

      if (data.security_option || data.security?.option) {
        setSecurityOption(data.security_option || data.security?.option);
      }
      if (data.jwt_issuer || data.security?.jwt_issuer) {
        setJwtIssuer(data.jwt_issuer || data.security?.jwt_issuer);
      }
      if (data.security_roles || data.security?.roles) {
        const roles = data.security_roles || data.security?.roles;
        setSecurityRoles(Array.isArray(roles) ? roles.join(', ') : String(roles));
      }

      if (data.communication_protocol || data.communication?.protocol) {
        setCommProtocol(data.communication_protocol || data.communication?.protocol);
      }
      if (Array.isArray(data.custom_endpoints || data.endpoints || data.communication?.endpoints)) {
        setCustomEndpoints(data.custom_endpoints || data.endpoints || data.communication?.endpoints);
      }

      if (data.database_option || data.database?.option) {
        setDatabaseOption(data.database_option || data.database?.option);
      }
      if (data.database_name || data.database?.name) {
        setDatabaseName(data.database_name || data.database?.name);
      }
      if (Array.isArray(data.entities || data.database?.entities)) {
        setEntities(data.entities || data.database?.entities);
      }

      if (Array.isArray(data.extensions || data.extensions?.selected)) {
        setSelectedExtensions(data.extensions || data.extensions?.selected);
      }
      if (data.custom_extensions) {
        setCustomExtensionsText(
          Array.isArray(data.custom_extensions) ? data.custom_extensions.join(', ') : data.custom_extensions
        );
      }
      if (data.custom_properties || data.properties) {
        const props = data.custom_properties || data.properties;
        setCustomPropertiesText(
          typeof props === 'object' && !Array.isArray(props)
            ? Object.entries(props).map(([k, v]) => `${k}=${v}`).join('\n')
            : String(props)
        );
      }

      if (data.requirements || data.raw_requirement) {
        setRequirementPrompt(data.requirements || data.raw_requirement);
      }

      setBlueprintFeedback({
        type: 'success',
        message: '✓ Blueprint aplicado exitosamente. Todas las fases y pasos han sido ajustados. Puedes editarlas en las pestañas antes de generar.',
      });
    } catch (err: any) {
      setBlueprintFeedback({
        type: 'error',
        message: `Error al parsear Blueprint JSON: ${err.message}`,
      });
    }
  };

  const handleLoadSampleIbk = () => {
    const ibkSample = {
      client_code: 'ibk',
      artifact_id: 'ibk-transfers-service',
      package_prefix: 'pe.com.interbank',
      http_port: 8080,
      java_version: '21',
      architecture_style: 'Hexagonal',
      custom_architecture_notes: 'Arquitectura hexagonal estricta para Interbank con puertos y adaptadores desacoplados, DTOs inmutables y reglas puras.',
      security_option: 'JWT',
      jwt_issuer: 'https://auth.interbank.pe',
      security_roles: ['ADMIN', 'OPERATOR', 'AUDITOR'],
      communication_protocol: 'REST',
      custom_endpoints: [
        {
          method: 'POST',
          path: '/api/v1/transfers',
          summary: 'Ejecutar transferencia inmediata interbancaria con validación de saldo'
        },
        {
          method: 'GET',
          path: '/api/v1/transfers/{id}',
          summary: 'Consultar estado y detalle de transferencia por UUID'
        },
        {
          method: 'GET',
          path: '/api/v1/transfers/accounts/{accountNumber}/history',
          summary: 'Historial de transferencias asociadas a una cuenta bancaria'
        }
      ],
      database_option: 'POSTGRESQL_PANACHE',
      database_name: 'ibk_transfers_db',
      entities: [
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
            { name: 'referenceNumber', type: 'String', required: false },
            { name: 'createdAt', type: 'LocalDateTime', required: true }
          ]
        }
      ],
      extensions: [
        'quarkus-resteasy-reactive-jackson',
        'quarkus-smallrye-openapi',
        'quarkus-smallrye-health',
        'quarkus-micrometer-registry-prometheus',
        'quarkus-hibernate-validator'
      ],
      custom_extensions: ['quarkus-smallrye-fault-tolerance'],
      custom_properties: 'interbank.transfers.daily-limit=50000.00\ninterbank.audit.async-logging=true\ninterbank.idempotency.ttl-seconds=3600',
      requirements: 'Implementar microservicio bancario de transferencias interbancarias para Interbank con validación de cuentas, registro de auditoría, control de idempotencia y persistencia transaccional ACID.'
    };
    const jsonStr = JSON.stringify(ibkSample, null, 2);
    setBlueprintJsonInput(jsonStr);
    handleApplyBlueprint(jsonStr);
  };

  const handleLoadSampleBcp = () => {
    const bcpSample = {
      client_code: 'bcp',
      artifact_id: 'bcp-accounts-service',
      package_prefix: 'pe.com.bcp',
      http_port: 8080,
      java_version: '21',
      architecture_style: 'CleanArchitecture',
      custom_architecture_notes: 'Clean Architecture para BCP con capas de Domain, UseCases e Infrastructure aisladas.',
      security_option: 'JWT',
      jwt_issuer: 'https://auth.viabcp.com',
      security_roles: ['ADMIN', 'MANAGER', 'TELLER'],
      communication_protocol: 'REST',
      custom_endpoints: [
        {
          method: 'POST',
          path: '/api/v1/accounts',
          summary: 'Aperturar cuenta bancaria'
        },
        {
          method: 'GET',
          path: '/api/v1/accounts/{accountNumber}/balance',
          summary: 'Consultar balance disponible'
        }
      ],
      database_option: 'POSTGRESQL_PANACHE',
      database_name: 'bcp_accounts_db',
      entities: [
        {
          name: 'Account',
          tableName: 'accounts',
          fields: [
            { name: 'id', type: 'String', required: true, isId: true },
            { name: 'accountNumber', type: 'String', required: true },
            { name: 'accountType', type: 'String', required: true },
            { name: 'balance', type: 'BigDecimal', required: true },
            { name: 'currency', type: 'String', required: true },
            { name: 'status', type: 'String', required: true },
            { name: 'updatedAt', type: 'LocalDateTime', required: true }
          ]
        }
      ],
      extensions: [
        'quarkus-resteasy-reactive-jackson',
        'quarkus-smallrye-openapi',
        'quarkus-smallrye-health',
        'quarkus-micrometer-registry-prometheus',
        'quarkus-hibernate-validator'
      ],
      custom_extensions: ['quarkus-smallrye-fault-tolerance'],
      custom_properties: 'bcp.accounts.audit.enabled=true\nbcp.cache.ttl-seconds=1800',
      requirements: 'Implementar microservicio de gestión de cuentas bancarias y balances para BCP con persistencia relacional y trazabilidad de operaciones.'
    };
    const jsonStr = JSON.stringify(bcpSample, null, 2);
    setBlueprintJsonInput(jsonStr);
    handleApplyBlueprint(jsonStr);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const content = evt.target?.result as string;
      setBlueprintJsonInput(content);
      handleApplyBlueprint(content);
    };
    reader.readAsText(file);
  };

  const handleExportBlueprint = () => {
    const blueprintObj = {
      client_code: selectedClient,
      artifact_id: artifactId,
      package_prefix: packagePrefix,
      http_port: httpPort,
      java_version: javaVersion,
      architecture_style: archStyle,
      custom_architecture_notes: customArchNotes,
      security_option: securityOption,
      jwt_issuer: jwtIssuer,
      security_roles: securityRoles.split(',').map((s) => s.trim()).filter(Boolean),
      communication_protocol: commProtocol,
      custom_endpoints: customEndpoints,
      database_option: databaseOption,
      database_name: databaseName,
      entities: entities,
      extensions: selectedExtensions,
      custom_extensions: customExtensionsText.split(',').map((s) => s.trim()).filter(Boolean),
      custom_properties: customPropertiesText,
      requirements: requirementPrompt,
    };
    const jsonStr = JSON.stringify(blueprintObj, null, 2);
    setBlueprintJsonInput(jsonStr);

    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifactId || 'microservice'}-blueprint.json`;
    a.click();
    URL.revokeObjectURL(url);

    setBlueprintFeedback({
      type: 'success',
      message: '✓ Blueprint exportado y descargado exitosamente como JSON.',
    });
  };

  const wizardSteps = [
    { num: 1, title: 'Cliente & Proyecto' },
    { num: 2, title: 'Arquitectura' },
    { num: 3, title: 'Seguridad' },
    { num: 4, title: 'Endpoints & APIs' },
    { num: 5, title: 'Base de Datos & Entidades' },
    { num: 6, title: 'Extensiones & Requisitos' },
    { num: 7, title: 'Resumen & Confirmar' },
  ];

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

  return (
    <div className="space-y-6">
      {/* Top Banner: Active Client Corporate Badge & Quick Actions */}
      <div className="bg-gradient-to-r from-tcs-navy via-tcs-card to-tcs-navy border border-tcs-border rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-4">
          {selectedClient === 'bcp' ? (
            <div className="w-14 h-14 rounded-xl bg-[#002A8F] p-2 flex items-center justify-center shadow-lg border border-blue-400/30 overflow-hidden shrink-0">
              <img src="/bcp-logo.png" alt="BCP Logo" className="w-full h-full object-contain" />
            </div>
          ) : (
            <div className="w-14 h-14 rounded-xl bg-tcs-blue/20 border border-tcs-border flex items-center justify-center text-tcs-cyan font-extrabold text-base shrink-0">
              {selectedClient.slice(0, 3).toUpperCase()}
            </div>
          )}
          <div>
            <div className="flex items-center space-x-2.5">
              <h2 className="text-base sm:text-lg font-extrabold text-white">
                {activeClient?.name || selectedClient.toUpperCase()}
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase">
                ● Cuenta Activa
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2 mt-1 text-xs font-mono text-tcs-muted">
              <span className="text-tcs-cyan font-semibold">{packagePrefix}</span>
              <span>•</span>
              <span className="text-white/80">Java {javaVersion}</span>
              <span>•</span>
              <span className="text-white/80">Quarkus {quarkusVersion}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
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
            onClick={() => handleResetToBlank()}
            className="px-3.5 py-2 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border hover:border-emerald-500/60 rounded-xl text-xs font-semibold text-emerald-300 flex items-center space-x-1.5 transition-all shadow"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>✨ Nuevo Pedido (En blanco)</span>
          </button>

          {selectedClient === 'bcp' && (
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
      {/* Configuration Box */}
      <div className="bg-tcs-card border border-tcs-border rounded-xl p-5 shadow">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-5 border-b border-tcs-border/60 pb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-tcs-cyan"></span>
              <span>Workspace Studio: Asistente y Captura Completa de Inputs Quarkus</span>
            </h2>
            <p className="text-xs text-tcs-muted">
              Ingresa libremente tus especificaciones, endpoints, entidades, base de datos y extensiones antes de generar tu microservicio.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-tcs-dark p-0.5 rounded-lg border border-tcs-border">
              <button
                type="button"
                onClick={() => setViewMode('wizard')}
                className={`px-3 py-1 text-xs font-semibold rounded ${
                  viewMode === 'wizard'
                    ? 'bg-tcs-blue text-white shadow'
                    : 'text-tcs-muted hover:text-white'
                }`}
              >
                Modo Pasos
              </button>
              <button
                type="button"
                onClick={() => setViewMode('unified')}
                className={`px-3 py-1 text-xs font-semibold rounded ${
                  viewMode === 'unified'
                    ? 'bg-tcs-blue text-white shadow'
                    : 'text-tcs-muted hover:text-white'
                }`}
              >
                Vista Unificada
              </button>
            </div>

            {currentJob && (
              <div className="flex items-center space-x-2 text-xs font-mono ml-2">
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
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Entry Mode Selector: Diseñar en Fases vs Ingestar Blueprint JSON */}
        <div className="mb-6 p-4 bg-tcs-dark/90 border border-tcs-border rounded-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-tcs-cyan"></span>
                <span>Modo de Entrada del Microservicio</span>
              </h3>
              <p className="text-xs text-tcs-muted">
                Escribe tu requerimiento libremente para darle forma en las fases, o ingesta un Blueprint JSON para preconfigurar todos los pasos y editarlos a medida.
              </p>
            </div>
            <div className="flex items-center space-x-2 bg-tcs-navy p-1 rounded-lg border border-tcs-border">
              <button
                type="button"
                onClick={() => setEntryMode('prompt')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  entryMode === 'prompt'
                    ? 'bg-tcs-blue text-white shadow'
                    : 'text-tcs-muted hover:text-white'
                }`}
              >
                Diseñar por Fases
              </button>
              <button
                type="button"
                onClick={() => setEntryMode('blueprint')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center space-x-1.5 ${
                  entryMode === 'blueprint'
                    ? 'bg-tcs-blue text-white shadow'
                    : 'text-tcs-muted hover:text-white'
                }`}
              >
                <span>Ingestar Blueprint JSON</span>
              </button>
            </div>
          </div>

          {entryMode === 'blueprint' && (
            <div className="space-y-3 pt-3 border-t border-tcs-border/60">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs text-tcs-muted">
                  Pega tu Blueprint JSON o carga plantillas predefinidas:
                </span>
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={handleLoadSampleIbk}
                    className="px-2.5 py-1 text-[11px] bg-tcs-surface border border-tcs-border rounded text-tcs-cyan hover:border-tcs-cyan transition-colors"
                  >
                    Plantilla IBK Transferencias
                  </button>
                  <button
                    type="button"
                    onClick={handleLoadSampleBcp}
                    className="px-2.5 py-1 text-[11px] bg-tcs-surface border border-tcs-border rounded text-tcs-muted hover:text-white transition-colors"
                  >
                    Plantilla BCP Cuentas
                  </button>
                  <label className="px-2.5 py-1 text-[11px] bg-tcs-surface border border-tcs-border rounded text-white cursor-pointer hover:border-tcs-blue transition-colors">
                    Subir archivo .json
                    <input
                      type="file"
                      accept=".json"
                      className="hidden"
                      onChange={handleFileUpload}
                    />
                  </label>
                </div>
              </div>

              <textarea
                rows={7}
                value={blueprintJsonInput}
                onChange={(e) => setBlueprintJsonInput(e.target.value)}
                placeholder='{\n  "client_code": "ibk",\n  "artifact_id": "ibk-transfers-service",\n  "package_prefix": "pe.com.interbank",\n  "architecture_style": "Hexagonal",\n  "security_option": "JWT",\n  "database_option": "POSTGRESQL_PANACHE",\n  "entities": [...]\n}'
                className="w-full px-3 py-2 bg-tcs-navy border border-tcs-border rounded text-xs text-emerald-300 font-mono focus:outline-none focus:border-tcs-blue"
              />

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => handleApplyBlueprint(blueprintJsonInput)}
                  disabled={!blueprintJsonInput.trim()}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-semibold rounded-lg shadow transition-colors flex items-center justify-center space-x-1.5"
                >
                  <span>✓ Aplicar y Ajustar Todas las Fases</span>
                </button>
                <button
                  type="button"
                  onClick={handleExportBlueprint}
                  className="px-3.5 py-2 bg-tcs-surface border border-tcs-border rounded text-xs text-tcs-cyan hover:border-tcs-cyan transition-colors flex items-center justify-center space-x-1"
                >
                  <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span>Exportar Blueprint JSON Actual</span>
                </button>
              </div>

              {blueprintFeedback && (
                <div
                  className={`p-3 rounded-lg text-xs font-mono border ${
                    blueprintFeedback.type === 'success'
                      ? 'bg-emerald-950/80 border-emerald-800 text-emerald-300'
                      : 'bg-rose-950/80 border-rose-800 text-rose-300'
                  }`}
                >
                  {blueprintFeedback.message}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Wizard Stepper Header (Only in Wizard Mode) */}
        {viewMode === 'wizard' && (
          <div className="mb-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
              {wizardSteps.map((step) => {
                const isCurrent = activeStep === step.num;
                const isDone = activeStep > step.num;
                return (
                  <button
                    key={step.num}
                    type="button"
                    onClick={() => setActiveStep(step.num)}
                    disabled={isGenerating}
                    className={`flex items-center p-2 rounded-lg border text-left transition-all ${
                      isCurrent
                        ? 'bg-tcs-blue/20 border-tcs-cyan text-white shadow'
                        : isDone
                        ? 'bg-tcs-dark border-emerald-800/60 text-emerald-300'
                        : 'bg-tcs-dark/50 border-tcs-border text-tcs-muted hover:border-tcs-blue/50'
                    }`}
                  >
                    <span
                      className={`w-5 h-5 rounded-full text-[11px] font-bold flex items-center justify-center mr-2 flex-shrink-0 ${
                        isCurrent
                          ? 'bg-tcs-cyan text-tcs-dark font-extrabold'
                          : isDone
                          ? 'bg-emerald-600 text-white'
                          : 'bg-tcs-border text-tcs-muted'
                      }`}
                    >
                      {isDone ? '✓' : step.num}
                    </span>
                    <span className="text-[11px] font-medium truncate">{step.title}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* SECCIÓN 1: IDENTIDAD Y PROYECTO */}
        {/* ========================================================================= */}
        {(viewMode === 'unified' || activeStep === 1) && (
          <div className="space-y-4 mb-6">
            <h3 className="text-sm font-semibold text-white border-b border-tcs-border/40 pb-2 flex items-center justify-between">
              <span>1. Identidad Corporativa y Configuración del Proyecto</span>
              {viewMode === 'unified' && <span className="text-xs text-tcs-cyan font-mono">Paso 1</span>}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
              {/* Client Selection */}
              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">
                  Cliente Corporativo
                </label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                >
                  {clients.map((c: any) => (
                    <option key={c.code || c.client_id} value={c.code || c.client_id}>
                      {c.name} ({c.code || c.client_id})
                    </option>
                  ))}
                  {clients.length === 0 && (
                    <>
                      <option value="ibk">Interbank Perú (ibk)</option>
                      <option value="bcp">Banco de Crédito del Perú (bcp)</option>
                    </>
                  )}
                </select>
              </div>

              {/* Artifact ID */}
              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">
                  Artifact ID (Nombre Microservicio)
                </label>
                <input
                  type="text"
                  value={artifactId}
                  onChange={(e) => setArtifactId(e.target.value)}
                  placeholder="ej. ibk-transfers-service"
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                />
              </div>

              {/* Package Prefix */}
              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">
                  Prefijo de Paquete Java
                </label>
                <input
                  type="text"
                  value={packagePrefix}
                  onChange={(e) => setPackagePrefix(e.target.value)}
                  placeholder="ej. pe.com.interbank"
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                />
              </div>

              {/* HTTP Port */}
              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">
                  Puerto HTTP Quarkus
                </label>
                <input
                  type="number"
                  value={httpPort}
                  onChange={(e) => setHttpPort(parseInt(e.target.value) || 8080)}
                  placeholder="8080"
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                />
              </div>

              {/* Java Version */}
              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">
                  Versión de Java LTS
                </label>
                <select
                  value={javaVersion}
                  onChange={(e) => setJavaVersion(e.target.value)}
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue"
                >
                  <option value="21">Java 21 LTS (Recomendado)</option>
                  <option value="17">Java 17 LTS</option>
                </select>
              </div>
            </div>

            {/* OpenAPI Contract Selection */}
            <div>
              <label className="block text-xs font-medium text-tcs-muted mb-1">
                Contrato OpenAPI 3.x de Referencia (Opcional)
              </label>
              <select
                value={selectedContractId}
                onChange={(e) => setSelectedContractId(e.target.value)}
                className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
              >
                <option value="">Ninguno (Generación Guiada por Requerimientos)</option>
                {contracts.map((c: any) => (
                  <option key={c.id} value={c.id}>
                    {c.title} (v{c.version}) — {c.endpoints_count || 2} endpoints
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* SECCIÓN 2: ARQUITECTURA */}
        {/* ========================================================================= */}
        {(viewMode === 'unified' || activeStep === 2) && (
          <div className="space-y-4 mb-6">
            <h3 className="text-sm font-semibold text-white border-b border-tcs-border/40 pb-2 flex items-center justify-between">
              <span>2. Patrón Arquitectónico</span>
              {viewMode === 'unified' && <span className="text-xs text-tcs-cyan font-mono">Paso 2</span>}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {[
                {
                  id: 'Hexagonal',
                  title: 'Arquitectura Hexagonal (Ports & Adapters)',
                  badge: 'Recomendado Banca',
                  desc: 'Desacoplamiento total con dominio puro, puertos in/out y adaptadores de infraestructura para APIs y base de datos.',
                },
                {
                  id: 'Layered',
                  title: 'Clean Layered (Por Capas)',
                  badge: 'Modular',
                  desc: 'Separación clásica en capas Model, Repository, Service y Controller, ideal para operaciones CRUD optimizadas.',
                },
                {
                  id: 'Event-Driven',
                  title: 'Event-Driven (Reactivo / EDA)',
                  badge: 'Streaming',
                  desc: 'Procesamiento de eventos asíncronos en tiempo real con SmallRye Reactive Messaging y tópicos Apache Kafka.',
                },
                {
                  id: 'BFF',
                  title: 'BFF (Backend for Frontend)',
                  badge: 'Agregador',
                  desc: 'Capa de agregación optimizada para canales digitales (móvil y web) con llamadas paralelas no bloqueantes.',
                },
                {
                  id: 'gRPC',
                  title: 'Microservicio gRPC de Alto Rendimiento',
                  badge: 'RPC Binario',
                  desc: 'Comunicación binaria sobre HTTP/2 con buffers de protocolo (Protobuf) para transacciones ultrarrápidas.',
                },
              ].map((item) => (
                <div
                  key={item.id}
                  onClick={() => setArchStyle(item.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    archStyle === item.id
                      ? 'bg-tcs-blue/25 border-tcs-cyan text-white shadow-md'
                      : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue/60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-white">{item.title}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-tcs-card border border-tcs-cyan/40 text-tcs-cyan font-mono">
                      {item.badge}
                    </span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-gray-300">{item.desc}</p>
                </div>
              ))}
            </div>

            {/* Custom Architecture Notes Input */}
            <div>
              <label className="block text-xs font-medium text-tcs-muted mb-1">
                Notas y Reglas de Arquitectura Personalizadas (Input libre)
              </label>
              <input
                type="text"
                value={customArchNotes}
                onChange={(e) => setCustomArchNotes(e.target.value)}
                placeholder="ej. Aplicar Value Objects inmutables, DTOs independientes para cada endpoint..."
                className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
              />
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* SECCIÓN 3: SEGURIDAD */}
        {/* ========================================================================= */}
        {(viewMode === 'unified' || activeStep === 3) && (
          <div className="space-y-4 mb-6">
            <h3 className="text-sm font-semibold text-white border-b border-tcs-border/40 pb-2 flex items-center justify-between">
              <span>3. Seguridad y Control de Acceso</span>
              {viewMode === 'unified' && <span className="text-xs text-tcs-cyan font-mono">Paso 3</span>}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {[
                {
                  id: 'JWT',
                  title: 'Quarkus SmallRye JWT (Bearer Token)',
                  badge: 'Estándar',
                  desc: 'Autenticación mediante tokens criptográficos JWT (RS256/HS256) con claims estándar y autorización RBAC (@RolesAllowed).',
                },
                {
                  id: 'OIDC',
                  title: 'Quarkus OIDC (Keycloak / Entra ID)',
                  badge: 'Federado',
                  desc: 'Integración federada con OpenID Connect corporativo, Keycloak bancario o Azure AD.',
                },
                {
                  id: 'MTLS',
                  title: 'Mutual TLS (mTLS / PKI)',
                  badge: 'Zero Trust',
                  desc: 'Autenticación mutua con certificados digitales X.509 para comunicación cifrada punto a punto.',
                },
                {
                  id: 'BASIC',
                  title: 'Basic Auth / API Key Header',
                  badge: 'Simple',
                  desc: 'Validación por cabecera HTTP estándar para integraciones específicas.',
                },
                {
                  id: 'NONE',
                  title: 'Pública / Sin Autenticación',
                  badge: 'Dev Mode',
                  desc: 'Endpoints públicos sin restricción de credenciales, útil para microservicios de utilidades.',
                },
              ].map((sec) => (
                <div
                  key={sec.id}
                  onClick={() => setSecurityOption(sec.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    securityOption === sec.id
                      ? 'bg-tcs-blue/25 border-tcs-cyan text-white shadow-md'
                      : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue/60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-white">{sec.title}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-tcs-card border border-tcs-cyan/40 text-tcs-cyan font-mono">
                      {sec.badge}
                    </span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-gray-300">{sec.desc}</p>
                </div>
              ))}
            </div>

            {/* Security Config Inputs */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">
                  JWT / OIDC Issuer URL (Input editable)
                </label>
                <input
                  type="text"
                  value={jwtIssuer}
                  onChange={(e) => setJwtIssuer(e.target.value)}
                  placeholder="https://auth.interbank.pe"
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">
                  Roles Autorizados (Separados por coma)
                </label>
                <input
                  type="text"
                  value={securityRoles}
                  onChange={(e) => setSecurityRoles(e.target.value)}
                  placeholder="ADMIN, OPERATOR, AUDITOR"
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                />
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* SECCIÓN 4: COMUNICACIÓN Y ENDPOINTS PERSONALIZADOS */}
        {/* ========================================================================= */}
        {(viewMode === 'unified' || activeStep === 4) && (
          <div className="space-y-4 mb-6">
            <h3 className="text-sm font-semibold text-white border-b border-tcs-border/40 pb-2 flex items-center justify-between">
              <span>4. Comunicación y Gestor de Endpoints Personalizados</span>
              {viewMode === 'unified' && <span className="text-xs text-tcs-cyan font-mono">Paso 4</span>}
            </h3>

            {/* Protocol Selector */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
              {[
                { id: 'REST', label: 'RESTEasy Reactive REST' },
                { id: 'GRPC', label: 'gRPC Protobuf' },
                { id: 'GRAPHQL', label: 'GraphQL' },
                { id: 'REACTIVE_MESSAGING', label: 'Reactive Messaging (Kafka)' },
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setCommProtocol(p.id)}
                  className={`p-2 rounded border text-xs font-medium transition-all ${
                    commProtocol === p.id
                      ? 'bg-tcs-blue/30 border-tcs-cyan text-white font-bold'
                      : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue/40'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Custom Endpoints Input Table */}
            <div className="bg-tcs-dark/70 border border-tcs-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <span className="text-xs font-bold text-white">
                    Endpoints del Microservicio ({customEndpoints.length})
                  </span>
                  <p className="text-[11px] text-tcs-muted">
                    Ingresa las rutas y métodos que debe exponer tu microservicio en Quarkus.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleAddEndpoint}
                  className="px-2.5 py-1 bg-tcs-blue hover:bg-tcs-cyan text-white hover:text-tcs-dark text-xs font-bold rounded transition-all"
                >
                  + Agregar Endpoint
                </button>
              </div>

              <div className="space-y-2">
                {customEndpoints.map((ep, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col sm:flex-row items-center gap-2 p-2 bg-tcs-card border border-tcs-border/80 rounded"
                  >
                    <select
                      value={ep.method}
                      onChange={(e) => handleEndpointChange(idx, 'method', e.target.value)}
                      className={`px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-xs font-bold font-mono ${
                        ep.method === 'GET'
                          ? 'text-sky-400'
                          : ep.method === 'POST'
                          ? 'text-emerald-400'
                          : ep.method === 'PUT'
                          ? 'text-amber-400'
                          : 'text-rose-400'
                      }`}
                    >
                      <option value="GET">GET</option>
                      <option value="POST">POST</option>
                      <option value="PUT">PUT</option>
                      <option value="DELETE">DELETE</option>
                      <option value="PATCH">PATCH</option>
                    </select>

                    <input
                      type="text"
                      value={ep.path}
                      onChange={(e) => handleEndpointChange(idx, 'path', e.target.value)}
                      placeholder="/api/v1/..."
                      className="w-full sm:w-1/3 px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-white font-mono"
                    />

                    <input
                      type="text"
                      value={ep.summary}
                      onChange={(e) => handleEndpointChange(idx, 'summary', e.target.value)}
                      placeholder="Descripción de la operación..."
                      className="w-full sm:flex-1 px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-gray-200"
                    />

                    <button
                      type="button"
                      onClick={() => handleRemoveEndpoint(idx)}
                      className="text-rose-400 hover:text-rose-200 text-xs px-2"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* SECCIÓN 5: BASE DE DATOS Y ENTIDADES EDITABLES */}
        {/* ========================================================================= */}
        {(viewMode === 'unified' || activeStep === 5) && (
          <div className="space-y-4 mb-6">
            <h3 className="text-sm font-semibold text-white border-b border-tcs-border/40 pb-2 flex items-center justify-between">
              <span>5. Persistencia y Arquetipo de Entidades Editables</span>
              {viewMode === 'unified' && <span className="text-xs text-tcs-cyan font-mono">Paso 5</span>}
            </h3>

            {/* Database Engine Selector */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-3">
              {[
                { id: 'POSTGRESQL_PANACHE', label: 'PostgreSQL Panache' },
                { id: 'MYSQL_PANACHE', label: 'MySQL Panache' },
                { id: 'MONGODB_PANACHE', label: 'MongoDB Panache' },
                { id: 'REACTIVE_PG', label: 'Reactive PostgreSQL' },
                { id: 'REDIS', label: 'Redis Cache' },
                { id: 'NONE', label: 'Sin Base de Datos' },
              ].map((db) => (
                <button
                  key={db.id}
                  type="button"
                  onClick={() => setDatabaseOption(db.id)}
                  className={`p-2 rounded border text-xs font-medium text-center transition-all ${
                    databaseOption === db.id
                      ? 'bg-tcs-blue/30 border-tcs-cyan text-white font-bold'
                      : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue/40'
                  }`}
                >
                  {db.label}
                </button>
              ))}
            </div>

            {databaseOption !== 'NONE' && (
              <div className="mb-3">
                <label className="block text-xs font-medium text-tcs-muted mb-1">
                  Nombre de la Base de Datos (Input editable)
                </label>
                <input
                  type="text"
                  value={databaseName}
                  onChange={(e) => setDatabaseName(e.target.value)}
                  placeholder="ej. ibk_transfers_db"
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                />
              </div>
            )}

            {/* Entities & Fields Editor */}
            <div className="bg-tcs-dark/70 border border-tcs-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <span className="text-xs font-bold text-white">
                    Entidades de Dominio ({entities.length})
                  </span>
                  <p className="text-[11px] text-tcs-muted">
                    Define las clases de entidad, sus atributos y tipos de datos que generará el microservicio.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleAddEntity}
                  className="px-2.5 py-1 bg-tcs-blue hover:bg-tcs-cyan text-white hover:text-tcs-dark text-xs font-bold rounded transition-all"
                >
                  + Agregar Entidad
                </button>
              </div>

              <div className="space-y-4">
                {entities.map((entity, eIdx) => (
                  <div key={eIdx} className="bg-tcs-card border border-tcs-border/80 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-tcs-muted">Clase:</span>
                        <input
                          type="text"
                          value={entity.name}
                          onChange={(e) => handleEntityNameChange(eIdx, e.target.value)}
                          className="px-2 py-0.5 bg-tcs-dark border border-tcs-border rounded text-xs text-white font-mono focus:border-tcs-cyan"
                        />
                        <span className="text-xs text-tcs-muted">Tabla:</span>
                        <span className="text-xs text-tcs-cyan font-mono">{entity.tableName}</span>
                      </div>
                      {entities.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveEntity(eIdx)}
                          className="text-xs text-rose-400 hover:text-rose-200"
                        >
                          Eliminar
                        </button>
                      )}
                    </div>

                    {/* Fields List */}
                    <div className="space-y-1.5 mt-2">
                      {entity.fields.map((field, fIdx) => (
                        <div key={fIdx} className="flex items-center space-x-2 text-xs">
                          <input
                            type="text"
                            value={field.name}
                            onChange={(e) => handleFieldChange(eIdx, fIdx, 'name', e.target.value)}
                            placeholder="Nombre del campo"
                            className="w-1/3 px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-white font-mono"
                          />
                          <select
                            value={field.type}
                            onChange={(e) => handleFieldChange(eIdx, fIdx, 'type', e.target.value)}
                            className="w-1/4 px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-white font-mono"
                          >
                            <option value="String">String</option>
                            <option value="BigDecimal">BigDecimal</option>
                            <option value="Long">Long</option>
                            <option value="Integer">Integer</option>
                            <option value="Boolean">Boolean</option>
                            <option value="LocalDateTime">LocalDateTime</option>
                            <option value="UUID">UUID</option>
                          </select>
                          <label className="flex items-center space-x-1 text-tcs-muted">
                            <input
                              type="checkbox"
                              checked={field.required}
                              onChange={(e) =>
                                handleFieldChange(eIdx, fIdx, 'required', e.target.checked)
                              }
                            />
                            <span>Requerido</span>
                          </label>
                          {entity.fields.length > 1 && (
                            <button
                              type="button"
                              onClick={() => handleRemoveField(eIdx, fIdx)}
                              className="text-rose-400 hover:text-rose-200 ml-auto"
                            >
                              ✕
                            </button>
                          )}
                        </div>
                      ))}
                    </div>

                    <button
                      type="button"
                      onClick={() => handleAddField(eIdx)}
                      className="mt-2 text-[11px] text-tcs-cyan hover:underline font-medium"
                    >
                      + Agregar Campo
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* SECCIÓN 6: EXTENSIONES, PROPIEDADES Y REQUERIMIENTO */}
        {/* ========================================================================= */}
        {(viewMode === 'unified' || activeStep === 6) && (
          <div className="space-y-4 mb-6">
            <h3 className="text-sm font-semibold text-white border-b border-tcs-border/40 pb-2 flex items-center justify-between">
              <span>6. Inyección de Extensiones Quarkus y Reglas de Negocio</span>
              {viewMode === 'unified' && <span className="text-xs text-tcs-cyan font-mono">Paso 6</span>}
            </h3>

            {/* Recommended Checkboxes */}
            <div>
              <label className="block text-xs font-medium text-tcs-muted mb-2">
                Extensiones Quarkus Recomendadas (Inyección a demanda)
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 mb-3">
                {[
                  {
                    id: 'quarkus-resteasy-reactive-jackson',
                    name: 'RESTEasy Reactive Jackson',
                    desc: 'Serialización JSON de alto rendimiento para endpoints HTTP.',
                  },
                  {
                    id: 'quarkus-smallrye-openapi',
                    name: 'SmallRye OpenAPI & Swagger UI',
                    desc: 'Documentación OpenAPI 3.0 en /q/openapi y UI interactiva.',
                  },
                  {
                    id: 'quarkus-smallrye-health',
                    name: 'SmallRye Health (Liveness/Readiness)',
                    desc: 'Sondas de salud para Kubernetes en /q/health/live y ready.',
                  },
                  {
                    id: 'quarkus-micrometer-registry-prometheus',
                    name: 'Micrometer Prometheus Metrics',
                    desc: 'Telemetría de métricas de aplicación en endpoint /q/metrics.',
                  },
                  {
                    id: 'quarkus-smallrye-fault-tolerance',
                    name: 'SmallRye Fault Tolerance',
                    desc: 'Resiliencia bancaria: @CircuitBreaker, @Retry y @Timeout.',
                  },
                  {
                    id: 'quarkus-hibernate-validator',
                    name: 'Hibernate Validator (Bean Validation)',
                    desc: 'Validaciones declarativas @NotNull, @Size, @Pattern en DTOs.',
                  },
                ].map((ext) => {
                  const isChecked = selectedExtensions.includes(ext.id);
                  return (
                    <div
                      key={ext.id}
                      onClick={() => toggleExtension(ext.id)}
                      className={`p-2.5 rounded border cursor-pointer transition-all flex items-start space-x-2 ${
                        isChecked
                          ? 'bg-tcs-blue/20 border-tcs-cyan text-white'
                          : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-blue/40'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}}
                        className="mt-0.5 rounded border-tcs-border"
                      />
                      <div>
                        <div className="text-xs font-semibold text-white">{ext.name}</div>
                        <div className="text-[11px] text-gray-400 leading-tight">{ext.desc}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Custom Extensions Input */}
            <div>
              <label className="block text-xs font-medium text-tcs-muted mb-1">
                Extensiones Quarkus Adicionales Libres (Input separado por comas o líneas)
              </label>
              <input
                type="text"
                value={customExtensionsText}
                onChange={(e) => setCustomExtensionsText(e.target.value)}
                placeholder="ej. quarkus-mailer, quarkus-cache, io.quarkiverse.cxf:quarkus-cxf"
                className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
              />
            </div>

            {/* Custom Application Properties Input */}
            <div>
              <label className="block text-xs font-medium text-tcs-muted mb-1">
                Propiedades Personalizadas (application.properties adicionales en formato clave=valor)
              </label>
              <textarea
                rows={3}
                value={customPropertiesText}
                onChange={(e) => setCustomPropertiesText(e.target.value)}
                placeholder="mi.propiedad.custom=valor&#10;otra.clave=123"
                className="w-full p-2.5 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono leading-relaxed"
              />
            </div>

            {/* Main Business Requirement Prompt */}
            <div>
              <label className="block text-xs font-medium text-tcs-muted mb-1">
                Especificación Detallada de Reglas y Requerimientos de Negocio (Prompt de IA)
              </label>
              <textarea
                rows={3}
                value={requirementPrompt}
                onChange={(e) => setRequirementPrompt(e.target.value)}
                placeholder="Describa el dominio bancario, validaciones, reglas de negocio y flujos que debe contener el microservicio..."
                className="w-full p-3 bg-tcs-dark border border-tcs-border rounded-lg text-xs text-white focus:outline-none focus:border-tcs-blue leading-relaxed font-mono"
              />
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* SECCIÓN 7: RESUMEN Y CONFIRMACIÓN */}
        {/* ========================================================================= */}
        {(viewMode === 'unified' || activeStep === 7) && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white border-b border-tcs-border/40 pb-2 flex items-center justify-between">
              <span>7. Resumen de Inputs y Confirmación de Generación</span>
              {viewMode === 'unified' && <span className="text-xs text-tcs-cyan font-mono">Paso 7</span>}
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
              <div className="bg-tcs-dark/80 p-3.5 rounded-lg border border-tcs-border space-y-1.5">
                <div className="text-tcs-cyan font-bold uppercase text-[11px] border-b border-tcs-border/50 pb-1">
                  Identidad & Arquitectura
                </div>
                <div><span className="text-tcs-muted">Cliente:</span> <strong className="text-white">{selectedClient.toUpperCase()}</strong></div>
                <div><span className="text-tcs-muted">Artifact ID:</span> <strong className="text-white">{artifactId}</strong></div>
                <div><span className="text-tcs-muted">Package:</span> <strong className="text-white">{packagePrefix}</strong></div>
                <div><span className="text-tcs-muted">Puerto:</span> <strong className="text-white">{httpPort}</strong></div>
                <div><span className="text-tcs-muted">Patrón:</span> <strong className="text-white">{archStyle}</strong></div>
              </div>

              <div className="bg-tcs-dark/80 p-3.5 rounded-lg border border-tcs-border space-y-1.5">
                <div className="text-tcs-cyan font-bold uppercase text-[11px] border-b border-tcs-border/50 pb-1">
                  Seguridad & Base de Datos
                </div>
                <div><span className="text-tcs-muted">Seguridad:</span> <strong className="text-white">{securityOption}</strong></div>
                <div><span className="text-tcs-muted">Issuer:</span> {jwtIssuer}</div>
                <div><span className="text-tcs-muted">Base de Datos:</span> <strong className="text-white">{databaseOption}</strong></div>
                <div><span className="text-tcs-muted">DB Name:</span> {databaseName}</div>
                <div><span className="text-tcs-muted">Entidades:</span> {entities.map((e) => e.name).join(', ')}</div>
              </div>

              <div className="bg-tcs-dark/80 p-3.5 rounded-lg border border-tcs-border space-y-1.5">
                <div className="text-tcs-cyan font-bold uppercase text-[11px] border-b border-tcs-border/50 pb-1">
                  Endpoints & Extensiones
                </div>
                <div><span className="text-tcs-muted">Protocolo:</span> {commProtocol}</div>
                <div><span className="text-tcs-muted">Endpoints:</span> {customEndpoints.length} definidos</div>
                <div><span className="text-tcs-muted">Extensiones:</span> {selectedExtensions.length} activas</div>
                {customExtensionsText && (
                  <div className="truncate"><span className="text-tcs-muted">Libres:</span> {customExtensionsText}</div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Stepper Navigation / Generation Button */}
        <div className="flex items-center justify-between gap-3 pt-4 border-t border-tcs-border/60 mt-5">
          <div>
            {viewMode === 'wizard' && activeStep > 1 && (
              <button
                type="button"
                onClick={() => setActiveStep(activeStep - 1)}
                disabled={isGenerating}
                className="px-4 py-2 bg-tcs-dark hover:bg-tcs-border text-white text-xs font-semibold rounded-lg border border-tcs-border transition-all"
              >
                ← Anterior
              </button>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={handleExportBlueprint}
              className="px-3.5 py-2 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border rounded-lg text-xs font-semibold text-tcs-cyan transition-colors"
              title="Descargar la configuración actual como JSON"
            >
              Exportar Blueprint JSON
            </button>
            {viewMode === 'wizard' && activeStep < 7 ? (
              <button
                type="button"
                onClick={() => setActiveStep(activeStep + 1)}
                className="px-5 py-2 bg-tcs-blue hover:bg-tcs-cyan text-white hover:text-tcs-dark text-xs font-bold rounded-lg shadow transition-all"
              >
                Siguiente →
              </button>
            ) : (
              <button
                type="button"
                onClick={handleStartGeneration}
                disabled={isGenerating}
                className="px-6 py-2.5 bg-gradient-to-r from-tcs-blue to-tcs-cyan hover:from-tcs-accent hover:to-tcs-blue text-white font-bold text-xs rounded-lg shadow-lg transition-all flex items-center space-x-2 disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>Generando Microservicio con LangGraph...</span>
                  </>
                ) : (
                  <>
                    <span>🚀 Generar Microservicio Quarkus con Mis Inputs</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Generated Code & HITL Editor */}
      {currentJob && currentJob.files && currentJob.files.length > 0 && (
        <div className="bg-tcs-card border border-tcs-border rounded-xl p-5 shadow space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-tcs-border pb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>Código Generado & Human-in-the-Loop (HITL)</span>
              </h3>
              <p className="text-xs text-tcs-muted">
                Inspecciona y edita los archivos antes de enviarlos a verificación y empaquetado.
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsVerifierOpen(true)}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg shadow transition-all flex items-center space-x-1.5"
              >
                <span>🛡️ Compilar en Sandbox & Descargar ZIP</span>
              </button>
            </div>
          </div>

          <CodeViewer
            files={currentJob.files}
            onSaveFiles={handleSaveFiles}
            isSaving={isSavingFiles}
            onVerifySandbox={() => setIsVerifierOpen(true)}
          />
        </div>
      )}

      {/* Ephemeral Sandbox Verifier Modal */}
      {isVerifierOpen && currentJob && (
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
