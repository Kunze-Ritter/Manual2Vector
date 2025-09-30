"""
Perfect Progress Tracker - The best solution for monitoring everything!
"""

import time
import psutil
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os
import sys

@dataclass
class ProcessingStats:
    """Comprehensive processing statistics"""
    start_time: float
    current_file: str = ""
    current_file_index: int = 0
    total_files: int = 0
    file_size: int = 0
    file_processed_bytes: int = 0
    document_id: str = ""
    current_stage: str = ""
    stage_progress: float = 0.0
    chunks_processed: int = 0
    total_chunks: int = 0
    images_processed: int = 0
    total_images: int = 0
    links_extracted: int = 0
    errors_found: int = 0
    
    # Hardware monitoring
    cpu_usage: float = 0.0
    ram_usage_mb: float = 0.0
    ram_usage_percent: float = 0.0
    gpu_usage: float = 0.0
    gpu_memory_mb: float = 0.0
    
    # Performance metrics
    files_per_minute: float = 0.0
    mb_per_second: float = 0.0
    eta_seconds: float = 0.0

class PerfectProgressTracker:
    """
    The perfect progress tracker - monitors everything!
    """
    
    def __init__(self, total_files: int = 1):
        self.total_files = total_files
        self.stats = ProcessingStats(start_time=time.time(), total_files=total_files)
        self.running = True
        self.update_thread = None
        self.hardware_thread = None
        
        # Performance monitoring
        self.peak_cpu = 0.0
        self.peak_ram = 0.0
        self.peak_gpu = 0.0
        self.cpu_samples = []
        self.ram_samples = []
        self.gpu_samples = []
        
        # File processing tracking
        self.files_completed = 0
        self.total_bytes_processed = 0
        self.last_update_time = time.time()
        
        # Start monitoring threads
        self._start_monitoring()
        
        # Print initial header
        self._print_header()
    
    def _start_monitoring(self):
        """Start background monitoring threads"""
        self.hardware_thread = threading.Thread(target=self._monitor_hardware, daemon=True)
        self.hardware_thread.start()
        
        self.update_thread = threading.Thread(target=self._monitor_progress, daemon=True)
        self.update_thread.start()
    
    def _monitor_hardware(self):
        """Monitor hardware usage in background"""
        while self.running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.stats.cpu_usage = cpu_percent
                self.cpu_samples.append(cpu_percent)
                if len(self.cpu_samples) > 50:
                    self.cpu_samples.pop(0)
                self.peak_cpu = max(self.peak_cpu, cpu_percent)
                
                # RAM usage
                ram = psutil.virtual_memory()
                self.stats.ram_usage_mb = (ram.total - ram.available) / 1024 / 1024
                self.stats.ram_usage_percent = ram.percent
                self.ram_samples.append(ram.percent)
                if len(self.ram_samples) > 50:
                    self.ram_samples.pop(0)
                self.peak_ram = max(self.peak_ram, ram.percent)
                
                # GPU usage (simplified - would need nvidia-ml-py for real GPU monitoring)
                try:
                    # Try to get GPU info if available
                    gpu_usage = 0.0  # Placeholder
                    self.stats.gpu_usage = gpu_usage
                    self.gpu_samples.append(gpu_usage)
                    if len(self.gpu_samples) > 50:
                        self.gpu_samples.pop(0)
                    self.peak_gpu = max(self.peak_gpu, gpu_usage)
                except:
                    pass
                
                time.sleep(1)  # Update every second
            except Exception:
                pass
    
    def _monitor_progress(self):
        """Monitor progress and update display"""
        while self.running:
            try:
                self._update_performance_metrics()
                self._print_perfect_status()
                time.sleep(2)  # Update every 2 seconds
            except Exception:
                pass
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        current_time = time.time()
        elapsed = current_time - self.stats.start_time
        
        if elapsed > 0:
            # Files per minute
            self.stats.files_per_minute = (self.files_completed / elapsed) * 60
            
            # MB per second
            self.stats.mb_per_second = (self.total_bytes_processed / 1024 / 1024) / elapsed
            
            # ETA calculation
            if self.files_completed > 0:
                avg_time_per_file = elapsed / self.files_completed
                remaining_files = self.total_files - self.files_completed
                self.stats.eta_seconds = remaining_files * avg_time_per_file
    
    def set_current_file(self, filename: str, file_size: int, document_id: str = ""):
        """Set current file being processed"""
        self.stats.current_file = filename
        self.stats.file_size = file_size
        self.stats.document_id = document_id
        self.stats.current_file_index += 1
        self.stats.file_processed_bytes = 0
        self._print_file_start()
    
    def update_file_progress(self, processed_bytes: int):
        """Update file processing progress"""
        self.stats.file_processed_bytes = processed_bytes
    
    def update_stage(self, stage_name: str, stage_progress: float = 0.0):
        """Update current processing stage"""
        self.stats.current_stage = stage_name
        self.stats.stage_progress = stage_progress
    
    def update_chunks(self, chunks_processed: int, total_chunks: int = 0):
        """Update chunk processing count"""
        self.stats.chunks_processed = chunks_processed
        if total_chunks > 0:
            self.stats.total_chunks = total_chunks
    
    def update_images(self, images_processed: int, total_images: int = 0):
        """Update image processing count"""
        self.stats.images_processed = images_processed
        if total_images > 0:
            self.stats.total_images = total_images
    
    def update_links(self, links_extracted: int):
        """Update links extracted count"""
        self.stats.links_extracted = links_extracted
    
    def file_completed(self):
        """Mark current file as completed"""
        self.files_completed += 1
        self.total_bytes_processed += self.stats.file_size
        self._print_file_completed()
    
    def _print_header(self):
        """Print header information"""
        print(f"\n{'='*120}")
        print(f"KR-AI-Engine Perfect Progress Tracker")
        print(f"{'='*120}")
        print(f"Total Files: {self.total_files} | Start Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*120}")
    
    def _print_file_start(self):
        """Print file start information"""
        file_size_mb = self.stats.file_size / (1024 * 1024)
        print(f"\n[{self.stats.current_file_index}/{self.total_files}] Starting: {self.stats.current_file}")
        print(f"   Size: {file_size_mb:.1f}MB | Document ID: {self.stats.document_id[:8]}...")
    
    def _print_file_completed(self):
        """Print file completion information"""
        file_size_mb = self.stats.file_size / (1024 * 1024)
        print(f"[{self.stats.current_file_index}/{self.total_files}] Completed: {self.stats.current_file}")
        print(f"   Chunks: {self.stats.chunks_processed} | Images: {self.stats.images_processed} | Links: {self.stats.links_extracted}")
    
    def _print_perfect_status(self):
        """Print perfect status line"""
        # Calculate overall progress
        file_progress = (self.stats.current_file_index - 1) / self.total_files * 100
        current_file_progress = (self.stats.file_processed_bytes / max(1, self.stats.file_size)) * 100
        overall_progress = file_progress + (current_file_progress / self.total_files)
        
        # Create progress bar
        bar_length = 40
        filled_length = int(bar_length * overall_progress / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        # Format file info
        file_info = self.stats.current_file[:25] + "..." if len(self.stats.current_file) > 25 else self.stats.current_file
        file_size_mb = self.stats.file_size / (1024 * 1024)
        file_progress_mb = self.stats.file_processed_bytes / (1024 * 1024)
        
        # Format hardware info
        cpu_bar = self._create_mini_bar(self.stats.cpu_usage, 10)
        ram_bar = self._create_mini_bar(self.stats.ram_usage_percent, 10)
        
        # Format ETA
        eta_str = self._format_eta(self.stats.eta_seconds)
        
        # Format stage info
        stage_info = f"{self.stats.current_stage} ({self.stats.stage_progress:.0f}%)" if self.stats.current_stage else "Initializing"
        
        # Clear line and print status
        print(f"\r{' ' * 150}\r", end="", flush=True)
        
        status_line = (
            f"KR-AI: {overall_progress:5.1f}% | "
            f"{self.stats.current_file_index:2d}/{self.total_files} {file_info} "
            f"({file_progress_mb:4.1f}/{file_size_mb:4.1f}MB) | "
            f"{stage_info} | "
            f"{self.stats.chunks_processed:4d}ch | "
            f"{self.stats.images_processed:2d}img | "
            f"{self.stats.links_extracted:2d}lnk | "
            f"CPU{cpu_bar} {self.stats.cpu_usage:4.0f}% | "
            f"RAM{ram_bar} {self.stats.ram_usage_percent:4.0f}% | "
            f"{self.stats.mb_per_second:4.1f}MB/s | "
            f"ETA: {eta_str}"
        )
        
        print(status_line, end="", flush=True)
    
    def _create_mini_bar(self, value: float, length: int) -> str:
        """Create mini progress bar for hardware usage"""
        filled = int(length * value / 100)
        return "█" * filled + "░" * (length - filled)
    
    def _format_eta(self, seconds: float) -> str:
        """Format ETA in human readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def print_final_summary(self):
        """Print final processing summary"""
        elapsed = time.time() - self.stats.start_time
        
        print(f"\n\n{'='*120}")
        print(f"KR-AI-Engine Processing Complete!")
        print(f"{'='*120}")
        print(f"Files Processed: {self.files_completed}/{self.total_files}")
        print(f"Total Time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
        print(f"Average Time per File: {elapsed/self.files_completed:.1f}s")
        print(f"Files per Minute: {self.stats.files_per_minute:.1f}")
        print(f"Total Data Processed: {self.total_bytes_processed/1024/1024:.1f}MB")
        print(f"Average Speed: {self.stats.mb_per_second:.1f}MB/s")
        print(f"")
        print(f"Hardware Performance:")
        print(f"   Peak CPU Usage: {self.peak_cpu:.1f}%")
        print(f"   Peak RAM Usage: {self.peak_ram:.1f}%")
        print(f"   Peak GPU Usage: {self.peak_gpu:.1f}%")
        print(f"")
        print(f"Processing Results:")
        print(f"   Total Chunks: {self.stats.chunks_processed}")
        print(f"   Total Images: {self.stats.images_processed}")
        print(f"   Total Links: {self.stats.links_extracted}")
        print(f"   Errors Found: {self.stats.errors_found}")
        print(f"{'='*120}")
    
    def stop(self):
        """Stop the progress tracker"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
        if self.hardware_thread:
            self.hardware_thread.join(timeout=1)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.print_final_summary()
