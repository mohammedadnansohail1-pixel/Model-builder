"""Analytics API endpoints."""

import logging
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.analytics import EventType
from app.schemas.analytics import (
    SystemMetricCreate,
    SystemMetricResponse,
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    UsageMetricCreate,
    UsageMetricResponse,
    AuditLogResponse,
    DashboardStats,
    UsageSummary,
    PerformanceMetrics,
)
from app.services.analytics import AnalyticsService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard statistics.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Dashboard statistics
    """
    try:
        service = AnalyticsService(db)
        stats = await service.get_dashboard_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard statistics",
        )


@router.get("/usage", response_model=UsageSummary)
async def get_usage_summary(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    organization_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get usage summary for billing.

    Args:
        start_time: Start of period
        end_time: End of period
        organization_id: Filter by organization
        current_user: Current authenticated user
        db: Database session

    Returns:
        Usage summary
    """
    try:
        service = AnalyticsService(db)
        summary = await service.get_usage_summary(
            user_id=current_user.id,
            organization_id=organization_id,
            start_time=start_time,
            end_time=end_time,
        )

        return {
            "period_start": start_time or datetime.utcnow(),
            "period_end": end_time or datetime.utcnow(),
            "total_gpu_hours": summary["total_gpu_hours"],
            "total_cpu_hours": summary["total_cpu_hours"],
            "total_storage_gb": summary["total_storage_gb"],
            "total_api_requests": summary["total_api_requests"],
            "total_tokens_generated": summary["total_tokens_generated"],
            "total_cost": summary["total_cost"],
            "currency": "USD",
            "breakdown_by_resource": summary["breakdown_by_resource"],
        }

    except Exception as e:
        logger.error(f"Error getting usage summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage summary",
        )


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get performance metrics.

    Args:
        start_time: Start of period
        end_time: End of period
        current_user: Current authenticated user
        db: Database session

    Returns:
        Performance metrics
    """
    try:
        service = AnalyticsService(db)
        metrics = await service.get_performance_metrics(
            start_time=start_time,
            end_time=end_time,
        )

        return {
            "period_start": start_time or datetime.utcnow(),
            "period_end": end_time or datetime.utcnow(),
            "avg_training_duration_minutes": 0.0,  # TODO: Calculate from training jobs
            "avg_deployment_latency_ms": 0.0,  # TODO: Calculate from deployments
            **metrics,
        }

    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance metrics",
        )


@router.post("/events", response_model=AnalyticsEventResponse, status_code=status.HTTP_201_CREATED)
async def track_event(
    event_data: AnalyticsEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Track an analytics event.

    Args:
        event_data: Event data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created event
    """
    try:
        service = AnalyticsService(db)

        event = await service.track_event(
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            user_id=event_data.user_id or current_user.id,
            organization_id=event_data.organization_id,
            project_id=event_data.project_id,
            properties=event_data.properties,
            session_id=event_data.session_id,
        )

        return event

    except Exception as e:
        logger.error(f"Error tracking event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track event",
        )


@router.get("/events", response_model=List[AnalyticsEventResponse])
async def get_events(
    event_types: Optional[str] = None,  # Comma-separated event types
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics events.

    Args:
        event_types: Comma-separated list of event types
        start_time: Start of period
        end_time: End of period
        limit: Maximum results
        offset: Offset for pagination
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of events
    """
    try:
        service = AnalyticsService(db)

        # Parse event types
        parsed_types = None
        if event_types:
            parsed_types = [EventType(t.strip()) for t in event_types.split(",")]

        events = await service.get_events(
            event_types=parsed_types,
            user_id=current_user.id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
        )

        return events

    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get events",
        )


@router.post("/metrics", response_model=SystemMetricResponse, status_code=status.HTTP_201_CREATED)
async def record_metric(
    metric_data: SystemMetricCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Record a system metric.

    Args:
        metric_data: Metric data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created metric
    """
    try:
        service = AnalyticsService(db)

        metric = await service.record_metric(
            metric_name=metric_data.metric_name,
            value=metric_data.value,
            metric_type=metric_data.metric_type,
            labels=metric_data.labels,
        )

        return metric

    except Exception as e:
        logger.error(f"Error recording metric: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record metric",
        )


@router.post("/usage", response_model=UsageMetricResponse, status_code=status.HTTP_201_CREATED)
async def record_usage(
    usage_data: UsageMetricCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Record a usage metric.

    Args:
        usage_data: Usage data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created usage metric
    """
    try:
        service = AnalyticsService(db)

        usage = await service.record_usage(
            user_id=current_user.id,
            resource_type=usage_data.resource_type,
            metric_name=usage_data.metric_name,
            quantity=usage_data.quantity,
            unit=usage_data.unit,
            resource_id=usage_data.resource_id,
            unit_cost=usage_data.unit_cost,
            period_start=usage_data.period_start,
            period_end=usage_data.period_end,
            metadata=usage_data.metadata,
        )

        return usage

    except Exception as e:
        logger.error(f"Error recording usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record usage",
        )


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get audit logs.

    Args:
        action: Filter by action
        resource_type: Filter by resource type
        start_time: Start of period
        end_time: End of period
        limit: Maximum results
        offset: Offset for pagination
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of audit logs
    """
    try:
        service = AnalyticsService(db)

        logs = await service.get_audit_logs(
            action=action,
            resource_type=resource_type,
            user_id=current_user.id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
        )

        return logs

    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs",
        )
