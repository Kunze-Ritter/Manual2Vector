"""Image CRUD and storage API routes."""
from __future__ import annotations

import io
import logging
import os
import uuid
from datetime import datetime, timezone
from math import ceil
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel
from api.app import get_database_adapter
from services.database_adapter import DatabaseAdapter
from api.middleware.auth_middleware import require_permission
from api.routes.response_models import ErrorResponse, SuccessResponse
from models.document import DocumentResponse, PaginationParams, SortOrder
from models.image import (
    BucketType,
    ImageCreateRequest,
    ImageFilterParams,
    ImageListResponse,
    ImageResponse,
    ImageSortParams,
    ImageStatsResponse,
    ImageType,
    ImageUpdateRequest,
    ImageUploadResponse,
    ImageWithRelationsResponse,
)
from services.object_storage_service import ObjectStorageService
from services.storage_factory import create_storage_service

LOGGER = logging.getLogger("krai.api.images")

router = APIRouter(prefix="/images", tags=["images"])

MAX_IMAGE_SIZE_BYTES = 50 * 1024 * 1024


class MessagePayload(BaseModel):
    """Simple message payload for delete responses."""

    message: str
    deleted_from_storage: bool = False


ALLOWED_BUCKETS = {
    BucketType.DOCUMENT_IMAGES,
    BucketType.ERROR_IMAGES,
    BucketType.PARTS_IMAGES,
}


def _infer_bucket_type_from_url(storage_url: Optional[str]) -> str:
    """Helper function to get public URL with backward compatibility."""
    def get_public_url(bucket_type: str) -> str:
        new_var = f"OBJECT_STORAGE_PUBLIC_URL_{bucket_type.upper()}"
        old_var = f"R2_PUBLIC_URL_{bucket_type.upper()}"
        url = os.getenv(new_var) or os.getenv(old_var, "")
        if not os.getenv(new_var) and os.getenv(old_var):
            LOGGER.warning(f"{old_var} is deprecated. Use {new_var}.")
        return url
    
    public_documents = get_public_url("documents")
    public_error = get_public_url("error")
    public_parts = get_public_url("parts")

    if storage_url and public_error and storage_url.startswith(public_error):
        return "error_images"
    if storage_url and public_parts and storage_url.startswith(public_parts):
        return "parts_images"
    if storage_url and public_documents and storage_url.startswith(public_documents):
        return "document_images"
    return "document_images"


def _guess_media_type(filename: Optional[str], image_format: Optional[str]) -> str:
    if image_format:
        return f"image/{image_format.lower()}"
    if filename and "." in filename:
        extension = filename.rsplit(".", 1)[-1].lower()
        return f"image/{extension}"
    return "application/octet-stream"


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
    return ceil(total / page_size) if total > 0 else 1


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


