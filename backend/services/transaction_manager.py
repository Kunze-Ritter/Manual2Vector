"""Transaction management utilities for batch operations."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Iterable, List, Optional

try:
    import asyncpg  # type: ignore
except ImportError:  # pragma: no cover - asyncpg optional
    asyncpg = None  # type: ignore

from backend.models.batch import (
    BatchOperationResponse,
    BatchOperationResult,
    BatchOperationResultStatus,
)


class TransactionManager:
    """Coordinates transactional execution for batch operations."""

    def __init__(self, supabase_adapter: "SupabaseAdapter") -> None:
        self._adapter = supabase_adapter
        self._logger = logging.getLogger("krai.services.transaction_manager")

    @property
    def pg_pool(self) -> Optional["asyncpg.pool.Pool"]:  # type: ignore[name-defined]
        """Expose the asyncpg pool provided by the adapter, when available."""

        return getattr(self._adapter, "pg_pool", None)

    def has_transaction_support(self) -> bool:
        """Return True when asyncpg transaction support is available."""

        return self.pg_pool is not None

    @asynccontextmanager
    async def begin_transaction(self) -> AsyncIterator[Optional["asyncpg.Connection"]]:  # type: ignore[name-defined]
        """Acquire a transactional connection when asyncpg is available.

        Falls back to a dummy context when no PostgreSQL pool is configured, in which
        case the caller is responsible for compensating transactions.
        """

        pool = self.pg_pool
        if not pool:
            self._logger.info(
                "Transaction fallback in use - asyncpg pool unavailable, executing without explicit transaction",
            )
            yield None
            return

        conn = await pool.acquire()
        self._logger.debug("Beginning PostgreSQL transaction")
        txn = conn.transaction()
        await txn.start()
        try:
            yield conn
            await txn.commit()
            self._logger.debug("Committed PostgreSQL transaction")
        except Exception:
            self._logger.warning("Rolling back PostgreSQL transaction due to error", exc_info=True)
            await txn.rollback()
            raise
        finally:
            await pool.release(conn)

    async def execute_batch_with_transaction(
        self,
        operations: Iterable[Callable[[Optional[Any]], Awaitable[BatchOperationResult]]],
        *,
        rollback_on_error: bool = True,
        total_items: Optional[int] = None,
        progress_callback: Optional[
            Callable[[BatchOperationResult, int, int, int, int], Awaitable[None]]
        ] = None,
    ) -> BatchOperationResponse:
        """Execute a collection of operations within a transaction scope.

        Each callable is awaited sequentially and receives the transactional connection
        when available (or ``None`` when the fallback path is used).
        """

        start_time = time.perf_counter()
        operations_list = list(operations)
        total_target = total_items if total_items is not None else len(operations_list)
        results: List[BatchOperationResult] = []
        failed = 0
        successful = 0
        processed = 0

        try:
            async with self.begin_transaction() as connection:
                for operation in operations_list:
                    try:
                        result = await operation(connection)
                        results.append(result)
                        processed += 1
                        if result.status == BatchOperationResultStatus.FAILED:
                            failed += 1
                            if rollback_on_error and self.has_transaction_support():
                                raise RuntimeError(
                                    f"Transactional operation failed: {result.error or 'unknown error'}",
                                )
                        else:
                            successful += 1

                        if progress_callback:
                            await progress_callback(result, processed, total_target, successful, failed)
                    except Exception as exc:  # pragma: no cover - defensive logging
                        self._logger.error("Batch operation callable raised an exception", exc_info=True)
                        failed += 1
                        processed += 1
                        failure_result = BatchOperationResult(
                            id=None,
                            status=BatchOperationResultStatus.FAILED,
                            error=str(exc),
                        )
                        results.append(failure_result)
                        if progress_callback:
                            await progress_callback(failure_result, processed, total_target, successful, failed)
                        if rollback_on_error and self.has_transaction_support():
                            raise
        except Exception as exc:
            self._logger.error("Transactional batch execution aborted", exc_info=True)
            execution_ms = int((time.perf_counter() - start_time) * 1000)
            total = total_target if total_target else processed
            return BatchOperationResponse(
                success=False,
                total=total,
                successful=max(successful, 0),
                failed=failed,
                results=results,
                execution_time_ms=execution_ms,
            )

        execution_ms = int((time.perf_counter() - start_time) * 1000)
        total = total_target if total_target else processed
        return BatchOperationResponse(
            success=failed == 0,
            total=total,
            successful=successful,
            failed=failed,
            results=results,
            execution_time_ms=execution_ms,
        )

    async def create_rollback_point(
        self,
        *,
        table: str,
        record_id: str,
        old_values: Dict[str, Any],
        changed_by: Optional[str] = None,
    ) -> str:
        """Persist a rollback point in the audit log and return its identifier."""

        client = getattr(self._adapter, "service_client", None) or getattr(self._adapter, "client", None)
        if client is None:
            raise RuntimeError("Supabase client is not connected; cannot create rollback point")

        rollback_point_id = str(uuid.uuid4())
        payload = {
            "table_name": table,
            "record_id": record_id,
            "operation": "ROLLBACK_POINT",
            "changed_by": changed_by,
            "old_values": old_values,
            "rollback_point_id": rollback_point_id,
            "is_rollback": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        client.table("krai_system.audit_log").insert(payload).execute()
        self._logger.debug("Created rollback point %s for %s", rollback_point_id, table)
        return rollback_point_id

    async def execute_rollback(self, rollback_point_id: str) -> bool:
        """Restore state using a rollback point previously recorded."""

        client = getattr(self._adapter, "service_client", None) or getattr(self._adapter, "client", None)
        if client is None:
            raise RuntimeError("Supabase client is not connected; cannot execute rollback")

        response = (
            client.table("krai_system.audit_log")
            .select("table_name, record_id, old_values")
            .eq("rollback_point_id", rollback_point_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        if not data:
            self._logger.warning("Rollback point %s not found", rollback_point_id)
            return False

        entry = data[0]
        table_name = entry.get("table_name")
        record_id = entry.get("record_id")
        old_values = entry.get("old_values") or {}
        if not table_name or not record_id or not old_values:
            self._logger.warning("Rollback point %s incomplete; aborting rollback", rollback_point_id)
            return False

        client.table(table_name).update(old_values).eq("id", record_id).execute()
        client.table("krai_system.audit_log").insert(
            {
                "table_name": table_name,
                "record_id": record_id,
                "operation": "ROLLBACK",
                "changed_by": None,
                "new_values": old_values,
                "rollback_point_id": rollback_point_id,
                "is_rollback": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        ).execute()
        self._logger.info("Executed rollback for %s via rollback point %s", record_id, rollback_point_id)
        return True

    async def execute_compensating_transaction(self, failed_operations: Iterable[Dict[str, Any]]) -> int:
        """Attempt to compensate previously successful operations.

        Each entry is expected to provide a ``rollback_data`` dictionary describing how to
        reverse the action. This method is intentionally defensive—when incomplete data is
        supplied, the operation is skipped and logged.
        """

        client = getattr(self._adapter, "service_client", None) or getattr(self._adapter, "client", None)
        if client is None:
            raise RuntimeError("Supabase client is not connected; cannot execute compensating transactions")

        compensated = 0
        for item in failed_operations:
            data = item.get("rollback_data") if isinstance(item, dict) else None
            if not data:
                self._logger.debug("Skipping compensating action lacking rollback_data: %s", item)
                continue

            table_name = data.get("table")
            record_id = data.get("record_id") or data.get("id")
            old_values = data.get("old_values")
            new_values = data.get("new_values")
            operation = data.get("operation")

            if not table_name:
                self._logger.debug("Rollback data missing table name: %s", data)
                continue

            try:
                if operation == "delete" and old_values and record_id:
                    client.table(table_name).insert(old_values).execute()
                    compensated += 1
                elif operation == "update" and old_values and record_id:
                    client.table(table_name).update(old_values).eq("id", record_id).execute()
                    compensated += 1
                elif operation == "create" and record_id:
                    client.table(table_name).delete().eq("id", record_id).execute()
                    compensated += 1
                elif old_values and record_id:
                    # Default to restoring old_values when operation type is ambiguous.
                    client.table(table_name).update(old_values).eq("id", record_id).execute()
                    compensated += 1
                else:
                    self._logger.debug("Insufficient rollback information: %s", data)
                    continue

                client.table("krai_system.audit_log").insert(
                    {
                        "table_name": table_name,
                        "record_id": record_id,
                        "operation": "ROLLBACK",
                        "changed_by": None,
                        "rollback_point_id": data.get("rollback_point_id"),
                        "is_rollback": True,
                        "old_values": old_values,
                        "new_values": new_values,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                ).execute()
            except Exception as exc:  # pragma: no cover - defensive logging
                self._logger.error("Compensating transaction failed for %s", data, exc_info=True)

        return compensated

    async def validate_transaction_scope(self, operations: Iterable[Dict[str, Any]]) -> bool:
        """Validate that all operations target the same table for transactional safety."""

        tables = {op.get("table") for op in operations if isinstance(op, dict)}
        if not tables:
            return False
        return len(tables) == 1

    async def estimate_transaction_size(self, operations: Iterable[Dict[str, Any]]) -> int:
        """Estimate the approximate payload size for a transaction in bytes."""

        size = 0
        for op in operations:
            if isinstance(op, dict):
                size += len(str(op).encode("utf-8"))
        return size


# Circular import avoidance: SupabaseAdapter is only needed for type checking.
from backend.services.supabase_adapter import SupabaseAdapter  # noqa: E402  # isort:skip
