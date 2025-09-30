"""
Enhanced Progress Tracker - Advanced logging with batch processing
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class ProcessingStats:
    """Statistics for processing tracking"""
    start_time: float
    current_stage: str = ""
    current_file: str = ""
    file_size: int = 0
    document_id: str = ""
    chunks_processed: int = 0
    images_processed: int = 0
    errors_found: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    eta_seconds: float = 0.0

class EnhancedProgressTracker:
    """
    Enhanced progress tracker with detailed logging and batch processing
    """
    
    def __init__(self, total_files: int = 1):
        self.total_files = total_files
        self.current_file_index = 0
        self.stats = ProcessingStats(start_time=time.time())
        self.stage_times = {}
        self.file_stats = []
        self.running = True
        self.update_thread = None
        
        # Performance monitoring
        self.peak_memory = 0.0
        self.avg_cpu = 0.0
        self.cpu_samples = []
        
        # Start monitoring thread
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        self.update_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        self.update_thread.start()
    
    def _monitor_performance(self):
        """Monitor system performance in background"""
        while self.running:
            try:
                # Get current memory usage
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.stats.memory_usage_mb = memory_mb
                self.peak_memory = max(self.peak_memory, memory_mb)
                
                # Get CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.stats.cpu_usage_percent = cpu_percent
                self.cpu_samples.append(cpu_percent)
                if len(self.cpu_samples) > 100:  # Keep last 100 samples
                    self.cpu_samples.pop(0)
                
                self.avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
                
                time.sleep(1)  # Update every second
            except Exception:
                pass
    
    def set_current_file(self, filename: str, file_size: int, document_id: str = ""):
        """Set current file being processed"""
        self.stats.current_file = filename
        self.stats.file_size = file_size
        self.stats.document_id = document_id
        self.current_file_index += 1
    
    def update_stage(self, stage_name: str, stage_number: int, total_stages: int):
        """Update current processing stage"""
        self.stats.current_stage = stage_name
        
        # Calculate stage progress
        stage_progress = (stage_number - 1) / total_stages
        file_progress = self.current_file_index / self.total_files
        overall_progress = (file_progress + stage_progress / self.total_files) * 100
        
        # Calculate ETA
        elapsed = time.time() - self.stats.start_time
        if overall_progress > 0:
            total_estimated = elapsed / (overall_progress / 100)
            self.stats.eta_seconds = max(0, total_estimated - elapsed)
        
        self._print_enhanced_status(overall_progress, stage_number, total_stages)
    
    def update_chunks(self, chunks_processed: int):
        """Update chunk processing count"""
        self.stats.chunks_processed = chunks_processed
    
    def update_images(self, images_processed: int):
        """Update image processing count"""
        self.stats.images_processed = images_processed
    
    def update_errors(self, errors_found: int):
        """Update error count"""
        self.stats.errors_found = errors_found
    
    def _print_enhanced_status(self, progress: float, stage_num: int, total_stages: int):
        """Print enhanced status with detailed information"""
        # Clear line and print status
        print(f"\r{' ' * 120}\r", end="", flush=True)
        
        # Progress bar
        bar_length = 30
        filled_length = int(bar_length * progress / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        # File info
        file_info = f"{self.stats.current_file[:30]}..." if len(self.stats.current_file) > 30 else self.stats.current_file
        file_size_mb = self.stats.file_size / (1024 * 1024)
        
        # Performance info
        memory_info = f"RAM: {self.stats.memory_usage_mb:.0f}MB"
        cpu_info = f"CPU: {self.stats.cpu_usage_percent:.0f}%"
        
        # ETA
        eta_str = self._format_eta(self.stats.eta_seconds)
        
        # Status line
        status_line = (
            f"KR-AI-Engine: {progress:.1f}% | "
            f"Stage {stage_num}/{total_stages}: {self.stats.current_stage} | "
            f"File: {file_info} ({file_size_mb:.1f}MB) | "
            f"Chunks: {self.stats.chunks_processed} | "
            f"Images: {self.stats.images_processed} | "
            f"Errors: {self.stats.errors_found} | "
            f"{memory_info} | {cpu_info} | "
            f"ETA: {eta_str}"
        )
        
        print(status_line, end="", flush=True)
    
    def _format_eta(self, seconds: float) -> str:
        """Format ETA in human readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def print_detailed_summary(self):
        """Print detailed processing summary"""
        elapsed = time.time() - self.stats.start_time
        
        print(f"\n{'='*80}")
        print(f"KR-AI-Engine Processing Summary")
        print(f"{'='*80}")
        print(f"Total Files Processed: {self.current_file_index}/{self.total_files}")
        print(f"Total Time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
        print(f"Average Time per File: {elapsed/self.current_file_index:.1f}s")
        print(f"")
        print(f"Performance Metrics:")
        print(f"  Peak Memory Usage: {self.peak_memory:.0f}MB")
        print(f"  Average CPU Usage: {self.avg_cpu:.1f}%")
        print(f"  Current Memory: {self.stats.memory_usage_mb:.0f}MB")
        print(f"  Current CPU: {self.stats.cpu_usage_percent:.1f}%")
        print(f"")
        print(f"Processing Results:")
        print(f"  Total Chunks: {self.stats.chunks_processed}")
        print(f"  Total Images: {self.stats.images_processed}")
        print(f"  Errors Found: {self.stats.errors_found}")
        print(f"  Success Rate: {((self.stats.chunks_processed + self.stats.images_processed) / max(1, self.stats.chunks_processed + self.stats.images_processed + self.stats.errors_found) * 100):.1f}%")
        print(f"{'='*80}")
    
    def stop(self):
        """Stop the progress tracker"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.print_detailed_summary()
