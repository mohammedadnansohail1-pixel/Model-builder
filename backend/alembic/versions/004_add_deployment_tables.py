"""add deployment tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-16 17:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create deployment enums
    op.execute("CREATE TYPE deploymentstatus AS ENUM ('deploying', 'running', 'stopped', 'failed', 'scaling', 'updating')")
    op.execute("CREATE TYPE inferencebackend AS ENUM ('tgi', 'vllm', 'triton', 'custom')")

    # Create deployments table
    op.create_table(
        'deployments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('model_registry.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('version', sa.String(50), nullable=False, default='v1'),
        sa.Column('backend', sa.Enum('tgi', 'vllm', 'triton', 'custom', name='inferencebackend'), nullable=False, server_default='tgi'),
        sa.Column('status', sa.Enum('deploying', 'running', 'stopped', 'failed', 'scaling', 'updating', name='deploymentstatus'), nullable=False, server_default='deploying', index=True),
        sa.Column('endpoint_url', sa.String(1000), nullable=True),
        sa.Column('internal_url', sa.String(1000), nullable=True),
        sa.Column('configuration', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('resource_allocation', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('replicas', sa.Integer, nullable=False, default=1),
        sa.Column('min_replicas', sa.Integer, nullable=False, default=1),
        sa.Column('max_replicas', sa.Integer, nullable=False, default=10),
        sa.Column('auto_scaling_enabled', sa.Boolean, nullable=False, default=False),
        sa.Column('total_requests', sa.Integer, nullable=False, default=0),
        sa.Column('total_errors', sa.Integer, nullable=False, default=0),
        sa.Column('average_latency_ms', sa.Float, nullable=True),
        sa.Column('requests_per_minute', sa.Float, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('last_health_check', sa.DateTime, nullable=True),
        sa.Column('health_status', sa.String(50), nullable=False, default='unknown'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('deployed_at', sa.DateTime, nullable=True),
        sa.Column('stopped_at', sa.DateTime, nullable=True),
    )

    # Create deployment_endpoints table
    op.create_table(
        'deployment_endpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('deployment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('deployments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('method', sa.String(10), nullable=False, default='POST'),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('authentication_required', sa.Boolean, nullable=False, default=True),
        sa.Column('api_key_required', sa.Boolean, nullable=False, default=True),
        sa.Column('rate_limit_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('rate_limit_requests', sa.Integer, nullable=False, default=100),
        sa.Column('rate_limit_period', sa.String(50), nullable=False, default='minute'),
        sa.Column('request_schema', postgresql.JSON, nullable=True),
        sa.Column('response_schema', postgresql.JSON, nullable=True),
        sa.Column('timeout_seconds', sa.Integer, nullable=False, default=30),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Create inference_logs table
    op.create_table(
        'inference_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('deployment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('deployments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('request_id', sa.String(100), nullable=False, index=True),
        sa.Column('endpoint_path', sa.String(500), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('request_data', postgresql.JSON, nullable=False),
        sa.Column('response_data', postgresql.JSON, nullable=True),
        sa.Column('latency_ms', sa.Float, nullable=False),
        sa.Column('tokens_input', sa.Integer, nullable=True),
        sa.Column('tokens_output', sa.Integer, nullable=True),
        sa.Column('tokens_per_second', sa.Float, nullable=True),
        sa.Column('status_code', sa.Integer, nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('success', sa.Boolean, nullable=False, default=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('api_key_used', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, index=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('inference_logs')
    op.drop_table('deployment_endpoints')
    op.drop_table('deployments')
    op.execute('DROP TYPE deploymentstatus')
    op.execute('DROP TYPE inferencebackend')
