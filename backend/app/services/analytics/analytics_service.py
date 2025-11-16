"""Analytics service for metrics collection and monitoring."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.analytics import (
    SystemMetric,
    AnalyticsEvent,
    UsageMetric,
    Alert,
    AuditLog,
    MetricType,
    EventType,
)
from app.models.user import User
from app.models.organization import Organization
from app.models.project import Project
from app.models.model_registry import ModelRegistry
from app.models.dataset import Dataset
from app.models.training import TrainingJob
from app.models.deployment import Deployment

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics and monitoring."""

    def __init__(self, db: AsyncSession):
        """
        Initialize analytics service.

        Args:
            db: Database session
        """
        self.db = db

    async def record_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, Any]] = None,
    ) -> SystemMetric:
        """
        Record a system metric.

        Args:
            metric_name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Optional labels/tags

        Returns:
            Created metric
        """
        metric = SystemMetric(
            id=uuid.uuid4(),
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            labels=labels or {},
        )

        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)

        logger.debug(f"Recorded metric: {metric_name}={value}")
        return metric

    async def track_event(
        self,
        event_type: EventType,
        event_name: str,
        user_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AnalyticsEvent:
        """
        Track an analytics event.

        Args:
            event_type: Type of event
            event_name: Event name
            user_id: User ID
            organization_id: Organization ID
            project_id: Project ID
            properties: Event properties
            session_id: Session ID
            ip_address: IP address
            user_agent: User agent

        Returns:
            Created event
        """
        event = AnalyticsEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            event_name=event_name,
            user_id=user_id,
            organization_id=organization_id,
            project_id=project_id,
            properties=properties or {},
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        logger.info(f"Tracked event: {event_type.value} - {event_name}")
        return event

    async def record_usage(
        self,
        user_id: uuid.UUID,
        resource_type: str,
        metric_name: str,
        quantity: float,
        unit: str,
        organization_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        resource_id: Optional[str] = None,
        unit_cost: Optional[float] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageMetric:
        """
        Record usage metric for billing/cost tracking.

        Args:
            user_id: User ID
            resource_type: Type of resource
            metric_name: Metric name
            quantity: Usage quantity
            unit: Unit of measurement
            organization_id: Organization ID
            project_id: Project ID
            resource_id: Resource ID
            unit_cost: Cost per unit
            period_start: Period start time
            period_end: Period end time
            metadata: Additional metadata

        Returns:
            Created usage metric
        """
        now = datetime.utcnow()
        period_start = period_start or now
        period_end = period_end or now

        total_cost = (quantity * unit_cost) if unit_cost else None

        usage = UsageMetric(
            id=uuid.uuid4(),
            user_id=user_id,
            organization_id=organization_id,
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            metric_name=metric_name,
            quantity=quantity,
            unit=unit,
            unit_cost=unit_cost,
            total_cost=total_cost,
            period_start=period_start,
            period_end=period_end,
            metadata=metadata or {},
        )

        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)

        logger.debug(f"Recorded usage: {resource_type}/{metric_name} = {quantity} {unit}")
        return usage

    async def create_audit_log(
        self,
        action: str,
        resource_type: str,
        user_id: Optional[uuid.UUID] = None,
        resource_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            action: Action performed
            resource_type: Type of resource
            user_id: User who performed action
            resource_id: ID of affected resource
            changes: Changes made
            status: Status of action
            error_message: Error message if failed
            ip_address: IP address
            user_agent: User agent
            request_id: Request ID

        Returns:
            Created audit log
        """
        audit_log = AuditLog(
            id=uuid.uuid4(),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            status=status,
            error_message=error_message,
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        logger.info(f"Audit log: {action} {resource_type} - {status}")
        return audit_log

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get dashboard statistics.

        Returns:
            Dashboard statistics
        """
        # Count various resources
        total_users = await self.db.scalar(select(func.count(User.id)))
        total_orgs = await self.db.scalar(select(func.count(Organization.id)))
        total_projects = await self.db.scalar(select(func.count(Project.id)))
        total_models = await self.db.scalar(select(func.count(ModelRegistry.id)))
        total_datasets = await self.db.scalar(select(func.count(Dataset.id)))
        total_training = await self.db.scalar(select(func.count(TrainingJob.id)))
        total_deployments = await self.db.scalar(select(func.count(Deployment.id)))

        # Active deployments
        active_deployments = await self.db.scalar(
            select(func.count(Deployment.id)).where(
                Deployment.status == "running"
            )
        )

        # Recent activity (last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)

        recent_events = await self.db.scalar(
            select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.timestamp >= last_24h
            )
        )

        # API requests (from inference logs)
        from app.models.deployment import InferenceLog
        api_requests = await self.db.scalar(
            select(func.count(InferenceLog.id))
        )

        api_errors = await self.db.scalar(
            select(func.count(InferenceLog.id)).where(
                InferenceLog.success == False
            )
        )

        return {
            "total_users": total_users or 0,
            "total_organizations": total_orgs or 0,
            "total_projects": total_projects or 0,
            "total_models": total_models or 0,
            "total_datasets": total_datasets or 0,
            "total_training_jobs": total_training or 0,
            "total_deployments": total_deployments or 0,
            "active_deployments": active_deployments or 0,
            "total_api_requests": api_requests or 0,
            "total_errors": api_errors or 0,
            "recent_events_24h": recent_events or 0,
        }

    async def get_usage_summary(
        self,
        user_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get usage summary for billing.

        Args:
            user_id: Filter by user
            organization_id: Filter by organization
            start_time: Start of period
            end_time: End of period

        Returns:
            Usage summary
        """
        query = select(UsageMetric)

        # Apply filters
        if user_id:
            query = query.where(UsageMetric.user_id == user_id)
        if organization_id:
            query = query.where(UsageMetric.organization_id == organization_id)
        if start_time:
            query = query.where(UsageMetric.period_start >= start_time)
        if end_time:
            query = query.where(UsageMetric.period_end <= end_time)

        result = await self.db.execute(query)
        usage_metrics = result.scalars().all()

        # Aggregate by metric name
        summary = {
            "total_gpu_hours": 0.0,
            "total_cpu_hours": 0.0,
            "total_storage_gb": 0.0,
            "total_api_requests": 0,
            "total_tokens_generated": 0,
            "total_cost": 0.0,
            "breakdown_by_resource": {},
        }

        for metric in usage_metrics:
            # Aggregate specific metrics
            if metric.metric_name == "gpu_hours":
                summary["total_gpu_hours"] += metric.quantity
            elif metric.metric_name == "cpu_hours":
                summary["total_cpu_hours"] += metric.quantity
            elif metric.metric_name == "storage_gb":
                summary["total_storage_gb"] += metric.quantity
            elif metric.metric_name == "api_requests":
                summary["total_api_requests"] += int(metric.quantity)
            elif metric.metric_name == "tokens_generated":
                summary["total_tokens_generated"] += int(metric.quantity)

            # Aggregate costs
            if metric.total_cost:
                summary["total_cost"] += metric.total_cost

            # Breakdown by resource type
            if metric.resource_type not in summary["breakdown_by_resource"]:
                summary["breakdown_by_resource"][metric.resource_type] = {
                    "quantity": 0.0,
                    "cost": 0.0,
                }
            summary["breakdown_by_resource"][metric.resource_type]["quantity"] += metric.quantity
            if metric.total_cost:
                summary["breakdown_by_resource"][metric.resource_type]["cost"] += metric.total_cost

        return summary

    async def get_performance_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get performance metrics.

        Args:
            start_time: Start of period
            end_time: End of period

        Returns:
            Performance metrics
        """
        from app.models.deployment import InferenceLog

        # Query inference logs for performance data
        query = select(InferenceLog)
        if start_time:
            query = query.where(InferenceLog.timestamp >= start_time)
        if end_time:
            query = query.where(InferenceLog.timestamp <= end_time)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        if not logs:
            return {
                "avg_inference_latency_ms": 0.0,
                "success_rate_percentage": 100.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
            }

        # Calculate metrics
        latencies = sorted([log.latency_ms for log in logs])
        successes = sum(1 for log in logs if log.success)

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        success_rate = (successes / len(logs) * 100) if logs else 100.0

        # Calculate percentiles
        def percentile(data, p):
            if not data:
                return 0.0
            k = (len(data) - 1) * p
            f = int(k)
            c = f + 1 if f < len(data) - 1 else f
            return data[f] + (data[c] - data[f]) * (k - f)

        return {
            "avg_inference_latency_ms": avg_latency,
            "success_rate_percentage": success_rate,
            "p50_latency_ms": percentile(latencies, 0.50),
            "p95_latency_ms": percentile(latencies, 0.95),
            "p99_latency_ms": percentile(latencies, 0.99),
        }

    async def get_events(
        self,
        event_types: Optional[List[EventType]] = None,
        user_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AnalyticsEvent]:
        """
        Query analytics events.

        Args:
            event_types: Filter by event types
            user_id: Filter by user
            organization_id: Filter by organization
            project_id: Filter by project
            start_time: Start of period
            end_time: End of period
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            List of events
        """
        query = select(AnalyticsEvent)

        # Apply filters
        if event_types:
            query = query.where(AnalyticsEvent.event_type.in_(event_types))
        if user_id:
            query = query.where(AnalyticsEvent.user_id == user_id)
        if organization_id:
            query = query.where(AnalyticsEvent.organization_id == organization_id)
        if project_id:
            query = query.where(AnalyticsEvent.project_id == project_id)
        if start_time:
            query = query.where(AnalyticsEvent.timestamp >= start_time)
        if end_time:
            query = query.where(AnalyticsEvent.timestamp <= end_time)

        # Order by timestamp descending
        query = query.order_by(AnalyticsEvent.timestamp.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_audit_logs(
        self,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """
        Query audit logs.

        Args:
            action: Filter by action
            resource_type: Filter by resource type
            user_id: Filter by user
            start_time: Start of period
            end_time: End of period
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            List of audit logs
        """
        query = select(AuditLog)

        # Apply filters
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if start_time:
            query = query.where(AuditLog.timestamp >= start_time)
        if end_time:
            query = query.where(AuditLog.timestamp <= end_time)

        # Order by timestamp descending
        query = query.order_by(AuditLog.timestamp.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())
