"""Project schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base project schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    organization_id: UUID
    tags: list[str] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    settings: Optional[dict] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: UUID
    slug: str
    organization_id: UUID
    created_by: UUID
    settings: dict
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
