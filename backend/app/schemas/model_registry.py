"""Model registry schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.model_registry import ModelType, ModelSource


class ModelRegistryBase(BaseModel):
    """Base model registry schema."""

    name: str = Field(..., min_length=1, max_length=255)
    model_type: ModelType
    model_id: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class ModelRegistryCreate(ModelRegistryBase):
    """Schema for creating a model registry entry."""

    source: ModelSource = ModelSource.HUGGINGFACE
    base_model: Optional[str] = None
    parameters: Optional[int] = None
    requirements: Optional[dict] = None
    metadata: Optional[dict] = None
    tags: list[str] = Field(default_factory=list)
    is_public: bool = True


class ModelRegistryUpdate(BaseModel):
    """Schema for updating a model registry entry."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    requirements: Optional[dict] = None
    metadata: Optional[dict] = None
    tags: Optional[list[str]] = None
    is_public: Optional[bool] = None


class ModelRegistryResponse(ModelRegistryBase):
    """Schema for model registry response."""

    id: UUID
    source: ModelSource
    base_model: Optional[str]
    parameters: Optional[int]
    requirements: dict
    metadata: dict
    is_public: bool
    organization_id: Optional[UUID]
    imported_by: Optional[UUID]
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelSearchRequest(BaseModel):
    """Schema for model search request."""

    query: str = Field(..., min_length=1)
    model_type: Optional[ModelType] = None
    limit: int = Field(default=20, ge=1, le=100)


class HuggingFaceModelInfo(BaseModel):
    """Schema for HuggingFace model information."""

    model_id: str
    author: Optional[str]
    description: Optional[str]
    downloads: int
    likes: int
    tags: list[str]
    pipeline_tag: Optional[str]
    model_type: Optional[str]
