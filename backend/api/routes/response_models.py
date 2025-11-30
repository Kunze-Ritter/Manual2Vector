"""Common response wrapper models for API routes."""
from __future__ import annotations

from typing import Generic, Literal, Optional, TypeVar, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from pydantic.generics import GenericModel

T = TypeVar("T")


class DocumentStatusResponse(BaseModel):
    """Document processing status response."""
    
    document_status: str = Field(..., description="Current processing status of the document")
    queue_position: int = Field(..., description="Position in processing queue")
    total_queue_items: int = Field(..., description="Total number of items in queue")


class SuccessResponse(GenericModel, Generic[T]):
    """Standard success response envelope."""

    success: Literal[True] = Field(default=True)
    data: T
    message: Optional[str] = Field(
        None,
        description="Optional human-readable message providing additional context.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "example-id", "name": "Example"},
                "message": "Operation completed successfully.",
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    success: Literal[False] = Field(default=False)
    error: str = Field(..., description="Short error type or key.")
    detail: Optional[str] = Field(
        None, description="Detailed error description or remediation guidance."
    )
    error_code: Optional[str] = Field(
        None,
        description="Stable machine-readable error code for programmatic handling.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Not Found",
                "detail": "Document not found",
                "error_code": "DOCUMENT_NOT_FOUND",
            }
        }


# Stage-Based Processing Models

class StageProcessingRequest(BaseModel):
    """Request model for processing multiple stages"""
    stages: List[str] = Field(..., description="List of stage names to process")
    stop_on_error: bool = Field(default=True, description="Stop processing on first error")

class StageResult(BaseModel):
    """Result of a single stage processing"""
    stage: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float

class StageProcessingResponse(BaseModel):
    """Response for stage processing"""
    success: bool
    total_stages: int
    successful: int
    failed: int
    stage_results: List[StageResult]
    success_rate: float

class StageListResponse(BaseModel):
    """Response for available stages"""
    stages: List[str]
    total: int

class StageStatusResponse(BaseModel):
    """Response for stage status"""
    document_id: str
    stage_status: Dict[str, str]  # {"text_extraction": "completed", ...}
    found: bool
    error: Optional[str] = None


# Video Processing Models

class VideoProcessingRequest(BaseModel):
    """Request model for video enrichment"""
    video_url: HttpUrl = Field(..., description="YouTube/Vimeo/Brightcove video URL")
    manufacturer_id: Optional[str] = Field(None, description="Manufacturer UUID")

class VideoProcessingResponse(BaseModel):
    """Response for video enrichment"""
    success: bool
    video_id: Optional[str] = None
    title: Optional[str] = None
    platform: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    channel_title: Optional[str] = None
    error: Optional[str] = None


# Thumbnail Generation Models

class ThumbnailGenerationRequest(BaseModel):
    """Request model for thumbnail generation"""
    size: Optional[List[int]] = Field(default=[300, 400], description="Thumbnail size [width, height]")
    page: Optional[int] = Field(default=0, description="Page number to render (0-indexed)")

class ThumbnailGenerationResponse(BaseModel):
    """Response for thumbnail generation"""
    success: bool
    thumbnail_url: Optional[str] = None
    size: Optional[List[int]] = None
    file_size: Optional[int] = None
    error: Optional[str] = None
