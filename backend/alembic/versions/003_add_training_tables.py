"""add training tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-16 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create training_configs table
    op.create_table(
        'training_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('model_type', sa.String(50), nullable=False, index=True),
        sa.Column('method', sa.Enum('lora', 'qlora', 'full', 'peft', name='finetuningmethod'), nullable=False),
        sa.Column('default_hyperparameters', postgresql.JSON, nullable=False),
        sa.Column('is_public', sa.Boolean, nullable=False, default=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Create training_jobs table
    op.create_table(
        'training_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('base_model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('model_registry.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('datasets.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('fine_tuning_method', sa.Enum('lora', 'qlora', 'full', 'peft', name='finetuningmethod'), nullable=False, index=True),
        sa.Column('hyperparameters', postgresql.JSON, nullable=False),
        sa.Column('status', sa.Enum('queued', 'initializing', 'running', 'paused', 'completed', 'failed', 'cancelled', name='trainingstatus'), nullable=False, index=True),
        sa.Column('progress', sa.Float, nullable=False, default=0.0),
        sa.Column('current_epoch', sa.Integer, nullable=False, default=0),
        sa.Column('total_epochs', sa.Integer, nullable=False),
        sa.Column('current_step', sa.Integer, nullable=False, default=0),
        sa.Column('total_steps', sa.Integer, nullable=True),
        sa.Column('metrics', postgresql.JSON, nullable=False),
        sa.Column('latest_train_loss', sa.Float, nullable=True),
        sa.Column('latest_eval_loss', sa.Float, nullable=True),
        sa.Column('best_eval_loss', sa.Float, nullable=True),
        sa.Column('logs', sa.Text, nullable=False, default=''),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('output_model_path', sa.String(1000), nullable=True),
        sa.Column('output_model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('model_registry.id', ondelete='SET NULL'), nullable=True),
        sa.Column('compute_used', postgresql.JSON, nullable=False),
        sa.Column('checkpoint_dir', sa.String(1000), nullable=True),
        sa.Column('best_checkpoint_path', sa.String(1000), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('training_jobs')
    op.drop_table('training_configs')
    op.execute('DROP TYPE trainingstatus')
    op.execute('DROP TYPE finetuningmethod')
