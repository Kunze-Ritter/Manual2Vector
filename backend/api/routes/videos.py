"""Video CRUD and enrichment API routes."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from math import ceil
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from api.app import get_supabase
from api.middleware.auth_middleware import require_permission
from api.routes.response_models import ErrorResponse, SuccessResponse
from models.document import DocumentResponse, PaginationParams, SortOrder
from models.manufacturer import ManufacturerResponse
from models.product import ProductListResponse, ProductResponse, ProductSeriesResponse
from models.video import (
    VideoCreateRequest,
    VideoEnrichmentRequest,
    VideoEnrichmentResponse,
    VideoFilterParams,
    VideoListResponse,
    VideoProductLinkRequest,
    VideoResponse,
    VideoSortParams,
    VideoUpdateRequest,
    VideoWithRelationsResponse,
)
from services.video_enrichment_service import VideoEnrichmentService

LOGGER = logging.getLogger("krai.api.videos")

router = APIRouter(prefix="/videos", tags=["videos"])


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


def _apply_filters(query: Any, filters: VideoFilterParams) -> Any:
    if filters.manufacturer_id:
        query = query.eq("manufacturer_id", filters.manufacturer_id)
    if filters.series_id:
        query = query.eq("series_id", filters.series_id)
    if filters.document_id:
        query = query.eq("document_id", filters.document_id)
    if filters.platform:
        query = query.eq("platform", filters.platform.value)
    if filters.youtube_id:
        query = query.eq("youtube_id", filters.youtube_id)
    if filters.search:
        search = filters.search
        query = query.or_(
            ",".join(
                [
                    f"title.ilike.%{search}%",
                    f"description.ilike.%{search}%",
                    f"channel_title.ilike.%{search}%",
                ]
            )
        )
    return query


def _apply_sorting(query: Any, sort: VideoSortParams) -> Any:
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


def _fetch_series(supabase: Client, series_id: Optional[str]) -> Optional[ProductSeriesResponse]:
    if not series_id:
        return None
    response = (
        supabase.table("krai_core.product_series").select("*").eq("id", series_id).limit(1).execute()
    )
    data = response.data or []
    if not data:
        return None
    return ProductSeriesResponse(**data[0])


def _fetch_linked_products(supabase: Client, video_id: str) -> List[ProductResponse]:
    links = (
        supabase.table("krai_content.video_products")
        .select("product_id")
        .eq("video_id", video_id)
        .execute()
    )
    product_ids = [link["product_id"] for link in links.data or [] if link.get("product_id")]
    if not product_ids:
        return []
    products = (
        supabase.table("krai_core.products")
        .select("*")
        .in_("id", product_ids)
        .execute()
    )
    return [ProductResponse(**item) for item in products.data or []]


def _validate_foreign_keys(
    supabase: Client,
    *,
    manufacturer_id: Optional[str] = None,
    series_id: Optional[str] = None,
    document_id: Optional[str] = None,
) -> None:
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
    if series_id:
        series = (
            supabase.table("krai_core.product_series").select("id").eq("id", series_id).limit(1).execute()
        )
        if not (series.data or []):
            _log_and_raise(
                status.HTTP_400_BAD_REQUEST,
                f"Product series with ID {series_id} not found",
                error="Invalid Series",
                error_code="SERIES_NOT_FOUND",
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


def _build_relations(
    supabase: Client,
    record: Dict[str, Any],
    include_relations: bool,
) -> VideoWithRelationsResponse:
    base = VideoResponse(**record)
    if not include_relations:
        return VideoWithRelationsResponse(**base.model_dump(), linked_products=[])

    return VideoWithRelationsResponse(
        **base.model_dump(),
        manufacturer=_fetch_manufacturer(supabase, record.get("manufacturer_id")),
        series=_fetch_series(supabase, record.get("series_id")),
        document=_fetch_document(supabase, record.get("document_id")),
        linked_products=_fetch_linked_products(supabase, record.get("id")),
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
            "table_name": "videos",
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
        LOGGER.warning("Audit log insert failed for video %s: %s", record_id, audit_exc)


def _deduplicate_video(
    supabase: Client,
    payload: VideoCreateRequest,
) -> Optional[Dict[str, Any]]:
    if payload.youtube_id:
        duplicate = (
            supabase.table("krai_content.videos")
            .select("*")
            .eq("youtube_id", payload.youtube_id)
            .limit(1)
            .execute()
        )
        if duplicate.data:
            return duplicate.data[0]
    duplicate = (
        supabase.table("krai_content.videos")
        .select("*")
        .eq("video_url", str(payload.video_url))
        .limit(1)
        .execute()
    )
    if duplicate.data:
        return duplicate.data[0]
    return None


def _detect_content_type(filename: str) -> Optional[str]:
    if "." not in filename:
        return None
    extension = filename.rsplit(".", 1)[1].lower()
    mapping = {
        "mp4": "video/mp4",
        "mov": "video/quicktime",
        "avi": "video/x-msvideo",
        "mkv": "video/x-matroska",
        "webm": "video/webm",
    }
    return mapping.get(extension)


def _deserialize_metadata(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _serialize_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not metadata:
        return {}
    return metadata


@router.get("", response_model=SuccessResponse[VideoListResponse])
def list_videos(
    pagination: PaginationParams = Depends(),
    filters: VideoFilterParams = Depends(),
    sort: VideoSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("videos:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[VideoListResponse]:
    try:
        query = supabase.table("krai_content.videos").select("*", count="exact")
        query = _apply_filters(query, filters)
        query = _apply_sorting(query, sort)
        query = _apply_pagination(query, pagination)

        response = query.execute()
        data = response.data or []
        total = response.count or 0

        payload = VideoListResponse(
            videos=[VideoResponse(**item) for item in data],
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
    "/{video_id}",
    response_model=SuccessResponse[VideoWithRelationsResponse],
)
def get_video(
    video_id: str,
    include_relations: bool = Query(False),
    current_user: Dict[str, Any] = Depends(require_permission("videos:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[VideoWithRelationsResponse]:
    try:
        response = (
            supabase.table("krai_content.videos")
            .select("*")
            .eq("id", video_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Video not found", "VIDEO_NOT_FOUND"),
            )

        enriched = _build_relations(supabase, data[0], include_relations)
        return SuccessResponse(data=enriched)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "",
    response_model=SuccessResponse[VideoResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_video(
    payload: VideoCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("videos:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[VideoResponse]:
    try:
        _validate_foreign_keys(
            supabase,
            manufacturer_id=payload.manufacturer_id,
            series_id=payload.series_id,
            document_id=payload.document_id,
        )

        duplicate = _deduplicate_video(supabase, payload)
        if duplicate:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail=_error_response(
                    "Conflict",
                    "Video already exists with the provided identifier or URL.",
                    "VIDEO_DUPLICATE",
                ),
            )

        now = datetime.now(timezone.utc).isoformat()
        record_dict = payload.model_dump(exclude_none=True)
        record_dict["created_at"] = now
        record_dict["updated_at"] = now

        insert_response = supabase.table("krai_content.videos").insert(record_dict).execute()
        data = insert_response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to create video"),
            )

        video_id = data[0]["id"]
        LOGGER.info("Created video %s", video_id)
        _insert_audit_log(
            supabase,
            record_id=video_id,
            operation="INSERT",
            changed_by=current_user.get("id"),
            new_values=data[0],
        )
        return SuccessResponse(data=VideoResponse(**data[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.put(
    "/{video_id}",
    response_model=SuccessResponse[VideoResponse],
)
def update_video(
    video_id: str,
    payload: VideoUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("videos:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[VideoResponse]:
    try:
        existing = (
            supabase.table("krai_content.videos")
            .select("*")
            .eq("id", video_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Video not found", "VIDEO_NOT_FOUND"),
            )

        update_payload = payload.model_dump(exclude_unset=True, exclude_none=True)
        if not update_payload:
            return SuccessResponse(data=VideoResponse(**data[0]))

        _validate_foreign_keys(
            supabase,
            manufacturer_id=update_payload.get("manufacturer_id"),
            series_id=update_payload.get("series_id"),
            document_id=update_payload.get("document_id"),
        )

        update_payload["updated_at"] = datetime.now(timezone.utc).isoformat()

        response = (
            supabase.table("krai_content.videos")
            .update(update_payload)
            .eq("id", video_id)
            .execute()
        )
        updated = response.data or []
        if not updated:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to update video"),
            )

        LOGGER.info("Updated video %s", video_id)
        _insert_audit_log(
            supabase,
            record_id=video_id,
            operation="UPDATE",
            changed_by=current_user.get("id"),
            new_values=updated[0],
            old_values=data[0],
        )
        return SuccessResponse(data=VideoResponse(**updated[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.delete(
    "/{video_id}",
    response_model=SuccessResponse[Dict[str, str]],
)
def delete_video(
    video_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("videos:delete")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[Dict[str, str]]:
    try:
        existing = (
            supabase.table("krai_content.videos")
            .select("*")
            .eq("id", video_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Video not found", "VIDEO_NOT_FOUND"),
            )

        links = (
            supabase.table("krai_content.video_products")
            .select("id", count="exact", head=True)
            .eq("video_id", video_id)
            .execute()
        )
        if (links.count or 0) > 0:
            LOGGER.warning("Deleting video %s which has linked products", video_id)

        supabase.table("krai_content.videos").delete().eq("id", video_id).execute()
        LOGGER.info("Deleted video %s", video_id)
        _insert_audit_log(
            supabase,
            record_id=video_id,
            operation="DELETE",
            changed_by=current_user.get("id"),
            old_values=data[0],
        )
        return SuccessResponse(data={"message": "Video deleted successfully"})
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "/enrich",
    response_model=SuccessResponse[VideoEnrichmentResponse],
)
async def enrich_video(
    payload: VideoEnrichmentRequest,
    current_user: Dict[str, Any] = Depends(require_permission("videos:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[VideoEnrichmentResponse]:
    try:
        service = VideoEnrichmentService()
        result = await service.enrich_video_url(
            url=str(payload.video_url),
            document_id=payload.document_id,
            manufacturer_id=payload.manufacturer_id,
        )
        success = bool(result.get("saved")) or bool(result.get("database_id"))
        response_payload = VideoEnrichmentResponse(
            success=success and "error" not in result,
            video_id=result.get("database_id"),
            title=result.get("title"),
            platform=result.get("platform"),
            duration=result.get("duration"),
            error=result.get("error"),
        )
        return SuccessResponse(data=response_payload)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "/{video_id}/link-products",
    response_model=SuccessResponse[Dict[str, Any]],
)
def link_video_products(
    video_id: str,
    payload: VideoProductLinkRequest,
    current_user: Dict[str, Any] = Depends(require_permission("videos:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[Dict[str, Any]]:
    try:
        video = (
            supabase.table("krai_content.videos")
            .select("id")
            .eq("id", video_id)
            .limit(1)
            .execute()
        )
        if not (video.data or []):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Video not found", "VIDEO_NOT_FOUND"),
            )

        linked_count = 0
        for product_id in payload.product_ids:
            product = (
                supabase.table("krai_core.products")
                .select("id")
                .eq("id", product_id)
                .limit(1)
                .execute()
            )
            if not (product.data or []):
                LOGGER.warning("Product %s not found when linking to video %s", product_id, video_id)
                continue

            link = (
                supabase.table("krai_content.video_products")
                .select("id")
                .eq("video_id", video_id)
                .eq("product_id", product_id)
                .limit(1)
                .execute()
            )
            if link.data:
                continue

            supabase.table("krai_content.video_products").insert(
                {"video_id": video_id, "product_id": product_id}
            ).execute()
            linked_count += 1

        return SuccessResponse(
            data={
                "success": True,
                "linked_count": linked_count,
                "video_id": video_id,
                "product_ids": payload.product_ids,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.delete(
    "/{video_id}/unlink-products/{product_id}",
    response_model=SuccessResponse[Dict[str, Any]],
)
def unlink_video_product(
    video_id: str,
    product_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("videos:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[Dict[str, Any]]:
    try:
        (
            supabase.table("krai_content.video_products")
            .delete()
            .eq("video_id", video_id)
            .eq("product_id", product_id)
            .execute()
        )

        return SuccessResponse(
            data={
                "success": True,
                "message": "Video unlinked from product",
                "video_id": video_id,
                "product_id": product_id,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/{video_id}/products",
    response_model=SuccessResponse[ProductListResponse],
)
def get_video_products(
    video_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("videos:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ProductListResponse]:
    try:
        products = _fetch_linked_products(supabase, video_id)
        payload = ProductListResponse(
            products=products,
            total=len(products),
            page=1,
            page_size=len(products) or 1,
            total_pages=1,
        )
        return SuccessResponse(data=payload)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/by-product/{product_id}",
    response_model=SuccessResponse[VideoListResponse],
)
def get_videos_by_product(
    product_id: str,
    pagination: PaginationParams = Depends(),
    sort: VideoSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("videos:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[VideoListResponse]:
    try:
        links = (
            supabase.table("krai_content.video_products")
            .select("video_id")
            .eq("product_id", product_id)
            .execute()
        )
        video_ids = [item["video_id"] for item in links.data or [] if item.get("video_id")]
        if not video_ids:
            payload = VideoListResponse(
                videos=[],
                total=0,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=1,
            )
            return SuccessResponse(data=payload)

        query = (
            supabase.table("krai_content.videos")
            .select("*", count="exact")
            .in_("id", video_ids)
        )
        query = _apply_sorting(query, sort)
        query = _apply_pagination(query, pagination)

        response = query.execute()
        data = response.data or []
        total = response.count or 0

        payload = VideoListResponse(
            videos=[VideoResponse(**item) for item in data],
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
