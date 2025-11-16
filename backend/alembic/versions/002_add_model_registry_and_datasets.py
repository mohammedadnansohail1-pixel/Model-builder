"""add model registry and datasets

Revision ID: 002
Revises: 001
Create Date: 2024-01-16 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create model_registry table
    op.create_table(
        'model_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('model_type', sa.Enum('llm', 'vision', 'multimodal', 'audio', 'custom', name='modeltype'), nullable=False, index=True),
        sa.Column('source', sa.Enum('huggingface', 'openai', 'custom', name='modelsource'), nullable=False),
        sa.Column('model_id', sa.String(500), nullable=False, index=True),
        sa.Column('base_model', sa.String(500), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('parameters', sa.BigInteger, nullable=True),
        sa.Column('requirements', postgresql.JSON, nullable=False),
        sa.Column('metadata', postgresql.JSON, nullable=False),
        sa.Column('is_public', sa.Boolean, nullable=False, default=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('imported_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('tags', postgresql.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Create datasets table
    op.create_table(
        'datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('format', sa.Enum('csv', 'json', 'jsonl', 'parquet', 'text', 'custom', name='datasetformat'), nullable=False),
        sa.Column('size_bytes', sa.BigInteger, nullable=False),
        sa.Column('row_count', sa.Integer, nullable=True),
        sa.Column('column_info', postgresql.JSON, nullable=False),
        sa.Column('validation_status', sa.Enum('pending', 'validating', 'valid', 'invalid', name='validationstatus'), nullable=False, index=True),
        sa.Column('validation_report', postgresql.JSON, nullable=False),
        sa.Column('train_split', sa.Float, nullable=True),
        sa.Column('validation_split', sa.Float, nullable=True),
        sa.Column('test_split', sa.Float, nullable=True),
        sa.Column('statistics', postgresql.JSON, nullable=False),
        sa.Column('sample_data', postgresql.JSON, nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tags', postgresql.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('datasets')
    op.drop_table('model_registry')
    op.execute('DROP TYPE validationstatus')
    op.execute('DROP TYPE datasetformat')
    op.execute('DROP TYPE modelsource')
    op.execute('DROP TYPE modeltype')
