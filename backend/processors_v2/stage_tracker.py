"""
Stage Status Tracker

Helper class for tracking processing stages per document.
Enables parallel processing and detailed monitoring.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


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
    
    STAGES = [
        'upload',
        'text_extraction',
        'image_processing',
        'classification',
        'metadata_extraction',
        'storage',
        'embedding',
        'search_indexing'
    ]
    
    def __init__(self, supabase_client):
        """Initialize tracker"""
        self.supabase = supabase_client
    
    def start_stage(self, document_id: str, stage_name: str) -> bool:
        """
        Mark stage as started
        
        Args:
            document_id: Document UUID
            stage_name: Name of the stage
            
        Returns:
            True if successful
        """
        try:
            self.supabase.rpc('start_stage', {
                'p_document_id': document_id,
                'p_stage_name': stage_name
            }).execute()
            return True
        except Exception as e:
            print(f"Error starting stage: {e}")
            return False
    
    def update_progress(
        self,
        document_id: str,
        stage_name: str,
        progress: float,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update stage progress
        
        Args:
            document_id: Document UUID
            stage_name: Name of the stage
            progress: Progress percentage (0-100)
            metadata: Additional metadata (e.g., pages_processed)
            
        Returns:
            True if successful
        """
        try:
            self.supabase.rpc('update_stage_progress', {
                'p_document_id': document_id,
                'p_stage_name': stage_name,
                'p_progress': progress,
                'p_metadata': metadata or {}
            }).execute()
            return True
        except Exception as e:
            print(f"Error updating progress: {e}")
            return False
    
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
        try:
            self.supabase.rpc('complete_stage', {
                'p_document_id': document_id,
                'p_stage_name': stage_name,
                'p_metadata': metadata or {}
            }).execute()
            return True
        except Exception as e:
            print(f"Error completing stage: {e}")
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
        try:
            self.supabase.rpc('fail_stage', {
                'p_document_id': document_id,
                'p_stage_name': stage_name,
                'p_error': error,
                'p_metadata': metadata or {}
            }).execute()
            return True
        except Exception as e:
            print(f"Error failing stage: {e}")
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
        try:
            self.supabase.rpc('skip_stage', {
                'p_document_id': document_id,
                'p_stage_name': stage_name,
                'p_reason': reason
            }).execute()
            return True
        except Exception as e:
            print(f"Error skipping stage: {e}")
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
            print(f"Error getting progress: {e}")
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
            print(f"Error getting current stage: {e}")
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
        try:
            result = self.supabase.rpc('can_start_stage', {
                'p_document_id': document_id,
                'p_stage_name': stage_name
            }).execute()
            
            return bool(result.data) if result.data is not None else False
        except Exception as e:
            print(f"Error checking stage: {e}")
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
            result = self.supabase.table("documents") \
                .select("stage_status") \
                .eq("id", document_id) \
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0].get('stage_status', {})
            return {}
        except Exception as e:
            print(f"Error getting stage status: {e}")
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
            print(f"Error getting statistics: {e}")
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
        stage_name: str
    ):
        self.tracker = tracker
        self.document_id = document_id
        self.stage_name = stage_name
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
    
    load_dotenv()
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    
    tracker = StageTracker(supabase)
    
    # Example document ID (replace with real one)
    doc_id = "5a30739d-d8d4-4a1a-b033-a32e39cf33ba"
    
    print("Stage Status Tracker Demo")
    print("="*60)
    
    # Get current status
    print(f"\nCurrent Stage: {tracker.get_current_stage(doc_id)}")
    print(f"Overall Progress: {tracker.get_progress(doc_id)}%")
    
    # Get detailed status
    status = tracker.get_stage_status(doc_id)
    if status:
        print("\nDetailed Status:")
        for stage, data in status.items():
            print(f"  {stage}: {data.get('status', 'unknown')}")
    
    # Get statistics
    stats = tracker.get_statistics()
    if stats:
        print("\nPipeline Statistics:")
        for stage, data in stats.items():
            print(f"  {stage}:")
            print(f"    Pending: {data['pending']}")
            print(f"    Processing: {data['processing']}")
            print(f"    Completed: {data['completed']}")
