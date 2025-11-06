"""
Stage Status Tracker

Helper class for tracking processing stages per document.
Enables parallel processing and detailed monitoring.
"""

from typing import Optional, Dict, Any, Union, Callable
from datetime import datetime
from uuid import UUID
import asyncio
import logging

from backend.core.base_processor import Stage


class StageTracker:
    """
    Track processing stages for documents
    
    Stages:
    - upload
    - text_extraction
    - image_processing
    - classification
    - metadata_extraction
    - storage
    - embedding
    - search_indexing
    
    Status values:
    - pending: Not started yet
    - processing: Currently running
    - completed: Successfully finished
    - failed: Error occurred
    - skipped: Not applicable for this document
    """
    
    STAGES = [stage.value for stage in Stage]
    
    def __init__(self, supabase_client, websocket_callback: Optional[Callable] = None):
        """Initialize tracker with optional WebSocket callback."""
        self.supabase = supabase_client
        self.logger = logging.getLogger("krai.stage_tracker")
        self.websocket_callback = websocket_callback

    @staticmethod
    def _make_json_safe(value: Any) -> Any:
        """Recursively convert values to JSON-serializable types."""
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(k): StageTracker._make_json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [StageTracker._make_json_safe(v) for v in value]
        return value
    
    def _normalize_stage(self, stage_name: Union[str, Stage]) -> str:
        if isinstance(stage_name, Stage):
            return stage_name.value
        return str(stage_name)

    def start_stage(self, document_id: str, stage_name: Union[str, Stage]) -> bool:
        """
        Mark stage as started
        
        Args:
            document_id: Document UUID
            stage_name: Name of the stage
            
        Returns:
            True if successful
        """
        stage = self._normalize_stage(stage_name)

        try:
            self.supabase.rpc('start_stage', {
                'p_document_id': document_id,
                'p_stage_name': stage
            }).execute()
            return True
        except Exception as e:
            self.logger.error(
                "Error starting stage %s for document %s: %s",
                stage,
                document_id,
                e,
                exc_info=True
            )
            return False
    
    def update_progress(
        self,
        document_id: str,
        stage_name: Union[str, Stage],
        progress: float,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update stage progress
        
        Args:
            document_id: Document UUID
            stage_name: Name of the stage
            progress: Progress percentage (0-100). Fractions (0-1] are
                automatically converted to percentages and logged.
            metadata: Additional metadata (e.g., pages_processed)
            
        Returns:
            True if successful
        """
        stage = self._normalize_stage(stage_name)

        try:
            metadata = metadata or {}
            metadata = self._make_json_safe(metadata)
            normalized_progress = progress

            if normalized_progress is None:
                self.logger.warning(
                    "Received None progress for stage '%s' on document '%s'; defaulting to 0.",
                    stage_name,
                    document_id
                )
                normalized_progress = 0.0

            if 0 < normalized_progress <= 1:
                self.logger.warning(
                    "Progress for stage '%s' on document '%s' provided as fraction %.4f;"
                    " scaling to percentage.",
                    stage_name,
                    document_id,
                    normalized_progress
                )
                normalized_progress = normalized_progress * 100
                metadata.setdefault('progress_scale_adjusted', True)

            normalized_progress = max(0.0, min(100.0, float(normalized_progress)))

            self.supabase.rpc('update_stage_progress', {
                'p_document_id': document_id,
                'p_stage_name': stage,
                'p_progress': normalized_progress,
                'p_metadata': metadata
            }).execute()
            return True
        except Exception as e:
            self.logger.error(
                "Error updating progress for stage '%s' on document '%s': %s",
                stage_name,
                document_id,
                e
            )
            return False
    
    # Alias for consistency
    def update_stage_progress(
        self,
        document_id: str,
        stage_name: Union[str, Stage],
        progress: float,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Alias for update_progress"""
        return self.update_progress(document_id, stage_name, progress, metadata)
    
    def complete_stage(
        self,
        document_id: str,
        stage_name: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Mark stage as completed
        
        Args:
            document_id: Document UUID
            stage_name: Name of the stage
            metadata: Additional metadata about completion
            
        Returns:
            True if successful
        """
        stage = self._normalize_stage(stage_name)

        try:
            self.supabase.rpc('complete_stage', {
                'p_document_id': document_id,
                'p_stage_name': stage,
                'p_metadata': metadata or {}
            }).execute()
            
            # Broadcast WebSocket event
            if self.websocket_callback:
                try:
                    from backend.models.monitoring import WebSocketEvent
                    asyncio.create_task(
                        self.websocket_callback(
                            WebSocketEvent.STAGE_COMPLETED,
                            stage,
                            document_id,
                            "completed"
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to broadcast stage completion: {e}")
            
            return True
        except Exception as e:
            self.logger.error(
                "Error completing stage %s for document %s: %s",
                stage,
                document_id,
                e,
                exc_info=True
            )
            return False
    
    def fail_stage(
        self,
        document_id: str,
        stage_name: str,
        error: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Mark stage as failed
        
        Args:
            document_id: Document UUID
            stage_name: Name of the stage
            error: Error message
            metadata: Additional error metadata
            
        Returns:
            True if successful
        """
        stage = self._normalize_stage(stage_name)

        try:
            self.supabase.rpc('fail_stage', {
                'p_document_id': document_id,
                'p_stage_name': stage,
                'p_error': error,
                'p_metadata': metadata or {}
            }).execute()
            
            # Broadcast WebSocket event
            if self.websocket_callback:
                try:
                    from backend.models.monitoring import WebSocketEvent
                    asyncio.create_task(
                        self.websocket_callback(
                            WebSocketEvent.STAGE_FAILED,
                            stage,
                            document_id,
                            "failed"
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to broadcast stage failure: {e}")
            
            return True
        except Exception as e:
            self.logger.error(
                "Error marking stage %s as failed for document %s: %s",
                stage,
                document_id,
                e,
                exc_info=True
            )
            return False
    
    def skip_stage(
        self,
        document_id: str,
        stage_name: str,
        reason: str = "Not applicable"
    ) -> bool:
        """
        Mark stage as skipped
        
        Args:
            document_id: Document UUID
            stage_name: Name of the stage
            reason: Reason for skipping
            
        Returns:
            True if successful
        """
        stage = self._normalize_stage(stage_name)

        try:
            self.supabase.rpc('skip_stage', {
                'p_document_id': document_id,
                'p_stage_name': stage,
                'p_reason': reason
            }).execute()
            return True
        except Exception as e:
            self.logger.error(
                "Error skipping stage %s for document %s: %s",
                stage,
                document_id,
                e,
                exc_info=True
            )
            return False
    
    def get_progress(self, document_id: str) -> float:
        """
        Get overall document progress (0-100)
        
        Args:
            document_id: Document UUID
            
        Returns:
            Progress percentage
        """
        try:
            result = self.supabase.rpc('get_document_progress', {
                'p_document_id': document_id
            }).execute()
            
            if result.data is not None:
                return float(result.data)
            return 0.0
        except Exception as e:
            self.logger.error(
                "Error getting progress for document %s: %s",
                document_id,
                e,
                exc_info=True
            )
            return 0.0
    
    def get_current_stage(self, document_id: str) -> str:
        """
        Get current processing stage
        
        Args:
            document_id: Document UUID
            
        Returns:
            Stage name or 'completed'
        """
        try:
            result = self.supabase.rpc('get_current_stage', {
                'p_document_id': document_id
            }).execute()
            
            if result.data:
                return result.data
            return 'upload'
        except Exception as e:
            self.logger.error(
                "Error getting current stage for document %s: %s",
                document_id,
                e,
                exc_info=True
            )
            return 'unknown'
    
    def can_start_stage(self, document_id: str, stage_name: str) -> bool:
        """
        Check if stage can be started (prerequisites met)
        
        Args:
            document_id: Document UUID
            stage_name: Name of the stage
            
        Returns:
            True if stage can start
        """
        stage = self._normalize_stage(stage_name)

        try:
            result = self.supabase.rpc('can_start_stage', {
                'p_document_id': document_id,
                'p_stage_name': stage
            }).execute()
            
            return bool(result.data) if result.data is not None else False
        except Exception as e:
            self.logger.error(
                "Error checking if stage %s can start for document %s: %s",
                stage,
                document_id,
                e,
                exc_info=True
            )
            return False
    
    def get_stage_status(self, document_id: str) -> Dict[str, Any]:
        """
        Get complete stage status for a document
        
        Args:
            document_id: Document UUID
            
        Returns:
            Dictionary with all stage statuses
        """
        try:
            result = self.supabase.table("vw_documents") \
                .select("stage_status") \
                .eq("id", document_id) \
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0].get('stage_status', {})
            return {}
        except Exception as e:
            self.logger.error(
                "Error getting stage status for document %s: %s",
                document_id,
                e,
                exc_info=True
            )
            return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics for all stages
        
        Returns:
            Dictionary with statistics per stage
        """
        try:
            result = self.supabase.table("vw_stage_statistics") \
                .select("*") \
                .execute()
            
            if result.data:
                return {
                    stage['stage_name']: {
                        'pending': stage['pending_count'],
                        'processing': stage['processing_count'],
                        'completed': stage['completed_count'],
                        'failed': stage['failed_count'],
                        'skipped': stage['skipped_count'],
                        'avg_duration': stage['avg_duration_seconds']
                    }
                    for stage in result.data
                }
            return {}
        except Exception as e:
            self.logger.error(
                "Error getting stage statistics: %s",
                e,
                exc_info=True
            )
            return {}


# Context manager for automatic stage tracking
class StageContext:
    """
    Context manager for automatic stage tracking
    
    Usage:
        tracker = StageTracker(supabase)
        with StageContext(tracker, document_id, 'text_extraction') as ctx:
            # Do processing
            ctx.update_progress(50, {'pages': 2000})
            # Stage automatically marked as completed on success
            # Or failed if exception occurs
    """
    
    def __init__(
        self,
        tracker: StageTracker,
        document_id: str,
        stage_name: Union[str, Stage]
    ):
        self.tracker = tracker
        self.document_id = document_id
        tracker_stage = tracker._normalize_stage(stage_name)
        self.stage_name = tracker_stage
        self.metadata = {}
    
    def __enter__(self):
        """Start stage"""
        self.tracker.start_stage(self.document_id, self.stage_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete or fail stage"""
        if exc_type is None:
            # Success
            self.tracker.complete_stage(
                self.document_id,
                self.stage_name,
                self.metadata
            )
        else:
            # Failure
            self.tracker.fail_stage(
                self.document_id,
                self.stage_name,
                str(exc_val),
                self.metadata
            )
        return False  # Don't suppress exception
    
    def update_progress(self, progress: float, metadata: Optional[Dict] = None):
        """Update progress during processing"""
        if metadata:
            self.metadata.update(metadata)
        self.tracker.update_progress(
            self.document_id,
            self.stage_name,
            progress,
            metadata
        )
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata value"""
        self.metadata[key] = value


# Example usage
if __name__ == "__main__":
    from supabase import create_client
    import os
    from dotenv import load_dotenv
    import logging
    
    load_dotenv()
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    
    tracker = StageTracker(supabase)
    
    # Example document ID (replace with real one)
    doc_id = "5a30739d-d8d4-4a1a-b033-a32e39cf33ba"
    
    logger = logging.getLogger("krai.stage_tracker.demo")
    logger.info("Stage Status Tracker Demo")
    logger.info("=" * 60)
    
    # Get current status
    logger.info("Current Stage: %s", tracker.get_current_stage(doc_id))
    logger.info("Overall Progress: %s%%", tracker.get_progress(doc_id))
    
    # Get detailed status
    status = tracker.get_stage_status(doc_id)
    if status:
        logger.info("Detailed Status:")
        for stage, data in status.items():
            logger.info("  %s: %s", stage, data.get('status', 'unknown'))
    
    # Get statistics
    stats = tracker.get_statistics()
    if stats:
        logger.info("Pipeline Statistics:")
        for stage, data in stats.items():
            logger.info("  %s:", stage)
            logger.info("    Pending: %s", data['pending'])
            logger.info("    Processing: %s", data['processing'])
            logger.info("    Completed: %s", data['completed'])
