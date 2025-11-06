"""Product CRUD and batch API routes."""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from math import ceil
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from supabase import Client

from backend.constants.product_types import ALLOWED_PRODUCT_TYPES
from backend.api.app import get_supabase
from backend.api.middleware.auth_middleware import require_permission
from backend.api.routes.response_models import ErrorResponse, SuccessResponse
from backend.models.document import PaginationParams
from backend.models.manufacturer import ManufacturerResponse
from backend.models.product import (
    ProductBatchCreateRequest,
    ProductBatchDeleteRequest,
    ProductBatchResponse,
    ProductBatchResult,
    ProductBatchUpdateRequest,
    ProductCreateRequest,
    ProductFilterParams,
    ProductListResponse,
    ProductResponse,
    ProductSeriesResponse,
    ProductSortParams,
    ProductStatsResponse,
    ProductUpdateRequest,
    ProductWithRelationsResponse,
    SortOrder,
)

LOGGER = logging.getLogger("krai.api.products")

router = APIRouter(prefix="/products", tags=["products"])


class MessagePayload(BaseModel):
    """Payload carrying a textual message."""

    message: str


class ProductTypesResponse(BaseModel):
    """Response payload listing all allowed product types."""

    product_types: List[str]


def _apply_product_filters(query: Any, filters: ProductFilterParams) -> Any:
    if filters.manufacturer_id:
        query = query.eq("manufacturer_id", filters.manufacturer_id)
    if filters.series_id:
        query = query.eq("series_id", filters.series_id)
    if filters.product_type:
        query = query.eq("product_type", filters.product_type)
    if filters.launch_date_from:
        query = query.gte("launch_date", filters.launch_date_from.isoformat())
    if filters.launch_date_to:
        query = query.lte("launch_date", filters.launch_date_to.isoformat())
    if filters.end_of_life_date_from:
        query = query.gte("end_of_life_date", filters.end_of_life_date_from.isoformat())
    if filters.end_of_life_date_to:
        query = query.lte("end_of_life_date", filters.end_of_life_date_to.isoformat())
    if filters.min_price is not None:
        query = query.gte("msrp_usd", filters.min_price)
    if filters.max_price is not None:
        query = query.lte("msrp_usd", filters.max_price)
    if filters.print_technology:
        query = query.eq("print_technology", filters.print_technology)
    if filters.network_capable is not None:
        query = query.eq("network_capable", filters.network_capable)
    if filters.search:
        search = filters.search
        query = query.or_(
            f"model_number.ilike.%{search}%,"
            f"model_name.ilike.%{search}%,"
            f"product_type.ilike.%{search}%"
        )
    return query


def _apply_sorting(query: Any, sort: ProductSortParams) -> Any:
    return query.order(sort.sort_by, desc=sort.sort_order == SortOrder.DESC)


def _apply_pagination(query: Any, pagination: PaginationParams) -> Any:
    start_index = (pagination.page - 1) * pagination.page_size
    end_index = start_index + pagination.page_size - 1
    return query.range(start_index, end_index)


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


def _build_product_relations(
    product: Dict[str, Any],
    supabase: Client,
    include_relations: bool,
) -> ProductWithRelationsResponse:
    product_payload: Dict[str, Any] = {**product}
    if not include_relations:
        return ProductWithRelationsResponse(**product_payload)

    manufacturer_id = product.get("manufacturer_id")
    if manufacturer_id:
        manufacturer_resp = (
            supabase.table("krai_core.manufacturers")
            .select("*")
            .eq("id", manufacturer_id)
            .limit(1)
            .execute()
        )
        manufacturer_data = (manufacturer_resp.data or [None])[0]
        if manufacturer_data:
            product_payload["manufacturer"] = ManufacturerResponse(**manufacturer_data)

    series_id = product.get("series_id")
    if series_id:
        series_resp = (
            supabase.table("krai_core.product_series")
            .select("*")
            .eq("id", series_id)
            .limit(1)
            .execute()
        )
        series_data = (series_resp.data or [None])[0]
        if series_data:
            product_payload["series"] = ProductSeriesResponse(**series_data)

    parent_id = product.get("parent_id")
    if parent_id:
        parent_resp = (
            supabase.table("krai_core.products")
            .select("*")
            .eq("id", parent_id)
            .limit(1)
            .execute()
        )
        parent_data = (parent_resp.data or [None])[0]
        if parent_data:
            product_payload["parent_product"] = ProductResponse(**parent_data)

    return ProductWithRelationsResponse(**product_payload)


