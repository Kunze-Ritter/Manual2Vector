"""Search Processor - Finalize document indexing for search readiness."""

from __future__ import annotations

from typing import Any, Dict, Optional
import time

from core.base_processor import BaseProcessor, Stage
from .stage_tracker import StageTracker
from .search_analytics import SearchAnalytics


class SearchProcessor(BaseProcessor):
    """Stage 10 processor: ensure document is ready for search & log analytics."""

    def __init__(self, database_service=None, ai_service=None):
        super().__init__(name="search_processor")
        self.stage = Stage.SEARCH_INDEXING
        self.database_service = database_service
        self.ai_service = ai_service  # Reserved for future semantic scoring

        supabase_client = getattr(database_service, "client", None)
        self.stage_tracker: Optional[StageTracker] = StageTracker(supabase_client) if supabase_client else None
        self.analytics = SearchAnalytics(supabase_client)

        if not supabase_client:
            self.logger.warning("SearchProcessor initialized without Supabase client")

    async def process(self, context) -> Any:
        """Finalize search indexing for the provided processing context."""
        document_id = str(context.document_id)

        supabase = getattr(self.database_service, "client", None)
        if not supabase:
            self.logger.error("SearchProcessor requires an active Supabase client")
            return self._create_result(False, "Supabase client not configured", {})

        with self.logger_context(document_id=document_id, stage=self.stage) as adapter:
            start_time = time.time()

            if self.stage_tracker:
                self.stage_tracker.start_stage(document_id, self.stage)

            try:
                chunks_count = self._count_records(supabase, "vw_chunks", document_id)
                embeddings_count = self._count_records(supabase, "vw_embeddings", document_id)
                links_count = self._count_records(supabase, "vw_links", document_id)
                videos_count = self._count_records(supabase, "vw_videos", document_id)

                if embeddings_count == 0 and chunks_count > 0:
                    adapter.warning("Embeddings missing - search results may be limited")

                self._update_document_flags(supabase, document_id, embeddings_ready=embeddings_count > 0, adapter=adapter)

                processing_time = time.time() - start_time

                self.analytics.log_document_indexed(
                    document_id=document_id,
                    chunks_count=chunks_count,
                    embeddings_count=embeddings_count,
                    processing_time_seconds=processing_time
                )

                stage_metadata = {
                    "chunks_indexed": chunks_count,
                    "embeddings_indexed": embeddings_count,
                    "links_indexed": links_count,
                    "videos_indexed": videos_count,
                    "processing_time_seconds": round(processing_time, 2)
                }

                if self.stage_tracker:
                    self.stage_tracker.complete_stage(document_id, self.stage, stage_metadata)

                return self._create_result(
                    success=True,
                    message="Search indexing completed",
                    data=stage_metadata
                )

            except Exception as exc:
                adapter.error("Search indexing failed: %s", exc)
                self.logger.error(f"Search indexing failed: {exc}")
                if self.stage_tracker:
                    self.stage_tracker.fail_stage(
                        document_id,
                        self.stage,
                        error=str(exc)
                    )
                return self._create_result(False, f"Search indexing error: {exc}", {})

    def _count_records(self, supabase, view_name: str, document_id: str) -> int:
        """Return exact count of records for a document in the given view."""
        try:
            response = supabase.table(view_name).select("id", count="exact").eq("document_id", document_id).execute()
            return response.count or 0
        except Exception as exc:
            self.logger.debug(f"Failed counting records in {view_name}: {exc}")
            return 0

    def _update_document_flags(self, supabase, document_id: str, embeddings_ready: bool, adapter=None) -> None:
        """Update document level flags to signal search readiness."""
        try:
            update_payload: Dict[str, Any] = {
                "search_ready": embeddings_ready,
                "search_ready_at": "now()" if embeddings_ready else None
            }

            # Remove None values to avoid overwriting with NULL
            update_payload = {k: v for k, v in update_payload.items() if v is not None}

            if update_payload:
                supabase.table("vw_documents").update(update_payload).eq("id", document_id).execute()
        except Exception as exc:
            logger = adapter if adapter else self.logger
            logger.debug("Failed updating document search flags: %s", exc)

    def _create_result(self, success: bool, message: str, data: Dict) -> Any:
        class Result:
            def __init__(self, success: bool, message: str, data: Dict):
                self.success = success
                self.message = message
                self.data = data

        return Result(success, message, data)
