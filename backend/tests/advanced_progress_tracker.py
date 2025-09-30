#!/usr/bin/env python3
"""
Advanced Progress Tracker for KR-AI-Engine
Combines the best features from all progress tracking implementations
"""

import time
import sys
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

class StageStatus(Enum):
    """Stage processing status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StageInfo:
    """Information about a processing stage"""
    number: int
    name: str
    description: str
    status: StageStatus = StageStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

class AdvancedProgressTracker:
    """
    Advanced Progress Tracker with real-time updates, ETA, and detailed logging
    
    Features:
    - Real-time progress bars with ASCII characters
    - ETA calculation based on average stage times
    - Detailed stage information and timing
    - Thread-safe output with immediate flushing
    - Configurable update frequency
    - Stage dependency tracking
    - Error handling and recovery tracking
    """
    
    def __init__(self, total_stages: int = 8, update_frequency: float = 0.5):
        self.total_stages = total_stages
        self.update_frequency = update_frequency
        self.start_time = time.time()
        self.stages: List[StageInfo] = []
        self.current_stage_index = -1
        self.completed_stages = 0
        self.failed_stages = 0
        self.skipped_stages = 0
        
        # Current file being processed
        self.current_file = None
        self.file_size = None
        self.document_id = None
        
        # Threading for real-time updates
        self._update_thread = None
        self._stop_updates = threading.Event()
        self._lock = threading.Lock()
        
        # Initialize stages
        self._initialize_stages()
        
        # Start real-time updates
        self._start_real_time_updates()
    
    def _initialize_stages(self):
        """Initialize the 8 processing stages"""
        stage_definitions = [
            (1, "Upload Processor", "Document upload and validation"),
            (2, "Text Processor", "Text extraction and chunking"),
            (3, "Image Processor", "Image extraction and AI analysis"),
            (4, "Classification Processor", "Document classification"),
            (5, "Metadata Processor", "Metadata extraction"),
            (6, "Storage Processor", "Object storage operations"),
            (7, "Embedding Processor", "Vector embedding generation"),
            (8, "Search Processor", "Search index creation")
        ]
        
        for number, name, description in stage_definitions:
            stage = StageInfo(number=number, name=name, description=description)
            self.stages.append(stage)
    
    def _start_real_time_updates(self):
        """Start real-time progress updates in background thread"""
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
    
    def _update_loop(self):
        """Background thread for real-time updates"""
        while not self._stop_updates.wait(self.update_frequency):
            if self.current_stage_index >= 0:
                self._print_current_status()
    
    def _print_current_status(self):
        """Print current processing status"""
        if self.current_stage_index < 0 or self.current_stage_index >= len(self.stages):
            return
        
        current_stage = self.stages[self.current_stage_index]
        
        # Calculate overall progress
        overall_progress = (self.completed_stages / self.total_stages) * 100
        
        # Calculate ETA
        eta = self._calculate_eta()
        
        # Build file info
        file_info = ""
        if self.current_file:
            file_info = f" | File: {self.current_file}"
            if self.file_size:
                file_info += f" ({self.file_size:,} bytes)"
            if self.document_id:
                file_info += f" | Doc: {self.document_id[:8]}..."
        
        # Print status line (overwrite previous)
        status_line = (
            f"\rKR-AI-Engine Progress: {overall_progress:.1f}% | "
            f"Stage {current_stage.number}/8: {current_stage.name} | "
            f"ETA: {eta} | "
            f"OK:{self.completed_stages} FAIL:{self.failed_stages} SKIP:{self.skipped_stages}"
            f"{file_info}"
        )
        
        print(status_line, end="", flush=True)
    
    def _calculate_eta(self) -> str:
        """Calculate estimated time to completion"""
        if self.completed_stages == 0:
            return "calculating..."
        
        # Calculate average time per completed stage
        completed_times = [
            stage.duration for stage in self.stages 
            if stage.status == StageStatus.COMPLETED and stage.duration is not None
        ]
        
        if not completed_times:
            return "calculating..."
        
        avg_time_per_stage = sum(completed_times) / len(completed_times)
        remaining_stages = self.total_stages - self.completed_stages
        eta_seconds = remaining_stages * avg_time_per_stage
        
        if eta_seconds < 60:
            return f"{eta_seconds:.0f}s"
        elif eta_seconds < 3600:
            return f"{eta_seconds/60:.1f}m"
        else:
            return f"{eta_seconds/3600:.1f}h"
    
    def start_stage(self, stage_number: int, custom_details: Dict[str, Any] = None):
        """Start processing a stage"""
        with self._lock:
            if stage_number < 1 or stage_number > self.total_stages:
                raise ValueError(f"Invalid stage number: {stage_number}")
            
            stage_index = stage_number - 1
            stage = self.stages[stage_index]
            
            # Update current stage
            self.current_stage_index = stage_index
            
            # Set stage info
            stage.status = StageStatus.IN_PROGRESS
            stage.start_time = time.time()
            stage.end_time = None
            stage.duration = None
            
            if custom_details:
                stage.details.update(custom_details)
            
            # Print stage start
            self._print_stage_header(stage)
            
            # Flush output
            sys.stdout.flush()
    
    def _print_stage_header(self, stage: StageInfo):
        """Print detailed stage header"""
        print(f"\n\n{'='*80}")
        print(f" STAGE {stage.number}/8: {stage.name}")
        print(f" {stage.description}")
        print(f"{'='*80}")
        
        if stage.details:
            print(" Stage Details:")
            for key, value in stage.details.items():
                print(f"   - {key}: {value}")
            print(f"{'='*80}")
    
    def end_stage(self, stage_number: int, success: bool = True, 
                  error_message: str = None, details: Dict[str, Any] = None):
        """End processing a stage"""
        with self._lock:
            if stage_number < 1 or stage_number > self.total_stages:
                raise ValueError(f"Invalid stage number: {stage_number}")
            
            stage_index = stage_number - 1
            stage = self.stages[stage_index]
            
            # Calculate duration
            stage.end_time = time.time()
            stage.duration = stage.end_time - stage.start_time
            
            # Update counters
            if success:
                stage.status = StageStatus.COMPLETED
                self.completed_stages += 1
            else:
                stage.status = StageStatus.FAILED
                self.failed_stages += 1
                if error_message:
                    stage.details['error'] = error_message
            
            # Update details
            if details:
                stage.details.update(details)
            
            # Print stage completion
            self._print_stage_completion(stage)
            
            # Flush output
            sys.stdout.flush()
    
    def _print_stage_completion(self, stage: StageInfo):
        """Print stage completion information"""
        status_emoji = "OK" if stage.status == StageStatus.COMPLETED else "FAIL"
        status_text = "COMPLETED" if stage.status == StageStatus.COMPLETED else "FAILED"
        
        print(f"\n{status_emoji} Stage {stage.number} {status_text}")
        print(f"  Duration: {stage.duration:.2f}s")
        
        # Show progress bar
        progress = stage.number / self.total_stages * 100
        bar_length = 20
        filled_length = int(bar_length * progress / 100)
        bar = '#' * filled_length + '-' * (bar_length - filled_length)
        print(f" Progress: [{bar}] {progress:.1f}%")
        
        # Show details if any
        if stage.details and len(stage.details) > 1:  # More than just error
            print(" Results:")
            for key, value in stage.details.items():
                if key != 'error':
                    print(f"   - {key}: {value}")
        
        # Show error if failed
        if stage.status == StageStatus.FAILED and 'error' in stage.details:
            print(f"FAIL Error: {stage.details['error']}")
        
        print(f"{'='*80}")
    
    def skip_stage(self, stage_number: int, reason: str = None):
        """Skip a stage"""
        with self._lock:
            if stage_number < 1 or stage_number > self.total_stages:
                raise ValueError(f"Invalid stage number: {stage_number}")
            
            stage_index = stage_number - 1
            stage = self.stages[stage_index]
            
            stage.status = StageStatus.SKIPPED
            stage.start_time = time.time()
            stage.end_time = time.time()
            stage.duration = 0
            
            if reason:
                stage.details['skip_reason'] = reason
            
            self.skipped_stages += 1
            
            print(f"\nSKIP  Stage {stage.number} SKIPPED: {reason or 'No reason provided'}")
            sys.stdout.flush()
    
    def update_stage_details(self, stage_number: int, details: Dict[str, Any]):
        """Update details for current stage"""
        with self._lock:
            if stage_number < 1 or stage_number > self.total_stages:
                raise ValueError(f"Invalid stage number: {stage_number}")
            
            stage_index = stage_number - 1
            stage = self.stages[stage_index]
            stage.details.update(details)
    
    def set_current_file(self, filename: str, file_size: int = None, document_id: str = None):
        """Set current file being processed"""
        with self._lock:
            self.current_file = filename
            self.file_size = file_size
            self.document_id = document_id
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive processing summary"""
        total_time = time.time() - self.start_time
        
        # Calculate statistics
        completed_times = [s.duration for s in self.stages if s.status == StageStatus.COMPLETED and s.duration]
        failed_times = [s.duration for s in self.stages if s.status == StageStatus.FAILED and s.duration]
        
        summary = {
            'total_time': total_time,
            'total_stages': self.total_stages,
            'completed_stages': self.completed_stages,
            'failed_stages': self.failed_stages,
            'skipped_stages': self.skipped_stages,
            'success_rate': (self.completed_stages / self.total_stages) * 100 if self.total_stages > 0 else 0,
            'average_stage_time': sum(completed_times) / len(completed_times) if completed_times else 0,
            'fastest_stage_time': min(completed_times) if completed_times else 0,
            'slowest_stage_time': max(completed_times) if completed_times else 0,
            'stages': [
                {
                    'number': stage.number,
                    'name': stage.name,
                    'status': stage.status.value,
                    'duration': stage.duration,
                    'details': stage.details
                }
                for stage in self.stages
            ]
        }
        
        return summary
    
    def print_final_summary(self):
        """Print comprehensive final summary"""
        summary = self.get_summary()
        
        print(f"\n\n{'=' * 20} FINAL SUMMARY {'=' * 20}")
        print(f"Total Processing Time: {summary['total_time']:.2f}s")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Completed: {summary['completed_stages']}/{summary['total_stages']}")
        print(f"Failed: {summary['failed_stages']}")
        print(f"Skipped: {summary['skipped_stages']}")
        
        if summary['average_stage_time'] > 0:
            print(f"Average Stage Time: {summary['average_stage_time']:.2f}s")
            print(f"Fastest Stage: {summary['fastest_stage_time']:.2f}s")
            print(f"Slowest Stage: {summary['slowest_stage_time']:.2f}s")
        
        print(f"\nStage Details:")
        for stage_info in summary['stages']:
            status_emoji = {
                'completed': '[OK]',
                'failed': '[FAIL]',
                'skipped': '[SKIP]',
                'pending': '[PEND]'
            }.get(stage_info['status'], '[?]')
            
            duration_str = f"{stage_info['duration']:.2f}s" if stage_info['duration'] else "N/A"
            print(f"   {status_emoji} Stage {stage_info['number']}: {stage_info['name']} ({duration_str})")
        
        print(f"{'=' * 53}")
        
        # Flush output
        sys.stdout.flush()
    
    def stop(self):
        """Stop the progress tracker"""
        self._stop_updates.set()
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=1.0)
        
        # Clear the status line
        print(f"\r{' ' * 100}\r", end="", flush=True)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()

# Example usage and testing
if __name__ == "__main__":
    print(" Testing Advanced Progress Tracker...")
    
    with AdvancedProgressTracker() as tracker:
        # Simulate processing stages
        for i in range(1, 9):
            tracker.start_stage(i, {"test": f"Stage {i} details"})
            time.sleep(1)  # Simulate work
            tracker.end_stage(i, success=True, details={"items_processed": i * 10})
        
        tracker.print_final_summary()
