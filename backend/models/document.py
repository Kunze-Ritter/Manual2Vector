"""
Document API models for CRUD operations.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from math import ceil
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator

from backend.core.data_models import DocumentType, ProcessingStatus


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    page: int = Field(1, ge=1, description="Page number (starting at 1)")
    page_size: int = Field(
        10,
        ge=1,
        le=100,
        description="Number of items per page (max 100)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 25,
            }
        }


class SortOrder(str, Enum):
    """Supported sort orders."""

    ASC = "asc"
    DESC = "desc"


class DocumentCreateRequest(BaseModel):
    """Payload for document creation."""

    filename: str = Field(..., min_length=1, max_length=255)
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., ge=0, description="File size in bytes")
    file_hash: str = Field(..., min_length=10, max_length=128)
    storage_path: str = Field(..., min_length=1, max_length=512)
    storage_url: str = Field(..., min_length=1, max_length=1024)
    document_type: DocumentType
    language: str = Field(..., min_length=2, max_length=10)
    manufacturer: Optional[str] = Field(None, max_length=255)
    series: Optional[str] = Field(None, max_length=255)
    models: List[str] = Field(default_factory=list)
    version: Optional[str] = Field(None, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "documents/2025/10/manual_123.pdf",
                "original_filename": "manual_123.pdf",
                "file_size": 2456789,
                "file_hash": "f5f1f9bab41bb53efab5d7e9c9123456",
                "storage_path": "krai-core/documents/manual_123.pdf",
                "storage_url": "https://storage.example.com/manual_123.pdf",
                "document_type": "service_manual",
                "language": "en",
                "manufacturer": "Lexmark",
                "series": "CS920",
                "models": ["CS921", "CS922"],
                "version": "v1.2",
            }
        }

    @validator("models", each_item=True)
    def validate_models(cls, value: str) -> str:
        if not value:
            raise ValueError("Model identifiers cannot be empty")
        return value


class DocumentUpdateRequest(BaseModel):
    """Payload for document updates."""

    document_type: Optional[DocumentType] = None
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    manufacturer: Optional[str] = Field(None, max_length=255)
    series: Optional[str] = Field(None, max_length=255)
    models: Optional[List[str]] = None
    version: Optional[str] = Field(None, max_length=50)
    processing_status: Optional[ProcessingStatus] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    manual_review_required: Optional[bool] = None
    manual_review_notes: Optional[str] = Field(None, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "service_manual",
                "language": "de",
                "processing_status": "completed",
                "confidence_score": 0.92,
                "manual_review_required": False,
                "manual_review_notes": "Verified by QA",
                "models": ["CS923"],
            }
        }

    @validator("models")
    def validate_models(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        if not value:
            raise ValueError("Models list cannot be empty when provided")
        if any(not item for item in value):
            raise ValueError("Model identifiers cannot be empty")
        return value


class DocumentFilterParams(BaseModel):
    """Supported filters for listing documents."""

    manufacturer_id: Optional[str] = Field(None, description="Filter by manufacturer ID")
    product_id: Optional[str] = Field(None, description="Filter by product ID")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    language: Optional[str] = Field(None, description="Filter by language")
    processing_status: Optional[str] = Field(None, description="Filter by processing status")
    search: Optional[str] = Field(None, description="Full-text search query")

    class Config:
        json_schema_extra = {
            "example": {
                "manufacturer_id": "8dc1d2a5-8ef3-4dc1-90f9-1d4b7c6c1234",
                "document_type": "service_manual",
                "language": "en",
                "processing_status": "completed",
                "search": "CS920 calibration",
            }
        }

    @validator("document_type")
    def validate_document_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            DocumentType(value)
        except ValueError as exc:
            allowed = ", ".join(sorted(item.value for item in DocumentType))
            raise ValueError(f"document_type must be one of: {allowed}") from exc
        return value

    @validator("processing_status")
    def validate_processing_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            ProcessingStatus(value)
        except ValueError as exc:
            allowed = ", ".join(sorted(item.value for item in ProcessingStatus))
            raise ValueError(f"processing_status must be one of: {allowed}") from exc
        return value


class DocumentSortParams(BaseModel):
    """Sorting parameters for documents."""

    sort_by: str = Field("created_at", description="Field name to sort by")
    sort_order: SortOrder = Field(
        SortOrder.DESC, description="Sort order: asc or desc"
    )

    ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "filename", "document_type"}

    class Config:
        json_schema_extra = {
            "example": {
                "sort_by": "updated_at",
                "sort_order": "asc",
            }
        }

    @validator("sort_by")
    def validate_sort_by(cls, value: str) -> str:
        if value not in cls.ALLOWED_SORT_FIELDS:
            allowed = ", ".join(sorted(cls.ALLOWED_SORT_FIELDS))
            raise ValueError(f"sort_by must be one of: {allowed}")
        return value

    @validator("sort_order", pre=True)
    def validate_sort_order(cls, value: Union[str, SortOrder]) -> SortOrder:
        try:
            return SortOrder(value)
        except ValueError as exc:
            allowed = ", ".join(item.value for item in SortOrder)
            raise ValueError(f"sort_order must be one of: {allowed}") from exc


class DocumentResponse(BaseModel):
    """Document representation for API responses."""

    id: str
    filename: str
    original_filename: str
    file_size: int
    file_hash: str
    storage_path: str
    storage_url: str
    document_type: DocumentType
    language: Optional[str] = None
    version: Optional[str] = None
    publish_date: Optional[datetime] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    processing_status: Optional[ProcessingStatus] = None
    confidence_score: Optional[float] = None
    manufacturer: Optional[str] = None
    series: Optional[str] = None
    models: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    manufacturer_id: Optional[str] = None
    product_id: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "c7f1b804-1a7a-44f9-9c27-9c3f7253b5c1",
                "filename": "documents/2025/10/manual_123.pdf",
                "original_filename": "manual_123.pdf",
                "file_size": 2456789,
                "file_hash": "f5f1f9bab41bb53efab5d7e9c9123456",
                "storage_path": "krai-core/documents/manual_123.pdf",
                "storage_url": "https://storage.example.com/manual_123.pdf",
                "document_type": "service_manual",
                "language": "en",
                "version": "v1.2",
                "publish_date": "2025-08-15T00:00:00Z",
                "page_count": 256,
                "word_count": 54000,
                "character_count": 325000,
                "processing_status": "completed",
                "confidence_score": 0.92,
                "manufacturer": "Lexmark",
                "series": "CS920",
                "models": ["CS921", "CS922"],
                "created_at": "2025-10-30T12:00:00Z",
                "updated_at": "2025-10-30T12:30:00Z",
                "manufacturer_id": "8dc1d2a5-8ef3-4dc1-90f9-1d4b7c6c1234",
                "product_id": "f214ab9d-6727-406d-bf4e-8e1f0346a123",
            }
        }

    @validator("models", pre=True, always=True)
    def ensure_models(cls, value: Optional[List[str]]) -> List[str]:
        return value or []


class DocumentListResponse(BaseModel):
    """Paginated document list response."""

    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "documents": [DocumentResponse.Config.json_schema_extra["example"]],
                "total": 150,
                "page": 1,
                "page_size": 10,
                "total_pages": 15,
            }
        }

    @root_validator
    def validate_pagination(cls, values: Dict[str, int]) -> Dict[str, int]:
        total = values.get("total", 0)
        page_size = values.get("page_size", 1)
        if page_size <= 0:
            raise ValueError("page_size must be greater than 0")
        values["total_pages"] = max(1, ceil(total / page_size)) if total else 1
        return values


class DocumentStatsResponse(BaseModel):
    """Aggregated document statistics."""

    total_documents: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_manufacturer: Dict[str, int]

    class Config:
        json_schema_extra = {
            "example": {
                "total_documents": 1500,
                "by_type": {
                    "service_manual": 820,
                    "parts_catalog": 430,
                    "user_manual": 250,
                },
                "by_status": {
                    "pending": 120,
                    "in_progress": 45,
                    "completed": 1285,
                    "failed": 50,
                },
                "by_manufacturer": {
                    "Lexmark": 340,
                    "Konica Minolta": 410,
                    "Canon": 280,
                },
            }
        }
