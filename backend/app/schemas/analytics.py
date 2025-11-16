"""Analytics schemas."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.analytics import MetricType, EventType


class SystemMetricCreate(BaseModel):
    """Schema for creating a system metric."""

    metric_name: str = Field(..., min_length=1, max_length=255)
    metric_type: MetricType = MetricType.GAUGE
    value: float
    labels: Optional[Dict[str, Any]] = None


class SystemMetricResponse(BaseModel):
    """Schema for system metric response."""

    id: UUID
    metric_name: str
    metric_type: MetricType
    value: float
    labels: Dict[str, Any]
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsEventCreate(BaseModel):
    """Schema for creating an analytics event."""

    event_type: EventType
    event_name: str = Field(..., min_length=1, max_length=255)
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    properties: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class AnalyticsEventResponse(BaseModel):
    """Schema for analytics event response."""

    id: UUID
    event_type: EventType
    event_name: str
    user_id: Optional[UUID]
    organization_id: Optional[UUID]
    project_id: Optional[UUID]
    properties: Dict[str, Any]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class UsageMetricCreate(BaseModel):
    """Schema for creating a usage metric."""

    resource_type: str = Field(..., min_length=1, max_length=100)
    resource_id: Optional[str] = None
    metric_name: str = Field(..., min_length=1, max_length=255)
    quantity: float
    unit: str = Field(..., min_length=1, max_length=50)
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None
    currency: str = "USD"
    period_start: datetime
    period_end: datetime
    metadata: Optional[Dict[str, Any]] = None


class UsageMetricResponse(BaseModel):
    """Schema for usage metric response."""

    id: UUID
    user_id: UUID
    organization_id: Optional[UUID]
    project_id: Optional[UUID]
    resource_type: str
    resource_id: Optional[str]
    metric_name: str
    quantity: float
    unit: str
    unit_cost: Optional[float]
    total_cost: Optional[float]
    currency: str
    period_start: datetime
    period_end: datetime
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    """Schema for creating an alert."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    alert_type: str = Field(..., min_length=1, max_length=100)
    severity: str = Field(..., pattern="^(critical|warning|info)$")
    condition: Dict[str, Any]
    target_type: str = Field(..., min_length=1, max_length=100)
    target_id: Optional[str] = None
    notification_channels: Optional[List[str]] = None


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    notification_channels: Optional[List[str]] = None


class AlertResponse(BaseModel):
    """Schema for alert response."""

    id: UUID
    name: str
    description: Optional[str]
    alert_type: str
    severity: str
    condition: Dict[str, Any]
    target_type: str
    target_id: Optional[str]
    is_active: bool
    is_triggered: bool
    triggered_at: Optional[datetime]
    resolved_at: Optional[datetime]
    notification_channels: List[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""

    id: UUID
    action: str
    resource_type: str
    resource_id: Optional[str]
    user_id: Optional[UUID]
    changes: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    status: str
    error_message: Optional[str]
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""

    total_users: int
    total_organizations: int
    total_projects: int
    total_models: int
    total_datasets: int
    total_training_jobs: int
    total_deployments: int
    active_deployments: int
    total_api_requests: int
    total_errors: int


class UsageSummary(BaseModel):
    """Schema for usage summary."""

    period_start: datetime
    period_end: datetime
    total_gpu_hours: float
    total_cpu_hours: float
    total_storage_gb: float
    total_api_requests: int
    total_tokens_generated: int
    total_cost: float
    currency: str
    breakdown_by_resource: Dict[str, Any]


class PerformanceMetrics(BaseModel):
    """Schema for performance metrics."""

    period_start: datetime
    period_end: datetime
    avg_training_duration_minutes: float
    avg_deployment_latency_ms: float
    avg_inference_latency_ms: float
    success_rate_percentage: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float


class TimeSeriesData(BaseModel):
    """Schema for time series data."""

    metric_name: str
    timestamps: List[datetime]
    values: List[float]
    labels: Optional[Dict[str, str]] = None


class MetricsQuery(BaseModel):
    """Schema for metrics query."""

    metric_names: Optional[List[str]] = None
    start_time: datetime
    end_time: datetime
    labels: Optional[Dict[str, str]] = None
    aggregation: Optional[str] = "avg"  # avg, sum, min, max, count
    interval: Optional[str] = "1h"  # 1m, 5m, 15m, 1h, 1d


class EventsQuery(BaseModel):
    """Schema for events query."""

    event_types: Optional[List[EventType]] = None
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    start_time: datetime
    end_time: datetime
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
