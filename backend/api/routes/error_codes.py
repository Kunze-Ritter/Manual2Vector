"""Error code CRUD and search API routes."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from math import ceil
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from supabase import Client

from backend.api.app import get_supabase
from backend.api.middleware.auth_middleware import require_permission
from backend.api.routes.response_models import ErrorResponse, SuccessResponse
from backend.models.document import DocumentResponse, PaginationParams, SortOrder
from backend.models.error_code import (
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
from backend.models.manufacturer import ManufacturerResponse

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


def _quote_filter_value(value: str) -> str:
    escaped = value.replace("\"", "\\\"")
    return f'"{escaped}"'


def _apply_filters(query: Any, filters: ErrorCodeFilterParams) -> Any:
    if filters.manufacturer_id:
        query = query.eq("manufacturer_id", filters.manufacturer_id)
    if filters.document_id:
        query = query.eq("document_id", filters.document_id)
    if filters.chunk_id:
        query = query.eq("chunk_id", filters.chunk_id)
    if filters.error_code:
        query = query.ilike("error_code", f"%{filters.error_code}%")
    if filters.severity_level:
        query = query.eq("severity_level", filters.severity_level.value)
    if filters.requires_technician is not None:
        query = query.eq("requires_technician", filters.requires_technician)
    if filters.requires_parts is not None:
        query = query.eq("requires_parts", filters.requires_parts)
    if filters.search:
        search = filters.search
        query = query.or_(
            ",".join(
                [
                    f"error_code.ilike.%{search}%",
                    f"error_description.ilike.%{search}%",
                    f"solution_text.ilike.%{search}%",
                ]
            )
        )
    return query


def _apply_sorting(query: Any, sort: ErrorCodeSortParams) -> Any:
    sort_order = sort.sort_order if isinstance(sort.sort_order, SortOrder) else SortOrder(sort.sort_order)
    return query.order(sort.sort_by, desc=sort_order == SortOrder.DESC)


def _apply_pagination(query: Any, pagination: PaginationParams) -> Any:
    start_index = (pagination.page - 1) * pagination.page_size
    end_index = start_index + pagination.page_size - 1
    return query.range(start_index, end_index)


def _fetch_document(supabase: Client, document_id: Optional[str]) -> Optional[DocumentResponse]:
    if not document_id:
        return None
    response = (
        supabase.table("krai_core.documents").select("*").eq("id", document_id).limit(1).execute()
    )
    data = response.data or []
    if not data:
        return None
    return DocumentResponse(**data[0])


def _fetch_manufacturer(
    supabase: Client, manufacturer_id: Optional[str]
) -> Optional[ManufacturerResponse]:
    if not manufacturer_id:
        return None
    response = (
        supabase.table("krai_core.manufacturers")
        .select("*")
        .eq("id", manufacturer_id)
        .limit(1)
        .execute()
    )
    data = response.data or []
    if not data:
        return None
    return ManufacturerResponse(**data[0])


def _fetch_chunk(supabase: Client, chunk_id: Optional[str]) -> Optional[ChunkExcerpt]:
    if not chunk_id:
        return None
    response = (
        supabase.table("krai_intelligence.chunks")
        .select("text_chunk,page_start,page_end")
        .eq("id", chunk_id)
        .limit(1)
        .execute()
    )
    data = response.data or []
    if not data:
        return None
    return ChunkExcerpt(**data[0])


def _validate_foreign_keys(
    supabase: Client,
    *,
    chunk_id: Optional[str] = None,
    document_id: Optional[str] = None,
    manufacturer_id: Optional[str] = None,
) -> None:
    if chunk_id:
        chunk = (
            supabase.table("krai_intelligence.chunks").select("id").eq("id", chunk_id).limit(1).execute()
        )
        if not (chunk.data or []):
            _log_and_raise(
                status.HTTP_400_BAD_REQUEST,
                f"Chunk with ID {chunk_id} not found",
                error="Invalid Chunk",
                error_code="CHUNK_NOT_FOUND",
            )
    if document_id:
        document = (
            supabase.table("krai_core.documents").select("id").eq("id", document_id).limit(1).execute()
        )
        if not (document.data or []):
            _log_and_raise(
                status.HTTP_400_BAD_REQUEST,
                f"Document with ID {document_id} not found",
                error="Invalid Document",
                error_code="DOCUMENT_NOT_FOUND",
            )
    if manufacturer_id:
        manufacturer = (
            supabase.table("krai_core.manufacturers").select("id").eq("id", manufacturer_id).limit(1).execute()
        )
        if not (manufacturer.data or []):
            _log_and_raise(
                status.HTTP_400_BAD_REQUEST,
                f"Manufacturer with ID {manufacturer_id} not found",
                error="Invalid Manufacturer",
                error_code="MANUFACTURER_NOT_FOUND",
            )


def _build_relations(
    supabase: Client, record: Dict[str, Any], include_relations: bool
) -> ErrorCodeWithRelationsResponse:
    error_code = ErrorCodeResponse(**record)
    if not include_relations:
        return ErrorCodeWithRelationsResponse(**error_code.dict())

    return ErrorCodeWithRelationsResponse(
        **error_code.dict(),
        document=_fetch_document(supabase, record.get("document_id")),
        manufacturer=_fetch_manufacturer(supabase, record.get("manufacturer_id")),
        chunk=_fetch_chunk(supabase, record.get("chunk_id")),
    )


def _insert_audit_log(
    supabase: Client,
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
        supabase.table("krai_system.audit_log").insert(payload).execute()
    except Exception as audit_exc:  # pragma: no cover - defensive
        LOGGER.warning("Audit log insert failed for error_code %s: %s", record_id, audit_exc)


@router.get("", response_model=SuccessResponse[ErrorCodeListResponse])
def list_error_codes(
    pagination: PaginationParams = Depends(),
    filters: ErrorCodeFilterParams = Depends(),
    sort: ErrorCodeSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ErrorCodeListResponse]:
    try:
        query = supabase.table("krai_intelligence.error_codes").select("*", count="exact")
        query = _apply_filters(query, filters)
        query = _apply_sorting(query, sort)
        query = _apply_pagination(query, pagination)

        response = query.execute()
        data = response.data or []
        total = response.count or 0

        LOGGER.info(
            "Listed error codes page=%s size=%s total=%s",
            pagination.page,
            pagination.page_size,
            total,
        )

        payload = ErrorCodeListResponse(
            error_codes=[ErrorCodeResponse(**item) for item in data],
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
def get_error_code(
    error_code_id: str,
    include_relations: bool = Query(False, description="Include related entities when true."),
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ErrorCodeWithRelationsResponse]:
    try:
        response = (
            supabase.table("krai_intelligence.error_codes")
            .select("*")
            .eq("id", error_code_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response(
                    "Not Found", "Error code not found", "ERROR_CODE_NOT_FOUND"
                ),
            )

        record = data[0]
        enriched = _build_relations(supabase, record, include_relations)
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
def create_error_code(
    payload: ErrorCodeCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ErrorCodeResponse]:
    try:
        _validate_foreign_keys(
            supabase,
            chunk_id=payload.chunk_id,
            document_id=payload.document_id,
            manufacturer_id=payload.manufacturer_id,
        )

        duplicate_query = supabase.table("krai_intelligence.error_codes")
        duplicate_query = duplicate_query.eq("error_code", payload.error_code)
        if payload.document_id:
            duplicate_query = duplicate_query.eq("document_id", payload.document_id)
        duplicate_query = duplicate_query.limit(1)
        duplicate = duplicate_query.execute()
        if duplicate.data:
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

        insert_response = (
            supabase.table("krai_intelligence.error_codes").insert(record_dict).execute()
        )
        data = insert_response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to create error code"),
            )

        error_code_id = data[0]["id"]
        LOGGER.info("Created error code %s", error_code_id)
        _insert_audit_log(
            supabase,
            record_id=error_code_id,
            operation="INSERT",
            changed_by=current_user.get("id"),
            new_values=data[0],
        )
        return SuccessResponse(data=ErrorCodeResponse(**data[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.put(
    "/{error_code_id}",
    response_model=SuccessResponse[ErrorCodeResponse],
)
def update_error_code(
    error_code_id: str,
    payload: ErrorCodeUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ErrorCodeResponse]:
    try:
        existing = (
            supabase.table("krai_intelligence.error_codes")
            .select("*")
            .eq("id", error_code_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response(
                    "Not Found", "Error code not found", "ERROR_CODE_NOT_FOUND"
                ),
            )

        update_payload = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not update_payload:
            return SuccessResponse(data=ErrorCodeResponse(**data[0]))

        _validate_foreign_keys(
            supabase,
            chunk_id=update_payload.get("chunk_id"),
            document_id=update_payload.get("document_id"),
            manufacturer_id=update_payload.get("manufacturer_id"),
        )

        update_payload["updated_at"] = datetime.now(timezone.utc).isoformat()

        update_response = (
            supabase.table("krai_intelligence.error_codes")
            .update(update_payload)
            .eq("id", error_code_id)
            .execute()
        )
        updated = update_response.data or []
        if not updated:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to update error code"),
            )

        LOGGER.info("Updated error code %s", error_code_id)
        _insert_audit_log(
            supabase,
            record_id=error_code_id,
            operation="UPDATE",
            changed_by=current_user.get("id"),
            new_values=updated[0],
            old_values=data[0],
        )
        return SuccessResponse(data=ErrorCodeResponse(**updated[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.delete(
    "/{error_code_id}",
    response_model=SuccessResponse[MessagePayload],
)
def delete_error_code(
    error_code_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:delete")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[MessagePayload]:
    try:
        existing = (
            supabase.table("krai_intelligence.error_codes")
            .select("*")
            .eq("id", error_code_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response(
                    "Not Found", "Error code not found", "ERROR_CODE_NOT_FOUND"
                ),
            )

        supabase.table("krai_intelligence.error_codes").delete().eq("id", error_code_id).execute()
        LOGGER.info("Deleted error code %s", error_code_id)
        _insert_audit_log(
            supabase,
            record_id=error_code_id,
            operation="DELETE",
            changed_by=current_user.get("id"),
            old_values=data[0],
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
def search_error_codes(
    payload: ErrorCodeSearchRequest,
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:read")),
    supabase: Client = Depends(get_supabase),
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
        query = supabase.table("krai_intelligence.error_codes").select("*")
        or_clause = ",".join(
            [f"{field}.ilike.%{payload.query}%" for field in search_fields]
        )
        query = query.or_(or_clause)
        if payload.manufacturer_id:
            query = query.eq("manufacturer_id", payload.manufacturer_id)
        if payload.severity_level:
            query = query.eq("severity_level", payload.severity_level.value)
        query = query.limit(payload.limit)

        response = query.execute()
        data = response.data or []
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        results: List[ErrorCodeWithRelationsResponse] = []
        for record in data:
            results.append(_build_relations(supabase, record, include_relations=True))

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
def get_error_codes_by_document(
    document_id: str,
    pagination: PaginationParams = Depends(),
    sort: ErrorCodeSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ErrorCodeListResponse]:
    try:
        chunk_response = (
            supabase.table("krai_intelligence.chunks")
            .select("id")
            .eq("document_id", document_id)
            .execute()
        )
        chunk_ids = [item["id"] for item in (chunk_response.data or []) if item.get("id")]

        query = supabase.table("krai_intelligence.error_codes").select("*", count="exact")

        if chunk_ids:
            chunk_values = ",".join(_quote_filter_value(chunk_id) for chunk_id in chunk_ids)
            doc_value = _quote_filter_value(document_id)
            filter_expression = f"document_id.eq.{doc_value},chunk_id.in.({chunk_values})"
            query = query.or_(filter_expression)
        else:
            query = query.eq("document_id", document_id)

        query = _apply_sorting(query, sort)
        query = _apply_pagination(query, pagination)

        response = query.execute()
        data = response.data or []
        total = response.count or 0

        payload = ErrorCodeListResponse(
            error_codes=[ErrorCodeResponse(**item) for item in data],
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
    "/by-manufacturer/{manufacturer_id}",
    response_model=SuccessResponse[ErrorCodeListResponse],
)
def get_error_codes_by_manufacturer(
    manufacturer_id: str,
    pagination: PaginationParams = Depends(),
    sort: ErrorCodeSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("error_codes:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ErrorCodeListResponse]:
    try:
        query = (
            supabase.table("krai_intelligence.error_codes")
            .select("*", count="exact")
            .eq("manufacturer_id", manufacturer_id)
        )
        query = _apply_sorting(query, sort)
        query = _apply_pagination(query, pagination)

        response = query.execute()
        data = response.data or []
        total = response.count or 0

        payload = ErrorCodeListResponse(
            error_codes=[ErrorCodeResponse(**item) for item in data],
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
