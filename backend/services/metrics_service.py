"""Metrics aggregation service for monitoring."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from models.monitoring import (
    DataQualityResponse,
    DuplicateMetrics,
    HardwareStatus,
    PipelineMetrics,
    ProcessingMetrics,
    QueueItem,
    QueueMetrics,
    StageMetrics,
    ValidationMetrics,
)
from processors.stage_tracker import StageTracker
from services.database_adapter import DatabaseAdapter

LOGGER = logging.getLogger(__name__)


class MetricsService:
    """Service for aggregating and caching metrics."""

    CACHE_TTL_SECONDS = 5

    def __init__(self, database_adapter: DatabaseAdapter, stage_tracker: StageTracker):
        """Initialize metrics service."""
        self.adapter = database_adapter
        self.stage_tracker = stage_tracker
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self.logger = LOGGER

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.CACHE_TTL_SECONDS):
                self.logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                self.logger.debug(f"Cache expired for key: {key}")
                del self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        """Set cache value with timestamp."""
        self._cache[key] = (value, datetime.utcnow())
        # Cleanup old entries
        cutoff = datetime.utcnow() - timedelta(minutes=1)
        self._cache = {k: v for k, v in self._cache.items() if v[1] > cutoff}

    def invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate cache entry or entire cache."""
        if key:
            self._cache.pop(key, None)
            self.logger.debug(f"Cache invalidated for key: {key}")
        else:
            self._cache.clear()
            self.logger.debug("Entire cache invalidated")

    async def get_pipeline_metrics(self) -> PipelineMetrics:
        """Get pipeline metrics with caching (server-side aggregation)."""
        cached = self._get_cached("pipeline_metrics")
        if cached:
            return cached

        try:
            # Query aggregated view using DatabaseAdapter
            query = "SELECT * FROM public.vw_pipeline_metrics_aggregated LIMIT 1"
            response = await self.adapter.execute_query(query)
            
            if not response or len(response) == 0:
                raise RuntimeError("No aggregated metrics available")
            
            data = response[0]
            
            # Calculate throughput from recent count
            current_throughput = float(data.get("recent_24h_count", 0)) / 24.0

            metrics = PipelineMetrics(
                total_documents=int(data.get("total_documents", 0)),
                documents_pending=int(data.get("documents_pending", 0)),
                documents_processing=int(data.get("documents_processing", 0)),
                documents_completed=int(data.get("documents_completed", 0)),
                documents_failed=int(data.get("documents_failed", 0)),
                success_rate=float(data.get("success_rate", 0.0)),
                avg_processing_time_seconds=0.0,  # Calculated separately if needed
                current_throughput_docs_per_hour=round(current_throughput, 2),
            )

            self._set_cache("pipeline_metrics", metrics)
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get pipeline metrics: {e}", exc_info=True)
            # Return default values
            return PipelineMetrics(
                total_documents=0,
                documents_pending=0,
                documents_processing=0,
                documents_completed=0,
                documents_failed=0,
                success_rate=0.0,
                avg_processing_time_seconds=0.0,
                current_throughput_docs_per_hour=0.0,
            )

    async def get_stage_metrics(self) -> List[StageMetrics]:
        """Get stage-specific metrics with caching (server-side aggregation)."""
        cached = self._get_cached("stage_metrics")
        if cached:
            return cached

        try:
            # Query aggregated stage metrics view using DatabaseAdapter
            query = "SELECT * FROM public.vw_stage_metrics_aggregated"
            stage_data = await self.adapter.execute_query(query)
            stage_data = stage_data or []

            metrics = []
            for stage in stage_data:
                completed = int(stage.get("completed_count", 0))
                failed = int(stage.get("failed_count", 0))
                total = int(stage.get("total_executions", 0))
                success_rate = (completed / total * 100) if total > 0 else 0.0

                metrics.append(
                    StageMetrics(
                        stage_name=stage.get("stage_name", "unknown"),
                        pending_count=0,  # Not in aggregated view
                        processing_count=0,  # Not in aggregated view
                        completed_count=completed,
                        failed_count=failed,
                        skipped_count=0,  # Not in aggregated view
                        avg_duration_seconds=round(float(stage.get("avg_duration_seconds", 0.0)), 2),
                        success_rate=round(success_rate, 2),
                    )
                )

            self._set_cache("stage_metrics", metrics)
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get stage metrics: {e}", exc_info=True)
            return []

    async def get_queue_metrics(self) -> QueueMetrics:
        """Get queue metrics with caching (server-side aggregation)."""
        cached = self._get_cached("queue_metrics")
        if cached:
            return cached

        try:
            # Query aggregated view using DatabaseAdapter
            query = "SELECT * FROM public.vw_queue_metrics_aggregated LIMIT 1"
            response = await self.adapter.execute_query(query)
            
            if not response or len(response) == 0:
                raise RuntimeError("No aggregated queue metrics available")
            
            data = response[0]
            
            # Get task type breakdown
            type_query = "SELECT task_type FROM krai_system.processing_queue"
            type_response = await self.adapter.execute_query(type_query)
            by_task_type: Dict[str, int] = {}
            for item in (type_response or []):
                task_type = item.get("task_type", "unknown")
                by_task_type[task_type] = by_task_type.get(task_type, 0) + 1

            metrics = QueueMetrics(
                total_items=int(data.get("total_items", 0)),
                pending_count=int(data.get("pending_count", 0)),
                processing_count=int(data.get("processing_count", 0)),
                completed_count=int(data.get("completed_count", 0)),
                failed_count=int(data.get("failed_count", 0)),
                avg_wait_time_seconds=round(float(data.get("avg_processing_time_seconds", 0.0)), 2),
                by_task_type=by_task_type,
            )

            self._set_cache("queue_metrics", metrics)
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get queue metrics: {e}", exc_info=True)
            return QueueMetrics(
                total_items=0,
                pending_count=0,
                processing_count=0,
                completed_count=0,
                failed_count=0,
                avg_wait_time_seconds=0.0,
                by_task_type={},
            )

    async def get_queue_items(self, limit: int = 100, status_filter: Optional[str] = None) -> List[QueueItem]:
        """Get queue items with optional filtering."""
        try:
            # Build query dynamically
            conditions = []
            params = []
            param_count = 0
            
            if status_filter:
                param_count += 1
                conditions.append(f"status = ${param_count}")
                params.append(status_filter)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            query = f"""
                SELECT * FROM krai_system.processing_queue 
                {where_clause}
                ORDER BY priority DESC, scheduled_at 
                LIMIT ${param_count + 1}
            """
            params.append(limit)

            items = await self.adapter.execute_query(query, params)
            items = items or []

            return [
                QueueItem(
                    id=str(item.get("id", "")),
                    task_type=item.get("task_type", "unknown"),
                    status=item.get("status", "unknown"),
                    priority=item.get("priority", 0),
                    document_id=item.get("document_id"),
                    scheduled_at=datetime.fromisoformat(item["scheduled_at"].replace("Z", "+00:00")) if item.get("scheduled_at") else datetime.utcnow(),
                    started_at=datetime.fromisoformat(item["started_at"].replace("Z", "+00:00")) if item.get("started_at") else None,
                    retry_count=item.get("retry_count", 0),
                    error_message=item.get("error_message"),
                )
                for item in items
            ]

        except Exception as e:
            self.logger.error(f"Failed to get queue items: {e}", exc_info=True)
            return []

    async def get_duplicate_metrics(self) -> DuplicateMetrics:
        """Get duplicate detection metrics with caching."""
        cached = self._get_cached("duplicate_metrics")
        if cached:
            return cached

        try:
            # Query duplicates by file_hash using RPC
            hash_duplicates = await self.adapter.rpc("get_duplicate_hashes", {})
            hash_duplicates = hash_duplicates or []

            # Query duplicates by filename using RPC
            filename_duplicates = await self.adapter.rpc("get_duplicate_filenames", {})
            filename_duplicates = filename_duplicates or []

            duplicate_documents = []
            for dup in hash_duplicates:
                duplicate_documents.append({
                    "file_hash": dup.get("file_hash"),
                    "count": dup.get("count", 0),
                    "filenames": dup.get("filenames", []),
                })

            metrics = DuplicateMetrics(
                total_duplicates=len(hash_duplicates) + len(filename_duplicates),
                duplicate_by_hash=len(hash_duplicates),
                duplicate_by_filename=len(filename_duplicates),
                duplicate_documents=duplicate_documents,
            )

            self._set_cache("duplicate_metrics", metrics)
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get duplicate metrics: {e}", exc_info=True)
            return DuplicateMetrics(
                total_duplicates=0,
                duplicate_by_hash=0,
                duplicate_by_filename=0,
                duplicate_documents=[],
            )

    async def get_validation_metrics(self) -> ValidationMetrics:
        """Get validation error metrics with caching."""
        cached = self._get_cached("validation_metrics")
        if cached:
            return cached

        try:
            # Query documents with errors using DatabaseAdapter
            query = "SELECT id, filename, stage_status FROM krai_core.documents"
            documents = await self.adapter.execute_query(query)
            documents = documents or []

            errors_by_stage: Dict[str, int] = {}
            documents_with_errors = []

            for doc in documents:
                stage_status = doc.get("stage_status", {})
                if isinstance(stage_status, dict):
                    for stage, data in stage_status.items():
                        if isinstance(data, dict) and data.get("status") == "failed":
                            errors_by_stage[stage] = errors_by_stage.get(stage, 0) + 1
                            documents_with_errors.append({
                                "document_id": str(doc.get("id", "")),
                                "stage": stage,
                                "error": data.get("error", "Unknown error"),
                            })

            metrics = ValidationMetrics(
                total_validation_errors=sum(errors_by_stage.values()),
                errors_by_stage=errors_by_stage,
                documents_with_errors=documents_with_errors[:50],  # Limit to 50
            )

            self._set_cache("validation_metrics", metrics)
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get validation metrics: {e}", exc_info=True)
            return ValidationMetrics(
                total_validation_errors=0,
                errors_by_stage={},
                documents_with_errors=[],
            )

    async def get_processing_metrics(self) -> ProcessingMetrics:
        """Get processing performance metrics with caching."""
        cached = self._get_cached("processing_metrics")
        if cached:
            return cached

        try:
            # Query documents using DatabaseAdapter
            query = "SELECT * FROM public.vw_documents"
            documents = await self.adapter.execute_query(query)
            documents = documents or []

            total_processed = len(documents)
            successful = sum(1 for d in documents if d.get("processing_status") == "completed")
            failed = sum(1 for d in documents if d.get("processing_status") == "failed")
            success_rate = (successful / total_processed * 100) if total_processed > 0 else 0.0

            # Calculate average processing time
            durations = []
            for doc in documents:
                if doc.get("stage_status") and isinstance(doc["stage_status"], dict):
                    for stage_data in doc["stage_status"].values():
                        if isinstance(stage_data, dict) and "duration_seconds" in stage_data:
                            durations.append(stage_data["duration_seconds"])
            avg_processing_time = sum(durations) / len(durations) if durations else 0.0

            # Aggregate by document type
            processing_by_type: Dict[str, int] = {}
            for doc in documents:
                doc_type = doc.get("document_type", "unknown")
                processing_by_type[doc_type] = processing_by_type.get(doc_type, 0) + 1

            metrics = ProcessingMetrics(
                total_processed=total_processed,
                successful=successful,
                failed=failed,
                success_rate=round(success_rate, 2),
                avg_processing_time=round(avg_processing_time, 2),
                processing_by_type=processing_by_type,
            )

            self._set_cache("processing_metrics", metrics)
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get processing metrics: {e}", exc_info=True)
            return ProcessingMetrics(
                total_processed=0,
                successful=0,
                failed=0,
                success_rate=0.0,
                avg_processing_time=0.0,
                processing_by_type={},
            )

    async def get_data_quality_metrics(self) -> DataQualityResponse:
        """Get comprehensive data quality metrics."""
        duplicate_metrics = await self.get_duplicate_metrics()
        validation_metrics = await self.get_validation_metrics()
        processing_metrics = await self.get_processing_metrics()

        return DataQualityResponse(
            duplicate_metrics=duplicate_metrics,
            validation_metrics=validation_metrics,
            processing_metrics=processing_metrics,
        )

    async def get_hardware_metrics(self) -> HardwareStatus:
        """Get hardware status metrics with caching."""
        cached = self._get_cached("hardware_metrics")
        if cached:
            return cached

        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            ram_available_gb = ram.available / (1024**3)

            # Try to get GPU metrics
            gpu_available = False
            gpu_percent = None
            gpu_memory_used_gb = None
            gpu_memory_total_gb = None

            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                gpu_available = True
                gpu_percent = float(gpu_util.gpu)
                gpu_memory_used_gb = gpu_info.used / (1024**3)
                gpu_memory_total_gb = gpu_info.total / (1024**3)
                pynvml.nvmlShutdown()
            except Exception:
                pass

            metrics = HardwareStatus(
                cpu_percent=round(cpu_percent, 2),
                ram_percent=round(ram_percent, 2),
                ram_available_gb=round(ram_available_gb, 2),
                gpu_available=gpu_available,
                gpu_percent=round(gpu_percent, 2) if gpu_percent is not None else None,
                gpu_memory_used_gb=round(gpu_memory_used_gb, 2) if gpu_memory_used_gb is not None else None,
                gpu_memory_total_gb=round(gpu_memory_total_gb, 2) if gpu_memory_total_gb is not None else None,
            )

            # Cache for 1 second (more frequent than other metrics)
            self._cache["hardware_metrics"] = (metrics, datetime.utcnow())
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get hardware metrics: {e}", exc_info=True)
            return HardwareStatus(
                cpu_percent=0.0,
                ram_percent=0.0,
                ram_available_gb=0.0,
                gpu_available=False,
            )
