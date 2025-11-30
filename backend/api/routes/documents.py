"""
Document CRUD API routes.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from math import ceil
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from api.app import get_database_adapter
from services.database_adapter import DatabaseAdapter
from api.middleware.auth_middleware import require_permission
from api.middleware.rate_limit_middleware import (
    limiter,
    rate_limit_standard,
    rate_limit_search,
    rate_limit_upload,
)
from models.document import (
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
from api.routes.response_models import ErrorResponse, SuccessResponse
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
@limiter.limit(rate_limit_search)
async def list_documents(
    pagination: PaginationParams = Depends(),
    filters: DocumentFilterParams = Depends(),
    sort: DocumentSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("documents:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[DocumentListResponse]:
    """List documents with pagination, filtering, and sorting."""
    try:
        # Build SQL query with filters and pagination
        where_clauses = []
        params = []
        param_count = 0
        
        # Apply filters
        if filters.manufacturer_id:
            param_count += 1
            where_clauses.append(f"manufacturer_id = ${param_count}")
            params.append(filters.manufacturer_id)
        
        if filters.status:
            param_count += 1
            where_clauses.append(f"status = ${param_count}")
            params.append(filters.status)
        
        where_clause = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Apply sorting
        order_clause = f" ORDER BY {sort.sort_by} {sort.order.value}"
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        limit_clause = f" LIMIT {pagination.page_size} OFFSET {offset}"
        
        # Execute query
        query = f"""
            SELECT *, COUNT(*) OVER() as total_count
            FROM krai_core.documents
            {where_clause}
            {order_clause}
            {limit_clause}
        """
        
        result = await adapter.execute_query(query, params)
        
        # Get total count from first row or execute separate count query
        total_count = 0
        if result:
            total_count = result[0].get('total_count', len(result))
        else:
            # Fallback count query
            count_query = f"SELECT COUNT(*) as count FROM krai_core.documents{where_clause}"
            count_result = await adapter.execute_query(count_query, params)
            total_count = count_result[0].get('count', 0) if count_result else 0
        
        return SuccessResponse(
            data=DocumentListResponse(
                documents=result or [],
                total=total_count,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=ceil(total_count / pagination.page_size) if pagination.page_size > 0 else 0,
            )
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/by-document/{document_id}",
    response_model=SuccessResponse[DocumentListResponse],
)
@limiter.limit(rate_limit_search)
async def get_error_codes_by_document(
    document_id: str,
    pagination: PaginationParams = Depends(),
    filters: DocumentFilterParams = Depends(),
    sort: DocumentSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("documents:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[DocumentListResponse]:
    """List error codes by document with pagination, filtering, and sorting."""
    try:
        # For now, return empty response as this seems to be an error codes by document endpoint
        # This would need to be properly implemented based on the actual requirements
        return SuccessResponse(
            data=DocumentListResponse(
                documents=[],
                total=0,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=0,
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
@limiter.limit(rate_limit_standard)
async def get_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("documents:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[DocumentResponse]:
    """Retrieve a single document by ID."""
    try:
        result = await adapter.execute_query(
            "SELECT * FROM krai_core.documents WHERE id = $1 LIMIT 1",
            [document_id]
        )
        
        if not result:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Document not found", "DOCUMENT_NOT_FOUND"),
            )

        LOGGER.info("Retrieved document %s", document_id)
        return SuccessResponse(data=DocumentResponse(**result[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "",
    response_model=SuccessResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(rate_limit_upload)
async def create_document(
    payload: DocumentCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("documents:write")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[DocumentResponse]:
    """Create a new document record."""
    try:
        # Detect duplicate file hash
        duplicate_check = await adapter.execute_query(
            "SELECT id FROM krai_core.documents WHERE file_hash = $1 LIMIT 1",
            [payload.file_hash]
        )
        
        if duplicate_check:
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

        result = await adapter.create_document(document_dict)
        
        if not result:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to create document"),
            )

        document_id = result["id"]
        LOGGER.info("Created document %s", document_id)

        # Audit log
        try:
            await adapter.execute_query(
                "INSERT INTO krai_system.audit_log (table_name, record_id, operation, changed_by, new_values) VALUES ($1, $2, $3, $4, $5)",
                ["documents", document_id, "INSERT", current_user.get("id"), document_dict]
            )
        except Exception as audit_exc:  # pragma: no cover - defensive
            LOGGER.warning("Audit log insert failed for document %s: %s", document_id, audit_exc)

        return SuccessResponse(data=DocumentResponse(**result))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.put(
    "/{document_id}",
    response_model=SuccessResponse[DocumentResponse],
)
@limiter.limit(rate_limit_standard)
async def update_document(
    document_id: str,
    payload: DocumentUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("documents:write")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[DocumentResponse]:
    """Update an existing document."""
    try:
        existing = await adapter.execute_query(
            "SELECT * FROM krai_core.documents WHERE id = $1 LIMIT 1",
            [document_id]
        )
        
        if not existing:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Document not found", "DOCUMENT_NOT_FOUND"),
            )

        update_payload = payload.dict(exclude_unset=True, exclude_none=True)
        update_payload["updated_at"] = datetime.now(timezone.utc).isoformat()

        result = await adapter.update_document(document_id, update_payload)
        
        if not result:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to update document"),
            )

        LOGGER.info("Updated document %s", document_id)

        # Audit log
        try:
            await adapter.execute_query(
                "INSERT INTO krai_system.audit_log (table_name, record_id, operation, changed_by, old_values, new_values) VALUES ($1, $2, $3, $4, $5, $6)",
                ["documents", document_id, "UPDATE", current_user.get("id"), existing[0], update_payload]
            )
        except Exception as audit_exc:  # pragma: no cover - defensive
            LOGGER.warning("Audit log update failed for document %s: %s", document_id, audit_exc)

        return SuccessResponse(data=DocumentResponse(**result))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.delete(
    "/{document_id}",
    response_model=SuccessResponse[MessagePayload],
)
@limiter.limit(rate_limit_standard)
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("documents:delete")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[MessagePayload]:
    """Delete a document by ID."""
    try:
        existing = await adapter.execute_query(
            "SELECT * FROM krai_core.documents WHERE id = $1 LIMIT 1",
            [document_id]
        )
        
        if not existing:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Document not found", "DOCUMENT_NOT_FOUND"),
            )

        await adapter.delete_document(document_id)
        LOGGER.info("Deleted document %s", document_id)

        # Audit log
        try:
            await adapter.execute_query(
                "INSERT INTO krai_system.audit_log (table_name, record_id, operation, changed_by, old_values) VALUES ($1, $2, $3, $4, $5)",
                ["documents", document_id, "DELETE", current_user.get("id"), existing[0]]
            )
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
@limiter.limit(rate_limit_search)
async def get_document_stats(
    current_user: Dict[str, Any] = Depends(require_permission("documents:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[DocumentStatsResponse]:
    """Return aggregated document statistics."""
    try:
        total_result = await adapter.execute_query("SELECT COUNT(*) as count FROM krai_core.documents")
        total_documents = total_result[0].get('count', 0) if total_result else 0

        type_result = await adapter.execute_query(
            "SELECT document_type, COUNT(*) as count FROM krai_core.documents GROUP BY document_type"
        )
        by_type: Dict[str, int] = {
            item.get("document_type"): int(item.get("count", 0))
            for item in type_result or []
            if item.get("document_type")
        }

        status_result = await adapter.execute_query(
            "SELECT processing_status, COUNT(*) as count FROM krai_core.documents GROUP BY processing_status"
        )
        by_status: Dict[str, int] = {
            item.get("processing_status"): int(item.get("count", 0))
            for item in status_result or []
            if item.get("processing_status")
        }

        manufacturer_result = await adapter.execute_query(
            "SELECT manufacturer, COUNT(*) as count FROM krai_core.documents GROUP BY manufacturer"
        )
        by_manufacturer: Dict[str, int] = {
            item.get("manufacturer"): int(item.get("count", 0))
            for item in manufacturer_result or []
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
