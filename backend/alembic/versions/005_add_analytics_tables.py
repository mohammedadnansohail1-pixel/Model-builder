"""add analytics tables

Revision ID: 005
Revises: 004
Create Date: 2024-01-16 20:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create analytics enums
    op.execute("CREATE TYPE metrictype AS ENUM ('counter', 'gauge', 'histogram', 'summary')")
    op.execute("""CREATE TYPE eventtype AS ENUM (
        'user_signup', 'user_login', 'model_imported', 'dataset_uploaded',
        'training_started', 'training_completed', 'training_failed',
        'deployment_created', 'deployment_started', 'deployment_stopped',
        'inference_request', 'api_error'
    )""")

    # Create system_metrics table
    op.create_table(
        'system_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('metric_name', sa.String(255), nullable=False, index=True),
        sa.Column('metric_type', sa.Enum('counter', 'gauge', 'histogram', 'summary', name='metrictype'), nullable=False, server_default='gauge'),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('labels', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('timestamp', sa.DateTime, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_type', sa.Enum(
            'user_signup', 'user_login', 'model_imported', 'dataset_uploaded',
            'training_started', 'training_completed', 'training_failed',
            'deployment_created', 'deployment_started', 'deployment_stopped',
            'inference_request', 'api_error',
            name='eventtype'
        ), nullable=False, index=True),
        sa.Column('event_name', sa.String(255), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('properties', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('session_id', sa.String(100), nullable=True, index=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # Create usage_metrics table
    op.create_table(
        'usage_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('resource_type', sa.String(100), nullable=False, index=True),
        sa.Column('resource_id', sa.String(100), nullable=True, index=True),
        sa.Column('metric_name', sa.String(255), nullable=False, index=True),
        sa.Column('quantity', sa.Float, nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('unit_cost', sa.Float, nullable=True),
        sa.Column('total_cost', sa.Float, nullable=True),
        sa.Column('currency', sa.String(10), nullable=False, default='USD'),
        sa.Column('period_start', sa.DateTime, nullable=False, index=True),
        sa.Column('period_end', sa.DateTime, nullable=False, index=True),
        sa.Column('metadata', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('alert_type', sa.String(100), nullable=False, index=True),
        sa.Column('severity', sa.String(50), nullable=False, index=True),
        sa.Column('condition', postgresql.JSON, nullable=False),
        sa.Column('target_type', sa.String(100), nullable=False),
        sa.Column('target_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('is_triggered', sa.Boolean, nullable=False, default=False),
        sa.Column('triggered_at', sa.DateTime, nullable=True),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('notification_channels', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('resource_type', sa.String(100), nullable=False, index=True),
        sa.Column('resource_id', sa.String(100), nullable=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('changes', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True, index=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('alerts')
    op.drop_table('usage_metrics')
    op.drop_table('analytics_events')
    op.drop_table('system_metrics')
    op.execute('DROP TYPE eventtype')
    op.execute('DROP TYPE metrictype')
