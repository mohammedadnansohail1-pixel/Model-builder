"""Organization schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.organization import SubscriptionTier


class OrganizationBase(BaseModel):
    """Base organization schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""

    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""

    id: UUID
    slug: str
    owner_id: UUID
    subscription_tier: SubscriptionTier
    usage_limits: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
