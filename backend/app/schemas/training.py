"""Training job schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.training import TrainingStatus, FineTuningMethod


class TrainingJobBase(BaseModel):
    """Base training job schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TrainingJobCreate(TrainingJobBase):
    """Schema for creating a training job."""

    project_id: UUID
    base_model_id: UUID
    dataset_id: UUID
    fine_tuning_method: FineTuningMethod
    hyperparameters: Optional[dict] = None


class TrainingJobUpdate(BaseModel):
    """Schema for updating a training job."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class TrainingJobResponse(TrainingJobBase):
    """Schema for training job response."""

    id: UUID
    project_id: UUID
    base_model_id: UUID
    dataset_id: UUID
    fine_tuning_method: FineTuningMethod
    hyperparameters: dict
    status: TrainingStatus
    progress: float
    current_epoch: int
    total_epochs: int
    current_step: int
    total_steps: Optional[int]
    metrics: dict
    latest_train_loss: Optional[float]
    latest_eval_loss: Optional[float]
    best_eval_loss: Optional[float]
    logs: str
    error_message: Optional[str]
    output_model_path: Optional[str]
    output_model_id: Optional[UUID]
    compute_used: dict
    checkpoint_dir: Optional[str]
    best_checkpoint_path: Optional[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TrainingConfigResponse(BaseModel):
    """Training configuration response."""

    id: UUID
    name: str
    description: Optional[str]
    model_type: str
    method: FineTuningMethod
    default_hyperparameters: dict
    is_public: bool
    organization_id: Optional[UUID]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
