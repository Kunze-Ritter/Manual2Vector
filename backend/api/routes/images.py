"""Image CRUD and storage API routes."""
from __future__ import annotations

import io
import logging
import os
from math import ceil
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel
from supabase import Client

from api.app import get_supabase
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


def _apply_filters(query: Any, filters: ImageFilterParams) -> Any:
    if filters.document_id:
        query = query.eq("document_id", filters.document_id)
    if filters.chunk_id:
        query = query.eq("chunk_id", filters.chunk_id)
    if filters.page_number is not None:
        query = query.eq("page_number", filters.page_number)
    if filters.image_type:
        query = query.eq("image_type", filters.image_type.value)
    if filters.contains_text is not None:
        query = query.eq("contains_text", filters.contains_text)
    if filters.file_hash:
        query = query.eq("file_hash", filters.file_hash)
    if filters.search:
        search = filters.search
        query = query.or_(
            ",".join(
                [
                    f"filename.ilike.%{search}%",
                    f"ai_description.ilike.%{search}%",
                    f"manual_description.ilike.%{search}%",
                    f"ocr_text.ilike.%{search}%",
                ]
            )
        )
    return query


def _apply_sorting(query: Any, sort: ImageSortParams) -> Any:
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


def _fetch_chunk(supabase: Client, chunk_id: Optional[str]) -> Optional[Dict[str, Any]]:
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
    return data[0]


def _build_relations(
    supabase: Client,
    record: Dict[str, Any],
    include_relations: bool,
) -> ImageWithRelationsResponse:
    base = ImageResponse(**record)
    if not include_relations:
        return ImageWithRelationsResponse(**base.model_dump())

    chunk = _fetch_chunk(supabase, record.get("chunk_id"))
    chunk_payload = None
    if chunk:
        from models.image import ChunkSnippet

        chunk_payload = ChunkSnippet(**chunk)

    return ImageWithRelationsResponse(
        **base.model_dump(),
        document=_fetch_document(supabase, record.get("document_id")),
        chunk=chunk_payload,
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
            "table_name": "images",
            "record_id": record_id,
            "operation": operation,
            "changed_by": changed_by,
        }
        if new_values is not None:
            payload["new_values"] = new_values
        if old_values is not None:
            payload["old_values"] = old_values
        supabase.table("krai_system.audit_log").insert(payload).execute()
    except Exception as audit_exc:  # pragma: no cover
        LOGGER.warning("Audit log insert failed for image %s: %s", record_id, audit_exc)


def _validate_foreign_keys(
    supabase: Client,
    *,
    document_id: Optional[str] = None,
    chunk_id: Optional[str] = None,
) -> None:
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


