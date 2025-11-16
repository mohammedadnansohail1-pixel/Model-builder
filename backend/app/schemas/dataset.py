"""Dataset schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.dataset import DatasetFormat, ValidationStatus


class DatasetBase(BaseModel):
    """Base dataset schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class DatasetCreate(DatasetBase):
    """Schema for creating a dataset."""

    project_id: UUID
    tags: list[str] = Field(default_factory=list)


class DatasetUpdate(BaseModel):
    """Schema for updating a dataset."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    train_split: Optional[float] = Field(None, ge=0.0, le=1.0)
    validation_split: Optional[float] = Field(None, ge=0.0, le=1.0)
    test_split: Optional[float] = Field(None, ge=0.0, le=1.0)


class DatasetResponse(DatasetBase):
    """Schema for dataset response."""

    id: UUID
    project_id: UUID
    file_path: str
    original_filename: str
    format: DatasetFormat
    size_bytes: int
    row_count: Optional[int]
    column_info: dict
    validation_status: ValidationStatus
    validation_report: dict
    train_split: Optional[float]
    validation_split: Optional[float]
    test_split: Optional[float]
    statistics: dict
    sample_data: dict
    created_by: UUID
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetUploadResponse(BaseModel):
    """Schema for dataset upload response."""

    dataset_id: UUID
    upload_url: str
    message: str


class DatasetValidationRequest(BaseModel):
    """Schema for dataset validation request."""

    dataset_id: UUID


class DatasetSplitRequest(BaseModel):
    """Schema for dataset split configuration."""

    train_split: float = Field(..., ge=0.0, le=1.0)
    validation_split: float = Field(..., ge=0.0, le=1.0)
    test_split: float = Field(..., ge=0.0, le=1.0)

    @classmethod
    def validate_splits(cls, values):
        """Validate that splits sum to 1.0."""
        total = values.get('train_split', 0) + values.get('validation_split', 0) + values.get('test_split', 0)
        if abs(total - 1.0) > 0.001:
            raise ValueError('Splits must sum to 1.0')
        return values
