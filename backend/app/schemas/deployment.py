"""Deployment schemas."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.deployment import DeploymentStatus, InferenceBackend


class DeploymentBase(BaseModel):
    """Base deployment schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class DeploymentCreate(DeploymentBase):
    """Schema for creating a deployment."""

    model_id: UUID
    project_id: UUID
    backend: InferenceBackend = InferenceBackend.TGI
    configuration: Optional[Dict[str, Any]] = None
    resource_allocation: Optional[Dict[str, Any]] = None
    replicas: int = Field(default=1, ge=1, le=100)
    min_replicas: int = Field(default=1, ge=1, le=100)
    max_replicas: int = Field(default=10, ge=1, le=100)
    auto_scaling_enabled: bool = False


class DeploymentUpdate(BaseModel):
    """Schema for updating a deployment."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    resource_allocation: Optional[Dict[str, Any]] = None
    auto_scaling_enabled: Optional[bool] = None


class DeploymentScale(BaseModel):
    """Schema for scaling a deployment."""

    replicas: int = Field(..., ge=1, le=100)


class DeploymentResponse(DeploymentBase):
    """Schema for deployment response."""

    id: UUID
    model_id: UUID
    project_id: UUID
    version: str
    backend: InferenceBackend
    status: DeploymentStatus
    endpoint_url: Optional[str]
    internal_url: Optional[str]
    configuration: Dict[str, Any]
    resource_allocation: Dict[str, Any]
    replicas: int
    min_replicas: int
    max_replicas: int
    auto_scaling_enabled: bool
    total_requests: int
    total_errors: int
    average_latency_ms: Optional[float]
    requests_per_minute: Optional[float]
    error_message: Optional[str]
    last_health_check: Optional[datetime]
    health_status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    deployed_at: Optional[datetime]
    stopped_at: Optional[datetime]

    class Config:
        from_attributes = True


class DeploymentEndpointBase(BaseModel):
    """Base deployment endpoint schema."""

    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(..., min_length=1, max_length=500)
    method: str = Field(default="POST", pattern="^(GET|POST|PUT|DELETE|PATCH)$")


class DeploymentEndpointCreate(DeploymentEndpointBase):
    """Schema for creating a deployment endpoint."""

    authentication_required: bool = True
    api_key_required: bool = True
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_period: str = Field(default="minute", pattern="^(second|minute|hour|day)$")
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    timeout_seconds: int = Field(default=30, ge=1, le=300)


class DeploymentEndpointResponse(DeploymentEndpointBase):
    """Schema for deployment endpoint response."""

    id: UUID
    deployment_id: UUID
    url: str
    authentication_required: bool
    api_key_required: bool
    rate_limit_enabled: bool
    rate_limit_requests: int
    rate_limit_period: str
    request_schema: Optional[Dict[str, Any]]
    response_schema: Optional[Dict[str, Any]]
    timeout_seconds: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InferenceRequest(BaseModel):
    """Schema for inference request."""

    inputs: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = None
    # Parameters can include:
    # - temperature: float (0.0 - 2.0)
    # - top_p: float (0.0 - 1.0)
    # - top_k: int
    # - max_new_tokens: int
    # - repetition_penalty: float
    # - do_sample: bool


class InferenceResponse(BaseModel):
    """Schema for inference response."""

    generated_text: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    tokens_per_second: float
    finish_reason: str


class InferenceLogResponse(BaseModel):
    """Schema for inference log response."""

    id: UUID
    deployment_id: UUID
    request_id: str
    endpoint_path: str
    method: str
    request_data: Dict[str, Any]
    response_data: Optional[Dict[str, Any]]
    latency_ms: float
    tokens_input: Optional[int]
    tokens_output: Optional[int]
    tokens_per_second: Optional[float]
    status_code: int
    error_message: Optional[str]
    success: bool
    user_id: Optional[UUID]
    timestamp: datetime
    ip_address: Optional[str]

    class Config:
        from_attributes = True


class DeploymentMetrics(BaseModel):
    """Schema for deployment metrics."""

    total_requests: int
    total_errors: int
    success_rate: float
    average_latency_ms: float
    requests_per_minute: float
    tokens_per_second: Optional[float]
    p50_latency_ms: Optional[float]
    p95_latency_ms: Optional[float]
    p99_latency_ms: Optional[float]
    uptime_percentage: float
    current_replicas: int
    cpu_usage_percent: Optional[float]
    memory_usage_percent: Optional[float]
    gpu_usage_percent: Optional[float]


class DeploymentHealthResponse(BaseModel):
    """Schema for deployment health check response."""

    status: str  # healthy, unhealthy, degraded
    deployment_id: UUID
    replicas_healthy: int
    replicas_total: int
    last_check: datetime
    error_message: Optional[str]
    latency_ms: float
