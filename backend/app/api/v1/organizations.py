"""Organizations API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slugify import slugify

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse
)
from app.api.dependencies import get_current_active_user

router = APIRouter()


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new organization.

    Args:
        org_data: Organization data
        current_user: Current authenticated user
        db: Database session

    Returns:
        OrganizationResponse: Created organization

    Raises:
        HTTPException: If slug already exists
    """
    # Check if slug exists
    result = await db.execute(
        select(Organization).where(Organization.slug == org_data.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already exists"
        )

    # Create organization
    organization = Organization(
        name=org_data.name,
        slug=org_data.slug,
        description=org_data.description,
        owner_id=current_user.id
    )

    db.add(organization)
    await db.commit()
    await db.refresh(organization)

    # Add creator to organization
    current_user.organization_id = organization.id
    await db.commit()

    return organization


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all organizations for current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[OrganizationResponse]: List of organizations
    """
    result = await db.execute(
        select(Organization).where(
            (Organization.owner_id == current_user.id) |
            (Organization.id == current_user.organization_id)
        )
    )
    organizations = result.scalars().all()

    return organizations


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get organization by ID.

    Args:
        org_id: Organization ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        OrganizationResponse: Organization details

    Raises:
        HTTPException: If organization not found or no access
    """
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user has access
    if (organization.owner_id != current_user.id and
        current_user.organization_id != org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return organization


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update organization.

    Args:
        org_id: Organization ID
        org_data: Updated organization data
        current_user: Current authenticated user
        db: Database session

    Returns:
        OrganizationResponse: Updated organization

    Raises:
        HTTPException: If not owner or organization not found
    """
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Only owner can update
    if organization.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can update"
        )

    # Update fields
    if org_data.name is not None:
        organization.name = org_data.name
    if org_data.description is not None:
        organization.description = org_data.description

    await db.commit()
    await db.refresh(organization)

    return organization


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete organization.

    Args:
        org_id: Organization ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If not owner or organization not found
    """
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Only owner can delete
    if organization.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can delete"
        )

    await db.delete(organization)
    await db.commit()
