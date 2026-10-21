// src/components/AdminPanel.tsx
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { User, ClientProfile, Directive, OpenApiSpecSummary, AiProvider, GatewayTier } from '../types';

export const AdminPanel: React.FC = () => {
  const [subTab, setSubTab] = useState<'users' | 'vault' | 'clients'>('users');
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // --- Users State ---
  const [users, setUsers] = useState<User[]>([]);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserFullName, setNewUserFullName] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [newUserRole, setNewUserRole] = useState<'ADMIN' | 'DEVELOPER'>('DEVELOPER');
  const [selectedUserForClients, setSelectedUserForClients] = useState<User | null>(null);
  const [userClientsInput, setUserClientsInput] = useState('');

  // --- Vault & Gateway State ---
  const [vaultStatus, setVaultStatus] = useState<Record<string, { configured: boolean; masked_key?: string }>>({});
  const [vaultKeyProvider, setVaultKeyProvider] = useState<AiProvider>('GEMINI');
  const [vaultApiKey, setVaultApiKey] = useState('');
  const [gatewayConfig, setGatewayConfig] = useState<{ active_provider: AiProvider; model_name: string }>({
    active_provider: 'MOCK',
    model_name: 'mock-fast',
  });
  const [testResult, setTestResult] = useState<{ provider: string; status: string; message: string } | null>(null);

  // --- Clients & Directives State ---
  const [clients, setClients] = useState<ClientProfile[]>([]);
  const [selectedClientCode, setSelectedClientCode] = useState<string>('');
  const [newClientCode, setNewClientCode] = useState('');
  const [newClientName, setNewClientName] = useState('');
  const [newClientDesc, setNewClientDesc] = useState('');

  const [directives, setDirectives] = useState<Directive[]>([]);
  const [newDirCategory, setNewDirCategory] = useState<'SECURITY' | 'ARCHITECTURE' | 'DATABASE' | 'OBSERVABILITY'>('ARCHITECTURE');
  const [newDirRuleCode, setNewDirRuleCode] = useState('');
  const [newDirTitle, setNewDirTitle] = useState('');
  const [newDirDesc, setNewDirDesc] = useState('');

  const [contracts, setContracts] = useState<OpenApiSpecSummary[]>([]);
  const [newContractTitle, setNewContractTitle] = useState('');
  const [newContractVersion, setNewContractVersion] = useState('1.0.0');
  const [newContractYaml, setNewContractYaml] = useState('');

  const showFeedback = (type: 'success' | 'error', message: string) => {
    setFeedback({ type, message });
    setTimeout(() => setFeedback(null), 5000);
  };

  // Loaders
  const loadUsers = async () => {
    try {
      const data = await api.auth.listUsers();
      setUsers(data);
    } catch (err: any) {
      showFeedback('error', 'Error al cargar colaboradores: ' + err.message);
    }
  };

  const loadVaultAndGateway = async () => {
    try {
      const vStatus = await api.orchestrator.getVaultStatus();
      setVaultStatus(vStatus.providers || {});
      const gConfig = await api.orchestrator.getGatewayConfig();
      setGatewayConfig({
        active_provider: (gConfig.active_provider ? gConfig.active_provider.toUpperCase() : 'MOCK') as AiProvider,
        model_name: gConfig.model_name || 'gemini-2.5-flash',
      });
    } catch (err: any) {
      showFeedback('error', 'Error al cargar bóveda de IA: ' + err.message);
    }
  };

  const loadClients = async () => {
    try {
      const data = await api.governance.listClients(false);
      setClients(data);
      if (data.length > 0 && !selectedClientCode) {
        setSelectedClientCode(data[0].code || data[0].client_id);
      }
    } catch (err: any) {
      showFeedback('error', 'Error al cargar clientes: ' + err.message);
    }
  };

  const loadClientDetails = async (clientCode: string) => {
    if (!clientCode) return;
    try {
      const [dirs, cts] = await Promise.all([
        api.governance.listDirectives(clientCode).catch(() => []),
        api.governance.listContracts(clientCode).catch(() => []),
      ]);
      setDirectives(dirs);
      setContracts(cts);
    } catch (err: any) {
      showFeedback('error', 'Error al cargar gobernanza del cliente: ' + err.message);
    }
  };

  useEffect(() => {
    if (subTab === 'users') loadUsers();
    if (subTab === 'vault') loadVaultAndGateway();
    if (subTab === 'clients') loadClients();
  }, [subTab]);

  useEffect(() => {
    if (selectedClientCode) {
      loadClientDetails(selectedClientCode);
    }
  }, [selectedClientCode]);

  // Actions: User Management
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.auth.createUser({
        email: newUserEmail,
        full_name: newUserFullName,
        password: newUserPassword,
        role: newUserRole,
      });
      showFeedback('success', `Usuario ${newUserEmail} creado exitosamente`);
      setNewUserEmail('');
      setNewUserFullName('');
      setNewUserPassword('');
      await loadUsers();
    } catch (err: any) {
      showFeedback('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateClients = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserForClients) return;
    setLoading(true);
    try {
      const clientList = userClientsInput
        .split(',')
        .map((c) => c.trim().toLowerCase())
        .filter(Boolean);
      await api.auth.updateUserClients(selectedUserForClients.id, clientList);
      showFeedback('success', 'Clientes asignados actualizados exitosamente');
      setSelectedUserForClients(null);
      await loadUsers();
    } catch (err: any) {
      showFeedback('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  // Actions: Vault & Gateway
  const handleSaveVaultKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.orchestrator.setVaultKey({
        provider: vaultKeyProvider,
        api_key: vaultApiKey,
      });
      showFeedback('success', `Credencial guardada para ${vaultKeyProvider}`);
      setVaultApiKey('');
      await loadVaultAndGateway();
    } catch (err: any) {
      showFeedback('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTestKey = async (provider: string) => {
    setLoading(true);
    setTestResult(null);
    try {
      const res = await api.orchestrator.testVaultKey(provider);
      setTestResult(res);
      showFeedback('success', `Prueba ${provider}: ${res.status}`);
    } catch (err: any) {
      setTestResult({ provider, status: 'FAILED', message: err.message });
      showFeedback('error', `Fallo al probar ${provider}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateGateway = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.orchestrator.updateGatewayConfig({
        active_provider: gatewayConfig.active_provider,
        model_name: gatewayConfig.model_name,
      });
      showFeedback('success', 'Configuración de Gateway de IA actualizada');
      await loadVaultAndGateway();
    } catch (err: any) {
      showFeedback('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  // Actions: Client Governance
  const handleCreateClient = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.governance.createClient({
        code: newClientCode.trim().toLowerCase(),
        name: newClientName.trim(),
        description: newClientDesc.trim(),
      });
      showFeedback('success', `Cliente ${newClientCode} creado exitosamente`);
      setNewClientCode('');
      setNewClientName('');
      setNewClientDesc('');
      await loadClients();
    } catch (err: any) {
      showFeedback('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDirective = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClientCode) return;
    setLoading(true);
    try {
      await api.governance.createDirective(selectedClientCode, {
        category: newDirCategory,
        rule_code: newDirRuleCode.trim().toUpperCase(),
        title: newDirTitle.trim(),
        description: newDirDesc.trim(),
        severity: 'MANDATORY',
        is_mandatory: true,
      });
      showFeedback('success', 'Directiva agregada exitosamente');
      setNewDirRuleCode('');
      setNewDirTitle('');
      setNewDirDesc('');
      await loadClientDetails(selectedClientCode);
    } catch (err: any) {
      showFeedback('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadContract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClientCode) return;
    setLoading(true);
    try {
      await api.governance.uploadContract(selectedClientCode, {
        title: newContractTitle.trim(),
        version: newContractVersion.trim(),
        raw_content: newContractYaml.trim(),
      });
      showFeedback('success', 'Contrato OpenAPI catalogado exitosamente');
      setNewContractTitle('');
      setNewContractYaml('');
      await loadClientDetails(selectedClientCode);
    } catch (err: any) {
      showFeedback('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* SubTab navigation */}
      <div className="flex items-center justify-between border-b border-tcs-border pb-4">
        <div className="flex space-x-2">
          <button
            onClick={() => setSubTab('users')}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
              subTab === 'users' ? 'bg-tcs-blue text-white shadow' : 'bg-tcs-card text-tcs-muted hover:text-white'
            }`}
          >
            Colaboradores & Roles (RBAC)
          </button>
          <button
            onClick={() => setSubTab('vault')}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
              subTab === 'vault' ? 'bg-tcs-blue text-white shadow' : 'bg-tcs-card text-tcs-muted hover:text-white'
            }`}
          >
            Bóveda de IA & Gateway
          </button>
          <button
            onClick={() => setSubTab('clients')}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
              subTab === 'clients' ? 'bg-tcs-blue text-white shadow' : 'bg-tcs-card text-tcs-muted hover:text-white'
            }`}
          >
            Gobernanza de Clientes & Contratos
          </button>
        </div>

        {feedback && (
          <div
            className={`text-xs px-3 py-1.5 rounded-lg border flex items-center space-x-2 ${
              feedback.type === 'success'
                ? 'bg-emerald-950/60 border-emerald-700 text-emerald-300'
                : 'bg-rose-950/60 border-rose-700 text-rose-300'
            }`}
          >
            <span>{feedback.message}</span>
          </div>
        )}
      </div>

      {/* SUBTAB 1: USERS */}
      {subTab === 'users' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Create User Card */}
          <div className="bg-tcs-card border border-tcs-border rounded-xl p-5 shadow">
            <h3 className="text-sm font-bold text-white mb-1 flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-tcs-blue"></span>
              <span>Registrar Colaborador TCS</span>
            </h3>
            <p className="text-xs text-tcs-muted mb-4">
              Crea usuarios con roles estrictos: ADMIN o DEVELOPER.
            </p>

            <form onSubmit={handleCreateUser} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">Nombre Completo</label>
                <input
                  type="text"
                  required
                  value={newUserFullName}
                  onChange={(e) => setNewUserFullName(e.target.value)}
                  placeholder="Ej. Juan Pérez"
                  className="w-full px-3 py-1.5 bg-tcs-dark border border-tcs-border rounded-md text-xs text-white focus:outline-none focus:border-tcs-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">Correo Corporativo</label>
                <input
                  type="email"
                  required
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  placeholder="jperez@tcs.com"
                  className="w-full px-3 py-1.5 bg-tcs-dark border border-tcs-border rounded-md text-xs text-white focus:outline-none focus:border-tcs-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">Contraseña</label>
                <input
                  type="password"
                  required
                  value={newUserPassword}
                  onChange={(e) => setNewUserPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-3 py-1.5 bg-tcs-dark border border-tcs-border rounded-md text-xs text-white focus:outline-none focus:border-tcs-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">Rol de Acceso (Principio XV)</label>
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value as any)}
                  className="w-full px-3 py-1.5 bg-tcs-dark border border-tcs-border rounded-md text-xs text-white focus:outline-none focus:border-tcs-blue"
                >
                  <option value="DEVELOPER">DEVELOPER (Acceso limitado a clientes asignados)</option>
                  <option value="ADMIN">ADMIN (Acceso total & configuración)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 py-2 bg-tcs-blue hover:bg-tcs-accent text-white text-xs font-semibold rounded-md transition-colors disabled:opacity-50"
              >
                {loading ? 'Creando...' : 'Crear Colaborador'}
              </button>
            </form>
          </div>

          {/* List Users Card */}
          <div className="lg:col-span-2 bg-tcs-card border border-tcs-border rounded-xl p-5 shadow">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-white">Directorio de Colaboradores</h3>
                <p className="text-xs text-tcs-muted">Control de asignaciones por cliente (Aislamiento de Cuentas)</p>
              </div>
              <button
                onClick={loadUsers}
                className="text-xs px-2.5 py-1 bg-tcs-surface border border-tcs-border rounded text-tcs-muted hover:text-white"
              >
                Actualizar
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-tcs-border text-tcs-muted font-medium">
                    <th className="pb-2">Colaborador</th>
                    <th className="pb-2">Rol</th>
                    <th className="pb-2">Clientes Asignados</th>
                    <th className="pb-2 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-tcs-border/50">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-tcs-surface/30">
                      <td className="py-2.5">
                        <div className="font-semibold text-white">{u.full_name || u.username}</div>
                        <div className="text-[11px] text-tcs-muted">{u.email}</div>
                      </td>
                      <td className="py-2.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                            u.role === 'ADMIN'
                              ? 'bg-purple-900/40 text-purple-300 border border-purple-800'
                              : 'bg-cyan-900/40 text-cyan-300 border border-cyan-800'
                          }`}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td className="py-2.5">
                        {u.role === 'ADMIN' ? (
                          <span className="text-[11px] text-tcs-muted italic">Todos (*)</span>
                        ) : u.assigned_clients && u.assigned_clients.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {u.assigned_clients.map((c) => (
                              <span
                                key={c}
                                className="px-1.5 py-0.5 rounded bg-tcs-dark border border-tcs-border text-[10px] text-tcs-cyan font-mono"
                              >
                                {c}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-[11px] text-rose-400 italic">Sin clientes asignados</span>
                        )}
                      </td>
                      <td className="py-2.5 text-right">
                        {u.role === 'DEVELOPER' && (
                          <button
                            onClick={() => {
                              setSelectedUserForClients(u);
                              setUserClientsInput((u.assigned_clients || []).join(', '));
                            }}
                            className="text-xs text-tcs-blue hover:text-tcs-cyan underline font-medium"
                          >
                            Asignar Clientes
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-4 text-center text-tcs-muted">
                        No hay usuarios registrados.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Modal for editing assigned clients */}
            {selectedUserForClients && (
              <div className="mt-4 p-4 bg-tcs-dark border border-tcs-blue rounded-lg animate-in fade-in">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold text-white">
                    Asignar Cuentas a {selectedUserForClients.full_name} ({selectedUserForClients.email})
                  </span>
                  <button
                    onClick={() => setSelectedUserForClients(null)}
                    className="text-xs text-tcs-muted hover:text-white"
                  >
                    ✕
                  </button>
                </div>
                <p className="text-[11px] text-tcs-muted mb-2">
                  Ingrese los códigos de clientes separados por coma (ej: <code>bcp, retail-corp</code>).
                </p>
                <form onSubmit={handleUpdateClients} className="flex gap-2">
                  <input
                    type="text"
                    value={userClientsInput}
                    onChange={(e) => setUserClientsInput(e.target.value)}
                    placeholder="bcp, retail-corp"
                    className="flex-1 px-3 py-1.5 bg-tcs-card border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-3 py-1.5 bg-tcs-blue hover:bg-tcs-accent text-white text-xs font-semibold rounded"
                  >
                    Guardar
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SUBTAB 2: VAULT & GATEWAY */}
      {subTab === 'vault' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* AI Vault Section */}
          <div className="bg-tcs-card border border-tcs-border rounded-xl p-5 shadow space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>Bóveda Cifrada de Credenciales (Fernet)</span>
              </h3>
              <p className="text-xs text-tcs-muted">
                Almacena llaves de API cifradas con Fernet sin fugas ni almacenamiento en plano.
              </p>
            </div>

            {/* Providers Status Cards */}
            <div className="grid grid-cols-2 gap-3">
              {(['GEMINI', 'DEEPSEEK', 'GROK', 'MOCK'] as AiProvider[]).map((prov) => {
                const info = vaultStatus[prov];
                const isConf = prov === 'MOCK' ? true : info?.configured;
                return (
                  <div key={prov} className="p-3 bg-tcs-dark border border-tcs-border rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-white">{prov}</span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                          isConf
                            ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800'
                            : 'bg-rose-950/60 text-rose-400 border border-rose-800'
                        }`}
                      >
                        {isConf ? 'CONFIGURADO' : 'PENDIENTE'}
                      </span>
                    </div>
                    {prov !== 'MOCK' && (
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-[10px] font-mono text-tcs-muted">
                          {info?.masked_key || '••••••••'}
                        </span>
                        <button
                          type="button"
                          disabled={!isConf || loading}
                          onClick={() => handleTestKey(prov)}
                          className="text-[10px] px-2 py-0.5 bg-tcs-surface border border-tcs-border rounded text-tcs-cyan hover:border-tcs-cyan disabled:opacity-30"
                        >
                          Probar
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {testResult && (
              <div
                className={`p-2.5 rounded-lg border text-xs font-mono ${
                  testResult.status === 'OK' || testResult.status === 'SUCCESS'
                    ? 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
                    : 'bg-rose-950/60 border-rose-800 text-rose-300'
                }`}
              >
                Prueba {testResult.provider}: {testResult.message}
              </div>
            )}

            {/* Add / Rotate Key Form */}
            <form onSubmit={handleSaveVaultKey} className="pt-3 border-t border-tcs-border space-y-3">
              <span className="text-xs font-bold text-white block">Registrar o Rotar Llave</span>
              <div className="grid grid-cols-3 gap-2">
                <select
                  value={vaultKeyProvider}
                  onChange={(e) => setVaultKeyProvider(e.target.value as AiProvider)}
                  className="px-2 py-1.5 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue"
                >
                  <option value="GEMINI">GEMINI</option>
                  <option value="DEEPSEEK">DEEPSEEK</option>
                  <option value="GROK">GROK</option>
                </select>
                <input
                  type="password"
                  required
                  value={vaultApiKey}
                  onChange={(e) => setVaultApiKey(e.target.value)}
                  placeholder="Pegar API Key"
                  className="col-span-2 px-3 py-1.5 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                />
              </div>
              <button
                type="submit"
                disabled={loading || !vaultApiKey}
                className="w-full py-1.5 bg-tcs-blue hover:bg-tcs-accent text-white text-xs font-semibold rounded transition-colors disabled:opacity-50"
              >
                Cifrar y Guardar en Bóveda
              </button>
            </form>
          </div>

          {/* AI Gateway Hot-Switching Section */}
          <div className="bg-tcs-card border border-tcs-border rounded-xl p-5 shadow space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-tcs-cyan"></span>
                <span>Conmutador de Gateway de IA en Caliente</span>
              </h3>
              <p className="text-xs text-tcs-muted">
                Cambia el motor LLM subyacente sin reiniciar microservicios ni interrumpir operaciones.
              </p>
            </div>

            <form onSubmit={handleUpdateGateway} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">Proveedor Activo</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['MOCK', 'GEMINI', 'DEEPSEEK', 'GROK'] as AiProvider[]).map((prov) => (
                    <button
                      type="button"
                      key={prov}
                      onClick={() => setGatewayConfig({ ...gatewayConfig, active_provider: prov })}
                      className={`p-3 text-left rounded-lg border transition-all ${
                        gatewayConfig.active_provider === prov
                          ? 'bg-tcs-blue/20 border-tcs-blue text-white'
                          : 'bg-tcs-dark border-tcs-border text-tcs-muted hover:border-tcs-muted'
                      }`}
                    >
                      <div className="text-xs font-bold">{prov}</div>
                      <div className="text-[10px] text-tcs-muted">
                        {prov === 'MOCK' ? 'Determinista offline' : 'Motor LLM en Vivo'}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-tcs-muted mb-1">Nombre del Modelo LLM</label>
                <input
                  type="text"
                  required
                  value={gatewayConfig.model_name}
                  onChange={(e) => setGatewayConfig({ ...gatewayConfig, model_name: e.target.value })}
                  placeholder="ej. gemini-2.5-flash, deepseek-chat, grok-beta, mock-fast"
                  className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                />
                <span className="text-[10px] text-tcs-muted mt-1 block">
                  Ingesta directa del modelo según el proveedor seleccionado (sin intermediarios de modos de consumo).
                </span>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2 bg-tcs-blue hover:bg-tcs-accent text-white text-xs font-semibold rounded transition-colors disabled:opacity-50"
              >
                {loading ? 'Guardando...' : 'Aplicar Cambio en Caliente'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* SUBTAB 3: CLIENT GOVERNANCE */}
      {subTab === 'clients' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Create Client Form */}
            <div className="bg-tcs-card border border-tcs-border rounded-xl p-5 shadow">
              <h3 className="text-sm font-bold text-white mb-1">Nuevo Perfil de Cliente</h3>
              <p className="text-xs text-tcs-muted mb-4">Crea una cuenta corporativa agnóstica.</p>

              <form onSubmit={handleCreateClient} className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-tcs-muted mb-1">Código de Cliente (slug)</label>
                  <input
                    type="text"
                    required
                    value={newClientCode}
                    onChange={(e) => setNewClientCode(e.target.value)}
                    placeholder="bcp, santander, falabella"
                    className="w-full px-3 py-1.5 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-tcs-muted mb-1">Nombre Comercial</label>
                  <input
                    type="text"
                    required
                    value={newClientName}
                    onChange={(e) => setNewClientName(e.target.value)}
                    placeholder="Banco de Crédito del Perú"
                    className="w-full px-3 py-1.5 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-tcs-muted mb-1">Descripción</label>
                  <textarea
                    rows={2}
                    value={newClientDesc}
                    onChange={(e) => setNewClientDesc(e.target.value)}
                    placeholder="Sector financiero, banca móvil..."
                    className="w-full px-3 py-1.5 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2 bg-tcs-blue hover:bg-tcs-accent text-white text-xs font-semibold rounded"
                >
                  Registrar Cuenta
                </button>
              </form>
            </div>

            {/* Client Selector & Overview */}
            <div className="lg:col-span-2 bg-tcs-card border border-tcs-border rounded-xl p-5 shadow">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold text-white">Cuentas Corporativas Activas</h3>
                  <p className="text-xs text-tcs-muted">Seleccione una cuenta para gestionar sus directivas y contratos</p>
                </div>
                <select
                  value={selectedClientCode}
                  onChange={(e) => setSelectedClientCode(e.target.value)}
                  className="px-3 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-white focus:outline-none focus:border-tcs-blue font-mono"
                >
                  {clients.map((c: any) => (
                    <option key={c.code || c.client_id} value={c.code || c.client_id}>
                      {c.name} ({c.code || c.client_id})
                    </option>
                  ))}
                  {clients.length === 0 && <option value="">Sin clientes</option>}
                </select>
              </div>

              {selectedClientCode ? (
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-tcs-dark border border-tcs-border rounded-lg">
                    <span className="text-xs font-semibold text-tcs-muted">Directivas Técnicas</span>
                    <div className="text-2xl font-bold text-white mt-1">{directives.length}</div>
                    <span className="text-[11px] text-tcs-cyan">Reglas arquitectónicas forzadas</span>
                  </div>
                  <div className="p-4 bg-tcs-dark border border-tcs-border rounded-lg">
                    <span className="text-xs font-semibold text-tcs-muted">Contratos OpenAPI</span>
                    <div className="text-2xl font-bold text-white mt-1">{contracts.length}</div>
                    <span className="text-[11px] text-tcs-cyan">Especificaciones catalogadas</span>
                  </div>
                </div>
              ) : (
                <div className="p-6 text-center text-tcs-muted text-xs">
                  No hay cuentas registradas. Utilice el formulario de la izquierda para registrar una cuenta piloto.
                </div>
              )}
            </div>
          </div>

          {/* Directives & OpenAPI Tabs for Selected Client */}
          {selectedClientCode && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Directives Management */}
              <div className="bg-tcs-card border border-tcs-border rounded-xl p-5 shadow space-y-4">
                <div className="flex justify-between items-center">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Directivas Técnicas ({selectedClientCode})
                  </h4>
                  <span className="text-[11px] text-tcs-muted">{directives.length} activas</span>
                </div>

                <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
                  {directives.map((d: any) => (
                    <div key={d.id} className="p-2.5 bg-tcs-dark border border-tcs-border rounded-md text-xs">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-white">{d.title}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-tcs-surface border border-tcs-border text-tcs-cyan font-mono">
                          {d.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-tcs-muted">{d.description || d.content}</p>
                    </div>
                  ))}
                  {directives.length === 0 && (
                    <div className="p-4 text-center text-tcs-muted text-xs italic">
                      Sin directivas registradas para este cliente.
                    </div>
                  )}
                </div>

                {/* Add Directive Form */}
                <form onSubmit={handleCreateDirective} className="pt-3 border-t border-tcs-border space-y-2">
                  <span className="text-xs font-bold text-white block">Agregar Directiva</span>
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={newDirCategory}
                      onChange={(e) => setNewDirCategory(e.target.value as any)}
                      className="px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-white"
                    >
                      <option value="ARCHITECTURE">ARCHITECTURE</option>
                      <option value="SECURITY">SECURITY</option>
                      <option value="DATABASE">DATABASE</option>
                      <option value="OBSERVABILITY">OBSERVABILITY</option>
                    </select>
                    <input
                      type="text"
                      required
                      placeholder="Código (ej. SEC-01)"
                      value={newDirRuleCode}
                      onChange={(e) => setNewDirRuleCode(e.target.value)}
                      className="px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-white uppercase font-mono"
                    />
                  </div>
                  <input
                    type="text"
                    required
                    placeholder="Título de la directiva"
                    value={newDirTitle}
                    onChange={(e) => setNewDirTitle(e.target.value)}
                    className="w-full px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-white"
                  />
                  <textarea
                    rows={2}
                    required
                    placeholder="Descripción técnica del lineamiento..."
                    value={newDirDesc}
                    onChange={(e) => setNewDirDesc(e.target.value)}
                    className="w-full px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-white"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-1.5 bg-tcs-blue hover:bg-tcs-accent text-white text-xs font-semibold rounded"
                  >
                    Guardar Directiva
                  </button>
                </form>
              </div>

              {/* OpenAPI Contracts Management */}
              <div className="bg-tcs-card border border-tcs-border rounded-xl p-5 shadow space-y-4">
                <div className="flex justify-between items-center">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Contratos OpenAPI ({selectedClientCode})
                  </h4>
                  <span className="text-[11px] text-tcs-muted">{contracts.length} catalogados</span>
                </div>

                <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
                  {contracts.map((c: any) => (
                    <div key={c.id} className="p-2.5 bg-tcs-dark border border-tcs-border rounded-md text-xs">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-white">{c.title}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-tcs-surface border border-tcs-border text-tcs-cyan font-mono">
                          v{c.version}
                        </span>
                      </div>
                      <div className="text-[10px] text-tcs-muted font-mono truncate">
                        ID: {c.id}
                      </div>
                    </div>
                  ))}
                  {contracts.length === 0 && (
                    <div className="p-4 text-center text-tcs-muted text-xs italic">
                      Sin especificaciones OpenAPI catalogadas.
                    </div>
                  )}
                </div>

                {/* Upload Contract Form */}
                <form onSubmit={handleUploadContract} className="pt-3 border-t border-tcs-border space-y-2">
                  <span className="text-xs font-bold text-white block">Catalogar Especificación OpenAPI</span>
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="text"
                      required
                      placeholder="Título (ej. Accounts API)"
                      value={newContractTitle}
                      onChange={(e) => setNewContractTitle(e.target.value)}
                      className="px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-white"
                    />
                    <input
                      type="text"
                      required
                      placeholder="Versión (ej. 1.0.0)"
                      value={newContractVersion}
                      onChange={(e) => setNewContractVersion(e.target.value)}
                      className="px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-white font-mono"
                    />
                  </div>
                  <textarea
                    rows={4}
                    required
                    placeholder="Pegar contenido YAML o JSON de OpenAPI 3.x..."
                    value={newContractYaml}
                    onChange={(e) => setNewContractYaml(e.target.value)}
                    className="w-full px-2 py-1 bg-tcs-dark border border-tcs-border rounded text-xs text-white font-mono"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-1.5 bg-tcs-blue hover:bg-tcs-accent text-white text-xs font-semibold rounded"
                  >
                    Catalogar Contrato
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

