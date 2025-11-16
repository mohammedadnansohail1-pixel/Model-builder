export enum DeploymentStatus {
  DEPLOYING = 'deploying',
  RUNNING = 'running',
  STOPPED = 'stopped',
  FAILED = 'failed',
  SCALING = 'scaling',
  UPDATING = 'updating',
}

export enum InferenceBackend {
  TGI = 'tgi',
  VLLM = 'vllm',
  TRITON = 'triton',
  CUSTOM = 'custom',
}

export interface Deployment {
  id: string;
  name: string;
  description?: string;
  model_id: string;
  project_id: string;
  version: string;
  backend: InferenceBackend;
  status: DeploymentStatus;
  endpoint_url?: string;
  internal_url?: string;
  configuration: Record<string, any>;
  resource_allocation: Record<string, any>;
  replicas: number;
  min_replicas: number;
  max_replicas: number;
  auto_scaling_enabled: boolean;
  total_requests: number;
  total_errors: number;
  average_latency_ms?: number;
  requests_per_minute?: number;
  error_message?: string;
  last_health_check?: string;
  health_status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  deployed_at?: string;
  stopped_at?: string;
}

export interface DeploymentMetrics {
  total_requests: number;
  total_errors: number;
  success_rate: number;
  average_latency_ms: number;
  requests_per_minute: number;
  tokens_per_second?: number;
  p50_latency_ms?: number;
  p95_latency_ms?: number;
  p99_latency_ms?: number;
  uptime_percentage: number;
  current_replicas: number;
  cpu_usage_percent?: number;
  memory_usage_percent?: number;
  gpu_usage_percent?: number;
}

export interface InferenceLog {
  id: string;
  deployment_id: string;
  request_id: string;
  endpoint_path: string;
  method: string;
  request_data: Record<string, any>;
  response_data?: Record<string, any>;
  latency_ms: number;
  tokens_input?: number;
  tokens_output?: number;
  tokens_per_second?: number;
  status_code: number;
  error_message?: string;
  success: boolean;
  user_id?: string;
  timestamp: string;
  ip_address?: string;
}

export interface CreateDeploymentData {
  name: string;
  description?: string;
  model_id: string;
  project_id: string;
  backend?: InferenceBackend;
  configuration?: Record<string, any>;
  resource_allocation?: Record<string, any>;
  replicas?: number;
  min_replicas?: number;
  max_replicas?: number;
  auto_scaling_enabled?: boolean;
}
