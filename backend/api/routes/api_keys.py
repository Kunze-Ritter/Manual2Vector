"""API key management routes."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.app import get_database_adapter
from api.middleware.auth_middleware import require_permission
from api.middleware.rate_limit_middleware import (
    limiter,
    rate_limit_search,
    rate_limit_standard,
)
from api.routes.response_models import SuccessResponse
from models.api_key import (
    APIKeyCreateRequest,
    APIKeyListResponse,
    APIKeyResponse,
    APIKeyWithSecretResponse,
)
from services.api_key_service import APIKeyService
from services.database_adapter import DatabaseAdapter

router = APIRouter(prefix="/api-keys", tags=["api_keys"])

# Reusable permission dependency so tests can override a single reference
require_api_keys_permission = require_permission("api_keys:manage")


def _get_service(adapter: DatabaseAdapter) -> APIKeyService:
    return APIKeyService(adapter)


def _resolve_target_user(
    requested_user_id: Optional[str],
    current_user: Dict[str, Any],
) -> str:
    if requested_user_id and requested_user_id != current_user["id"]:
        if current_user.get("role") != "admin":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Only admins can act on other users' API keys",
            )
        return requested_user_id
    return requested_user_id or current_user["id"]


@router.get("", response_model=SuccessResponse[APIKeyListResponse])
@limiter.limit(rate_limit_search)
async def list_api_keys(
    current_user: Dict[str, Any] = Depends(require_api_keys_permission),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
    user_id: Optional[str] = Query(None, description="Filter keys for a specific user (admin only)"),
) -> SuccessResponse[APIKeyListResponse]:
    """List API keys for the current user or a specified user (admin only)."""

    target_user_id = _resolve_target_user(user_id, current_user)
    service = _get_service(adapter)
    rows = await service.list_user_api_keys(target_user_id)
    payload = APIKeyListResponse(keys=[APIKeyResponse(**row) for row in rows])
    return SuccessResponse(data=payload)


@router.post(
    "",
    response_model=SuccessResponse[APIKeyWithSecretResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(rate_limit_standard)
async def create_api_key(
    payload: APIKeyCreateRequest,
    current_user: Dict[str, Any] = Depends(require_api_keys_permission),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
) -> SuccessResponse[APIKeyWithSecretResponse]:
    """Create a new API key for the current user or (admin) another user."""

    target_user_id = _resolve_target_user(payload.user_id, current_user)
    service = _get_service(adapter)
    record = await service.create_api_key(
        user_id=target_user_id,
        name=payload.name,
        permissions=payload.permissions,
        expires_in_days=payload.expires_in_days,
    )
    response_payload = APIKeyWithSecretResponse(**record)
    return SuccessResponse(data=response_payload, message="API key created")


@router.post(
    "/{key_id}/rotate",
    response_model=SuccessResponse[APIKeyWithSecretResponse],
)
@limiter.limit(rate_limit_standard)
async def rotate_api_key(
    key_id: str,
    current_user: Dict[str, Any] = Depends(require_api_keys_permission),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
    user_id: Optional[str] = Query(None, description="User that owns the key (admin only)"),
) -> SuccessResponse[APIKeyWithSecretResponse]:
    """Rotate an API key and return the new secret."""

    target_user_id = _resolve_target_user(user_id, current_user)
    service = _get_service(adapter)
    record = await service.rotate_api_key(key_id, target_user_id)
    response_payload = APIKeyWithSecretResponse(**record)
    return SuccessResponse(data=response_payload, message="API key rotated")


@router.post(
    "/{key_id}/revoke",
    response_model=SuccessResponse[Dict[str, Any]],
)
@limiter.limit(rate_limit_standard)
async def revoke_api_key(
    key_id: str,
    current_user: Dict[str, Any] = Depends(require_api_keys_permission),
    adapter: DatabaseAdapter = Depends(get_database_adapter),
    user_id: Optional[str] = Query(None, description="User that owns the key (admin only)"),
) -> SuccessResponse[Dict[str, Any]]:
    """Revoke an API key."""

    target_user_id = _resolve_target_user(user_id, current_user)
    service = _get_service(adapter)
    await service.revoke_api_key(key_id, target_user_id)
    return SuccessResponse(
        data={"id": key_id, "revoked": True, "user_id": target_user_id},
        message="API key revoked",
    )
