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
  client_id: string;
  name: string;
  description?: string;
  status: 'ACTIVE' | 'INACTIVE';
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

export type AiProvider = 'GEMINI' | 'DEEPSEEK' | 'GROK' | 'MOCK';
export type GatewayTier = 'economic' | 'balanced' | 'advanced';

export interface AiGatewayConfig {
  active_provider: AiProvider;
  tier: GatewayTier;
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
  created_at?: string;
}
