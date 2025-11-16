"""Deployment API endpoints."""

import logging
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.deployment import Deployment, DeploymentStatus, InferenceLog
from app.schemas.deployment import (
    DeploymentCreate,
    DeploymentUpdate,
    DeploymentScale,
    DeploymentResponse,
    InferenceRequest,
    InferenceResponse,
    InferenceLogResponse,
    DeploymentMetrics,
    DeploymentHealthResponse,
)
from app.services.deployment import DeploymentService, InferenceService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    deployment_data: DeploymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new deployment.

    Args:
        deployment_data: Deployment configuration
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created deployment
    """
    try:
        service = DeploymentService(db)

        deployment = await service.create_deployment(
            model_id=deployment_data.model_id,
            project_id=deployment_data.project_id,
            name=deployment_data.name,
            user_id=current_user.id,
            backend=deployment_data.backend,
            description=deployment_data.description,
            configuration=deployment_data.configuration,
            resource_allocation=deployment_data.resource_allocation,
            replicas=deployment_data.replicas,
            min_replicas=deployment_data.min_replicas,
            max_replicas=deployment_data.max_replicas,
            auto_scaling_enabled=deployment_data.auto_scaling_enabled,
        )

        # Auto-start deployment
        await service.start_deployment(deployment.id)

        return deployment

    except ValueError as e:
        logger.error(f"Error creating deployment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create deployment",
        )


@router.get("", response_model=List[DeploymentResponse])
async def list_deployments(
    project_id: Optional[UUID] = None,
    status_filter: Optional[DeploymentStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List deployments.

    Args:
        project_id: Filter by project
        status_filter: Filter by status
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of deployments
    """
    query = select(Deployment)

    # Filter by project if specified
    if project_id:
        query = query.where(Deployment.project_id == project_id)

    # Filter by status if specified
    if status_filter:
        query = query.where(Deployment.status == status_filter)

    # Order by created date
    query = query.order_by(Deployment.created_at.desc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    deployments = result.scalars().all()

    return deployments


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get deployment details.

    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Deployment details
    """
    result = await db.execute(
        select(Deployment).where(Deployment.id == deployment_id)
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found",
        )

    return deployment


@router.put("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: UUID,
    deployment_data: DeploymentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update deployment.

    Args:
        deployment_id: Deployment ID
        deployment_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated deployment
    """
    try:
        service = DeploymentService(db)

        deployment = await service.update_deployment(
            deployment_id=deployment_id,
            name=deployment_data.name,
            description=deployment_data.description,
            configuration=deployment_data.configuration,
            resource_allocation=deployment_data.resource_allocation,
            auto_scaling_enabled=deployment_data.auto_scaling_enabled,
        )

        return deployment

    except ValueError as e:
        logger.error(f"Error updating deployment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update deployment",
        )


@router.post("/{deployment_id}/start", response_model=DeploymentResponse)
async def start_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a deployment.

    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated deployment
    """
    try:
        service = DeploymentService(db)
        deployment = await service.start_deployment(deployment_id)
        return deployment

    except ValueError as e:
        logger.error(f"Error starting deployment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error starting deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start deployment",
        )


@router.post("/{deployment_id}/stop", response_model=DeploymentResponse)
async def stop_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stop a deployment.

    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated deployment
    """
    try:
        service = DeploymentService(db)
        deployment = await service.stop_deployment(deployment_id)
        return deployment

    except ValueError as e:
        logger.error(f"Error stopping deployment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error stopping deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop deployment",
        )


@router.post("/{deployment_id}/scale", response_model=DeploymentResponse)
async def scale_deployment(
    deployment_id: UUID,
    scale_data: DeploymentScale,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Scale a deployment.

    Args:
        deployment_id: Deployment ID
        scale_data: Scaling configuration
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated deployment
    """
    try:
        service = DeploymentService(db)
        deployment = await service.scale_deployment(
            deployment_id=deployment_id,
            replicas=scale_data.replicas,
        )
        return deployment

    except ValueError as e:
        logger.error(f"Error scaling deployment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error scaling deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scale deployment",
        )


@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a deployment.

    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        db: Database session
    """
    try:
        service = DeploymentService(db)
        await service.delete_deployment(deployment_id)

    except ValueError as e:
        logger.error(f"Error deleting deployment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete deployment",
        )


@router.post("/{deployment_id}/inference", response_model=InferenceResponse)
async def run_inference(
    deployment_id: UUID,
    inference_request: InferenceRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run inference on a deployment.

    Args:
        deployment_id: Deployment ID
        inference_request: Inference request
        request: HTTP request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Inference result
    """
    try:
        service = InferenceService(db)

        result = await service.run_inference(
            deployment_id=deployment_id,
            inputs=inference_request.inputs,
            parameters=inference_request.parameters,
            user_id=current_user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return result

    except ValueError as e:
        logger.error(f"Error running inference: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error running inference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference failed",
        )


@router.get("/{deployment_id}/logs", response_model=List[InferenceLogResponse])
async def get_inference_logs(
    deployment_id: UUID,
    limit: int = 100,
    offset: int = 0,
    success_only: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get inference logs for a deployment.

    Args:
        deployment_id: Deployment ID
        limit: Maximum number of logs
        offset: Offset for pagination
        success_only: Filter by success status
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of inference logs
    """
    service = InferenceService(db)
    logs = await service.get_inference_logs(
        deployment_id=deployment_id,
        limit=limit,
        offset=offset,
        success_only=success_only,
    )
    return logs


@router.get("/{deployment_id}/metrics", response_model=DeploymentMetrics)
async def get_deployment_metrics(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get deployment metrics.

    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Deployment metrics
    """
    try:
        service = DeploymentService(db)
        metrics = await service.get_deployment_metrics(deployment_id)
        return metrics

    except ValueError as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get metrics",
        )


@router.get("/{deployment_id}/health", response_model=DeploymentHealthResponse)
async def check_deployment_health(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check deployment health.

    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Health check result
    """
    try:
        service = DeploymentService(db)
        health = await service.check_health(deployment_id)
        return health

    except ValueError as e:
        logger.error(f"Error checking health: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error checking health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed",
        )
