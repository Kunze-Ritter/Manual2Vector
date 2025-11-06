"""
Document CRUD API routes.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from math import ceil
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from backend.api.app import get_supabase
from backend.api.middleware.auth_middleware import require_permission
from backend.models.document import (
    DocumentCreateRequest,
    DocumentListResponse,
    DocumentResponse,
    DocumentSortParams,
    SortOrder,
    DocumentStatsResponse,
    DocumentUpdateRequest,
    PaginationParams,
    DocumentFilterParams,
)
from backend.api.routes.response_models import ErrorResponse, SuccessResponse
from pydantic import BaseModel

LOGGER = logging.getLogger("krai.api.documents")

router = APIRouter(prefix="/documents", tags=["documents"])


class MessagePayload(BaseModel):
    """Payload carrying a textual message."""

    message: str


def _apply_document_filters(query: Any, filters: DocumentFilterParams) -> Any:
    """Apply filter parameters to the Supabase query."""
    if filters.manufacturer_id:
        query = query.eq("manufacturer_id", filters.manufacturer_id)
    if filters.product_id:
        query = query.eq("product_id", filters.product_id)
    if filters.document_type:
        query = query.eq("document_type", filters.document_type)
    if filters.language:
        query = query.eq("language", filters.language)
    if filters.processing_status:
        query = query.eq("processing_status", filters.processing_status)
    if filters.search:
        search = filters.search
        query = query.or_(
            f"filename.ilike.%{search}%,"
            f"manufacturer.ilike.%{search}%,"
            f"series.ilike.%{search}%"
        )
    return query


def _apply_sorting(query: Any, sort: DocumentSortParams) -> Any:
    """Apply sorting parameters to the Supabase query."""
    return query.order(sort.sort_by, desc=sort.sort_order == SortOrder.DESC)


def _apply_pagination(query: Any, pagination: PaginationParams) -> Any:
    """Apply pagination parameters to the Supabase query."""
    start_index = (pagination.page - 1) * pagination.page_size
    end_index = start_index + pagination.page_size - 1
    return query.range(start_index, end_index)


def _calculate_total_pages(total: int, page_size: int) -> int:
    if total <= 0:
        return 1
    return ceil(total / page_size)


def _error_response(
    error: str,
    detail: Optional[str] = None,
    error_code: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    return ErrorResponse(error=error, detail=detail, error_code=error_code).dict()


def _log_and_raise(
    status_code: int,
    message: str,
    *,
    error: str = "Error",
    error_code: Optional[str] = None,
) -> None:
    LOGGER.error(message)
    raise HTTPException(
        status_code=status_code,
        detail=_error_response(error=error, detail=message, error_code=error_code),
    )


@router.get(
    "",
    response_model=SuccessResponse[DocumentListResponse],
)
def list_documents(
    pagination: PaginationParams = Depends(),
    filters: DocumentFilterParams = Depends(),
    sort: DocumentSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("documents:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[DocumentListResponse]:
    """List documents with pagination, filtering, and sorting."""
    try:
        query = supabase.table("krai_core.documents").select("*", count="exact")
        query = _apply_document_filters(query, filters)
        query = _apply_sorting(query, sort)
        query = _apply_pagination(query, pagination)

        response = query.execute()
        data = response.data or []
        total = response.count or 0

        LOGGER.info(
            "Listed documents page=%s page_size=%s total=%s",
            pagination.page,
            pagination.page_size,
            total,
        )

        return SuccessResponse(
            data=DocumentListResponse(
                documents=[DocumentResponse(**item) for item in data],
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=_calculate_total_pages(total, pagination.page_size),
            )
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/{document_id}",
    response_model=SuccessResponse[DocumentResponse],
)
def get_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("documents:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[DocumentResponse]:
    """Retrieve a single document by ID."""
    try:
        response = (
            supabase.table("krai_core.documents")
            .select("*")
            .eq("id", document_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Document not found", "DOCUMENT_NOT_FOUND"),
            )

        LOGGER.info("Retrieved document %s", document_id)
        return SuccessResponse(data=DocumentResponse(**data[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "",
    response_model=SuccessResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    payload: DocumentCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("documents:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[DocumentResponse]:
    """Create a new document record."""
    try:
        # Detect duplicate file hash
        duplicate_check = (
            supabase.table("krai_core.documents")
            .select("id")
            .eq("file_hash", payload.file_hash)
            .limit(1)
            .execute()
        )
        if duplicate_check.data:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail=_error_response(
                    "Conflict",
                    "Document with this hash already exists",
                    error_code="DOCUMENT_DUPLICATE",
                ),
            )

        now = datetime.now(timezone.utc).isoformat()
        document_dict = payload.dict(exclude_none=True)
        document_dict["created_at"] = now
        document_dict["updated_at"] = now

        insert_response = (
            supabase.table("krai_core.documents").insert(document_dict).execute()
        )
        data = insert_response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to create document"),
            )

        document_id = data[0]["id"]
        LOGGER.info("Created document %s", document_id)

        # Audit log
        try:
            supabase.table("krai_system.audit_log").insert(
                {
                    "table_name": "documents",
                    "record_id": document_id,
                    "operation": "INSERT",
                    "changed_by": current_user.get("id"),
                    "new_values": document_dict,
                }
            ).execute()
        except Exception as audit_exc:  # pragma: no cover - defensive
            LOGGER.warning("Audit log insert failed for document %s: %s", document_id, audit_exc)

        return SuccessResponse(data=DocumentResponse(**data[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.put(
    "/{document_id}",
    response_model=SuccessResponse[DocumentResponse],
)
def update_document(
    document_id: str,
    payload: DocumentUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("documents:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[DocumentResponse]:
    """Update an existing document."""
    try:
        existing = (
            supabase.table("krai_core.documents")
            .select("*")
            .eq("id", document_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Document not found", "DOCUMENT_NOT_FOUND"),
            )

        update_payload = payload.dict(exclude_unset=True, exclude_none=True)
        update_payload["updated_at"] = datetime.now(timezone.utc).isoformat()

        update_response = (
            supabase.table("krai_core.documents")
            .update(update_payload)
            .eq("id", document_id)
            .execute()
        )
        updated_data = update_response.data or []
        if not updated_data:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to update document"),
            )

        LOGGER.info("Updated document %s", document_id)

        # Audit log
        try:
            supabase.table("krai_system.audit_log").insert(
                {
                    "table_name": "documents",
                    "record_id": document_id,
                    "operation": "UPDATE",
                    "changed_by": current_user.get("id"),
                    "old_values": data[0],
                    "new_values": update_payload,
                }
            ).execute()
        except Exception as audit_exc:  # pragma: no cover - defensive
            LOGGER.warning("Audit log update failed for document %s: %s", document_id, audit_exc)

        return SuccessResponse(data=DocumentResponse(**updated_data[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.delete(
    "/{document_id}",
    response_model=SuccessResponse[MessagePayload],
)
def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("documents:delete")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[MessagePayload]:
    """Delete a document by ID."""
    try:
        existing = (
            supabase.table("krai_core.documents")
            .select("*")
            .eq("id", document_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Document not found", "DOCUMENT_NOT_FOUND"),
            )

        supabase.table("krai_core.documents").delete().eq("id", document_id).execute()
        LOGGER.info("Deleted document %s", document_id)

        # Audit log
        try:
            supabase.table("krai_system.audit_log").insert(
                {
                    "table_name": "documents",
                    "record_id": document_id,
                    "operation": "DELETE",
                    "changed_by": current_user.get("id"),
                    "old_values": data[0],
                }
            ).execute()
        except Exception as audit_exc:  # pragma: no cover - defensive
            LOGGER.warning("Audit log delete failed for document %s: %s", document_id, audit_exc)

        return SuccessResponse(data=MessagePayload(message="Document deleted successfully"))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/stats",
    response_model=SuccessResponse[DocumentStatsResponse],
)
def get_document_stats(
    current_user: Dict[str, Any] = Depends(require_permission("documents:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[DocumentStatsResponse]:
    """Return aggregated document statistics."""
    try:
        total_response = (
            supabase.table("krai_core.documents")
            .select("id", count="exact", head=True)
            .execute()
        )
        total_documents = total_response.count or 0

        type_response = (
            supabase.table("krai_core.documents")
            .select("document_type,count:id", group="document_type")
            .execute()
        )
        by_type: Dict[str, int] = {
            item.get("document_type"): int(item.get("count", 0))
            for item in type_response.data or []
            if item.get("document_type")
        }

        status_response = (
            supabase.table("krai_core.documents")
            .select("processing_status,count:id", group="processing_status")
            .execute()
        )
        by_status: Dict[str, int] = {
            item.get("processing_status"): int(item.get("count", 0))
            for item in status_response.data or []
            if item.get("processing_status")
        }

        manufacturer_response = (
            supabase.table("krai_core.documents")
            .select("manufacturer,count:id", group="manufacturer")
            .execute()
        )
        by_manufacturer: Dict[str, int] = {
            item.get("manufacturer"): int(item.get("count", 0))
            for item in manufacturer_response.data or []
            if item.get("manufacturer")
        }

        LOGGER.info(
            "Document stats computed totals=%s types=%s statuses=%s manufacturers=%s",
            total_documents,
            len(by_type),
            len(by_status),
            len(by_manufacturer),
        )

        return SuccessResponse(
            data=DocumentStatsResponse(
                total_documents=total_documents,
                by_type=by_type,
                by_status=by_status,
                by_manufacturer=by_manufacturer,
            )
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))
