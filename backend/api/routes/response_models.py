"""Common response wrapper models for API routes."""
from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class SuccessResponse(GenericModel, Generic[T]):
    """Standard success response envelope."""

    success: bool = Field(True, const=True)
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

    success: bool = Field(False, const=True)
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
