"""Batch task management service for background batch operations."""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from models.batch import (
    BatchOperationResult,
    BatchOperationResultStatus,
    BatchTaskRequest,
    BatchTaskResponse,
    BatchTaskStatus,
)


class BatchTaskService:
    """Handles creation, tracking, and execution state of batch tasks."""

    def __init__(self, supabase_adapter: "SupabaseAdapter") -> None:
        self._adapter = supabase_adapter
        self._logger = logging.getLogger("krai.services.batch_task_service")
        self._tasks: Dict[str, Dict[str, Any]] = {}

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _generate_task_id(self, request: BatchTaskRequest) -> str:
        suffix = uuid.uuid4().hex[:8]
        timestamp = int(time.time())
        return f"batch_{request.operation_type}_{timestamp}_{suffix}"

    async def create_task(self, task_request: BatchTaskRequest) -> str:
        """Persist a new batch task and return its identifier."""

        client = getattr(self._adapter, "service_client", None) or getattr(self._adapter, "client", None)
        if client is None:
            raise RuntimeError("Supabase client is not connected; cannot create task")

        task_id = self._generate_task_id(task_request)
        metadata = {
            "resource_type": task_request.resource_type,
            "payload": task_request.payload,
            "user_id": task_request.user_id,
            "progress": 0.0,
            "results": [],
            "total_items": 0,
            "processed_items": 0,
            "successful_items": 0,
            "failed_items": 0,
        }

        client.table("krai_system.processing_queue").insert(
            {
                "id": task_id,
                "task_type": f"batch_{task_request.operation_type}",
                "status": BatchTaskStatus.QUEUED.value,
                "priority": task_request.priority,
                "metadata": metadata,
                "user_id": task_request.user_id,
                "scheduled_at": self._now().isoformat(),
            },
        ).execute()

        self._tasks[task_id] = {
            "status": BatchTaskStatus.QUEUED,
            "progress": 0.0,
            "metadata": metadata,
            "created_at": self._now(),
        }
        self._logger.info("Created batch task %s (%s)", task_id, task_request.operation_type)
        return task_id

    async def get_task_status(self, task_id: str) -> BatchTaskResponse:
        """Return the current status of a batch task."""

        client = getattr(self._adapter, "service_client", None) or getattr(self._adapter, "client", None)
        if client is None:
            raise RuntimeError("Supabase client is not connected; cannot retrieve task status")

        in_memory = self._tasks.get(task_id)
        status = BatchTaskStatus.QUEUED
        progress = 0.0
        metadata: Dict[str, Any] = {}
        started_at = None
        completed_at = None
        error_message = None

        if in_memory:
            status = in_memory.get("status", status)
            progress = in_memory.get("progress", progress)
            metadata = in_memory.get("metadata", metadata)
            started_at = in_memory.get("started_at")
            completed_at = in_memory.get("completed_at")
            error_message = in_memory.get("error")

        response = (
            client.table("krai_system.processing_queue")
            .select("status, metadata, started_at, completed_at, error_message")
            .eq("id", task_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        if data:
            entry = data[0]
            status = BatchTaskStatus(entry.get("status", status.value))
            metadata = entry.get("metadata", metadata) or {}
            progress = float(metadata.get("progress", progress))
            started_at = entry.get("started_at") or started_at
            completed_at = entry.get("completed_at") or completed_at
            error_message = entry.get("error_message") or error_message

        results = metadata.get("results") or []
        total_items = int(metadata.get("total_items", 0))
        processed_items = int(metadata.get("processed_items", 0))
        successful_items = int(metadata.get("successful_items", 0))
        failed_items = int(metadata.get("failed_items", 0))

        return BatchTaskResponse(
            task_id=task_id,
            status=status,
            progress=progress,
            total_items=total_items,
            processed_items=processed_items,
            successful_items=successful_items,
            failed_items=failed_items,
            started_at=started_at,
            completed_at=completed_at,
            error=error_message,
            results=[BatchOperationResult(**result) for result in results],
        )

    async def update_task_status(
        self,
        task_id: str,
        status: BatchTaskStatus,
        *,
        error: Optional[str] = None,
        metadata_updates: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update the task status and persist it in the processing queue."""

        client = getattr(self._adapter, "service_client", None) or getattr(self._adapter, "client", None)
        if client is None:
            raise RuntimeError("Supabase client is not connected; cannot update task status")

        now_iso = self._now().isoformat()
        metadata = self._tasks.get(task_id, {}).get("metadata", {}).copy()
        if metadata_updates:
            metadata.update(metadata_updates)

        update_payload: Dict[str, Any] = {
            "status": status.value,
            "metadata": metadata,
        }

        if status == BatchTaskStatus.RUNNING and "started_at" not in metadata:
            update_payload["started_at"] = now_iso
            metadata["started_at"] = now_iso
        if status in {BatchTaskStatus.COMPLETED, BatchTaskStatus.FAILED, BatchTaskStatus.CANCELLED}:
            update_payload["completed_at"] = now_iso
            metadata["completed_at"] = now_iso
        if error:
            update_payload["error_message"] = error
            metadata["error_message"] = error

        client.table("krai_system.processing_queue").update(update_payload).eq("id", task_id).execute()
        self._tasks[task_id] = {
            **self._tasks.get(task_id, {}),
            "status": status,
            "metadata": metadata,
            "progress": metadata.get("progress", 0.0),
            "error": error,
            "started_at": metadata.get("started_at"),
            "completed_at": metadata.get("completed_at"),
        }
        self._logger.debug("Updated task %s status to %s", task_id, status.value)

    async def update_task_progress(
        self,
        task_id: str,
        *,
        processed_items: int,
        total_items: int,
        successful_items: int,
        failed_items: int,
        current_result: Optional[BatchOperationResult] = None,
    ) -> None:
        """Update progress metrics for the task."""

        progress = 0.0 if total_items == 0 else (processed_items / total_items) * 100.0
        metadata_updates: Dict[str, Any] = {
            "progress": progress,
            "processed_items": processed_items,
            "total_items": total_items,
            "successful_items": successful_items,
            "failed_items": failed_items,
        }

        if current_result is not None:
            metadata = self._tasks.get(task_id, {}).get("metadata", {})
            results = metadata.get("results", [])
            results.append(current_result.model_dump())
            metadata_updates["results"] = results

        await self.update_task_status(
            task_id,
            self._tasks.get(task_id, {}).get("status", BatchTaskStatus.RUNNING),
            metadata_updates=metadata_updates,
        )

    async def execute_task(
        self,
        task_id: str,
        executor: "BatchTaskExecutor",
    ) -> BatchTaskResponse:
        """Execute the provided callable and update task state accordingly."""

        self._logger.info("Starting execution for task %s", task_id)
        await self.update_task_status(task_id, BatchTaskStatus.RUNNING)

        try:
            response = await executor()
            await self.update_task_status(
                task_id,
                BatchTaskStatus.COMPLETED,
                metadata_updates={
                    "progress": 100.0,
                    "results": [result.model_dump() for result in response.results],
                    "total_items": response.total,
                    "processed_items": response.total,
                    "successful_items": response.successful,
                    "failed_items": response.failed,
                },
            )
            return await self.get_task_status(task_id)
        except Exception as exc:
            self._logger.error("Task %s execution failed", task_id, exc_info=True)
            await self.update_task_status(
                task_id,
                BatchTaskStatus.FAILED,
                error=str(exc),
            )
            raise

    async def cleanup_completed_tasks(self, older_than_hours: int = 24) -> int:
        """Remove completed/cancelled tasks older than the specified age."""

        client = getattr(self._adapter, "service_client", None) or getattr(self._adapter, "client", None)
        if client is None:
            raise RuntimeError("Supabase client is not connected; cannot cleanup tasks")

        cutoff = self._now() - timedelta(hours=older_than_hours)
        query = (
            client.table("processing_queue", schema="krai_system")
            .select("id", count="exact")
            .like("task_type", "batch_%")
            .in_("status", [
                BatchTaskStatus.COMPLETED.value,
                BatchTaskStatus.FAILED.value,
                BatchTaskStatus.CANCELLED.value,
            ])
            .lte("completed_at", cutoff.isoformat())
        )
        response = query.execute()
        rows = response.data or []
        count = response.count if response.count is not None else len(rows)

        if rows:
            ids_to_remove = [row["id"] for row in rows if row.get("id")]
            if ids_to_remove:
                client.table("processing_queue", schema="krai_system").delete().in_("id", ids_to_remove).execute()

        # Remove from in-memory cache
        for task_id, details in list(self._tasks.items()):
            completed_at = details.get("completed_at")
            if completed_at and isinstance(completed_at, datetime) and completed_at < cutoff:
                del self._tasks[task_id]

        self._logger.info("Cleaned up %s batch tasks older than %s hours", count, older_than_hours)
        return count

    async def cancel_task(self, task_id: str, reason: str) -> bool:
        """Cancel a queued or running task."""

        await self.update_task_status(task_id, BatchTaskStatus.CANCELLED, error=reason)
        return True

    async def list_tasks(
        self,
        *,
        user_id: Optional[str] = None,
        status: Optional[BatchTaskStatus] = None,
        limit: int = 50,
    ) -> List[BatchTaskResponse]:
        """Return a list of tasks filtered by user or status."""

        client = getattr(self._adapter, "service_client", None) or getattr(self._adapter, "client", None)
        if client is None:
            raise RuntimeError("Supabase client is not connected; cannot list tasks")

        query = client.table("krai_system.processing_queue").select("id, status, metadata, started_at, completed_at, error_message").order(
            "created_at", desc=True
        )
        if user_id:
            query = query.eq("user_id", user_id)
        if status:
            query = query.eq("status", status.value)
        if limit:
            query = query.limit(limit)

        response = query.execute()
        rows = response.data or []
        results: List[BatchTaskResponse] = []
        for row in rows:
            task_id = row["id"]
            metadata = row.get("metadata") or {}
            results.append(
                BatchTaskResponse(
                    task_id=task_id,
                    status=BatchTaskStatus(row.get("status", BatchTaskStatus.QUEUED.value)),
                    progress=float(metadata.get("progress", 0.0)),
                    total_items=int(metadata.get("total_items", 0)),
                    processed_items=int(metadata.get("processed_items", 0)),
                    successful_items=int(metadata.get("successful_items", 0)),
                    failed_items=int(metadata.get("failed_items", 0)),
                    started_at=row.get("started_at"),
                    completed_at=row.get("completed_at"),
                    error=row.get("error_message"),
                    results=[BatchOperationResult(**result) for result in metadata.get("results", [])],
                ),
            )
        return results

    async def retry_failed_task(self, task_id: str) -> str:
        """Clone a failed task and return the new task identifier."""

        status = await self.get_task_status(task_id)
        if status.status != BatchTaskStatus.FAILED:
            raise ValueError("Only failed tasks can be retried")

        payload = status.results or []
        request = BatchTaskRequest(
            operation_type="update",
            resource_type="documents",
            payload={"results": [result.model_dump() for result in payload]},
            user_id="system",
        )
        return await self.create_task(request)


# Circular import guard
from services.supabase_adapter import SupabaseAdapter  # noqa: E402, F401  # isort:skip