@router.get(
    "",
    response_model=SuccessResponse[ProductListResponse],
)
def list_products(
    pagination: PaginationParams = Depends(),
    filters: ProductFilterParams = Depends(),
    sort: ProductSortParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_permission("products:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ProductListResponse]:
    try:
        query = supabase.table("krai_core.products").select("*", count="exact")
        query = _apply_product_filters(query, filters)
        query = _apply_sorting(query, sort)
        query = _apply_pagination(query, pagination)

        response = query.execute()
        data = response.data or []
        total = response.count or 0

        LOGGER.info(
            "Listed products page=%s page_size=%s total=%s",
            pagination.page,
            pagination.page_size,
            total,
        )

        product_list = ProductListResponse(
            products=[ProductResponse(**item) for item in data],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=_calculate_total_pages(total, pagination.page_size),
        )
        return SuccessResponse(data=product_list)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/types",
    response_model=SuccessResponse[ProductTypesResponse],
)
def get_product_types(
    current_user: Dict[str, Any] = Depends(require_permission("products:read")),
) -> SuccessResponse[ProductTypesResponse]:
    """Return the canonical list of allowed product types."""

    product_types = sorted(ALLOWED_PRODUCT_TYPES)
    return SuccessResponse(data=ProductTypesResponse(product_types=product_types))


@router.get(
    "/{product_id}",
    response_model=SuccessResponse[ProductWithRelationsResponse],
)
def get_product(
    product_id: str,
    include_relations: bool = Query(False),
    current_user: Dict[str, Any] = Depends(require_permission("products:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ProductWithRelationsResponse]:
    try:
        response = (
            supabase.table("krai_core.products")
            .select("*")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Product not found", "PRODUCT_NOT_FOUND"),
            )

        product = _build_product_relations(data[0], supabase, include_relations)
        LOGGER.info("Retrieved product %s include_relations=%s", product_id, include_relations)
        return SuccessResponse(data=product)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "",
    response_model=SuccessResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: ProductCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("products:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ProductResponse]:
    try:
        now = datetime.now(timezone.utc).isoformat()
        product_dict = payload.dict(exclude_none=True)
        product_dict["created_at"] = now
        product_dict["updated_at"] = now

        response = supabase.table("krai_core.products").insert(product_dict).execute()
        data = response.data or []
        if not data:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to create product"),
            )

        product_id = data[0]["id"]
        LOGGER.info("Created product %s", product_id)

        try:
            supabase.table("krai_system.audit_log").insert(
                {
                    "table_name": "products",
                    "record_id": product_id,
                    "operation": "INSERT",
                    "changed_by": current_user.get("id"),
                    "new_values": data[0],
                }
            ).execute()
        except Exception as audit_exc:  # pragma: no cover - defensive
            LOGGER.warning("Audit log insert failed for product %s: %s", product_id, audit_exc)

        return SuccessResponse(data=ProductResponse(**data[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.put(
    "/{product_id}",
    response_model=SuccessResponse[ProductResponse],
)
def update_product(
    product_id: str,
    payload: ProductUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("products:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ProductResponse]:
    try:
        existing = (
            supabase.table("krai_core.products")
            .select("*")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Product not found", "PRODUCT_NOT_FOUND"),
            )

        previous_record = data[0]

        update_payload = payload.dict(exclude_unset=True, exclude_none=True)
        update_payload["updated_at"] = datetime.now(timezone.utc).isoformat()

        response = (
            supabase.table("krai_core.products")
            .update(update_payload)
            .eq("id", product_id)
            .execute()
        )
        updated = response.data or []
        if not updated:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_response("Server Error", "Failed to update product"),
            )

        LOGGER.info("Updated product %s", product_id)

        try:
            supabase.table("krai_system.audit_log").insert(
                {
                    "table_name": "products",
                    "record_id": product_id,
                    "operation": "UPDATE",
                    "changed_by": current_user.get("id"),
                    "old_values": previous_record,
                    "new_values": update_payload,
                }
            ).execute()
        except Exception as audit_exc:  # pragma: no cover - defensive
            LOGGER.warning("Audit log update failed for product %s: %s", product_id, audit_exc)

        return SuccessResponse(data=ProductResponse(**updated[0]))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.delete(
    "/{product_id}",
    response_model=SuccessResponse[MessagePayload],
)
def delete_product(
    product_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("products:delete")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[MessagePayload]:
    try:
        existing = (
            supabase.table("krai_core.products")
            .select("*")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
        data = existing.data or []
        if not data:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=_error_response("Not Found", "Product not found", "PRODUCT_NOT_FOUND"),
            )

        supabase.table("krai_core.products").delete().eq("id", product_id).execute()
        LOGGER.info("Deleted product %s", product_id)

        try:
            supabase.table("krai_system.audit_log").insert(
                {
                    "table_name": "products",
                    "record_id": product_id,
                    "operation": "DELETE",
                    "changed_by": current_user.get("id"),
                    "old_values": data[0],
                }
            ).execute()
        except Exception as audit_exc:  # pragma: no cover - defensive
            LOGGER.warning("Audit log delete failed for product %s: %s", product_id, audit_exc)

        return SuccessResponse(data=MessagePayload(message="Product deleted successfully"))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/stats",
    response_model=SuccessResponse[ProductStatsResponse],
)
def get_product_stats(
    current_user: Dict[str, Any] = Depends(require_permission("products:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ProductStatsResponse]:
    try:
        total_resp = (
            supabase.table("krai_core.products")
            .select("id", count="exact", head=True)
            .execute()
        )
        total_products = total_resp.count or 0

        type_resp = (
            supabase.table("krai_core.products")
            .select("product_type,count:id", group="product_type")
            .execute()
        )
        by_type = {
            item.get("product_type"): int(item.get("count", 0))
            for item in type_resp.data or []
            if item.get("product_type")
        }

        manufacturer_resp = (
            supabase.table("krai_core.products")
            .select("manufacturer_id,count:id", group="manufacturer_id")
            .execute()
        )
        manufacturer_counts = {
            item.get("manufacturer_id"): int(item.get("count", 0))
            for item in manufacturer_resp.data or []
            if item.get("manufacturer_id")
        }

        manufacturer_names: Dict[str, str] = {}
        if manufacturer_counts:
            ids = list(manufacturer_counts.keys())
            manufacturer_data = (
                supabase.table("krai_core.manufacturers")
                .select("id,name")
                .in_("id", ids)
                .execute()
            ).data or []
            manufacturer_names = {item["id"]: item["name"] for item in manufacturer_data if item.get("id")}

        by_manufacturer = {
            manufacturer_names.get(manufacturer_id, manufacturer_id): count
            for manufacturer_id, count in manufacturer_counts.items()
        }

        today = date.today().isoformat()
        active_resp = (
            supabase.table("krai_core.products")
            .select("id", count="exact", head=True)
            .or_(f"end_of_life_date.is.null,end_of_life_date.gt.{today}")
            .execute()
        )
        active_products = active_resp.count or 0

        discontinued_resp = (
            supabase.table("krai_core.products")
            .select("id", count="exact", head=True)
            .lt("end_of_life_date", today)
            .execute()
        )
        discontinued_products = discontinued_resp.count or 0

        LOGGER.info(
            "Product stats computed totals=%s types=%s manufacturers=%s",
            total_products,
            len(by_type),
            len(by_manufacturer),
        )

        stats = ProductStatsResponse(
            total_products=total_products,
            by_type=by_type,
            by_manufacturer=by_manufacturer,
            active_products=active_products,
            discontinued_products=discontinued_products,
        )
        return SuccessResponse(data=stats)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.post(
    "/batch/create",
    response_model=SuccessResponse[ProductBatchResponse],
)
def batch_create_products(
    payload: ProductBatchCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("products:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ProductBatchResponse]:
    results: List[ProductBatchResult] = []
    success_count = 0
    try:
        for product in payload.products:
            try:
                now = datetime.now(timezone.utc).isoformat()
                product_dict = product.dict(exclude_none=True)
                product_dict["created_at"] = now
                product_dict["updated_at"] = now
                response = supabase.table("krai_core.products").insert(product_dict).execute()
                data = response.data or []
                if not data:
                    raise ValueError("Failed to insert product")
                results.append(ProductBatchResult(id=data[0]["id"], status="success"))
                success_count += 1

                try:
                    supabase.table("krai_system.audit_log").insert(
                        {
                            "table_name": "products",
                            "record_id": data[0]["id"],
                            "operation": "INSERT",
                            "changed_by": current_user.get("id"),
                            "new_values": data[0],
                        }
                    ).execute()
                except Exception as audit_exc:  # pragma: no cover - defensive
                    LOGGER.warning(
                        "Batch audit log insert failed for product %s: %s",
                        data[0]["id"],
                        audit_exc,
                    )
            except Exception as inner_exc:
                LOGGER.warning("Batch create failed for product %s: %s", product.model_number, inner_exc)
                results.append(
                    ProductBatchResult(
                        id=None,
                        status="failed",
                        error=str(inner_exc),
                    )
                )

        summary = ProductBatchResponse(
            success=success_count == len(payload.products),
            total=len(payload.products),
            successful=success_count,
            failed=len(payload.products) - success_count,
            results=results,
        )
        return SuccessResponse(data=summary)
    except HTTPException:
        raise
    except Exception as exc:
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.put(
    "/batch/update",
    response_model=SuccessResponse[ProductBatchResponse],
)
def batch_update_products(
    payload: ProductBatchUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("products:write")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ProductBatchResponse]:
    results: List[ProductBatchResult] = []
    success_count = 0
    try:
        for item in payload.updates:
            try:
                update_data = item.update_data.dict(exclude_unset=True, exclude_none=True)
                if not update_data:
                    raise ValueError("No update data provided")
                update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
                response = (
                    supabase.table("krai_core.products")
                    .update(update_data)
                    .eq("id", item.id)
                    .execute()
                )
                data = response.data or []
                if not data:
                    raise ValueError("Product not found or update failed")
                results.append(ProductBatchResult(id=item.id, status="success"))
                success_count += 1

                try:
                    supabase.table("krai_system.audit_log").insert(
                        {
                            "table_name": "products",
                            "record_id": item.id,
                            "operation": "UPDATE",
                            "changed_by": current_user.get("id"),
                            "new_values": update_data,
                        }
                    ).execute()
                except Exception as audit_exc:  # pragma: no cover - defensive
                    LOGGER.warning(
                        "Batch audit log update failed for product %s: %s",
                        item.id,
                        audit_exc,
                    )
            except Exception as inner_exc:
                LOGGER.warning("Batch update failed for product %s: %s", item.id, inner_exc)
                results.append(
                    ProductBatchResult(
                        id=item.id,
                        status="failed",
                        error=str(inner_exc),
                    )
                )

        summary = ProductBatchResponse(
            success=success_count == len(payload.updates),
            total=len(payload.updates),
            successful=success_count,
            failed=len(payload.updates) - success_count,
            results=results,
        )
        return SuccessResponse(data=summary)
    except HTTPException:
        raise
    except Exception as exc:
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.delete(
    "/batch/delete",
    response_model=SuccessResponse[ProductBatchResponse],
)
def batch_delete_products(
    payload: ProductBatchDeleteRequest,
    current_user: Dict[str, Any] = Depends(require_permission("products:delete")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[ProductBatchResponse]:
    results: List[ProductBatchResult] = []
    success_count = 0
    try:
        for product_id in payload.product_ids:
            try:
                response = (
                    supabase.table("krai_core.products")
                    .delete()
                    .eq("id", product_id)
                    .execute()
                )
                deleted = response.data or []
                if not deleted:
                    raise ValueError("Product not found")
                results.append(ProductBatchResult(id=product_id, status="success"))
                success_count += 1

                try:
                    supabase.table("krai_system.audit_log").insert(
                        {
                            "table_name": "products",
                            "record_id": product_id,
                            "operation": "DELETE",
                            "changed_by": current_user.get("id"),
                        }
                    ).execute()
                except Exception as audit_exc:  # pragma: no cover - defensive
                    LOGGER.warning(
                        "Batch audit log delete failed for product %s: %s",
                        product_id,
                        audit_exc,
                    )
            except Exception as inner_exc:
                LOGGER.warning("Batch delete failed for product %s: %s", product_id, inner_exc)
                results.append(
                    ProductBatchResult(
                        id=product_id,
                        status="failed",
                        error=str(inner_exc),
                    )
                )

        summary = ProductBatchResponse(
            success=success_count == len(payload.product_ids),
            total=len(payload.product_ids),
            successful=success_count,
            failed=len(payload.product_ids) - success_count,
            results=results,
        )
        return SuccessResponse(data=summary)
    except HTTPException:
        raise
    except Exception as exc:
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))


@router.get(
    "/series/by-manufacturer/{manufacturer_id}",
    response_model=SuccessResponse[List[ProductSeriesResponse]],
)
def get_manufacturer_series(
    manufacturer_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("products:read")),
    supabase: Client = Depends(get_supabase),
) -> SuccessResponse[List[ProductSeriesResponse]]:
    """Get all product series for a manufacturer."""
    try:
        response = (
            supabase.table("krai_core.product_series")
            .select("*")
            .eq("manufacturer_id", manufacturer_id)
            .execute()
        )
        series_data = response.data or []
        series_list = [ProductSeriesResponse(**item) for item in series_data]
        return SuccessResponse(data=series_list)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log_and_raise(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))
