"""Model registry API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.models.user import User
from app.models.model_registry import ModelRegistry, ModelType
from app.schemas.model_registry import (
    ModelRegistryCreate,
    ModelRegistryUpdate,
    ModelRegistryResponse,
    ModelSearchRequest,
    HuggingFaceModelInfo
)
from app.api.dependencies import get_current_active_user
from app.services.model_hub_service import model_hub_service

router = APIRouter()


@router.post("/search-huggingface", response_model=List[HuggingFaceModelInfo])
async def search_huggingface_models(
    search_request: ModelSearchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Search for models on HuggingFace.

    Args:
        search_request: Search parameters
        current_user: Current authenticated user

    Returns:
        List[HuggingFaceModelInfo]: List of models
    """
    try:
        models = model_hub_service.search_huggingface_models(
            query=search_request.query,
            model_type=search_request.model_type.value if search_request.model_type else None,
            limit=search_request.limit
        )
        return models
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search models: {str(e)}"
        )


@router.post("", response_model=ModelRegistryResponse, status_code=status.HTTP_201_CREATED)
async def import_model(
    model_data: ModelRegistryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import a model to the registry.

    Args:
        model_data: Model data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ModelRegistryResponse: Created model registry entry
    """
    # Check if model already exists
    result = await db.execute(
        select(ModelRegistry).where(
            ModelRegistry.model_id == model_data.model_id
        )
    )
    existing_model = result.scalar_one_or_none()

    if existing_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model already exists in registry"
        )

    # Get model requirements if not provided
    requirements = model_data.requirements
    if not requirements and model_data.source.value == "huggingface":
        try:
            requirements = model_hub_service.get_model_requirements(model_data.model_id)
        except Exception:
            requirements = {}

    # Create model registry entry
    model = ModelRegistry(
        name=model_data.name,
        model_type=model_data.model_type,
        source=model_data.source,
        model_id=model_data.model_id,
        base_model=model_data.base_model,
        description=model_data.description,
        parameters=model_data.parameters,
        requirements=requirements or {},
        metadata=model_data.metadata or {},
        tags=model_data.tags,
        is_public=model_data.is_public,
        organization_id=current_user.organization_id,
        imported_by=current_user.id
    )

    db.add(model)
    await db.commit()
    await db.refresh(model)

    return model


@router.get("", response_model=List[ModelRegistryResponse])
async def list_models(
    model_type: ModelType = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all models in registry.

    Args:
        model_type: Filter by model type
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[ModelRegistryResponse]: List of models
    """
    query = select(ModelRegistry).where(
        or_(
            ModelRegistry.is_public == True,
            ModelRegistry.organization_id == current_user.organization_id
        )
    )

    if model_type:
        query = query.where(ModelRegistry.model_type == model_type)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    models = result.scalars().all()

    return models


@router.get("/{model_id}", response_model=ModelRegistryResponse)
async def get_model(
    model_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get model by ID.

    Args:
        model_id: Model ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ModelRegistryResponse: Model details
    """
    result = await db.execute(
        select(ModelRegistry).where(ModelRegistry.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    # Check access
    if not model.is_public and model.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return model


@router.put("/{model_id}", response_model=ModelRegistryResponse)
async def update_model(
    model_id: UUID,
    model_data: ModelRegistryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update model in registry.

    Args:
        model_id: Model ID
        model_data: Updated model data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ModelRegistryResponse: Updated model
    """
    result = await db.execute(
        select(ModelRegistry).where(ModelRegistry.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    # Check permissions
    if model.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Update fields
    if model_data.name is not None:
        model.name = model_data.name
    if model_data.description is not None:
        model.description = model_data.description
    if model_data.requirements is not None:
        model.requirements = model_data.requirements
    if model_data.metadata is not None:
        model.metadata = model_data.metadata
    if model_data.tags is not None:
        model.tags = model_data.tags
    if model_data.is_public is not None:
        model.is_public = model_data.is_public

    await db.commit()
    await db.refresh(model)

    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete model from registry.

    Args:
        model_id: Model ID
        current_user: Current authenticated user
        db: Database session
    """
    result = await db.execute(
        select(ModelRegistry).where(ModelRegistry.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    # Check permissions
    if model.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    await db.delete(model)
    await db.commit()
