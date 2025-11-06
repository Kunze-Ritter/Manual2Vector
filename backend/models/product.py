"""
Product API models for CRUD operations and batch processing.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from math import ceil
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, root_validator, validator


class SortOrder(str, Enum):
    """Supported sort orders."""

    ASC = "asc"
    DESC = "desc"


class ProductCreateRequest(BaseModel):
    """Payload used to create a new product record."""

    manufacturer_id: str = Field(..., min_length=1)
    series_id: str = Field(..., min_length=1)
    model_number: str = Field(..., min_length=1, max_length=100)
    model_name: str = Field(..., min_length=1, max_length=255)
    product_type: str = Field(..., min_length=1, max_length=100)
    launch_date: Optional[date] = None
    end_of_life_date: Optional[date] = None
    msrp_usd: Optional[float] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    dimensions_mm: Optional[Dict[str, Union[int, float]]] = None
    color_options: Optional[List[str]] = None
    connectivity_options: Optional[List[str]] = None
    print_technology: Optional[str] = Field(None, max_length=100)
    max_print_speed_ppm: Optional[int] = Field(None, ge=0)
    max_resolution_dpi: Optional[int] = Field(None, ge=0)
    max_paper_size: Optional[str] = Field(None, max_length=50)
    duplex_capable: Optional[bool] = None
    network_capable: Optional[bool] = None
    mobile_print_support: Optional[bool] = None
    supported_languages: Optional[List[str]] = None
    energy_star_certified: Optional[bool] = None
    warranty_months: Optional[int] = Field(None, ge=0)
    service_manual_url: Optional[HttpUrl] = None
    parts_catalog_url: Optional[HttpUrl] = None
    driver_download_url: Optional[HttpUrl] = None
    firmware_version: Optional[str] = Field(None, max_length=100)
    option_dependencies: Optional[Dict[str, List[str]]] = None
    replacement_parts: Optional[Dict[str, List[str]]] = None
    common_issues: Optional[Dict[str, str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "manufacturer_id": "8dc1d2a5-8ef3-4dc1-90f9-1d4b7c6c1234",
                "series_id": "2b6450f2-58f3-41f6-a03b-84b324adf943",
                "model_number": "CS920",
                "model_name": "Lexmark CS920",
                "product_type": "printer",
                "launch_date": "2023-04-01",
                "msrp_usd": 3299.99,
                "print_technology": "laser",
                "network_capable": True,
                "supported_languages": ["en", "de", "fr"],
                "warranty_months": 24,
                "service_manual_url": "https://example.com/manuals/cs920",
                "driver_download_url": "https://example.com/drivers/cs920",
                "option_dependencies": {"finisher": ["duplex_module"]},
                "replacement_parts": {"fuser": ["40X7702"]},
                "common_issues": {"900.01": "Controller board reset"},
            }
        }

    @validator("color_options", "connectivity_options", "supported_languages")
    def validate_non_empty_lists(
        cls, value: Optional[List[str]]
    ) -> Optional[List[str]]:
        if value is None:
            return value
        if not value:
            raise ValueError("List cannot be empty when provided")
        if any(not item for item in value):
            raise ValueError("List items cannot be empty strings")
        return value

    @validator("dimensions_mm")
    def validate_dimensions(cls, value: Optional[Dict[str, Union[int, float]]]):
        if value is None:
            return value
        if not value:
            raise ValueError("dimensions_mm cannot be empty when provided")
        for key, number in value.items():
            if number is None or float(number) <= 0:
                raise ValueError(
                    "dimensions_mm values must be positive numbers"
                )
            if key not in {"width", "height", "depth"}:
                raise ValueError(
                    "dimensions_mm keys must be one of: width, height, depth"
                )
        return value

    @root_validator
    def validate_dates(cls, values: Dict[str, object]) -> Dict[str, object]:
        launch_date = values.get("launch_date")
        end_of_life = values.get("end_of_life_date")
        if launch_date and end_of_life and launch_date > end_of_life:
            raise ValueError("launch_date must be before end_of_life_date")
        return values


class ProductUpdateRequest(BaseModel):
    """Payload used to update an existing product."""

    manufacturer_id: Optional[str] = None
    series_id: Optional[str] = None
    model_number: Optional[str] = Field(None, min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, min_length=1, max_length=255)
    product_type: Optional[str] = Field(None, min_length=1, max_length=100)
    launch_date: Optional[date] = None
    end_of_life_date: Optional[date] = None
    msrp_usd: Optional[float] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    dimensions_mm: Optional[Dict[str, Union[int, float]]] = None
    color_options: Optional[List[str]] = None
    connectivity_options: Optional[List[str]] = None
    print_technology: Optional[str] = Field(None, max_length=100)
    max_print_speed_ppm: Optional[int] = Field(None, ge=0)
    max_resolution_dpi: Optional[int] = Field(None, ge=0)
    max_paper_size: Optional[str] = Field(None, max_length=50)
    duplex_capable: Optional[bool] = None
    network_capable: Optional[bool] = None
    mobile_print_support: Optional[bool] = None
    supported_languages: Optional[List[str]] = None
    energy_star_certified: Optional[bool] = None
    warranty_months: Optional[int] = Field(None, ge=0)
    service_manual_url: Optional[HttpUrl] = None
    parts_catalog_url: Optional[HttpUrl] = None
    driver_download_url: Optional[HttpUrl] = None
    firmware_version: Optional[str] = Field(None, max_length=100)
    option_dependencies: Optional[Dict[str, List[str]]] = None
    replacement_parts: Optional[Dict[str, List[str]]] = None
    common_issues: Optional[Dict[str, str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "Lexmark CS920 Pro",
                "network_capable": True,
                "launch_date": "2024-01-15",
                "max_print_speed_ppm": 50,
                "supported_languages": ["en", "es"],
            }
        }

    @validator("color_options", "connectivity_options", "supported_languages")
    def validate_non_empty_lists(
        cls, value: Optional[List[str]]
    ) -> Optional[List[str]]:
        if value is None:
            return value
        if not value:
            raise ValueError("List cannot be empty when provided")
        if any(not item for item in value):
            raise ValueError("List items cannot be empty strings")
        return value

    @validator("dimensions_mm")
    def validate_dimensions(cls, value: Optional[Dict[str, Union[int, float]]]):
        if value is None:
            return value
        if not value:
            raise ValueError("dimensions_mm cannot be empty when provided")
        for key, number in value.items():
            if number is None or float(number) <= 0:
                raise ValueError(
                    "dimensions_mm values must be positive numbers"
                )
            if key not in {"width", "height", "depth"}:
                raise ValueError(
                    "dimensions_mm keys must be one of: width, height, depth"
                )
        return value

    @root_validator
    def validate_dates(cls, values: Dict[str, object]) -> Dict[str, object]:
        launch_date = values.get("launch_date")
        end_of_life = values.get("end_of_life_date")
        if launch_date and end_of_life and launch_date > end_of_life:
            raise ValueError("launch_date must be before end_of_life_date")
        return values


class ProductFilterParams(BaseModel):
    """Query parameters used to filter products in list view."""

    manufacturer_id: Optional[str] = None
    series_id: Optional[str] = None
    product_type: Optional[str] = None
    launch_date_from: Optional[date] = None
    launch_date_to: Optional[date] = None
    end_of_life_date_from: Optional[date] = None
    end_of_life_date_to: Optional[date] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    print_technology: Optional[str] = None
    network_capable: Optional[bool] = None
    search: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "manufacturer_id": "8dc1d2a5-8ef3-4dc1-90f9-1d4b7c6c1234",
                "product_type": "printer",
                "launch_date_from": "2022-01-01",
                "launch_date_to": "2024-12-31",
                "min_price": 1000,
                "max_price": 5000,
                "network_capable": True,
                "search": "Lexmark CS",
            }
        }

    @root_validator
    def validate_ranges(cls, values: Dict[str, object]) -> Dict[str, object]:
        launch_from = values.get("launch_date_from")
        launch_to = values.get("launch_date_to")
        if launch_from and launch_to and launch_from > launch_to:
            raise ValueError("launch_date_from must be before launch_date_to")

        eol_from = values.get("end_of_life_date_from")
        eol_to = values.get("end_of_life_date_to")
        if eol_from and eol_to and eol_from > eol_to:
            raise ValueError(
                "end_of_life_date_from must be before end_of_life_date_to"
            )

        min_price = values.get("min_price")
        max_price = values.get("max_price")
        if (min_price is not None and max_price is not None) and (
            min_price > max_price
        ):
            raise ValueError("min_price cannot exceed max_price")

        return values


class ProductSortParams(BaseModel):
    """Sorting parameters for product listings."""

    sort_by: str = Field("created_at", description="Field name to sort by")
    sort_order: SortOrder = Field(
        SortOrder.DESC, description="Sort order: asc or desc"
    )

    ALLOWED_SORT_FIELDS = {
        "created_at",
        "updated_at",
        "model_number",
        "model_name",
        "product_type",
        "launch_date",
        "msrp_usd",
    }

    class Config:
        json_schema_extra = {
            "example": {
                "sort_by": "launch_date",
                "sort_order": "asc",
            }
        }

    @validator("sort_by")
    def validate_sort_by(cls, value: str) -> str:
        if value not in cls.ALLOWED_SORT_FIELDS:
            allowed = ", ".join(sorted(cls.ALLOWED_SORT_FIELDS))
            raise ValueError(f"sort_by must be one of: {allowed}")
        return value

    @validator("sort_order", pre=True)
    def validate_sort_order(cls, value: Union[str, SortOrder]) -> SortOrder:
        try:
            return SortOrder(value)
        except ValueError as exc:
            allowed = ", ".join(item.value for item in SortOrder)
            raise ValueError(f"sort_order must be one of: {allowed}") from exc


class ProductResponse(BaseModel):
    """Product representation used in API responses."""

    id: str
    parent_id: Optional[str] = None
    manufacturer_id: str
    series_id: str
    model_number: str
    model_name: str
    product_type: str
    launch_date: Optional[date] = None
    end_of_life_date: Optional[date] = None
    msrp_usd: Optional[float] = None
    weight_kg: Optional[float] = None
    dimensions_mm: Optional[Dict[str, Union[int, float]]] = None
    color_options: Optional[List[str]] = None
    connectivity_options: Optional[List[str]] = None
    print_technology: Optional[str] = None
    max_print_speed_ppm: Optional[int] = None
    max_resolution_dpi: Optional[int] = None
    max_paper_size: Optional[str] = None
    duplex_capable: Optional[bool] = None
    network_capable: Optional[bool] = None
    mobile_print_support: Optional[bool] = None
    supported_languages: Optional[List[str]] = None
    energy_star_certified: Optional[bool] = None
    warranty_months: Optional[int] = None
    service_manual_url: Optional[HttpUrl] = None
    parts_catalog_url: Optional[HttpUrl] = None
    driver_download_url: Optional[HttpUrl] = None
    firmware_version: Optional[str] = None
    option_dependencies: Optional[Dict[str, List[str]]] = None
    replacement_parts: Optional[Dict[str, List[str]]] = None
    common_issues: Optional[Dict[str, str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "f214ab9d-6727-406d-bf4e-8e1f0346a123",
                "manufacturer_id": "8dc1d2a5-8ef3-4dc1-90f9-1d4b7c6c1234",
                "series_id": "2b6450f2-58f3-41f6-a03b-84b324adf943",
                "model_number": "CS920",
                "model_name": "Lexmark CS920",
                "product_type": "printer",
                "launch_date": "2023-04-01",
                "network_capable": True,
                "supported_languages": ["en", "de", "fr"],
                "created_at": "2025-10-30T12:00:00Z",
                "updated_at": "2025-10-30T12:30:00Z",
            }
        }


class ProductSeriesResponse(BaseModel):
    """Related product series information."""

    id: str
    manufacturer_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "2b6450f2-58f3-41f6-a03b-84b324adf943",
                "manufacturer_id": "8dc1d2a5-8ef3-4dc1-90f9-1d4b7c6c1234",
                "name": "CS900 Series",
                "description": "High-performance color laser printers",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-06-15T12:00:00Z",
            }
        }


class ProductWithRelationsResponse(ProductResponse):
    """Product response enriched with related entities."""

    manufacturer: Optional["ManufacturerResponse"] = None
    series: Optional[ProductSeriesResponse] = None
    parent_product: Optional[ProductResponse] = None

    class Config(ProductResponse.Config):
        json_schema_extra = {
            "example": {
                **ProductResponse.Config.json_schema_extra["example"],
                "manufacturer": {
                    "id": "b686a4a8-59e3-4f7b-befe-0bbb9fa77b12",
                    "name": "Lexmark",
                    "country": "United States",
                    "created_at": "2020-01-01T00:00:00Z",
                    "updated_at": "2025-09-01T12:00:00Z",
                },
                "series": ProductSeriesResponse.Config.json_schema_extra["example"],
                "parent_product": None,
            }
        }


class ProductListResponse(BaseModel):
    """Paginated list response for products."""

    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "products": [ProductResponse.Config.json_schema_extra["example"]],
                "total": 42,
                "page": 1,
                "page_size": 10,
                "total_pages": 5,
            }
        }

    @root_validator
    def validate_pagination(cls, values: Dict[str, int]) -> Dict[str, int]:
        total = values.get("total", 0)
        page_size = values.get("page_size", 1)
        if page_size <= 0:
            raise ValueError("page_size must be greater than 0")
        values["total_pages"] = max(1, ceil(total / page_size)) if total else 1
        return values


class ProductStatsResponse(BaseModel):
    """Aggregated statistics about products."""

    total_products: int
    by_type: Dict[str, int]
    by_manufacturer: Dict[str, int]
    active_products: int
    discontinued_products: int

    class Config:
        json_schema_extra = {
            "example": {
                "total_products": 1200,
                "by_type": {"printer": 800, "multifunction": 400},
                "by_manufacturer": {"Lexmark": 300, "Canon": 250},
                "active_products": 950,
                "discontinued_products": 250,
            }
        }


class ProductBatchCreateRequest(BaseModel):
    """Batch creation payload for products."""

    products: List[ProductCreateRequest] = Field(..., max_items=100)

    @validator("products")
    def validate_batch_size(cls, value: List[ProductCreateRequest]) -> List[ProductCreateRequest]:
        if len(value) > 100:
            raise ValueError("Maximum 100 products per batch")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "products": [
                    ProductCreateRequest.Config.json_schema_extra["example"],
                ]
            }
        }


class ProductBatchUpdateItem(BaseModel):
    """Individual update entry used in batch updates."""

    id: str = Field(..., min_length=1)
    update_data: ProductUpdateRequest

    class Config:
        json_schema_extra = {
            "example": {
                "id": "f214ab9d-6727-406d-bf4e-8e1f0346a123",
                "update_data": ProductUpdateRequest.Config.json_schema_extra[
                    "example"
                ],
            }
        }


class ProductBatchUpdateRequest(BaseModel):
    """Batch update payload for products."""

    updates: List[ProductBatchUpdateItem] = Field(..., max_items=100)

    @validator("updates")
    def validate_batch_size(cls, value: List[ProductBatchUpdateItem]) -> List[ProductBatchUpdateItem]:
        if len(value) > 100:
            raise ValueError("Maximum 100 updates per batch")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "updates": [ProductBatchUpdateItem.Config.json_schema_extra["example"]]
            }
        }


class ProductBatchDeleteRequest(BaseModel):
    """Batch delete payload for products."""

    product_ids: List[str] = Field(..., max_items=100)

    @validator("product_ids")
    def validate_ids(cls, value: List[str]) -> List[str]:
        if len(value) > 100:
            raise ValueError("Maximum 100 products per batch")
        if any(not item for item in value):
            raise ValueError("product_ids cannot contain empty strings")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "product_ids": [
                    "f214ab9d-6727-406d-bf4e-8e1f0346a123",
                    "c0b0c10f-5e94-4b29-8d9f-8cbb8fbd8d02",
                ]
            }
        }


class ProductBatchResult(BaseModel):
    """Individual result entry for batch responses."""

    id: Optional[str]
    status: str
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "f214ab9d-6727-406d-bf4e-8e1f0346a123",
                "status": "success",
                "error": None,
            }
        }


class ProductBatchResponse(BaseModel):
    """Response summarising batch operation outcomes."""

    success: bool
    total: int
    successful: int
    failed: int
    results: List[ProductBatchResult]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total": 3,
                "successful": 2,
                "failed": 1,
                "results": [
                    {
                        "id": "f214ab9d-6727-406d-bf4e-8e1f0346a123",
                        "status": "success",
                        "error": None,
                    },
                    {
                        "id": None,
                        "status": "failed",
                        "error": "Duplicate model_number for manufacturer",
                    },
                ],
            }
        }
