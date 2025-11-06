"""Batch operations API routes."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from backend.api.app import get_supabase_adapter
from backend.api.middleware.auth_middleware import require_permission
from backend.api.routes.response_models import SuccessResponse
from backend.models.batch import (
    BatchDeleteRequest,
    BatchOperationRequest,
    BatchOperationResponse,
    BatchOperationResult,
    BatchOperationResultStatus,
    BatchStatusChangeRequest,
    BatchTaskRequest,
    BatchTaskResponse,
    BatchTaskStatus,
    BatchUpdateRequest,
    RollbackRequest,
    RollbackResponse,
)
from backend.services.batch_task_service import BatchTaskService
from backend.services.transaction_manager import TransactionManager
from backend.services.supabase_adapter import SupabaseAdapter

LOGGER = logging.getLogger("krai.api.batch")

router = APIRouter(prefix="/batch", tags=["batch_operations"])

RESOURCE_TABLE_MAP: Dict[str, str] = {
    "documents": "krai_core.documents",
    "products": "krai_core.products",
    "manufacturers": "krai_core.manufacturers",
    "error_codes": "krai_intelligence.error_codes",
    "videos": "krai_content.videos",
    "images": "krai_content.images",
}

RESOURCE_PERMISSIONS: Dict[str, str] = {
    "documents": "documents",
    "products": "products",
    "manufacturers": "products",  # Reuse existing product permissions for manufacturers
    "error_codes": "error_codes",
    "videos": "videos",
    "images": "images",
}

MAX_SYNC_ITEMS = 100
ASYNC_THRESHOLD = 50


ProgressCallback = Callable[[BatchOperationResult, int, int, int, int], Awaitable[None]]

COLUMN_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _run_background(coro: Awaitable[Any]) -> None:
    """Schedule an async coroutine in the event loop."""

    asyncio.create_task(coro)


def _split_schema_table(table_name: str) -> Tuple[Optional[str], str]:
    if "." in table_name:
        schema, tbl = table_name.split(".", 1)
        return schema, tbl
    return None, table_name


def _get_table_query(client: Any, table_name: str):
    schema, base_table = _split_schema_table(table_name)
    if schema:
        return client.table(base_table, schema=schema)
    return client.table(base_table)


def should_run_async(item_count: int) -> bool:
    return item_count >= ASYNC_THRESHOLD


def _get_resource_permission(resource_type: str, action: str) -> str:
    if resource_type not in RESOURCE_PERMISSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Unsupported resource_type: {resource_type}")
    return f"{RESOURCE_PERMISSIONS[resource_type]}:{action}"


async def _get_services(supabase: SupabaseAdapter) -> Dict[str, Any]:
    from backend.api.app import get_batch_task_service, get_transaction_manager  # Circular import guard

    task_service = await get_batch_task_service()
    transaction_manager = await get_transaction_manager()

    return {
        "task_service": task_service,
        "transaction_manager": transaction_manager,
        "supabase_adapter": supabase,
    }


async def _validate_resource_type(resource_type: str) -> None:
    if resource_type not in RESOURCE_TABLE_MAP:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Unsupported resource_type: {resource_type}")


def _ensure_user_permission(current_user: Dict[str, Any], permission: str) -> None:
    permissions = set(current_user.get("permissions", []))
    if permission not in permissions:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions for operation: {permission}",
        )


async def _fetch_record(
    connection: Optional[Any],
    client: Any,
    table_name: str,
    record_id: str,
) -> Optional[Dict[str, Any]]:
    if connection:
        query = f"SELECT * FROM {table_name} WHERE id = $1"
        row = await connection.fetchrow(query, record_id)
        return dict(row) if row else None

    response = (
        _get_table_query(client, table_name)
        .select("*")
        .eq("id", record_id)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


async def _delete_record(
    connection: Optional[Any],
    client: Any,
    table_name: str,
    record_id: str,
) -> None:
    if connection:
        query = f"DELETE FROM {table_name} WHERE id = $1"
        await connection.execute(query, record_id)
        return

    _get_table_query(client, table_name).delete().eq("id", record_id).execute()


async def _update_record(
    connection: Optional[Any],
    client: Any,
    table_name: str,
    record_id: str,
    update_data: Dict[str, Any],
) -> None:
    if connection:
        set_clauses: List[str] = []
        parameters: List[Any] = [record_id]
        index = 2
        for column, value in update_data.items():
            if not COLUMN_NAME_PATTERN.match(column):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Invalid update column: {column}")

            prepared_value = _prepare_update_value(value)
            cast_suffix = "::jsonb" if isinstance(value, (dict, list)) else ""
            set_clauses.append(f"{column} = ${index}{cast_suffix}")
            parameters.append(prepared_value)
            index += 1

        if not set_clauses:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="update_data must contain at least one field")

        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = $1"
        await connection.execute(query, *parameters)
        return

    _get_table_query(client, table_name).update(update_data).eq("id", record_id).execute()


async def _insert_audit_log(
    connection: Optional[Any],
    client: Any,
    payload: Dict[str, Any],
) -> None:
    old_values = payload.get("old_values")
    new_values = payload.get("new_values")

    if connection:
        query = """
            INSERT INTO krai_system.audit_log (
                table_name,
                record_id,
                operation,
                changed_by,
                old_values,
                new_values,
                notes,
                rollback_point_id,
                is_rollback
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, $9)
        """
        await connection.execute(
            query,
            payload.get("table_name"),
            payload.get("record_id"),
            payload.get("operation"),
            payload.get("changed_by"),
            payload.get("old_values"),
            payload.get("new_values"),
            payload.get("notes"),
            payload.get("rollback_point_id"),
            payload.get("is_rollback", False),
        )
        return

    _get_table_query(client, "krai_system.audit_log").insert(payload).execute()


def _build_result(
    *,
    identifier: Optional[str],
    success: bool,
    error: Optional[str] = None,
    rollback_data: Optional[Dict[str, Any]] = None,
) -> BatchOperationResult:
    return BatchOperationResult(
        id=identifier,
        status=BatchOperationResultStatus.SUCCESS if success else BatchOperationResultStatus.FAILED,
        error=error,
        rollback_data=rollback_data,
    )


async def _execute_sync_delete(
    *,
    supabase: SupabaseAdapter,
    transaction_manager: TransactionManager,
    resource_type: str,
    ids: List[str],
    user_id: str,
    progress_callback: Optional[ProgressCallback] = None,
) -> BatchOperationResponse:
    table_name = RESOURCE_TABLE_MAP[resource_type]
    client = supabase.service_client or supabase.client
    if client is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database client not available")

    operations: List[Callable[[Optional[Any]], Awaitable[BatchOperationResult]]] = []

    for record_id in ids:

        async def _delete_operation(connection: Optional[Any], record_id: str = record_id) -> BatchOperationResult:
            try:
                existing_data = await _fetch_record(connection, client, table_name, record_id)
                if not existing_data:
                    LOGGER.info("Skipping delete for %s - not found", record_id)
                    return _build_result(identifier=record_id, success=False, error="Not found")

                await _delete_record(connection, client, table_name, record_id)
                await _insert_audit_log(
                    connection,
                    client,
                    {
                        "table_name": table_name,
                        "record_id": record_id,
                        "operation": "DELETE",
                        "changed_by": user_id,
                        "old_values": existing_data,
                    },
                )

                return _build_result(
                    identifier=record_id,
                    success=True,
                    rollback_data={
                        "operation": "delete",
                        "table": table_name,
                        "record_id": record_id,
                        "old_values": existing_data,
                    },
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.error("Failed to delete %s %s", resource_type, record_id, exc_info=True)
                return _build_result(identifier=record_id, success=False, error=str(exc))

        operations.append(_delete_operation)

    return await transaction_manager.execute_batch_with_transaction(
        operations,
        total_items=len(ids),
        rollback_on_error=transaction_manager.has_transaction_support(),
        progress_callback=progress_callback,
    )


async def _execute_sync_update(
    *,
    supabase: SupabaseAdapter,
    transaction_manager: TransactionManager,
    resource_type: str,
    updates: List[Dict[str, Any]],
    user_id: str,
    progress_callback: Optional[ProgressCallback] = None,
) -> BatchOperationResponse:
    table_name = RESOURCE_TABLE_MAP[resource_type]
    client = supabase.service_client or supabase.client
    if client is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database client not available")

    operations: List[Callable[[Optional[Any]], Awaitable[BatchOperationResult]]] = []
    for payload in updates:
        record_id = payload["id"]
        update_data = dict(payload["update_data"])

        async def _update_operation(connection: Optional[Any], record_id: str = record_id, update_data: Dict[str, Any] = update_data) -> BatchOperationResult:
            try:
                existing_data = await _fetch_record(connection, client, table_name, record_id)
                if not existing_data:
                    LOGGER.info("Skipping update for %s - not found", record_id)
                    return _build_result(identifier=record_id, success=False, error="Not found")

                await _update_record(connection, client, table_name, record_id, update_data)
                await _insert_audit_log(
                    connection,
                    client,
                    {
                        "table_name": table_name,
                        "record_id": record_id,
                        "operation": "UPDATE",
                        "changed_by": user_id,
                        "old_values": existing_data,
                        "new_values": update_data,
                    },
                )

                return _build_result(
                    identifier=record_id,
                    success=True,
                    rollback_data={
                        "operation": "update",
                        "table": table_name,
                        "record_id": record_id,
                        "old_values": existing_data,
                        "new_values": update_data,
                    },
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.error("Failed to update %s %s", resource_type, record_id, exc_info=True)
                return _build_result(identifier=record_id, success=False, error=str(exc))

        operations.append(_update_operation)

    return await transaction_manager.execute_batch_with_transaction(
        operations,
        total_items=len(updates),
        rollback_on_error=transaction_manager.has_transaction_support(),
        progress_callback=progress_callback,
    )


async def _execute_sync_status_change(
    *,
    supabase: SupabaseAdapter,
    transaction_manager: TransactionManager,
    resource_type: str,
    ids: List[str],
    new_status: str,
    user_id: str,
    reason: Optional[str],
    progress_callback: Optional[ProgressCallback] = None,
) -> BatchOperationResponse:
    table_name = RESOURCE_TABLE_MAP[resource_type]
    client = supabase.service_client or supabase.client
    if client is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database client not available")

    operations: List[Callable[[Optional[Any]], Awaitable[BatchOperationResult]]] = []
    for record_id in ids:
        async def _status_operation(connection: Optional[Any], record_id: str = record_id) -> BatchOperationResult:
            try:
                existing_data = await _fetch_record(connection, client, table_name, record_id)
                if not existing_data:
                    LOGGER.info("Skipping status change for %s - not found", record_id)
                    return _build_result(identifier=record_id, success=False, error="Not found")

                update_payload = {"status": new_status}
                await _update_record(connection, client, table_name, record_id, update_payload)

                audit_payload = {
                    "table_name": table_name,
                    "record_id": record_id,
                    "operation": "STATUS_CHANGE",
                    "changed_by": user_id,
                    "old_values": existing_data,
                    "new_values": update_payload,
                }
                if reason:
                    audit_payload["notes"] = reason
                await _insert_audit_log(connection, client, audit_payload)

                return _build_result(
                    identifier=record_id,
                    success=True,
                    rollback_data={
                        "operation": "update",
                        "table": table_name,
                        "record_id": record_id,
                        "old_values": existing_data,
                        "new_values": update_payload,
                    },
                )
            except Exception as exc:
                LOGGER.error("Failed to update status for %s %s", resource_type, record_id, exc_info=True)
                return _build_result(identifier=record_id, success=False, error=str(exc))

        operations.append(_status_operation)

    return await transaction_manager.execute_batch_with_transaction(
        operations,
        total_items=len(ids),
        rollback_on_error=transaction_manager.has_transaction_support(),
        progress_callback=progress_callback,
    )


def _build_task_executor(
    *,
    operation: str,
    resource_type: str,
    payload: Dict[str, Any],
    supabase: SupabaseAdapter,
    transaction_manager: TransactionManager,
    user_id: str,
    progress_callback: Optional[ProgressCallback],
) -> Callable[[], Awaitable[BatchOperationResponse]]:
    async def _executor() -> BatchOperationResponse:
        if operation == "delete":
            ids = payload.get("ids")
            if not isinstance(ids, list) or not ids:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="delete operation requires non-empty 'ids' list")
            return await _execute_sync_delete(
                supabase=supabase,
                transaction_manager=transaction_manager,
                resource_type=resource_type,
                ids=ids,
                user_id=user_id,
                progress_callback=progress_callback,
            )

        if operation == "update":
            updates = payload.get("updates")
            if not isinstance(updates, list) or not updates:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="update operation requires non-empty 'updates' list")
            return await _execute_sync_update(
                supabase=supabase,
                transaction_manager=transaction_manager,
                resource_type=resource_type,
                updates=updates,
                user_id=user_id,
                progress_callback=progress_callback,
            )

        if operation == "status_change":
            ids = payload.get("ids")
            new_status = payload.get("new_status")
            if not isinstance(ids, list) or not ids:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="status_change operation requires non-empty 'ids' list")
            if not new_status:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="status_change operation requires 'new_status'")
            return await _execute_sync_status_change(
                supabase=supabase,
                transaction_manager=transaction_manager,
                resource_type=resource_type,
                ids=ids,
                new_status=new_status,
                user_id=user_id,
                reason=payload.get("reason"),
                progress_callback=progress_callback,
            )

        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Unsupported batch operation: {operation}")

    return _executor


async def _schedule_async_operation(
    *,
    background_tasks: BackgroundTasks,
    task_service: BatchTaskService,
    transaction_manager: TransactionManager,
    supabase: SupabaseAdapter,
    request: BatchOperationRequest,
    user_id: str,
) -> BatchOperationResponse:
    options = request.options or {}
    payload = {"items": request.items, **options}
    if request.operation == "delete":
        payload = {"ids": [item.get("id") for item in request.items if item.get("id")]}
    elif request.operation == "update":
        payload = {
            "updates": request.items,
        }
    elif request.operation == "status_change":
        new_status = options.get("new_status")
        if not new_status:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="status_change operation requires new_status option")
        payload = {
            "ids": [item.get("id") for item in request.items if item.get("id")],
            "new_status": new_status,
            "reason": options.get("reason"),
        }

    task_request = BatchTaskRequest(
        operation_type=request.operation,
        resource_type=request.resource_type,
        payload=payload,
        user_id=user_id,
    )

    async def _background_executor(task_id: str) -> None:
        total_items = len(request.items)

        async def _progress_callback(
            result: BatchOperationResult,
            processed: int,
            total: int,
            successful: int,
            failed: int,
        ) -> None:
            await task_service.update_task_progress(
                task_id,
                processed_items=processed,
                total_items=total,
                successful_items=successful,
                failed_items=failed,
                current_result=result,
            )

        executor = _build_task_executor(
            operation=request.operation,
            resource_type=request.resource_type,
            payload=payload,
            supabase=supabase,
            transaction_manager=transaction_manager,
            user_id=user_id,
            progress_callback=_progress_callback,
        )
        await task_service.execute_task(task_id, executor)

    task_id = await task_service.create_task(task_request)
    await task_service.update_task_status(
        task_id,
        BatchTaskStatus.QUEUED,
        metadata_updates={
            "total_items": len(request.items),
            "processed_items": 0,
            "successful_items": 0,
            "failed_items": 0,
            "results": [],
        },
    )

    background_tasks.add_task(_run_background, _background_executor(task_id))

    return BatchOperationResponse(
        success=True,
        total=len(request.items),
        successful=0,
        failed=0,
        results=[],
        task_id=task_id,
    )


@router.post("/delete", response_model=SuccessResponse[BatchOperationResponse])
async def batch_delete(
    request: BatchDeleteRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("batch:delete")),
    supabase: SupabaseAdapter = Depends(get_supabase_adapter),
) -> SuccessResponse[BatchOperationResponse]:
    await _validate_resource_type(request.resource_type)
    permission = _get_resource_permission(request.resource_type, "delete")
    _ensure_user_permission(current_user, permission)

    services = await _get_services(supabase)
    task_service: BatchTaskService = services["task_service"]
    transaction_manager: TransactionManager = services["transaction_manager"]

    item_count = len(request.ids)
    LOGGER.info("Batch delete requested: resource=%s count=%s", request.resource_type, item_count)

    if should_run_async(item_count):
        batch_request = BatchOperationRequest(
            resource_type=request.resource_type,
            operation="delete",
            items=[{"id": identifier} for identifier in request.ids],
            options={}
        )
        response = await _schedule_async_operation(
            background_tasks=background_tasks,
            task_service=task_service,
            transaction_manager=transaction_manager,
            supabase=supabase,
            request=batch_request,
            user_id=current_user.get("id"),
        )
        return SuccessResponse(data=response)

    response = await _execute_sync_delete(
        supabase=supabase,
        transaction_manager=transaction_manager,
        resource_type=request.resource_type,
        ids=request.ids,
        user_id=current_user.get("id"),
    )
    return SuccessResponse(data=response)


@router.put("/update", response_model=SuccessResponse[BatchOperationResponse])
async def batch_update(
    request: BatchUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("batch:update")),
    supabase: SupabaseAdapter = Depends(get_supabase_adapter),
) -> SuccessResponse[BatchOperationResponse]:
    await _validate_resource_type(request.resource_type)
    permission = _get_resource_permission(request.resource_type, "write")
    _ensure_user_permission(current_user, permission)

    services = await _get_services(supabase)
    task_service: BatchTaskService = services["task_service"]
    transaction_manager: TransactionManager = services["transaction_manager"]

    item_count = len(request.updates)
    LOGGER.info("Batch update requested: resource=%s count=%s", request.resource_type, item_count)

    if should_run_async(item_count):
        batch_request = BatchOperationRequest(
            resource_type=request.resource_type,
            operation="update",
            items=request.updates,
            options={}
        )
        response = await _schedule_async_operation(
            background_tasks=background_tasks,
            task_service=task_service,
            transaction_manager=transaction_manager,
            supabase=supabase,
            request=batch_request,
            user_id=current_user.get("id"),
        )
        return SuccessResponse(data=response)

    response = await _execute_sync_update(
        supabase=supabase,
        transaction_manager=transaction_manager,
        resource_type=request.resource_type,
        updates=request.updates,
        user_id=current_user.get("id"),
    )
    return SuccessResponse(data=response)


@router.post("/status-change", response_model=SuccessResponse[BatchOperationResponse])
async def batch_status_change(
    request: BatchStatusChangeRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("batch:update")),
    supabase: SupabaseAdapter = Depends(get_supabase_adapter),
) -> SuccessResponse[BatchOperationResponse]:
    await _validate_resource_type(request.resource_type)
    permission = _get_resource_permission(request.resource_type, "write")
    _ensure_user_permission(current_user, permission)

    services = await _get_services(supabase)
    task_service: BatchTaskService = services["task_service"]
    transaction_manager: TransactionManager = services["transaction_manager"]

    item_count = len(request.ids)
    LOGGER.info(
        "Batch status change requested: resource=%s count=%s status=%s",
        request.resource_type,
        item_count,
        request.new_status,
    )

    batch_request = BatchOperationRequest(
        resource_type=request.resource_type,
        operation="status_change",
        items=[{"id": identifier} for identifier in request.ids],
        options={"new_status": request.new_status, "reason": request.reason},
    )

    if should_run_async(item_count):
        response = await _schedule_async_operation(
            background_tasks=background_tasks,
            task_service=task_service,
            transaction_manager=transaction_manager,
            supabase=supabase,
            request=batch_request,
            user_id=current_user.get("id"),
        )
        return SuccessResponse(data=response)

    response = await _execute_sync_status_change(
        supabase=supabase,
        transaction_manager=transaction_manager,
        resource_type=request.resource_type,
        ids=request.ids,
        new_status=request.new_status,
        user_id=current_user.get("id"),
        reason=request.reason,
    )
    return SuccessResponse(data=response)


@router.get("/tasks/{task_id}", response_model=SuccessResponse[BatchTaskResponse])
async def get_batch_task_status(
    task_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("batch:read")),
    supabase: SupabaseAdapter = Depends(get_supabase_adapter),
) -> SuccessResponse[BatchTaskResponse]:
    services = await _get_services(supabase)
    task_service: BatchTaskService = services["task_service"]
    status_response = await task_service.get_task_status(task_id)
    return SuccessResponse(data=status_response)


@router.get("/tasks", response_model=SuccessResponse[List[BatchTaskResponse]])
async def list_batch_tasks(
    status_filter: Optional[BatchTaskStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(require_permission("batch:read")),
    supabase: SupabaseAdapter = Depends(get_supabase_adapter),
) -> SuccessResponse[List[BatchTaskResponse]]:
    services = await _get_services(supabase)
    task_service: BatchTaskService = services["task_service"]
    tasks = await task_service.list_tasks(
        user_id=current_user.get("id"),
        status=status_filter,
        limit=limit,
    )
    return SuccessResponse(data=tasks)


@router.post("/tasks/{task_id}/cancel", response_model=SuccessResponse[Dict[str, Any]])
async def cancel_batch_task(
    task_id: str,
    reason: str = Query(..., min_length=5, max_length=200),
    current_user: Dict[str, Any] = Depends(require_permission("batch:delete")),
    supabase: SupabaseAdapter = Depends(get_supabase_adapter),
) -> SuccessResponse[Dict[str, Any]]:
    services = await _get_services(supabase)
    task_service: BatchTaskService = services["task_service"]
    await task_service.cancel_task(task_id, reason)
    return SuccessResponse(data={"success": True, "message": "Task cancelled"})


@router.post("/rollback", response_model=SuccessResponse[RollbackResponse])
async def rollback_batch_operation(
    request: RollbackRequest,
    current_user: Dict[str, Any] = Depends(require_permission("batch:rollback")),
    supabase: SupabaseAdapter = Depends(get_supabase_adapter),
) -> SuccessResponse[RollbackResponse]:
    services = await _get_services(supabase)
    task_service: BatchTaskService = services["task_service"]
    transaction_manager: TransactionManager = services["transaction_manager"]

    task_status = await task_service.get_task_status(request.task_id)
    if task_status.status not in {BatchTaskStatus.COMPLETED, BatchTaskStatus.FAILED}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Rollback only allowed for completed or failed tasks")

    if not task_status.results:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Task does not contain rollback metadata")

    compensated = await transaction_manager.execute_compensating_transaction(
        [result.model_dump() for result in task_status.results],
    )

    response = RollbackResponse(
        success=True,
        rolled_back_count=compensated,
        message=f"Rollback completed ({compensated} operations)",
    )
    return SuccessResponse(data=response)
