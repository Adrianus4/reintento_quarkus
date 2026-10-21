# Data Model: Spec 005 — tcs-factory-ui

## 1. Domain Entities & Frontend Types

### 1.1 User & Auth Session (`auth-access-service` :8001)
```typescript
export type Role = 'ADMIN' | 'DEVELOPER';

export interface User {
  id: string;
  username: string;
  email: string;
  role: Role;
  assigned_clients: string[];
  is_active: boolean;
  created_at: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  role: Role;
  username: string;
  assigned_clients: string[];
}
```

### 1.2 Client Profile & Directives (`client-governance-service` :8002)
```typescript
export interface ClientProfile {
  client_id: string;
  name: string;
  description?: string;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string;
}

export interface Directive {
  id: string;
  client_id: string;
  category: 'SECURITY' | 'ARCHITECTURE' | 'DATABASE' | 'OBSERVABILITY';
  title: string;
  content: string;
  priority: number;
}

export interface OpenApiSpecSummary {
  id: string;
  client_id: string;
  title: string;
  version: string;
  description?: string;
  endpoints_count?: number;
}
```

### 1.3 AI Gateway, Vault & Orchestrator Job (`ai-orchestrator-service` :8003)
```typescript
export type AiProvider = 'GEMINI' | 'DEEPSEEK' | 'GROK' | 'MOCK';
export type GatewayTier = 'economic' | 'balanced' | 'advanced';

export interface AiGatewayConfig {
  active_provider: AiProvider;
  tier: GatewayTier;
}

export interface VaultCredentialStatus {
  provider: AiProvider;
  configured: boolean;
  last_updated?: string;
}

export type JobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'REJECTED';
export type PipelineStage = 'INGESTION' | 'ARCHITECTURE' | 'GENERATION' | 'COMPILATION_TEST' | 'COMPLETED';

export interface GeneratedFile {
  path: string;
  content: string;
}

export interface CustomEndpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  path: string;
  summary: string;
  status_code?: number;
}

export interface EntityField {
  name: string;
  type: string;
  required: boolean;
  isId?: boolean;
}

export interface EntityDefinition {
  name: string;
  tableName?: string;
  fields: EntityField[];
}

export interface MicroserviceConfig {
  client_code: string;
  artifact_id: string;
  package_prefix: string;
  http_port: number;
  java_version: string;
  quarkus_version: string;
  requirements: string;
  architecture_style: string;
  custom_architecture_notes?: string;
  security_option: string;
  jwt_issuer?: string;
  security_roles?: string[];
  communication_protocol: string;
  custom_endpoints?: CustomEndpoint[];
  database_option: string;
  database_name?: string;
  entities: EntityDefinition[];
  extensions: string[];
  custom_extensions?: string[];
  custom_properties?: Record<string, string>;
  contract_id?: string;
}

export interface OrchestrationJob {
  job_id: string;
  client_id: string;
  user_id: string;
  status: JobStatus;
  current_stage: PipelineStage;
  requirements: string;
  files: GeneratedFile[];
  metrics: {
    total_tokens?: number;
    prompt_tokens?: number;
    completion_tokens?: number;
    estimated_cost_usd?: number;
    duration_seconds?: number;
  };
  created_at: string;
  updated_at: string;
}
```

### 1.4 Sandbox Verification & Manifest (`sandbox-verifier-service` :8004)
```typescript
export interface ManifestFileEntry {
  path: string;
  sha256: string;
  size_bytes: number;
}

export interface VerificationManifest {
  manifest_version: string;
  client_id: string;
  project_name: string;
  generated_at: string;
  total_files: number;
  files: ManifestFileEntry[];
}

export interface VerificationResult {
  run_id: string;
  status: 'SUCCESS' | 'FAILED' | 'ERROR';
  build_tool: string;
  compiler_logs: string;
  manifest?: VerificationManifest;
  zip_url?: string;
  created_at: string;
}
```

