"""Projects API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slugify import slugify

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.organization import Organization
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse
)
from app.api.dependencies import get_current_active_user

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new project.

    Args:
        project_data: Project data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ProjectResponse: Created project

    Raises:
        HTTPException: If organization not found or no access
    """
    # Verify organization exists and user has access
    result = await db.execute(
        select(Organization).where(Organization.id == project_data.organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user is member or owner
    if (organization.owner_id != current_user.id and
        current_user.organization_id != organization.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Create project
    slug = slugify(project_data.name)
    project = Project(
        name=project_data.name,
        slug=slug,
        description=project_data.description,
        organization_id=project_data.organization_id,
        created_by=current_user.id,
        tags=project_data.tags
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return project


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    organization_id: UUID = Query(None, description="Filter by organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all projects accessible to current user.

    Args:
        organization_id: Optional organization filter
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[ProjectResponse]: List of projects
    """
    query = select(Project)

    if organization_id:
        # Verify access to organization
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        if (organization.owner_id != current_user.id and
            current_user.organization_id != organization.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        query = query.where(Project.organization_id == organization_id)
    else:
        # Get all projects from user's organization(s)
        if current_user.organization_id:
            query = query.where(Project.organization_id == current_user.organization_id)

    result = await db.execute(query)
    projects = result.scalars().all()

    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get project by ID.

    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ProjectResponse: Project details

    Raises:
        HTTPException: If project not found or no access
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Verify access
    result = await db.execute(
        select(Organization).where(Organization.id == project.organization_id)
    )
    organization = result.scalar_one_or_none()

    if (organization.owner_id != current_user.id and
        current_user.organization_id != organization.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update project.

    Args:
        project_id: Project ID
        project_data: Updated project data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ProjectResponse: Updated project

    Raises:
        HTTPException: If project not found or no access
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Verify access
    result = await db.execute(
        select(Organization).where(Organization.id == project.organization_id)
    )
    organization = result.scalar_one_or_none()

    if (organization.owner_id != current_user.id and
        current_user.organization_id != organization.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Update fields
    if project_data.name is not None:
        project.name = project_data.name
        project.slug = slugify(project_data.name)
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.tags is not None:
        project.tags = project_data.tags
    if project_data.settings is not None:
        project.settings = project_data.settings

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete project.

    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If project not found or no access
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Verify access (only org owner or project creator can delete)
    result = await db.execute(
        select(Organization).where(Organization.id == project.organization_id)
    )
    organization = result.scalar_one_or_none()

    if (organization.owner_id != current_user.id and
        project.created_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    await db.delete(project)
    await db.commit()
