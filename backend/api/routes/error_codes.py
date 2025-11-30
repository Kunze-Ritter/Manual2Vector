"""Error code CRUD and search API routes."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from math import ceil
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from api.app import get_database_adapter
from services.database_adapter import DatabaseAdapter
from api.middleware.auth_middleware import require_permission
from api.middleware.rate_limit_middleware import (
    limiter,
    rate_limit_search,
    rate_limit_standard,
    rate_limit_upload,
)
from api.routes.response_models import ErrorResponse, SuccessResponse
from models.document import DocumentResponse, PaginationParams, SortOrder
from models.error_code import (
    ChunkExcerpt,
    ErrorCodeCreateRequest,
    ErrorCodeFilterParams,
    ErrorCodeListResponse,
    ErrorCodeResponse,
    ErrorCodeSearchRequest,
    ErrorCodeSearchResponse,
    ErrorCodeSortParams,
    ErrorCodeUpdateRequest,
    ErrorCodeWithRelationsResponse,
)
from models.manufacturer import ManufacturerResponse

LOGGER = logging.getLogger("krai.api.error_codes")

router = APIRouter(prefix="/error_codes", tags=["error_codes"])


class MessagePayload(BaseModel):
    """Simple message payload for delete responses."""

    message: str


ALLOWED_SEARCH_FIELDS = {"error_code", "error_description", "solution_text"}


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


def _calculate_total_pages(total: int, page_size: int) -> int:
    if total <= 0:
        return 1
    return ceil(total / page_size)


async def _fetch_document(adapter: DatabaseAdapter, document_id: Optional[str]) -> Optional[DocumentResponse]:
    if not document_id:
        return None
    result = await adapter.execute_query(
        "SELECT * FROM krai_core.documents WHERE id = $1 LIMIT 1",
        [document_id]
    )
    if not result:
        return None
    return DocumentResponse(**result[0])


async def _fetch_manufacturer(
    adapter: DatabaseAdapter, manufacturer_id: Optional[str]
) -> Optional[ManufacturerResponse]:
    if not manufacturer_id:
        return None
    result = await adapter.execute_query(
        "SELECT * FROM krai_core.manufacturers WHERE id = $1 LIMIT 1",
        [manufacturer_id]
    )
    if not result:
        return None
    return ManufacturerResponse(**result[0])


async def _fetch_chunk(adapter: DatabaseAdapter, chunk_id: Optional[str]) -> Optional[ChunkExcerpt]:
    if not chunk_id:
        return None
    result = await adapter.execute_query(
        "SELECT text_chunk,page_start,page_end FROM krai_intelligence.chunks WHERE id = $1 LIMIT 1",
        [chunk_id]
    )
    if not result:
        return None
    return ChunkExcerpt(**result[0])


async def _validate_foreign_keys(
    adapter: DatabaseAdapter,
    *,
    chunk_id: Optional[str] = None,
    document_id: Optional[str] = None,
    manufacturer_id: Optional[str] = None,
) -> None:
    if chunk_id:
        chunk = await adapter.execute_query(
            "SELECT id FROM krai_intelligence.chunks WHERE id = $1 LIMIT 1",
            [chunk_id]
        )
        if not chunk:
            _log_and_raise(
                status.HTTP_400_BAD_REQUEST,
                f"Chunk with ID {chunk_id} not found",
                error="Invalid Chunk",
                error_code="CHUNK_NOT_FOUND",
            )
    if document_id:
        document = await adapter.execute_query(
            "SELECT id FROM krai_core.documents WHERE id = $1 LIMIT 1",
            [document_id]
        )
        if not document:
            _log_and_raise(
                status.HTTP_400_BAD_REQUEST,
                f"Document with ID {document_id} not found",
                error="Invalid Document",
                error_code="DOCUMENT_NOT_FOUND",
            )
    if manufacturer_id:
        manufacturer = await adapter.execute_query(
            "SELECT id FROM krai_core.manufacturers WHERE id = $1 LIMIT 1",
            [manufacturer_id]
        )
        if not manufacturer:
            _log_and_raise(
                status.HTTP_400_BAD_REQUEST,
                f"Manufacturer with ID {manufacturer_id} not found",
                error="Invalid Manufacturer",
                error_code="MANUFACTURER_NOT_FOUND",
            )


async def _build_relations(
    adapter: DatabaseAdapter, record: Dict[str, Any], include_relations: bool
) -> ErrorCodeWithRelationsResponse:
    error_code = ErrorCodeResponse(**record)
    if not include_relations:
        return ErrorCodeWithRelationsResponse(**error_code.dict())

    return ErrorCodeWithRelationsResponse(
        **error_code.dict(),
        document=await _fetch_document(adapter, record.get("document_id")),
        manufacturer=await _fetch_manufacturer(adapter, record.get("manufacturer_id")),
        chunk=await _fetch_chunk(adapter, record.get("chunk_id")),
    )


async def _insert_audit_log(
    adapter: DatabaseAdapter,
    *,
    record_id: str,
    operation: str,
    changed_by: Optional[str],
    new_values: Optional[Dict[str, Any]] = None,
    old_values: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        payload = {
            "table_name": "error_codes",
            "record_id": record_id,
            "operation": operation,
            "changed_by": changed_by,
        }
        if new_values is not None:
            payload["new_values"] = new_values
        if old_values is not None:
            payload["old_values"] = old_values
        await adapter.execute_query(
            "INSERT INTO krai_system.audit_log (table_name, record_id, operation, changed_by, new_values, old_values) VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb)",
            [payload.get("table_name"), payload.get("record_id"), payload.get("operation"), payload.get("changed_by"), payload.get("new_values"), payload.get("old_values")]
        )
    except Exception as audit_exc:  # pragma: no cover - defensive
        LOGGER.warning("Audit log insert failed for error_code %s: %s", record_id, audit_exc)


@router.get("", response_model=SuccessResponse[ErrorCodeListResponse])
@limiter.limit(rate_limit_search)
async def list_error_codes(
    pagination: PaginationParams = Depends(),
    filters: ErrorCodeFilterParams = Depends(),
    sort: ErrorCodeSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ErrorCodeListResponse]:
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
        
        if filters.document_id:
            param_count += 1
            where_clauses.append(f"document_id = ${param_count}")
            params.append(filters.document_id)
        
        if filters.chunk_id:
            param_count += 1
            where_clauses.append(f"chunk_id = ${param_count}")
            params.append(filters.chunk_id)
        
        if filters.error_code:
            param_count += 1
            where_clauses.append(f"error_code ILIKE ${param_count}")
            params.append(f"%{filters.error_code}%")
        
        if filters.severity_level:
            param_count += 1
            where_clauses.append(f"severity_level = ${param_count}")
            params.append(filters.severity_level.value)
        
        if filters.requires_technician is not None:
            param_count += 1
            where_clauses.append(f"requires_technician = ${param_count}")
            params.append(filters.requires_technician)
        
        if filters.requires_parts is not None:
            param_count += 1
            where_clauses.append(f"requires_parts = ${param_count}")
            params.append(filters.requires_parts)
        
        if filters.search:
            param_count += 1
            where_clauses.append(f"(error_code ILIKE ${param_count} OR error_description ILIKE ${param_count} OR solution_text ILIKE ${param_count})")
            search_term = f"%{filters.search}%"
            params.extend([search_term, search_term, search_term])
            param_count += 2
        
        where_clause = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Apply sorting
        order_direction = "DESC" if sort.sort_order == SortOrder.DESC else "ASC"
        order_clause = f" ORDER BY {sort.sort_by} {order_direction}"
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        limit_clause = f" LIMIT {pagination.page_size} OFFSET {offset}"
        
        # Execute query
        query = f"""
            SELECT *, COUNT(*) OVER() as total_count
            FROM krai_intelligence.error_codes
            {where_clause}
            {order_clause}
            {limit_clause}
        """
        
        result = await adapter.execute_query(query, params)
        
        # Get total count from first row or execute separate count query
        total = 0
        if result:
            total = result[0].get('total_count', len(result))
        else:
            # Fallback count query
            count_query = f"SELECT COUNT(*) as count FROM krai_intelligence.error_codes{where_clause}"
            count_result = await adapter.execute_query(count_query, params)
            total = count_result[0].get('count', 0) if count_result else 0

        LOGGER.info(
            "Listed error codes page=%s size=%s total=%s",
            pagination.page,
            pagination.page_size,
            total,
        )

        payload = ErrorCodeListResponse(
            error_codes=[ErrorCodeResponse(**item) for item in result or []],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=_calculate_total_pages(total, pagination.page_size),
        )
        return SuccessResponse(data=payload)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/{error_code_id}",
    response_model=SuccessResponse[ErrorCodeWithRelationsResponse],
)
@limiter.limit(rate_limit_standard)
async def get_error_code(
    error_code_id: str,
    include_relations: bool = Query(False, description="Include related entities when true."),
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ErrorCodeWithRelationsResponse]:
    try:
        result = await adapter.execute_query(
            "SELECT * FROM krai_intelligence.error_codes WHERE id = $1 LIMIT 1",
            [error_code_id]
        )
        if not result:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response(
                    "Not Found", "Error code not found", "ERROR_CODE_NOT_FOUND"
                ),
            )

        record = result[0]
        enriched = await _build_relations(adapter, record, include_relations)
        LOGGER.info("Retrieved error code %s include_relations=%s", error_code_id, include_relations)
        return SuccessResponse(data=enriched)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "",
    response_model=SuccessResponse[ErrorCodeResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(rate_limit_upload)
async def create_error_code(
    payload: ErrorCodeCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:write")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ErrorCodeResponse]:
    try:
        await _validate_foreign_keys(
            adapter,
            chunk_id=payload.chunk_id,
            document_id=payload.document_id,
            manufacturer_id=payload.manufacturer_id,
        )

        # Check for duplicates
        duplicate_check = await adapter.execute_query(
            "SELECT id FROM krai_intelligence.error_codes WHERE error_code = $1 AND document_id = $2 LIMIT 1",
            [payload.error_code, payload.document_id] if payload.document_id else [payload.error_code, None]
        )
        if duplicate_check:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail=_error_response(
                    "Conflict",
                    "An error code with this identifier already exists for the document.",
                    "ERROR_CODE_DUPLICATE",
                ),
            )

        now = datetime.now(timezone.utc).isoformat()
        record_dict = payload.model_dump(exclude_none=True)
        record_dict["created_at"] = now
        record_dict["updated_at"] = now

        result = await adapter.execute_query(
            "INSERT INTO krai_intelligence.error_codes (error_code, error_description, solution_text, severity_level, requires_technician, requires_parts, manufacturer_id, document_id, chunk_id, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING *",
            [
                record_dict.get("error_code"),
                record_dict.get("error_description"),
                record_dict.get("solution_text"),
                record_dict.get("severity_level"),
                record_dict.get("requires_technician"),
                record_dict.get("requires_parts"),
                record_dict.get("manufacturer_id"),
                record_dict.get("document_id"),
                record_dict.get("chunk_id"),
                record_dict.get("created_at"),
                record_dict.get("updated_at")
            ]
        )
        
        if not result:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to create error code"),
            )

        error_code_id = result[0]["id"]
        LOGGER.info("Created error code %s", error_code_id)
        await _insert_audit_log(
            adapter,
            record_id=error_code_id,
            operation="INSERT",
            changed_by=current_user.get("id"),
            new_values=result[0],
        )
        return SuccessResponse(data=ErrorCodeResponse(**result[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.put(
    "/{error_code_id}",
    response_model=SuccessResponse[ErrorCodeResponse],
)
@limiter.limit(rate_limit_standard)
async def update_error_code(
    error_code_id: str,
    payload: ErrorCodeUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:write")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ErrorCodeResponse]:
    try:
        existing = await adapter.execute_query(
            "SELECT * FROM krai_intelligence.error_codes WHERE id = $1 LIMIT 1",
            [error_code_id]
        )
        if not existing:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response(
                    "Not Found", "Error code not found", "ERROR_CODE_NOT_FOUND"
                ),
            )

        update_payload = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not update_payload:
            return SuccessResponse(data=ErrorCodeResponse(**existing[0]))

        await _validate_foreign_keys(
            adapter,
            chunk_id=update_payload.get("chunk_id"),
            document_id=update_payload.get("document_id"),
            manufacturer_id=update_payload.get("manufacturer_id"),
        )

        update_payload["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Build dynamic UPDATE query
        set_clauses = []
        params = []
        param_count = 0
        
        for key, value in update_payload.items():
            param_count += 1
            set_clauses.append(f"{key} = ${param_count}")
            params.append(value)
        
        param_count += 1
        params.append(error_code_id)
        
        result = await adapter.execute_query(
            f"UPDATE krai_intelligence.error_codes SET {', '.join(set_clauses)} WHERE id = ${param_count} RETURNING *",
            params
        )
        
        if not result:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to update error code"),
            )

        LOGGER.info("Updated error code %s", error_code_id)
        await _insert_audit_log(
            adapter,
            record_id=error_code_id,
            operation="UPDATE",
            changed_by=current_user.get("id"),
            new_values=result[0],
            old_values=existing[0],
        )
        return SuccessResponse(data=ErrorCodeResponse(**result[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.delete(
    "/{error_code_id}",
    response_model=SuccessResponse[MessagePayload],
)
@limiter.limit(rate_limit_standard)
async def delete_error_code(
    error_code_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:delete")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[MessagePayload]:
    try:
        existing = await adapter.execute_query(
            "SELECT * FROM krai_intelligence.error_codes WHERE id = $1 LIMIT 1",
            [error_code_id]
        )
        if not existing:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response(
                    "Not Found", "Error code not found", "ERROR_CODE_NOT_FOUND"
                ),
            )

        await adapter.execute_query(
            "DELETE FROM krai_intelligence.error_codes WHERE id = $1",
            [error_code_id]
        )
        LOGGER.info("Deleted error code %s", error_code_id)
        await _insert_audit_log(
            adapter,
            record_id=error_code_id,
            operation="DELETE",
            changed_by=current_user.get("id"),
            old_values=existing[0],
        )
        return SuccessResponse(data=MessagePayload(message="Error code deleted successfully"))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "/search",
    response_model=SuccessResponse[ErrorCodeSearchResponse],
)
@limiter.limit(rate_limit_search)
async def search_error_codes(
    payload: ErrorCodeSearchRequest,
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ErrorCodeSearchResponse]:
    try:
        search_fields = [field for field in payload.search_in if field in ALLOWED_SEARCH_FIELDS]
        if not search_fields:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=_error_response(
                    "Bad Request",
                    "search_in must contain at least one valid field",
                    "INVALID_SEARCH_FIELDS",
                ),
            )

        start_time = time.perf_counter()
        
        # Build search query
        where_clauses = []
        params = []
        param_count = 0
        
        # Add search conditions
        search_conditions = []
        for field in search_fields:
            param_count += 1
            search_conditions.append(f"{field} ILIKE ${param_count}")
            params.append(f"%{payload.query}%")
        
        where_clauses.append(f"({' OR '.join(search_conditions)})")
        
        # Add manufacturer filter
        if payload.manufacturer_id:
            param_count += 1
            where_clauses.append(f"manufacturer_id = ${param_count}")
            params.append(payload.manufacturer_id)
        
        # Add severity level filter
        if payload.severity_level:
            param_count += 1
            where_clauses.append(f"severity_level = ${param_count}")
            params.append(payload.severity_level.value)
        
        where_clause = f" WHERE {' AND '.join(where_clauses)}"
        limit_clause = f" LIMIT {payload.limit}"
        
        query = f"SELECT * FROM krai_intelligence.error_codes{where_clause}{limit_clause}"
        
        result = await adapter.execute_query(query, params)
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        results: List[ErrorCodeWithRelationsResponse] = []
        for record in result or []:
            results.append(await _build_relations(adapter, record, include_relations=True))

        LOGGER.info(
            "Search error codes query='%s' results=%s duration=%sms",
            payload.query,
            len(results),
            duration_ms,
        )

        return SuccessResponse(
            data=ErrorCodeSearchResponse(
                results=results,
                total=len(results),
                query=payload.query,
                search_duration_ms=duration_ms,
            )
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/by-document/{document_id}",
    response_model=SuccessResponse[ErrorCodeListResponse],
)
@limiter.limit(rate_limit_standard)
async def get_error_codes_by_document(
    document_id: str,
    pagination: PaginationParams = Depends(),
    sort: ErrorCodeSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ErrorCodeListResponse]:
    try:
        # Build base query
        base_query = """
            SELECT 
                ec.id,
                ec.code,
                ec.description,
                ec.severity,
                ec.category,
                ec.frequency,
                ec.document_id,
                ec.manufacturer_id,
                ec.created_at,
                ec.updated_at,
                d.title as document_title,
                d.document_type,
                m.name as manufacturer_name,
                COUNT(*) OVER() as total_count
            FROM krai_intelligence.error_codes ec
            LEFT JOIN krai_core.documents d ON ec.document_id = d.id
            LEFT JOIN krai_core.manufacturers m ON ec.manufacturer_id = m.id
            WHERE ec.document_id = $1
        """
        
        params = [document_id]
        
        # Add sorting
        order_by = "ORDER BY " + sort.sort_by + (" DESC" if sort.sort_order == "desc" else " ASC")
        
        # Add pagination
        limit_clause = f"LIMIT {pagination.limit} OFFSET {(pagination.page - 1) * pagination.limit}"
        
        full_query = f"{base_query} {order_by} {limit_clause}"
        
        result = await adapter.execute_query(full_query, params)
        
        # Extract total count from first row
        total_count = result[0]["total_count"] if result else 0
        
        error_codes = []
        for row in result:
            error_code_data = {
                "id": row["id"],
                "code": row["code"],
                "description": row["description"],
                "severity": row["severity"],
                "category": row["category"],
                "frequency": row["frequency"],
                "document_id": row["document_id"],
                "manufacturer_id": row["manufacturer_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "document": {
                    "id": row["document_id"],
                    "title": row["document_title"],
                    "document_type": row["document_type"]
                } if row["document_id"] else None,
                "manufacturer": {
                    "id": row["manufacturer_id"],
                    "name": row["manufacturer_name"]
                } if row["manufacturer_id"] else None,
            }
            error_codes.append(ErrorCode(**error_code_data))
        
        response_data = ErrorCodeListResponse(
            items=error_codes,
            total=total_count,
            page=pagination.page,
            limit=pagination.limit,
            total_pages=(total_count + pagination.limit - 1) // pagination.limit
        )
        
        return SuccessResponse(data=response_data)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/by-manufacturer/{manufacturer_id}",
    response_model=SuccessResponse[ErrorCodeListResponse],
)
async def get_error_codes_by_manufacturer(
    manufacturer_id: str,
    pagination: PaginationParams = Depends(),
    sort: ErrorCodeSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ErrorCodeListResponse]:
    try:
        # Build base query
        base_query = """
            SELECT 
                ec.id,
                ec.code,
                ec.description,
                ec.severity,
                ec.category,
                ec.frequency,
                ec.document_id,
                ec.manufacturer_id,
                ec.created_at,
                ec.updated_at,
                d.title as document_title,
                d.document_type,
                m.name as manufacturer_name,
                COUNT(*) OVER() as total_count
            FROM krai_intelligence.error_codes ec
            LEFT JOIN krai_core.documents d ON ec.document_id = d.id
            LEFT JOIN krai_core.manufacturers m ON ec.manufacturer_id = m.id
            WHERE ec.manufacturer_id = $1
        """
        
        params = [manufacturer_id]
        
        # Add sorting
        order_by = "ORDER BY " + sort.sort_by + (" DESC" if sort.sort_order == "desc" else " ASC")
        
        # Add pagination
        limit_clause = f"LIMIT {pagination.limit} OFFSET {(pagination.page - 1) * pagination.limit}"
        
        full_query = f"{base_query} {order_by} {limit_clause}"
        
        result = await adapter.execute_query(full_query, params)
        
        # Extract total count from first row
        total_count = result[0]["total_count"] if result else 0
        
        error_codes = []
        for row in result:
            error_code_data = {
                "id": row["id"],
                "code": row["code"],
                "description": row["description"],
                "severity": row["severity"],
                "category": row["category"],
                "frequency": row["frequency"],
                "document_id": row["document_id"],
                "manufacturer_id": row["manufacturer_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "document": {
                    "id": row["document_id"],
                    "title": row["document_title"],
                    "document_type": row["document_type"]
                } if row["document_id"] else None,
                "manufacturer": {
                    "id": row["manufacturer_id"],
                    "name": row["manufacturer_name"]
                } if row["manufacturer_id"] else None,
            }
            error_codes.append(ErrorCode(**error_code_data))
        
        response_data = ErrorCodeListResponse(
            items=error_codes,
            total=total_count,
            page=pagination.page,
            limit=pagination.limit,
            total_pages=(total_count + pagination.limit - 1) // pagination.limit
        )
        
        return SuccessResponse(data=response_data)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))
