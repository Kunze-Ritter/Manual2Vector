"""Pydantic models for video content management APIs."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, PositiveInt, model_validator

from models.document import DocumentResponse, PaginationParams, SortOrder
from models.manufacturer import ManufacturerResponse
from models.product import ProductResponse, ProductSeriesResponse


class VideoPlatform(str, Enum):
    """Supported video distribution platforms."""

    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    BRIGHTCOVE = "brightcove"
    DIRECT = "direct"


class VideoBase(BaseModel):
    """Shared video attributes."""

    link_id: Optional[str] = Field(None, description="External link identifier if available.")
    youtube_id: Optional[str] = Field(
        None, max_length=20, description="YouTube video identifier when applicable."
    )
    platform: Optional[VideoPlatform] = Field(
        None, description="Platform hosting the video (YouTube, Vimeo, etc.)."
    )
    video_url: Optional[HttpUrl] = Field(
        None, description="Canonical accessible URL for the video resource."
    )
    title: Optional[str] = Field(None, description="Human-friendly video title.")
    description: Optional[str] = Field(
        None, description="Long-form description or transcript excerpt."
    )
    thumbnail_url: Optional[HttpUrl] = Field(
        None, description="Publicly accessible thumbnail image URL."
    )
    duration: Optional[int] = Field(
        None, ge=0, description="Video duration in seconds (if known)."
    )
    view_count: Optional[int] = Field(
        None, ge=0, description="Total number of views across the hosting platform."
    )
    like_count: Optional[int] = Field(
        None, ge=0, description="Total number of positive reactions.")
    comment_count: Optional[int] = Field(
        None, ge=0, description="Total number of comments for the video."
    )
    channel_id: Optional[str] = Field(
        None, description="Channel identifier on the source platform."
    )
    channel_title: Optional[str] = Field(
        None, description="Friendly name of the channel or publisher."
    )
    published_at: Optional[datetime] = Field(
        None, description="Original publication timestamp provided by the platform."
    )
    manufacturer_id: Optional[str] = Field(
        None, description="Associated manufacturer identifier, if applicable."
    )
    series_id: Optional[str] = Field(
        None, description="Associated product series identifier, if available."
    )
    document_id: Optional[str] = Field(
        None, description="Associated document identifier within the knowledge base."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata collected during enrichment."
    )

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_published_at(cls, values: "VideoBase") -> "VideoBase":
        if values.published_at and values.published_at > datetime.utcnow():
            raise ValueError("published_at cannot be in the future.")
        return values


class VideoCreateRequest(VideoBase):
    """Payload for creating a new video record."""

    platform: VideoPlatform = Field(..., description="Hosting platform for the video.")
    video_url: HttpUrl = Field(..., description="Canonical URL pointing to the video.")
    title: str = Field(..., min_length=1, description="Video title.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "How to replace the fuser unit",
                "video_url": "https://www.youtube.com/watch?v=abcd1234",
                "platform": "youtube",
                "youtube_id": "abcd1234",
                "description": "Step-by-step instructions for replacing the fuser unit.",
                "thumbnail_url": "https://img.youtube.com/vi/abcd1234/hqdefault.jpg",
                "duration": 420,
                "manufacturer_id": "mfg-001",
                "series_id": "series-01",
                "document_id": "doc-001",
            }
        }
    )


class VideoUpdateRequest(VideoBase):
    """Payload for updating video information."""

    platform: Optional[VideoPlatform] = Field(
        None, description="Hosting platform for the video."
    )
    video_url: Optional[HttpUrl] = Field(None)
    title: Optional[str] = Field(None, min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Updated how-to video title",
                "duration": 450,
                "view_count": 2500,
                "metadata": {"captions_available": True},
            }
        }
    )


class VideoFilterParams(BaseModel):
    """Filtering options for listing videos."""

    manufacturer_id: Optional[str] = Field(None)
    series_id: Optional[str] = Field(None)
    document_id: Optional[str] = Field(None)
    platform: Optional[VideoPlatform] = Field(None)
    youtube_id: Optional[str] = Field(None)
    search: Optional[str] = Field(
        None,
        description="Full-text search across title, description, and channel_title.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "manufacturer_id": "mfg-001",
                "platform": "youtube",
                "search": "installation guide",
            }
        }
    )


class VideoSortParams(BaseModel):
    """Sorting configuration for video listings."""

    sort_by: str = Field(
        "created_at",
        description="Column to sort by (created_at, published_at, title, view_count, etc.).",
    )
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort direction.")


class VideoResponse(VideoBase):
    """Video record representation."""

    id: str = Field(..., description="Unique identifier for the video record.")
    platform: VideoPlatform = Field(...)
    video_url: HttpUrl = Field(...)
    title: str = Field(...)
    created_at: Optional[str] = Field(None)
    updated_at: Optional[str] = Field(None)
    enriched_at: Optional[str] = Field(
        None, description="Timestamp when enrichment was performed, if applicable."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "vid-001",
                "title": "How to replace the fuser unit",
                "video_url": "https://www.youtube.com/watch?v=abcd1234",
                "platform": "youtube",
                "youtube_id": "abcd1234",
                "duration": 420,
                "view_count": 12345,
                "created_at": "2024-10-05T12:34:56Z",
            }
        }
    )


class VideoWithRelationsResponse(VideoResponse):
    """Video response that includes related resources."""

    manufacturer: Optional[ManufacturerResponse] = Field(None)
    series: Optional[ProductSeriesResponse] = Field(None)
    document: Optional[DocumentResponse] = Field(None)
    linked_products: List[ProductResponse] = Field(
        default_factory=list, description="Products linked to this video via junction table."
    )


class VideoListResponse(BaseModel):
    """Paginated video listing."""

    videos: List[VideoResponse] = Field(...)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "videos": [
                    {
                        "id": "vid-001",
                        "title": "How to replace the fuser unit",
                        "platform": "youtube",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 25,
                "total_pages": 1,
            }
        }
    )


class VideoProductLinkRequest(BaseModel):
    """Request payload for linking videos to products."""

    product_ids: List[str] = Field(..., min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"product_ids": ["prod-001", "prod-002"]}
        }
    )


class VideoEnrichmentRequest(BaseModel):
    """Payload for enrichment endpoint."""

    video_url: HttpUrl = Field(...)
    document_id: Optional[str] = Field(None)
    manufacturer_id: Optional[str] = Field(None)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "video_url": "https://www.youtube.com/watch?v=abcd1234",
                "document_id": "doc-123",
                "manufacturer_id": "mfg-001",
            }
        }
    )


class VideoEnrichmentResponse(BaseModel):
    """Response payload returned from enrichment."""

    success: bool = Field(...)
    video_id: Optional[str] = Field(None)
    title: Optional[str] = Field(None)
    platform: Optional[VideoPlatform] = Field(None)
    duration: Optional[int] = Field(None, ge=0)
    error: Optional[str] = Field(None)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "video_id": "vid-001",
                "title": "How to replace the fuser unit",
                "platform": "youtube",
                "duration": 420,
            }
        }
    )
