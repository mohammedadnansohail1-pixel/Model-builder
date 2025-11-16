"""Dataset API endpoints."""

import io
from typing import List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.dataset import Dataset, DatasetFormat, ValidationStatus
from app.schemas.dataset import (
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    DatasetSplitRequest
)
from app.api.dependencies import get_current_active_user
from app.services.dataset_service import dataset_service
from app.services.storage_service import storage_service

router = APIRouter()


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    name: str,
    project_id: UUID,
    file: UploadFile = File(...),
    description: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a dataset.

    Args:
        name: Dataset name
        project_id: Project ID
        file: Uploaded file
        description: Optional description
        current_user: Current authenticated user
        db: Database session

    Returns:
        DatasetResponse: Created dataset
    """
    # Verify project exists and user has access
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check user has access to project
    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Read file data
    file_content = await file.read()
    file_data = io.BytesIO(file_content)
    file_size = len(file_content)

    # Detect format
    dataset_format = dataset_service.detect_format(file.filename, file_data)

    # Validate dataset
    file_data.seek(0)
    validation_report = dataset_service.validate_dataset(file_data, dataset_format)

    validation_status = ValidationStatus.VALID if validation_report["is_valid"] else ValidationStatus.INVALID

    # Generate statistics
    file_data.seek(0)
    statistics = dataset_service.generate_statistics(file_data, dataset_format)

    # Upload to storage
    file_path = f"datasets/{current_user.id}/{uuid4()}/{file.filename}"
    file_data.seek(0)
    storage_service.upload_file(
        file_path,
        file_data,
        content_type=file.content_type or "application/octet-stream"
    )

    # Create dataset record
    dataset = Dataset(
        name=name,
        description=description,
        project_id=project_id,
        file_path=file_path,
        original_filename=file.filename,
        format=dataset_format,
        size_bytes=file_size,
        row_count=validation_report.get("row_count"),
        column_info=validation_report.get("column_info", {}),
        validation_status=validation_status,
        validation_report=validation_report,
        statistics=statistics,
        sample_data={"rows": validation_report.get("sample_rows", [])},
        created_by=current_user.id
    )

    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    return dataset


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    project_id: UUID = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List datasets.

    Args:
        project_id: Optional project filter
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[DatasetResponse]: List of datasets
    """
    query = select(Dataset)

    if project_id:
        # Verify project access
        result = await db.execute(
            select(Project).where(Project.id == project_id)
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

        query = query.where(Dataset.project_id == project_id)
    else:
        # Get all datasets from user's organization projects
        query = query.join(Project).where(
            Project.organization_id == current_user.organization_id
        )

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    datasets = result.scalars().all()

    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dataset by ID.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        DatasetResponse: Dataset details
    """
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # Verify access through project
    result = await db.execute(
        select(Project).where(Project.id == dataset.project_id)
    )
    project = result.scalar_one_or_none()

    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return dataset


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: UUID,
    dataset_data: DatasetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update dataset.

    Args:
        dataset_id: Dataset ID
        dataset_data: Updated dataset data
        current_user: Current authenticated user
        db: Database session

    Returns:
        DatasetResponse: Updated dataset
    """
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # Verify access
    result = await db.execute(
        select(Project).where(Project.id == dataset.project_id)
    )
    project = result.scalar_one_or_none()

    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Update fields
    if dataset_data.name is not None:
        dataset.name = dataset_data.name
    if dataset_data.description is not None:
        dataset.description = dataset_data.description
    if dataset_data.tags is not None:
        dataset.tags = dataset_data.tags
    if dataset_data.train_split is not None:
        dataset.train_split = dataset_data.train_split
    if dataset_data.validation_split is not None:
        dataset.validation_split = dataset_data.validation_split
    if dataset_data.test_split is not None:
        dataset.test_split = dataset_data.test_split

    await db.commit()
    await db.refresh(dataset)

    return dataset


@router.post("/{dataset_id}/configure-split", response_model=DatasetResponse)
async def configure_dataset_split(
    dataset_id: UUID,
    split_request: DatasetSplitRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Configure dataset split ratios.

    Args:
        dataset_id: Dataset ID
        split_request: Split configuration
        current_user: Current authenticated user
        db: Database session

    Returns:
        DatasetResponse: Updated dataset
    """
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # Verify access
    result = await db.execute(
        select(Project).where(Project.id == dataset.project_id)
    )
    project = result.scalar_one_or_none()

    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Validate splits sum to 1.0
    total = split_request.train_split + split_request.validation_split + split_request.test_split
    if abs(total - 1.0) > 0.001:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Splits must sum to 1.0"
        )

    dataset.train_split = split_request.train_split
    dataset.validation_split = split_request.validation_split
    dataset.test_split = split_request.test_split

    await db.commit()
    await db.refresh(dataset)

    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete dataset.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session
    """
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # Verify access
    result = await db.execute(
        select(Project).where(Project.id == dataset.project_id)
    )
    project = result.scalar_one_or_none()

    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Delete file from storage
    try:
        storage_service.delete_file(dataset.file_path)
    except Exception as e:
        print(f"Failed to delete file from storage: {e}")

    await db.delete(dataset)
    await db.commit()
