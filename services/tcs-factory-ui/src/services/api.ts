// src/services/api.ts

const PORTS = {
  AUTH: 'http://localhost:8001/api/v1',
  GOVERNANCE: 'http://localhost:8002/api/v1',
  ORCHESTRATOR: 'http://localhost:8003/api/v1',
  VERIFIER: 'http://localhost:8004/api/v1',
};

function getAuthToken(): string | null {
  return localStorage.getItem('tcs_auth_token') || sessionStorage.getItem('tcs_auth_token');
}

export function setStoredToken(token: string, persist: boolean = true) {
  if (persist) {
    localStorage.setItem('tcs_auth_token', token);
  } else {
    sessionStorage.setItem('tcs_auth_token', token);
  }
}

export function clearStoredToken() {
  localStorage.removeItem('tcs_auth_token');
  sessionStorage.removeItem('tcs_auth_token');
}

async function request<T>(baseUrl: string, endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${baseUrl}${endpoint}`;
  const token = getAuthToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err: any) {
    throw new Error(`Microservicio no disponible (${baseUrl}). Asegúrese de que el clúster esté iniciado ejecutando: python scripts/start_factory.py`);
  }

  if (response.status === 401) {
    // If token expired, clear token
    if (endpoint !== '/auth/login' && endpoint !== '/auth/setup-admin') {
      clearStoredToken();
      window.dispatchEvent(new CustomEvent('tcs:unauthorized'));
    }
  }

  if (!response.ok) {
    let errorDetail = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore json parse error on raw error response
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

function normalizeJob(job: any): any {
  if (!job) return job;
  let filesArray: Array<{ path: string; content: string }> = [];
  if (Array.isArray(job.files)) {
    filesArray = job.files;
  } else if (job.files && typeof job.files === 'object') {
    filesArray = Object.entries(job.files).map(([path, content]) => ({
      path,
      content: String(content),
    }));
  }
  return {
    ...job,
    job_id: job.id || job.job_id,
    files: filesArray,
    metrics: {
      total_tokens: (job.prompt_tokens || 0) + (job.completion_tokens || 0),
      prompt_tokens: job.prompt_tokens,
      completion_tokens: job.completion_tokens,
      estimated_cost_usd: job.cost_usd,
      duration_seconds: job.duration_ms ? (job.duration_ms / 1000).toFixed(2) : undefined,
    },
  };
}

export const api = {
  // --- AUTH-ACCESS-SERVICE (:8001) ---
  auth: {
    checkHealth: () => request<{ status: string }>(PORTS.AUTH, '/health'),
    setupAdmin: (data: { email: string; password: string; full_name: string }) =>
      request<any>(PORTS.AUTH, '/auth/setup-admin', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    login: (data: { email: string; password: string }) =>
      request<{ access_token: string; token_type: string; user: any }>(PORTS.AUTH, '/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getMe: () => request<any>(PORTS.AUTH, '/auth/me'),
    getMeClients: () => request<{ user_id: string; role: string; is_admin: boolean; client_codes: string[] }>(PORTS.AUTH, '/auth/me/clients'),
    listUsers: (role?: string) =>
      request<any[]>(PORTS.AUTH, `/users${role ? `?role=${role}` : ''}`),
    createUser: (data: { email: string; password: string; full_name: string; role: string }) =>
      request<any>(PORTS.AUTH, '/users', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    updateUserClients: (userId: string, clientCodes: string[]) =>
      request<any>(PORTS.AUTH, `/users/${userId}/clients`, {
        method: 'PUT',
        body: JSON.stringify({ client_codes: clientCodes }),
      }),
  },

  // --- CLIENT-GOVERNANCE-SERVICE (:8002) ---
  governance: {
    checkHealth: () => request<{ status: string }>(PORTS.GOVERNANCE, '/health'),
    listClients: (activeOnly: boolean = false) =>
      request<any[]>(PORTS.GOVERNANCE, `/clients?active_only=${activeOnly}`),
    createClient: (data: { code: string; name: string; description?: string; package_prefix?: string; java_version?: string; quarkus_version?: string }) =>
      request<any>(PORTS.GOVERNANCE, '/clients', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getClient: (clientCode: string) =>
      request<any>(PORTS.GOVERNANCE, `/clients/${clientCode}`),
    listDirectives: (clientCode: string) =>
      request<any[]>(PORTS.GOVERNANCE, `/clients/${clientCode}/directives`),
    createDirective: (clientCode: string, data: {
      category: string;
      rule_code: string;
      title: string;
      description: string;
      pattern?: string;
      severity?: string;
      is_mandatory?: boolean;
    }) =>
      request<any>(PORTS.GOVERNANCE, `/clients/${clientCode}/directives`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    listContracts: (clientCode: string) =>
      request<any[]>(PORTS.GOVERNANCE, `/clients/${clientCode}/contracts`),
    uploadContract: (clientCode: string, data: { title: string; version: string; raw_content: string }) =>
      request<any>(PORTS.GOVERNANCE, `/clients/${clientCode}/contracts`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getConsolidated: (clientCode: string) =>
      request<any>(PORTS.GOVERNANCE, `/governance/clients/${clientCode}`),
  },

  // --- AI-ORCHESTRATOR-SERVICE (:8003) ---
  orchestrator: {
    checkHealth: () => request<{ status: string }>(PORTS.ORCHESTRATOR, '/health'),
    setupDirectKey: (data: { api_key: string; model_name?: string; provider?: string }) =>
      request<{ success: boolean; provider: string; model_name?: string; masked_key?: string; message: string; latency_ms: number }>(
        PORTS.ORCHESTRATOR,
        '/vault/direct-key',
        {
          method: 'POST',
          body: JSON.stringify(data),
        }
      ),
    getVaultStatus: async () => {
      try {
        const res = await request<any>(PORTS.ORCHESTRATOR, '/vault/status');
        if (res && res.providers) return res;
      } catch {
        // Fallback to /vault/keys
      }
      try {
        const keysList = await request<any[]>(PORTS.ORCHESTRATOR, '/vault/keys');
        const providers: Record<string, { configured: boolean; masked_key?: string }> = {};
        if (Array.isArray(keysList)) {
          for (const k of keysList) {
            providers[k.provider.toUpperCase()] = {
              configured: !!k.is_active,
              masked_key: k.masked_key,
            };
          }
        }
        return { providers };
      } catch {
        return { providers: {} };
      }
    },
    setVaultKey: (data: { provider: string; api_key: string }) =>
      request<any>(PORTS.ORCHESTRATOR, '/vault/keys', {
        method: 'POST',
        body: JSON.stringify({
          provider: data.provider.toLowerCase(),
          api_key: data.api_key,
        }),
      }),
    testVaultKey: async (provider: string, apiKey?: string, modelName?: string) => {
      const payload: any = { provider: provider.toLowerCase() };
      if (apiKey) payload.api_key = apiKey;
      if (modelName) payload.model_name = modelName;
      try {
        const res = await request<any>(PORTS.ORCHESTRATOR, '/vault/test-connection', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        return {
          status: res.connected ? 'OK' : 'FAILED',
          provider: res.provider || provider,
          message: res.message || (res.connected ? 'Conectado exitosamente' : 'Fallo de autenticación'),
        };
      } catch (err: any) {
        return {
          status: 'FAILED',
          provider,
          message: err.message || 'Error en prueba de conexión',
        };
      }
    },
    getGatewayConfig: () =>
      request<{ active_provider: string; model_name?: string; consumption_mode?: string; tier?: string }>(PORTS.ORCHESTRATOR, '/ai-gateway/config'),
    updateGatewayConfig: (data: { active_provider: string; model_name?: string; tier?: string }) =>
      request<any>(PORTS.ORCHESTRATOR, '/ai-gateway/config', {
        method: 'PUT',
        body: JSON.stringify({
          active_provider: data.active_provider.toLowerCase(),
          model_name: data.model_name || undefined,
          consumption_mode: data.tier ? data.tier.toLowerCase() : 'balanced',
        }),
      }),
    listJobs: async () => {
      const list = await request<any[]>(PORTS.ORCHESTRATOR, '/orchestrator/jobs');
      return Array.isArray(list) ? list.map(normalizeJob) : [];
    },
    getConsumptionTelemetry: () =>
      request<any>(PORTS.ORCHESTRATOR, '/orchestrator/consumption'),
    inferSpec: (data: { client_code: string; requirements: string }) =>
      request<any>(PORTS.ORCHESTRATOR, '/orchestrator/infer-spec', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    createJob: async (data: {
      client_code: string;
      raw_requirement?: string;
      requirements?: string;
      architecture_style?: string;
      custom_architecture_notes?: string;
      security_option?: string;
      jwt_issuer?: string;
      security_roles?: string[];
      communication_protocol?: string;
      custom_endpoints?: any[];
      database_option?: string;
      database_name?: string;
      package_prefix?: string;
      artifact_id?: string;
      http_port?: number;
      java_version?: string;
      quarkus_version?: string;
      build_tool?: string;
      design_patterns?: string[];
      naming_conventions?: any;
      event_broker?: string;
      channels?: any[];
      extensions?: string[];
      custom_extensions?: string[];
      custom_properties?: any;
      entities?: any[];
      contract_id?: string;
    }) => {
      const reqText = data.requirements || data.raw_requirement || '';
      const payload = {
        client_code: data.client_code.toLowerCase(),
        requirements: reqText,
        raw_requirement: reqText,
        architecture_style: data.architecture_style || undefined,
        custom_architecture_notes: data.custom_architecture_notes || undefined,
        security_option: data.security_option || undefined,
        jwt_issuer: data.jwt_issuer || undefined,
        security_roles: data.security_roles || undefined,
        communication_protocol: data.communication_protocol || undefined,
        custom_endpoints: data.custom_endpoints || [],
        database_option: data.database_option || undefined,
        database_name: data.database_name || undefined,
        package_prefix: data.package_prefix || undefined,
        artifact_id: data.artifact_id || undefined,
        http_port: data.http_port || 8080,
        java_version: data.java_version || undefined,
        quarkus_version: data.quarkus_version || undefined,
        build_tool: data.build_tool || 'maven',
        design_patterns: data.design_patterns || [],
        naming_conventions: data.naming_conventions || {},
        event_broker: data.event_broker || 'none',
        channels: data.channels || [],
        extensions: data.extensions || [],
        custom_extensions: data.custom_extensions || [],
        custom_properties: data.custom_properties || undefined,
        entities: data.entities || [],
        contract_id: data.contract_id || undefined,
      };
      const res = await request<any>(PORTS.ORCHESTRATOR, '/orchestrator/jobs', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      return normalizeJob(res);
    },
    getJob: async (jobId: string) => {
      const res = await request<any>(PORTS.ORCHESTRATOR, `/orchestrator/jobs/${jobId}`);
      return normalizeJob(res);
    },
    patchJobFiles: async (jobId: string, files: Array<{ path: string; content: string }>) => {
      const filesMap: Record<string, string> = {};
      if (Array.isArray(files)) {
        files.forEach((f) => {
          filesMap[f.path] = f.content;
        });
      }
      const res = await request<any>(PORTS.ORCHESTRATOR, `/orchestrator/jobs/${jobId}/files`, {
        method: 'PATCH',
        body: JSON.stringify({ files: filesMap }),
      });
      return normalizeJob(res);
    },
  },

  // --- SANDBOX-VERIFIER-SERVICE (:8004) ---
  verifier: {
    checkHealth: () => request<{ status: string }>(PORTS.VERIFIER, '/health'),
    createRun: (data: {
      client_code: string;
      job_id?: string;
      files: Array<{ path: string; content: string }>;
    }) => {
      const filesMap: Record<string, string> = {};
      if (Array.isArray(data.files)) {
        data.files.forEach((f) => {
          filesMap[f.path] = f.content;
        });
      }
      return request<any>(PORTS.VERIFIER, '/verifier/runs', {
        method: 'POST',
        body: JSON.stringify({
          client_code: data.client_code.toLowerCase(),
          job_id: data.job_id,
          files: filesMap,
        }),
      });
    },
    getRun: (runId: string) =>
      request<any>(PORTS.VERIFIER, `/verifier/runs/${runId}`),
    getManifest: (runId: string) =>
      request<any>(PORTS.VERIFIER, `/verifier/runs/${runId}/manifest`),
    getDownloadUrl: (runId: string) => `http://localhost:8004/api/v1/verifier/runs/${runId}/download`,
  },
};