async def _fetch_chunk(adapter: DatabaseAdapter, chunk_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not chunk_id:
        return None
    result = await adapter.execute_query(
        "SELECT text_chunk,page_start,page_end FROM krai_intelligence.chunks WHERE id = $1 LIMIT 1",
        [chunk_id]
    )
    if not result:
        return None
    return result[0]


async def _build_relations(
    adapter: DatabaseAdapter,
    record: Dict[str, Any],
    include_relations: bool,
) -> ImageWithRelationsResponse:
    base = ImageResponse(**record)
    if not include_relations:
        return ImageWithRelationsResponse(**base.model_dump())

    chunk = await _fetch_chunk(adapter, record.get("chunk_id"))
    chunk_payload = None
    if chunk:
        from models.image import ChunkSnippet
        chunk_payload = ChunkSnippet(**chunk)

    return ImageWithRelationsResponse(
        **base.model_dump(),
        document=await _fetch_document(adapter, record.get("document_id")),
        chunk=chunk_payload,
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
            "table_name": "images",
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
    except Exception as audit_exc:  # pragma: no cover
        LOGGER.warning("Audit log insert failed for image %s: %s", record_id, audit_exc)


async def _validate_foreign_keys(
    adapter: DatabaseAdapter,
    *,
    document_id: Optional[str] = None,
    chunk_id: Optional[str] = None,
) -> None:
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


async def _deduplicate_hash(adapter: DatabaseAdapter, file_hash: Optional[str]) -> Optional[Dict[str, Any]]:
    if not file_hash:
        return None
    result = await adapter.execute_query(
        "SELECT * FROM krai_content.images WHERE file_hash = $1 LIMIT 1",
        [file_hash]
    )
    if not result:
        return None
    return result[0]


def _map_bucket(bucket: Optional[str]) -> BucketType:
    if not bucket:
        return BucketType.DOCUMENT_IMAGES
    try:
        candidate = BucketType(bucket)
        if candidate not in ALLOWED_BUCKETS:
            raise ValueError
        return candidate
    except ValueError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=_error_response(
                "Invalid Bucket",
                f"Unsupported bucket type '{bucket}'.",
                "INVALID_BUCKET",
            ),
        )


def _decode_upload(file: UploadFile) -> bytes:
    content = file.file.read()
    file.file.seek(0)
    return content


def _determine_bucket(bucket: Optional[str]) -> str:
    mapped = _map_bucket(bucket)
    return mapped.value


def _calculate_stats(records: List[Dict[str, Any]]) -> ImageStatsResponse:
    by_type: Dict[str, int] = {}
    by_document: Dict[str, int] = {}
    total = len(records)
    with_ocr = 0
    with_ai = 0

    for record in records:
        image_type = record.get("image_type")
        if image_type:
            by_type[image_type] = by_type.get(image_type, 0) + 1
        document_id = record.get("document_id")
        if document_id:
            by_document[document_id] = by_document.get(document_id, 0) + 1
        if record.get("ocr_text"):
            with_ocr += 1
        if record.get("ai_description"):
            with_ai += 1

    return ImageStatsResponse(
        total_images=total,
        by_type=by_type,
        by_document=by_document,
        with_ocr_text=with_ocr,
        with_ai_description=with_ai,
    )


@router.get("", response_model=SuccessResponse[ImageListResponse])
async def list_images(
    pagination: PaginationParams = Depends(),
    filters: ImageFilterParams = Depends(),
    sort: ImageSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("images:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ImageListResponse]:
    try:
        # Build SQL query with filters and pagination
        where_clauses = []
        params = []
        param_count = 0
        
        # Apply filters
        if filters.document_id:
            param_count += 1
            where_clauses.append(f"document_id = ${param_count}")
            params.append(filters.document_id)
        
        if filters.bucket_type:
            param_count += 1
            where_clauses.append(f"bucket_type = ${param_count}")
            params.append(filters.bucket_type.value)
        
        if filters.has_ocr_text is not None:
            param_count += 1
            where_clauses.append(f"has_ocr_text = ${param_count}")
            params.append(filters.has_ocr_text)
        
        if filters.has_ai_description is not None:
            param_count += 1
            where_clauses.append(f"has_ai_description = ${param_count}")
            params.append(filters.has_ai_description)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            placeholders = []
            for _ in range(4):
                param_count += 1
                placeholders.append(f"${param_count}")
                params.append(search_term)
            where_clauses.append(
                f"(filename ILIKE {placeholders[0]} OR original_filename ILIKE {placeholders[1]} OR ai_description ILIKE {placeholders[2]} OR ocr_text ILIKE {placeholders[3]})"
            )

        if filters.file_size_min is not None:
            param_count += 1
            where_clauses.append(f"file_size >= ${param_count}")
            params.append(filters.file_size_min)

        if filters.file_size_max is not None:
            param_count += 1
            where_clauses.append(f"file_size <= ${param_count}")
            params.append(filters.file_size_max)

        if filters.date_from:
            param_count += 1
            where_clauses.append(f"created_at::date >= ${param_count}::date")
            params.append(filters.date_from)

        if filters.date_to:
            param_count += 1
            where_clauses.append(f"created_at::date <= ${param_count}::date")
            params.append(filters.date_to)
        
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
            FROM krai_content.images
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
            count_query = f"SELECT COUNT(*) as count FROM krai_content.images{where_clause}"
            count_result = await adapter.execute_query(count_query, params)
            total = count_result[0].get('count', 0) if count_result else 0

        LOGGER.info(
            "Listed images page=%s size=%s total=%s",
            pagination.page,
            pagination.page_size,
            total,
        )

        payload = ImageListResponse(
            images=[ImageResponse(**item) for item in result or []],
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
    "/{image_id}",
    response_model=SuccessResponse[ImageWithRelationsResponse],
)
async def get_image(
    image_id: str,
    include_relations: bool = Query(False),
    current_user: Dict[str, Any] = Depends(require_permission("images:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ImageWithRelationsResponse]:
    try:
        result = await adapter.execute_query(
            "SELECT * FROM krai_content.images WHERE id = $1 LIMIT 1",
            [image_id]
        )
        if not result:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Image not found", "IMAGE_NOT_FOUND"),
            )

        enriched = await _build_relations(adapter, result[0], include_relations)
        return SuccessResponse(data=enriched)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "",
    response_model=SuccessResponse[ImageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_image(
    payload: ImageCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("images:write")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ImageResponse]:
    try:
        await _validate_foreign_keys(
            adapter,
            document_id=payload.document_id,
            chunk_id=payload.chunk_id,
        )

        if payload.file_hash:
            duplicate = await _deduplicate_hash(adapter, payload.file_hash)
            if duplicate:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail=_error_response(
                        "Conflict",
                        "Image with this hash already exists.",
                        "IMAGE_DUPLICATE",
                    ),
                )

        # Build INSERT query dynamically
        record_dict = payload.model_dump()
        columns = list(record_dict.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        values = list(record_dict.values())
        
        query = f"INSERT INTO krai_content.images ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING *"
        result = await adapter.execute_query(query, values)
        
        if not result:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to create image"),
            )

        image_id = result[0]["id"]
        LOGGER.info("Created image %s", image_id)
        await _insert_audit_log(
            adapter,
            record_id=image_id,
            operation="INSERT",
            changed_by=current_user.get("id"),
            new_values=result[0],
        )
        return SuccessResponse(data=ImageResponse(**result[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.put(
    "/{image_id}",
    response_model=SuccessResponse[ImageResponse],
)
async def update_image(
    image_id: str,
    payload: ImageUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("images:write")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ImageResponse]:
    try:
        existing = await adapter.execute_query(
            "SELECT * FROM krai_content.images WHERE id = $1 LIMIT 1",
            [image_id]
        )
        if not existing:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Image not found", "IMAGE_NOT_FOUND"),
            )

        update_payload = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not update_payload:
            return SuccessResponse(data=ImageResponse(**existing[0]))

        await _validate_foreign_keys(
            adapter,
            document_id=update_payload.get("document_id"),
            chunk_id=update_payload.get("chunk_id"),
        )

        # Build dynamic UPDATE query
        set_clauses = []
        params = []
        param_count = 0
        
        for key, value in update_payload.items():
            param_count += 1
            set_clauses.append(f"{key} = ${param_count}")
            params.append(value)
        
        param_count += 1
        params.append(image_id)
        
        result = await adapter.execute_query(
            f"UPDATE krai_content.images SET {', '.join(set_clauses)} WHERE id = ${param_count} RETURNING *",
            params
        )
        
        if not result:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to update image"),
            )

        LOGGER.info("Updated image %s", image_id)
        await _insert_audit_log(
            adapter,
            record_id=image_id,
            operation="UPDATE",
            changed_by=current_user.get("id"),
            new_values=result[0],
            old_values=existing[0],
        )
        return SuccessResponse(data=ImageResponse(**result[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.delete(
    "/{image_id}",
    response_model=SuccessResponse[MessagePayload],
)
async def delete_image(
    image_id: str,
    delete_from_storage: bool = Query(
        False, description="Also delete the backing object from Cloudflare R2 storage."
    ),
    current_user: Dict[str, Any] = Depends(require_permission("images:delete")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[MessagePayload]:
    try:
        existing = await adapter.execute_query(
            "SELECT * FROM krai_content.images WHERE id = $1 LIMIT 1",
            [image_id]
        )
        if not existing:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Image not found", "IMAGE_NOT_FOUND"),
            )

        storage_deleted = False
        await adapter.execute_query(
            "DELETE FROM krai_content.images WHERE id = $1",
            [image_id]
        )
        LOGGER.info("Deleted image %s", image_id)
        await _insert_audit_log(
            adapter,
            record_id=image_id,
            operation="DELETE",
            changed_by=current_user.get("id"),
            old_values=existing[0],
        )

        if delete_from_storage:
            storage_service = create_storage_service()

            try:
                await storage_service.connect()
                storage_url = (existing[0].get("storage_url") or "") if existing else ""
                storage_path = existing[0].get("storage_path") if existing else None

                bucket_type = "document_images"

                public_error = os.getenv("OBJECT_STORAGE_PUBLIC_URL_ERROR") or os.getenv("R2_PUBLIC_URL_ERROR", "")
                public_parts = os.getenv("OBJECT_STORAGE_PUBLIC_URL_PARTS") or os.getenv("R2_PUBLIC_URL_PARTS", "")

                if storage_url and public_error and storage_url.startswith(public_error):
                    bucket_type = "error_images"
                elif storage_url and public_parts and storage_url.startswith(public_parts):
                    bucket_type = "parts_images"

                if storage_path:
                    try:
                        storage_deleted = await storage_service.delete_image(bucket_type, storage_path)
                    except Exception as delete_exc:  # pragma: no cover
                        LOGGER.warning(
                            "Failed to delete image %s from storage (%s/%s): %s",
                            image_id,
                            bucket_type,
                            storage_path,
                            delete_exc,
                        )
                else:
                    LOGGER.warning(
                        "Storage path missing for image %s; skipping storage deletion.",
                        image_id,
                    )
            except Exception as storage_exc:  # pragma: no cover
                LOGGER.warning(
                    "Object storage unavailable while deleting image %s: %s",
                    image_id,
                    storage_exc,
                )

        return SuccessResponse(
            data=MessagePayload(
                message="Image deleted successfully",
                deleted_from_storage=storage_deleted,
            )
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "/upload",
    response_model=SuccessResponse[ImageUploadResponse],
)
async def upload_image(
    file: UploadFile = File(...),
    document_id: Optional[str] = None,
    alt_text: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_permission("images:write")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ImageUploadResponse]:
    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=_error_response(
                    "Invalid File",
                    "Only image uploads are allowed.",
                    "INVALID_CONTENT_TYPE",
                ),
            )

        content = _decode_upload(file)
        file_size = len(content)

        if file_size > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=_error_response(
                    "Payload Too Large",
                    "Image exceeds 50MB limit.",
                    "FILE_TOO_LARGE",
                ),
            )

        storage_service = create_storage_service()

        try:
            await storage_service.connect()
        except Exception as exc:
            LOGGER.error("Failed to connect to object storage: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=_error_response(
                    "Storage Unavailable",
                    "Image storage service is temporarily unavailable. Please try again later.",
                    "STORAGE_UNAVAILABLE",
                ),
            )

        storage_result = await storage_service.upload_image(
            content=content,
            filename=file.filename or "upload.bin",
            bucket_type="document_images",
            metadata={}
        )

        is_duplicate = storage_result.get("is_duplicate", False)
        file_hash = storage_result.get("file_hash")
        resolved_url = (
            storage_result.get("storage_url")
            or storage_result.get("public_url")
            or storage_result.get("url")
        )

        # Check for duplicates
        existing = await adapter.execute_query(
            "SELECT id FROM krai_content.images WHERE file_hash = $1 LIMIT 1",
            [file_hash]
        )
        if existing:
            existing_image = await adapter.execute_query(
                "SELECT * FROM krai_content.images WHERE id = $1 LIMIT 1",
                [existing[0]["id"]]
            )
            return SuccessResponse(
                data=ImageUploadResponse(
                    image_id=existing_image[0]["id"],
                    storage_url=existing_image[0].get("storage_url"),
                    storage_path=existing_image[0].get("storage_path"),
                    message="Image already exists (deduplicated)",
                    is_duplicate=True,
                )
            )

        storage_path = storage_result.get("storage_path") or storage_result.get("key")
        original_filename = file.filename or "upload.bin"
        image_format = (original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else None)
        file_size = storage_result.get("size")

        image_id = str(uuid.uuid4())
        result = await adapter.execute_query(
            """
            INSERT INTO krai_content.images (
                id, filename, original_filename, storage_path, storage_url, file_size, image_format,
                file_hash, document_id, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING *
            """,
            [
                image_id,
                storage_path or original_filename,
                original_filename,
                storage_path,
                resolved_url,
                file_size,
                image_format,
                file_hash,
                document_id,
                datetime.now(timezone.utc).isoformat(),
            ],
        )

        await _insert_audit_log(
            adapter,
            record_id=result[0]["id"],
            operation="CREATE",
            changed_by=current_user.get("id"),
            new_values=result[0],
        )
        
        return SuccessResponse(
            data=ImageUploadResponse(
                image_id=result[0]["id"],
                storage_url=result[0].get("storage_url"),
                storage_path=result[0].get("storage_path"),
                message="Image uploaded successfully",
            )
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/{image_id}/download",
)
async def download_image(
    image_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("images:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> Response:
    try:
        existing = await adapter.execute_query(
            "SELECT id, storage_url, storage_path, filename, image_format FROM krai_content.images WHERE id = $1 LIMIT 1",
            [image_id]
        )
        if not existing:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Image not found", "IMAGE_NOT_FOUND"),
            )

        record = existing[0]
        storage_path = record.get("storage_path")
        storage_url = record.get("storage_url") or ""

        bucket_type = _infer_bucket_type_from_url(storage_url)

        if not storage_path and storage_url:
            public_documents = os.getenv("OBJECT_STORAGE_PUBLIC_URL_DOCUMENTS") or os.getenv("R2_PUBLIC_URL_DOCUMENTS", "")
            public_error = os.getenv("OBJECT_STORAGE_PUBLIC_URL_ERROR") or os.getenv("R2_PUBLIC_URL_ERROR", "")
            public_parts = os.getenv("OBJECT_STORAGE_PUBLIC_URL_PARTS") or os.getenv("R2_PUBLIC_URL_PARTS", "")

            prefix = ""
            if public_documents and storage_url.startswith(public_documents):
                prefix = public_documents
            elif public_error and storage_url.startswith(public_error):
                prefix = public_error
            elif public_parts and storage_url.startswith(public_parts):
                prefix = public_parts

            if prefix:
                trimmed = storage_url[len(prefix):]
                if trimmed.startswith("/"):
                    trimmed = trimmed[1:]
                storage_path = trimmed or None

        if not storage_path:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=_error_response(
                    "Bad Request",
                    "Image does not have a storage path for download.",
                    "IMAGE_STORAGE_PATH_MISSING",
                ),
            )

        storage_service = create_storage_service()

        try:
            await storage_service.connect()
        except Exception as exc:
            LOGGER.error("Failed to connect to object storage for download: %s", exc)
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=_error_response(
                    "Storage Unavailable",
                    "Image storage service is temporarily unavailable. Please try again later.",
                    "STORAGE_UNAVAILABLE",
                ),
            )

        try:
            content = await storage_service.download_image(bucket_type, storage_path)
        except Exception as exc:  # pragma: no cover
            LOGGER.error(
                "Failed to download image %s from storage (%s/%s): %s",
                image_id,
                bucket_type,
                storage_path,
                exc,
            )
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response(
                    "Server Error",
                    "Failed to download image from storage.",
                    "IMAGE_DOWNLOAD_FAILED",
                ),
            )

        media_type = _guess_media_type(record.get("filename"), record.get("image_format"))
        disposition_filename = record.get("filename") or f"{image_id}.bin"

        response = Response(content=content or b"", media_type=media_type)
        response.headers["Content-Disposition"] = f"attachment; filename={disposition_filename}"
        return response
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/by-document/{document_id}",
    response_model=SuccessResponse[ImageListResponse],
)
async def get_images_by_document(
    document_id: str,
    pagination: PaginationParams = Depends(),
    sort: ImageSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("images:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ImageListResponse]:
    try:
        # Build base query
        base_query = """
            SELECT 
                i.id,
                i.filename,
                i.original_filename,
                i.storage_url,
                i.storage_path,
                i.file_size,
                i.file_hash,
                i.document_id,
                i.created_at,
                i.updated_at,
                COUNT(*) OVER() as total_count
            FROM krai_content.images i
            WHERE i.document_id = $1
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
        
        images = [ImageResponse(**row) for row in result]
        
        payload = ImageListResponse(
            images=images,
            total=total_count,
            page=pagination.page,
            page_size=pagination.limit,
            total_pages=(total_count + pagination.limit - 1) // pagination.limit,
        )
        return SuccessResponse(data=payload)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/stats",
    response_model=SuccessResponse[ImageStatsResponse],
)
async def get_image_stats(
    current_user: Dict[str, Any] = Depends(require_permission("images:read")),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[ImageStatsResponse]:
    try:
        result = await adapter.execute_query("SELECT * FROM krai_content.images")
        records = result or []
        stats = _calculate_stats(records)
        return SuccessResponse(data=stats)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))
