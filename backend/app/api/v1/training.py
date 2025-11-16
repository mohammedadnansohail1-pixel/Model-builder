"""Training API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.training import TrainingJob, TrainingStatus, TrainingConfig
from app.models.model_registry import ModelRegistry
from app.models.dataset import Dataset
from app.schemas.training import (
    TrainingJobCreate,
    TrainingJobUpdate,
    TrainingJobResponse,
    TrainingConfigResponse
)
from app.api.dependencies import get_current_active_user
from app.tasks.training_tasks import train_model, cancel_training

router = APIRouter()


@router.post("", response_model=TrainingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_training_job(
    job_data: TrainingJobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create and start a training job.

    Args:
        job_data: Training job data
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session

    Returns:
        TrainingJobResponse: Created training job
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == job_data.project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Verify model exists
    result = await db.execute(
        select(ModelRegistry).where(ModelRegistry.id == job_data.base_model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    # Verify dataset exists and belongs to project
    result = await db.execute(
        select(Dataset).where(Dataset.id == job_data.dataset_id)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    if dataset.project_id != job_data.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset does not belong to the specified project"
        )

    # Set default hyperparameters if not provided
    hyperparameters = job_data.hyperparameters or {
        "learning_rate": 2e-4,
        "num_epochs": 3,
        "batch_size": 4,
        "warmup_steps": 100,
        "weight_decay": 0.01,
        "max_grad_norm": 1.0,
        "gradient_accumulation_steps": 1,
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.1,
        "target_modules": ["q_proj", "v_proj"]
    }

    # Create training job
    training_job = TrainingJob(
        name=job_data.name,
        description=job_data.description,
        project_id=job_data.project_id,
        base_model_id=job_data.base_model_id,
        dataset_id=job_data.dataset_id,
        fine_tuning_method=job_data.fine_tuning_method,
        hyperparameters=hyperparameters,
        total_epochs=hyperparameters.get("num_epochs", 3),
        created_by=current_user.id
    )

    db.add(training_job)
    await db.commit()
    await db.refresh(training_job)

    # Start training in background (Celery)
    train_model.delay(str(training_job.id))

    return training_job


@router.get("", response_model=List[TrainingJobResponse])
async def list_training_jobs(
    project_id: UUID = Query(None),
    status_filter: TrainingStatus = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List training jobs.

    Args:
        project_id: Optional project filter
        status_filter: Optional status filter
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[TrainingJobResponse]: List of training jobs
    """
    query = select(TrainingJob).join(Project).where(
        Project.organization_id == current_user.organization_id
    )

    if project_id:
        query = query.where(TrainingJob.project_id == project_id)

    if status_filter:
        query = query.where(TrainingJob.status == status_filter)

    query = query.order_by(TrainingJob.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return jobs


@router.get("/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get training job by ID.

    Args:
        job_id: Training job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        TrainingJobResponse: Training job details
    """
    result = await db.execute(
        select(TrainingJob).where(TrainingJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training job not found"
        )

    # Verify access through project
    result = await db.execute(
        select(Project).where(Project.id == job.project_id)
    )
    project = result.scalar_one_or_none()

    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return job


@router.post("/{job_id}/cancel", response_model=TrainingJobResponse)
async def cancel_training_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a running training job.

    Args:
        job_id: Training job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        TrainingJobResponse: Updated training job
    """
    result = await db.execute(
        select(TrainingJob).where(TrainingJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training job not found"
        )

    # Verify access
    result = await db.execute(
        select(Project).where(Project.id == job.project_id)
    )
    project = result.scalar_one_or_none()

    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Check if job can be cancelled
    if job.status not in [TrainingStatus.QUEUED, TrainingStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job.status.value}"
        )

    # Cancel the job (Celery task)
    cancel_training.delay(str(job_id))

    job.status = TrainingStatus.CANCELLED

    await db.commit()
    await db.refresh(job)

    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a training job.

    Args:
        job_id: Training job ID
        current_user: Current authenticated user
        db: Database session
    """
    result = await db.execute(
        select(TrainingJob).where(TrainingJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training job not found"
        )

    # Verify access
    result = await db.execute(
        select(Project).where(Project.id == job.project_id)
    )
    project = result.scalar_one_or_none()

    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Can only delete completed/failed/cancelled jobs
    if job.status in [TrainingStatus.RUNNING, TrainingStatus.QUEUED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running or queued job. Cancel it first."
        )

    await db.delete(job)
    await db.commit()


@router.get("/configs", response_model=List[TrainingConfigResponse])
async def list_training_configs(
    model_type: str = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List available training configurations.

    Args:
        model_type: Optional model type filter
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[TrainingConfigResponse]: List of training configs
    """
    query = select(TrainingConfig).where(
        or_(
            TrainingConfig.is_public == True,
            TrainingConfig.organization_id == current_user.organization_id
        )
    )

    if model_type:
        query = query.where(TrainingConfig.model_type == model_type)

    result = await db.execute(query)
    configs = result.scalars().all()

    return configs
