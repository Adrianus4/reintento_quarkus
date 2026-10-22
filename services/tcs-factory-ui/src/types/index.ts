// src/types/index.ts

export type Role = 'ADMIN' | 'DEVELOPER';

export interface User {
  id: string;
  username?: string;
  full_name: string;
  email: string;
  role: Role;
  assigned_clients: string[];
  is_active: boolean;
  created_at?: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  role: Role;
  username: string;
  assigned_clients: string[];
}

export interface ClientProfile {
  id?: string;
  client_id?: string;
  code?: string;
  name: string;
  description?: string;
  package_prefix?: string;
  java_version?: string;
  quarkus_version?: string;
  status?: 'ACTIVE' | 'INACTIVE';
  is_active?: boolean;
  created_at?: string;
}

export interface Directive {
  id: string;
  client_id: string;
  category: 'SECURITY' | 'ARCHITECTURE' | 'DATABASE' | 'OBSERVABILITY';
  title: string;
  content: string;
  priority: number;
  created_at?: string;
}

export interface OpenApiSpecSummary {
  id: string;
  client_id: string;
  title: string;
  version: string;
  description?: string;
  endpoints_count?: number;
  created_at?: string;
}

export interface ConsolidatedGovernance {
  client: ClientProfile;
  directives: Directive[];
  contracts: OpenApiSpecSummary[];
}

export type AiProvider = 'OPENAI' | 'GEMINI' | 'DEEPSEEK' | 'ANTHROPIC' | 'GROK' | 'OPENROUTER' | 'GROQ' | 'OLLAMA' | 'CUSTOM' | 'MOCK';
export type GatewayTier = 'economic' | 'balanced' | 'advanced';

export interface AiGatewayConfig {
  active_provider: AiProvider;
  model_name?: string;
  tier?: GatewayTier;
}

export interface ProviderTelemetry {
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost_usd: number;
  job_count: number;
}

export interface ConsumptionRecord {
  job_id: string;
  client_code: string;
  provider: string;
  model: string;
  status: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  created_at: string;
}

export interface ConsumptionSummary {
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost_usd: number;
  total_jobs: number;
  by_provider: Record<string, ProviderTelemetry>;
  recent_records: ConsumptionRecord[];
}

export interface VaultCredentialStatus {
  provider: AiProvider;
  configured: boolean;
  masked_key?: string;
  last_updated?: string;
}

export type JobStatus = 'PENDING' | 'RUNNING' | 'IN_PROGRESS' | 'AWAITING_REVIEW' | 'COMPLETED' | 'FAILED' | 'REJECTED';
export type PipelineStage = 'INGESTION' | 'ARCHITECTURE' | 'GENERATION' | 'COMPILATION_TEST' | 'COMPLETED';

export interface GeneratedFile {
  path: string;
  content: string;
}

export interface OrchestrationJob {
  job_id: string;
  client_id: string;
  user_id: string;
  status: JobStatus;
  current_stage: PipelineStage;
  requirements: string;
  files: GeneratedFile[];
  blueprint?: any;
  architecture_style?: string;
  artifact_id?: string;
  error_message?: string;
  metrics: {
    total_tokens?: number;
    prompt_tokens?: number;
    completion_tokens?: number;
    estimated_cost_usd?: number;
    duration_seconds?: number;
  };
  created_at?: string;
  updated_at?: string;
}

export interface ManifestFileEntry {
  path: string;
  sha256: string;
  size_bytes: number;
}

export interface CustomEndpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  path: string;
  summary: string;
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
  architecture_style: string;
  custom_architecture_notes?: string;
  security_option: string;
  jwt_issuer?: string;
  security_roles?: string[];
  communication_protocol: string;
  custom_endpoints?: CustomEndpoint[];
  database_option: string;
  database_name?: string;
  package_prefix: string;
  artifact_id: string;
  http_port: number;
  java_version: string;
  quarkus_version: string;
  build_tool?: string;
  design_patterns?: string[];
  naming_conventions?: Record<string, any>;
  event_broker?: string;
  channels?: Array<{ name: string; type: 'incoming' | 'outgoing'; topic: string }>;
  extensions: string[];
  custom_extensions?: string[];
  custom_properties?: string;
  entities: EntityDefinition[];
  requirements: string;
  contract_id?: string;
}

export interface VerificationManifest {
  manifest_version: string;
  client_id: string;
  project_name: string;
  generated_at: string;
  total_files: number;
  files: ManifestFileEntry[];
}

export interface StructuredFailure {
  phase: string;
  file?: string;
  line?: number;
  message: string;
  test_name?: string;
}

export interface PhaseResult {
  phase: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'SKIPPED';
  duration_ms: number;
  details?: string;
  failures: StructuredFailure[];
}

export interface VerificationResult {
  run_id: string;
  status: 'SUCCESS' | 'FAILED' | 'ERROR';
  verdict?: 'PASSED' | 'FAILED' | 'ERROR';
  veto_applied?: boolean;
  phase_results?: PhaseResult[];
  structured_failures?: StructuredFailure[];
  build_tool: string;
  compiler_logs: string;
  manifest?: VerificationManifest;
  zip_url?: string;
  created_at?: string;
}