def _deduplicate_hash(supabase: Client, file_hash: Optional[str]) -> Optional[Dict[str, Any]]:
    if not file_hash:
        return None
    response = (
        supabase.table("krai_content.images").select("*").eq("file_hash", file_hash).limit(1).execute()
    )
    data = response.data or []
    if not data:
        return None
    return data[0]


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
def list_images(
    pagination: PaginationParams = Depends(),
    filters: ImageFilterParams = Depends(),
    sort: ImageSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("images:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ImageListResponse]:
    try:
        query = supabase.table("krai_content.images").select("*", count="exact")
        query = _apply_filters(query, filters)
        query = _apply_sorting(query, sort)
        query = _apply_pagination(query, pagination)

        response = query.execute()
        data = response.data or []
        total = response.count or 0

        payload = ImageListResponse(
            images=[ImageResponse(**item) for item in data],
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
def get_image(
    image_id: str,
    include_relations: bool = Query(False),
    current_user: Dict[str, Any] = Depends(require_permission("images:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ImageWithRelationsResponse]:
    try:
        response = (
            supabase.table("krai_content.images")
            .select("*")
            .eq("id", image_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Image not found", "IMAGE_NOT_FOUND"),
            )

        enriched = _build_relations(supabase, data[0], include_relations)
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
def create_image(
    payload: ImageCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("images:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ImageResponse]:
    try:
        _validate_foreign_keys(
            supabase,
            document_id=payload.document_id,
            chunk_id=payload.chunk_id,
        )

        if payload.file_hash:
            duplicate = _deduplicate_hash(supabase, payload.file_hash)
            if duplicate:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail=_error_response(
                        "Conflict",
                        "Image with this hash already exists.",
                        "IMAGE_DUPLICATE",
                    ),
                )

        insert_response = supabase.table("krai_content.images").insert(payload.model_dump()).execute()
        data = insert_response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to create image"),
            )

        image_id = data[0]["id"]
        LOGGER.info("Created image %s", image_id)
        _insert_audit_log(
            supabase,
            record_id=image_id,
            operation="INSERT",
            changed_by=current_user.get("id"),
            new_values=data[0],
        )
        return SuccessResponse(data=ImageResponse(**data[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.put(
    "/{image_id}",
    response_model=SuccessResponse[ImageResponse],
)
def update_image(
    image_id: str,
    payload: ImageUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("images:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ImageResponse]:
    try:
        existing = (
            supabase.table("krai_content.images")
            .select("*")
            .eq("id", image_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Image not found", "IMAGE_NOT_FOUND"),
            )

        update_payload = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not update_payload:
            return SuccessResponse(data=ImageResponse(**data[0]))

        _validate_foreign_keys(
            supabase,
            document_id=update_payload.get("document_id"),
            chunk_id=update_payload.get("chunk_id"),
        )

        response = (
            supabase.table("krai_content.images")
            .update(update_payload)
            .eq("id", image_id)
            .execute()
        )
        updated = response.data or []
        if not updated:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to update image"),
            )

        LOGGER.info("Updated image %s", image_id)
        _insert_audit_log(
            supabase,
            record_id=image_id,
            operation="UPDATE",
            changed_by=current_user.get("id"),
            new_values=updated[0],
            old_values=data[0],
        )
        return SuccessResponse(data=ImageResponse(**updated[0]))
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
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[MessagePayload]:
    try:
        existing = (
            supabase.table("krai_content.images")
            .select("*")
            .eq("id", image_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Image not found", "IMAGE_NOT_FOUND"),
            )

        storage_deleted = False
        supabase.table("krai_content.images").delete().eq("id", image_id).execute()
        LOGGER.info("Deleted image %s", image_id)
        _insert_audit_log(
            supabase,
            record_id=image_id,
            operation="DELETE",
            changed_by=current_user.get("id"),
            old_values=data[0],
        )

        if delete_from_storage:
            storage_service = create_storage_service()

            try:
                await storage_service.connect()
                storage_url = (data[0].get("storage_url") or "") if data else ""
                storage_path = data[0].get("storage_path") if data else None

                bucket_type = "document_images"
                public_documents = os.getenv("R2_PUBLIC_URL_DOCUMENTS", "")
                public_error = os.getenv("R2_PUBLIC_URL_ERROR", "")
                public_parts = os.getenv("R2_PUBLIC_URL_PARTS", "")

                if storage_url and public_error and storage_url.startswith(public_error):
                    bucket_type = "error_images"
                elif storage_url and public_parts and storage_url.startswith(public_parts):
                    bucket_type = "parts_images"
                elif storage_url and public_documents and storage_url.startswith(public_documents):
                    bucket_type = "document_images"

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
    bucket: Optional[str] = Query(None, description="Bucket type (document_images, error_images, parts_images)."),
    document_id: Optional[str] = Query(None),
    chunk_id: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(require_permission("images:write")),
    supabase: Client = Depends(get_supabase),
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

        bucket_type = _map_bucket(bucket)

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
            bucket_type=bucket_type.value,
            metadata={}
        )

        is_duplicate = storage_result.get("is_duplicate", False)
        file_hash = storage_result.get("file_hash")
        resolved_url = (
            storage_result.get("storage_url")
            or storage_result.get("public_url")
            or storage_result.get("url")
        )

        if is_duplicate:
            existing = _deduplicate_hash(supabase, file_hash)
            if existing:
                return SuccessResponse(
                    data=ImageUploadResponse(
                        success=True,
                        image_id=existing.get("id"),
                        storage_url=existing.get("storage_url"),
                        storage_path=existing.get("storage_path"),
                        file_hash=file_hash,
                        file_size=existing.get("file_size"),
                        is_duplicate=True,
                        bucket=bucket_type.value,
                    )
                )

        metadata_payload = {
            "document_id": document_id,
            "chunk_id": chunk_id,
            "storage_url": resolved_url,
            "storage_path": storage_result.get("storage_path"),
            "filename": storage_result.get("key"),
            "original_filename": file.filename,
            "file_size": storage_result.get("size"),
            "file_hash": file_hash,
        }

        _validate_foreign_keys(
            supabase,
            document_id=document_id,
            chunk_id=chunk_id,
        )

        insert_payload = ImageCreateRequest(**metadata_payload)
        insert_response = supabase.table("krai_content.images").insert(insert_payload.model_dump()).execute()
        data = insert_response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to persist uploaded image"),
            )

        image_id = data[0]["id"]
        LOGGER.info("Uploaded image %s via API", image_id)
        _insert_audit_log(
            supabase,
            record_id=image_id,
            operation="INSERT",
            changed_by=current_user.get("id"),
            new_values=data[0],
        )

        return SuccessResponse(
            data=ImageUploadResponse(
                success=True,
                image_id=image_id,
                storage_url=resolved_url,
                storage_path=storage_result.get("storage_path"),
                file_hash=file_hash,
                file_size=storage_result.get("size"),
                is_duplicate=False,
                bucket=bucket_type.value,
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
    supabase: Client = Depends(get_supabase),
) -> Response:
    try:
        existing = (
            supabase.table("krai_content.images")
            .select("id, storage_url, storage_path, filename, image_format")
            .eq("id", image_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Image not found", "IMAGE_NOT_FOUND"),
            )

        record = data[0]
        storage_path = record.get("storage_path")
        if not storage_path:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=_error_response(
                    "Bad Request",
                    "Image does not have a storage path for download.",
                    "IMAGE_STORAGE_PATH_MISSING",
                ),
            )

        bucket_type = _infer_bucket_type_from_url(record.get("storage_url"))

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
def get_images_by_document(
    document_id: str,
    pagination: PaginationParams = Depends(),
    sort: ImageSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("images:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ImageListResponse]:
    try:
        query = (
            supabase.table("krai_content.images")
            .select("*", count="exact")
            .eq("document_id", document_id)
        )
        query = _apply_sorting(query, sort)
        query = _apply_pagination(query, pagination)

        response = query.execute()
        data = response.data or []
        total = response.count or 0

        payload = ImageListResponse(
            images=[ImageResponse(**item) for item in data],
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
    "/stats",
    response_model=SuccessResponse[ImageStatsResponse],
)
def get_image_stats(
    current_user: Dict[str, Any] = Depends(require_permission("images:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ImageStatsResponse]:
    try:
        response = supabase.table("krai_content.images").select("*").execute()
        records = response.data or []
        stats = _calculate_stats(records)
        return SuccessResponse(data=stats)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))
