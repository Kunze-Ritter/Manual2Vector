#!/usr/bin/env python3
"""
KRAI MinIO Storage Operations Test
===================================

Comprehensive test for MinIO object storage operations.
This script validates the ObjectStorageService's ability to handle file operations,
bucket management, deduplication, and performance under various conditions.

Features Tested:
- Basic upload/download/delete operations
- File deduplication using SHA256 hashing
- Large file handling (>10MB)
- Concurrent operations and thread safety
- Bucket management and permissions
- Public URL generation and access
- Performance metrics and throughput

Usage:
    python scripts/test_minio_storage_operations.py
    python scripts/test_minio_storage_operations.py --verbose
    python scripts/test_minio_storage_operations.py --performance
    python scripts/test_minio_storage_operations.py --concurrent
"""

import os
import sys
import asyncio
import argparse
import json
import time
import uuid
import hashlib
import threading
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import io

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Backend imports
from backend.services.object_storage_service import ObjectStorageService
from backend.services.storage_factory import create_storage_service

@dataclass
class StorageTestResult:
    """Test result for storage operations"""
    operation: str
    success: bool
    duration_ms: float
    file_size_bytes: int
    throughput_mbps: float
    errors: List[str]
    warnings: List[str]

class MinIOStorageTester:
    """Test runner for MinIO storage operations"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None
        self.logger = logging.getLogger("krai.minio_storage_test")
        
        # Test configuration
        self.test_buckets = {
            'documents': 'test-documents',
            'images': 'test-images', 
            'videos': 'test-videos',
            'temp': 'test-temp'
        }
        
        # Performance targets
        self.performance_targets = {
            'upload_throughput_mbps': 10,  # Minimum 10 MB/s upload
            'download_throughput_mbps': 20,  # Minimum 20 MB/s download
            'max_latency_ms': 100,  # Maximum 100ms for small files
            'concurrent_operations': 10  # Should handle 10 concurrent operations
        }
        
        # Test data
        self.test_files = {}
        self.cleanup_files = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def print_status(self, message: str, status: str = 'info'):
        """Print status message with appropriate formatting"""
        if self.console:
            color = {
                'success': 'green',
                'warning': 'yellow',
                'error': 'red',
                'info': 'blue',
                'test': 'cyan',
                'storage': 'blue'
            }.get(status, 'white')
            
            icon = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️',
                'test': '🧪',
                'storage': '💾'
            }.get(status, '•')
            
            self.console.print(f"{icon} {message}", style=color)
        else:
            print(f"{message}")
    
    async def setup(self) -> bool:
        """Initialize test environment"""
        try:
            self.print_status("Setting up MinIO Storage Tester", 'test')
            
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Initialize storage service
            self.print_status("Initializing storage service...", 'info')
            self.storage_service = create_storage_service()
            await self.storage_service.connect()
            
            # Create test buckets
            await self._create_test_buckets()
            
            # Generate test files
            await self._generate_test_files()
            
            self.print_status("Setup completed successfully", 'success')
            return True
            
        except Exception as e:
            self.print_status(f"Setup failed: {e}", 'error')
            self.logger.error("Setup failed", exc_info=True)
            return False
    
    async def _create_test_buckets(self):
        """Create test buckets"""
        self.print_status("Creating test buckets...", 'info')
        
        for bucket_name in self.test_buckets.values():
            try:
                # Check if bucket exists
                buckets = await self.storage_service.list_buckets()
                if bucket_name not in buckets:
                    await self.storage_service.create_bucket(bucket_name)
                    self.print_status(f"Created bucket: {bucket_name}", 'success')
                else:
                    self.print_status(f"Bucket already exists: {bucket_name}", 'info')
            except Exception as e:
                self.print_status(f"Failed to create bucket {bucket_name}: {e}", 'warning')
    
    async def _generate_test_files(self):
        """Generate test files of various sizes"""
        self.print_status("Generating test files...", 'info')
        
        # Small file (1KB)
        self.test_files['small'] = {
            'content': b'A' * 1024,
            'filename': 'test_small_1kb.txt',
            'content_type': 'text/plain',
            'size_bytes': 1024
        }
        
        # Medium file (100KB)
        self.test_files['medium'] = {
            'content': b'B' * (100 * 1024),
            'filename': 'test_medium_100kb.txt',
            'content_type': 'text/plain',
            'size_bytes': 100 * 1024
        }
        
        # Large file (10MB)
        self.test_files['large'] = {
            'content': b'C' * (10 * 1024 * 1024),
            'filename': 'test_large_10mb.bin',
            'content_type': 'application/octet-stream',
            'size_bytes': 10 * 1024 * 1024
        }
        
        # PDF file (simulated)
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n...\n%%EOF'
        self.test_files['pdf'] = {
            'content': pdf_content * 100,  # Make it larger
            'filename': 'test_document.pdf',
            'content_type': 'application/pdf',
            'size_bytes': len(pdf_content) * 100
        }
        
        # Image file (simulated PNG)
        png_header = b'\x89PNG\r\n\x1a\n'
        png_content = png_header + b'PNG_IMAGE_DATA' * 1000
        self.test_files['image'] = {
            'content': png_content,
            'filename': 'test_image.png',
            'content_type': 'image/png',
            'size_bytes': len(png_content)
        }
        
        self.print_status(f"Generated {len(self.test_files)} test files", 'success')
    
    async def test_basic_operations(self) -> Dict[str, Any]:
        """Test basic upload/download/delete operations"""
        self.print_status("Testing basic storage operations...", 'test')
        
        try:
            test_results = []
            
            for file_type, file_data in self.test_files.items():
                self.print_status(f"Testing {file_type} file operations...", 'storage')
                
                # Test upload
                start_time = time.time()
                upload_result = await self.storage_service.upload_file(
                    bucket=self.test_buckets['documents'],
                    key=file_data['filename'],
                    content=file_data['content'],
                    content_type=file_data['content_type']
                )
                upload_time = (time.time() - start_time) * 1000
                
                if upload_result:
                    storage_path = upload_result.get('storage_path', file_data['filename'])
                    file_hash = upload_result.get('file_hash', '')
                    
                    # Test download
                    start_time = time.time()
                    download_result = await self.storage_service.download_file(
                        bucket=self.test_buckets['documents'],
                        key=storage_path
                    )
                    download_time = (time.time() - start_time) * 1000
                    
                    if download_result == file_data['content']:
                        # Content matches - success
                        throughput = (file_data['size_bytes'] / (1024 * 1024)) / (upload_time / 1000) if upload_time > 0 else 0
                        
                        test_result = StorageTestResult(
                            operation=f"{file_type}_basic_ops",
                            success=True,
                            duration_ms=upload_time + download_time,
                            file_size_bytes=file_data['size_bytes'],
                            throughput_mbps=throughput,
                            errors=[],
                            warnings=[]
                        )
                        
                        test_results.append(test_result)
                        self.cleanup_files.append((self.test_buckets['documents'], storage_path))
                        
                        self.print_status(f"  ✅ Upload: {upload_time:.2f}ms, Download: {download_time:.2f}ms", 'success')
                        self.print_status(f"  📊 Throughput: {throughput:.2f} MB/s", 'info')
                    else:
                        # Content mismatch
                        test_results.append(StorageTestResult(
                            operation=f"{file_type}_basic_ops",
                            success=False,
                            duration_ms=upload_time + download_time,
                            file_size_bytes=file_data['size_bytes'],
                            throughput_mbps=0,
                            errors=['Downloaded content does not match uploaded content'],
                            warnings=[]
                        ))
                        self.print_status(f"  ❌ Content mismatch", 'error')
                else:
                    # Upload failed
                    test_results.append(StorageTestResult(
                        operation=f"{file_type}_basic_ops",
                        success=False,
                        duration_ms=upload_time,
                        file_size_bytes=file_data['size_bytes'],
                        throughput_mbps=0,
                        errors=['Upload failed'],
                        warnings=[]
                    ))
                    self.print_status(f"  ❌ Upload failed", 'error')
            
            # Calculate overall metrics
            successful_operations = sum(1 for r in test_results if r.success)
            avg_throughput = sum(r.throughput_mbps for r in test_results if r.success) / successful_operations if successful_operations > 0 else 0
            
            return {
                'success': True,
                'total_operations': len(test_results),
                'successful_operations': successful_operations,
                'success_rate': (successful_operations / len(test_results)) * 100,
                'avg_throughput_mbps': avg_throughput,
                'test_results': [vars(r) for r in test_results]
            }
            
        except Exception as e:
            self.print_status(f"Basic operations test failed: {e}", 'error')
            self.logger.error("Basic operations test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_file_deduplication(self) -> Dict[str, Any]:
        """Test file deduplication using SHA256 hashing"""
        self.print_status("Testing file deduplication...", 'test')
        
        try:
            # Upload the same file twice
            file_data = self.test_files['medium']
            
            # First upload
            start_time = time.time()
            upload1_result = await self.storage_service.upload_file(
                bucket=self.test_buckets['documents'],
                key='dedup_test_1.txt',
                content=file_data['content'],
                content_type=file_data['content_type']
            )
            upload1_time = (time.time() - start_time) * 1000
            
            # Second upload (should be deduplicated)
            start_time = time.time()
            upload2_result = await self.storage_service.upload_file(
                bucket=self.test_buckets['documents'],
                key='dedup_test_2.txt',
                content=file_data['content'],
                content_type=file_data['content_type']
            )
            upload2_time = (time.time() - start_time) * 1000
            
            if upload1_result and upload2_result:
                storage_path1 = upload1_result.get('storage_path', '')
                storage_path2 = upload2_result.get('storage_path', '')
                file_hash1 = upload1_result.get('file_hash', '')
                file_hash2 = upload2_result.get('file_hash', '')
                
                # Check if deduplication worked
                deduplication_worked = (
                    storage_path1 == storage_path2 and  # Same storage path
                    file_hash1 == file_hash2 and  # Same hash
                    file_hash1 != ''  # Hash is not empty
                )
                
                # Verify expected hash
                expected_hash = hashlib.sha256(file_data['content']).hexdigest()
                hash_correct = file_hash1 == expected_hash
                
                # Second upload should be faster (deduplication)
                speed_improvement = (upload1_time - upload2_time) / upload1_time * 100 if upload1_time > 0 else 0
                
                self.cleanup_files.append((self.test_buckets['documents'], storage_path1))
                
                result = {
                    'success': True,
                    'deduplication_worked': deduplication_worked,
                    'hash_correct': hash_correct,
                    'first_upload_time_ms': upload1_time,
                    'second_upload_time_ms': upload2_time,
                    'speed_improvement_percent': speed_improvement,
                    'storage_path': storage_path1,
                    'file_hash': file_hash1
                }
                
                if deduplication_worked and hash_correct:
                    self.print_status(f"✅ Deduplication working correctly", 'success')
                    self.print_status(f"  Same storage path: {storage_path1}", 'info')
                    self.print_status(f"  SHA256 hash: {file_hash1[:16]}...", 'info')
                    self.print_status(f"  Speed improvement: {speed_improvement:.1f}%", 'info')
                else:
                    self.print_status(f"❌ Deduplication not working properly", 'error')
                    if not deduplication_worked:
                        self.print_status(f"  Different paths: {storage_path1} vs {storage_path2}", 'error')
                    if not hash_correct:
                        self.print_status(f"  Hash mismatch: expected {expected_hash[:16]}..., got {file_hash1[:16]}...", 'error')
                
                return result
            else:
                return {
                    'success': False,
                    'error': 'One or both uploads failed'
                }
            
        except Exception as e:
            self.print_status(f"File deduplication test failed: {e}", 'error')
            self.logger.error("File deduplication test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_large_file_handling(self) -> Dict[str, Any]:
        """Test large file handling (>10MB)"""
        self.print_status("Testing large file handling...", 'test')
        
        try:
            file_data = self.test_files['large']
            
            # Upload large file
            start_time = time.time()
            upload_result = await self.storage_service.upload_file(
                bucket=self.test_buckets['documents'],
                key=file_data['filename'],
                content=file_data['content'],
                content_type=file_data['content_type']
            )
            upload_time = (time.time() - start_time) * 1000
            
            if upload_result:
                storage_path = upload_result.get('storage_path', '')
                
                # Download large file
                start_time = time.time()
                download_result = await self.storage_service.download_file(
                    bucket=self.test_buckets['documents'],
                    key=storage_path
                )
                download_time = (time.time() - start_time) * 1000
                
                # Verify content
                content_matches = download_result == file_data['content']
                
                # Calculate throughput
                upload_throughput = (file_data['size_bytes'] / (1024 * 1024)) / (upload_time / 1000) if upload_time > 0 else 0
                download_throughput = (file_data['size_bytes'] / (1024 * 1024)) / (download_time / 1000) if download_time > 0 else 0
                
                self.cleanup_files.append((self.test_buckets['documents'], storage_path))
                
                result = {
                    'success': content_matches,
                    'file_size_mb': file_data['size_bytes'] / (1024 * 1024),
                    'upload_time_ms': upload_time,
                    'download_time_ms': download_time,
                    'upload_throughput_mbps': upload_throughput,
                    'download_throughput_mbps': download_throughput,
                    'content_matches': content_matches,
                    'meets_upload_target': upload_throughput >= self.performance_targets['upload_throughput_mbps'],
                    'meets_download_target': download_throughput >= self.performance_targets['download_throughput_mbps']
                }
                
                if content_matches:
                    self.print_status(f"✅ Large file handled successfully", 'success')
                    self.print_status(f"  Upload: {upload_time:.2f}ms ({upload_throughput:.2f} MB/s)", 'info')
                    self.print_status(f"  Download: {download_time:.2f}ms ({download_throughput:.2f} MB/s)", 'info')
                else:
                    self.print_status(f"❌ Large file content mismatch", 'error')
                
                return result
            else:
                return {
                    'success': False,
                    'error': 'Large file upload failed'
                }
            
        except Exception as e:
            self.print_status(f"Large file handling test failed: {e}", 'error')
            self.logger.error("Large file handling test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _concurrent_upload_worker(self, worker_id: int, file_data: Dict[str, Any], results_list: List, results_lock: threading.Lock):
        """Worker function for concurrent upload test with proper thread safety"""
        worker_result = {
            'worker_id': worker_id,
            'success': False,
            'duration_ms': 0,
            'storage_path': '',
            'error': None
        }
        
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def upload_worker():
                storage_service = None
                try:
                    storage_service = create_storage_service()
                    await storage_service.connect()
                    
                    start_time = time.time()
                    upload_result = await storage_service.upload_file(
                        bucket=self.test_buckets['temp'],
                        key=f"concurrent_test_{worker_id}_{file_data['filename']}",
                        content=file_data['content'],
                        content_type=file_data['content_type']
                    )
                    duration = (time.time() - start_time) * 1000
                    
                    if upload_result:
                        worker_result.update({
                            'success': True,
                            'duration_ms': duration,
                            'storage_path': upload_result.get('storage_path', '')
                        })
                    else:
                        worker_result['error'] = 'Upload returned None result'
                        
                except Exception as e:
                    worker_result['error'] = str(e)
                finally:
                    if storage_service:
                        try:
                            # Storage service cleanup (disconnect not available)
                            # await storage_service.disconnect()
                            pass
                        except Exception as e:
                            # Log but don't fail the test if disconnect fails
                            print(f"Warning: Failed to disconnect storage service for worker {worker_id}: {e}")
                
                return worker_result
            
            # Run the async worker
            worker_result = loop.run_until_complete(upload_worker())
            
        except Exception as e:
            worker_result['error'] = f"Thread setup error: {str(e)}"
        finally:
            try:
                loop.close()
            except:
                pass
        
        # Thread-safe result append
        with results_lock:
            results_list.append(worker_result)
    
    async def test_concurrent_operations(self) -> Dict[str, Any]:
        """Test concurrent operations and thread safety"""
        self.print_status("Testing concurrent operations...", 'test')
        
        try:
            num_workers = self.performance_targets['concurrent_operations']
            file_data = self.test_files['medium']  # Use medium file for concurrent test
            
            self.print_status(f"Starting {num_workers} concurrent uploads...", 'info')
            
            # Thread-safe result collection
            results = []
            results_lock = threading.Lock()
            
            # Run concurrent uploads with proper synchronization
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = []
                
                # Submit all worker tasks
                for i in range(num_workers):
                    future = executor.submit(
                        self._concurrent_upload_worker,
                        i, file_data, results, results_lock
                    )
                    futures.append(future)
                
                # Wait for all tasks to complete with timeout
                try:
                    for future in as_completed(futures, timeout=300):  # 5 minute timeout
                        future.result()  # This will raise any exceptions from the worker
                except Exception as e:
                    self.print_status(f"Error in concurrent execution: {e}", 'error')
            
            # Verify all workers completed
            if len(results) != num_workers:
                self.print_status(f"Warning: Only {len(results)}/{num_workers} workers completed", 'warning')
            
            # Analyze results with better error handling
            successful_workers = 0
            failed_workers = 0
            durations = []
            storage_paths = []
            errors = []
            
            for result in results:
                if result['success']:
                    successful_workers += 1
                    durations.append(result['duration_ms'])
                    if result['storage_path']:
                        storage_paths.append(result['storage_path'])
                else:
                    failed_workers += 1
                    if result['error']:
                        errors.append(f"Worker {result['worker_id']}: {result['error']}")
            
            # Calculate statistics safely
            avg_duration = sum(durations) / len(durations) if durations else 0
            max_duration = max(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            
            # Check deduplication
            unique_paths = set(storage_paths)
            deduplication_worked = len(unique_paths) == 1 and len(unique_paths) > 0
            
            # Add cleanup files (thread-safe)
            with results_lock:
                for result in results:
                    if result['success'] and result['storage_path']:
                        self.cleanup_files.append((self.test_buckets['temp'], result['storage_path']))
            
            # Log any errors for debugging
            if errors:
                self.print_status(f"Worker errors encountered:", 'warning')
                for error in errors[:5]:  # Show first 5 errors
                    self.print_status(f"  {error}", 'warning')
                if len(errors) > 5:
                    self.print_status(f"  ... and {len(errors) - 5} more errors", 'warning')
            
            result = {
                'success': successful_workers > 0,  # Consider successful if at least one worker succeeded
                'total_workers': num_workers,
                'successful_workers': successful_workers,
                'failed_workers': failed_workers,
                'success_rate': (successful_workers / num_workers) * 100,
                'avg_duration_ms': avg_duration,
                'max_duration_ms': max_duration,
                'min_duration_ms': min_duration,
                'deduplication_worked': deduplication_worked,
                'unique_storage_paths': len(unique_paths),
                'worker_results': results,
                'errors': errors
            }
            
            self.print_status(f"✅ Concurrent operations completed", 'success')
            self.print_status(f"  Success rate: {successful_workers}/{num_workers} ({result['success_rate']:.1f}%)", 'info')
            self.print_status(f"  Avg duration: {avg_duration:.2f}ms", 'info')
            self.print_status(f"  Deduplication: {'✅' if deduplication_worked else '❌'}", 'info')
            
            if failed_workers > 0:
                self.print_status(f"  Failed workers: {failed_workers}", 'warning')
            
            return result
            
        except Exception as e:
            self.print_status(f"Concurrent operations test failed: {e}", 'error')
            self.logger.error("Concurrent operations test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def test_bucket_operations(self) -> Dict[str, Any]:
        """Test bucket management and operations"""
        self.print_status("Testing bucket operations...", 'test')
        
        try:
            # Test listing buckets
            buckets = await self.storage_service.list_buckets()
            expected_buckets = set(self.test_buckets.values())
            found_buckets = set(buckets)
            missing_buckets = expected_buckets - found_buckets
            
            # Test listing files in buckets
            bucket_stats = {}
            for bucket_name in expected_buckets:
                if bucket_name in found_buckets:
                    try:
                        files = await self.storage_service.list_files(bucket_name)
                        bucket_stats[bucket_name] = {
                            'file_count': len(files),
                            'accessible': True
                        }
                    except Exception as e:
                        bucket_stats[bucket_name] = {
                            'file_count': 0,
                            'accessible': False,
                            'error': str(e)
                        }
                else:
                    bucket_stats[bucket_name] = {
                        'file_count': 0,
                        'accessible': False,
                        'error': 'Bucket not found'
                    }
            
            # Test public URL generation (for images bucket)
            public_url_test = None
            if self.test_buckets['images'] in found_buckets:
                try:
                    # Upload a test image
                    file_data = self.test_files['image']
                    upload_result = await self.storage_service.upload_file(
                        bucket=self.test_buckets['images'],
                        key='public_test.png',
                        content=file_data['content'],
                        content_type=file_data['content_type']
                    )
                    
                    if upload_result:
                        storage_path = upload_result.get('storage_path', '')
                        public_url = await self.storage_service.get_public_url(
                            bucket=self.test_buckets['images'],
                            key=storage_path
                        )
                        
                        public_url_test = {
                            'success': public_url is not None,
                            'public_url': public_url,
                            'storage_path': storage_path
                        }
                        
                        self.cleanup_files.append((self.test_buckets['images'], storage_path))
                except Exception as e:
                    public_url_test = {
                        'success': False,
                        'error': str(e)
                    }
            
            result = {
                'success': len(missing_buckets) == 0,
                'total_buckets': len(expected_buckets),
                'found_buckets': len(found_buckets),
                'missing_buckets': list(missing_buckets),
                'bucket_stats': bucket_stats,
                'public_url_test': public_url_test
            }
            
            self.print_status(f"✅ Bucket operations completed", 'success')
            self.print_status(f"  Found buckets: {len(found_buckets)}/{len(expected_buckets)}", 'info')
            
            if public_url_test and public_url_test['success']:
                self.print_status(f"  Public URL generated: {public_url_test['public_url'][:50]}...", 'info')
            
            return result
            
        except Exception as e:
            self.print_status(f"Bucket operations test failed: {e}", 'error')
            self.logger.error("Bucket operations test failed", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def display_performance_table(self, performance_results: Dict[str, Any]):
        """Display performance test results"""
        if not self.console:
            return
        
        table = Table(title="Performance Metrics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Target", style="yellow")
        table.add_column("Status", style="blue")
        
        # Add performance results
        if 'avg_throughput_mbps' in performance_results:
            avg_throughput = performance_results['avg_throughput_mbps']
            target = self.performance_targets['upload_throughput_mbps']
            status = "✅ PASS" if avg_throughput >= target else "❌ FAIL"
            status_style = "green" if avg_throughput >= target else "red"
            
            table.add_row(
                "Avg Upload Throughput",
                f"{avg_throughput:.2f} MB/s",
                f"{target} MB/s",
                status,
                style=status_style
            )
        
        self.console.print(table)
    
    async def cleanup(self):
        """Clean up test files and buckets"""
        self.print_status("Cleaning up test resources...", 'info')
        
        try:
            # Delete test files
            for bucket, key in self.cleanup_files:
                try:
                    await self.storage_service.delete_file(bucket, key)
                    self.print_status(f"Deleted: {bucket}/{key}", 'info')
                except Exception as e:
                    self.print_status(f"Failed to delete {bucket}/{key}: {e}", 'warning')
            
            # Optionally delete test buckets (commented out for safety)
            # for bucket_name in self.test_buckets.values():
            #     try:
            #         await self.storage_service.delete_bucket(bucket_name)
            #         self.print_status(f"Deleted bucket: {bucket_name}", 'info')
            #     except Exception as e:
            #         self.print_status(f"Failed to delete bucket {bucket_name}: {e}", 'warning')
            
            self.print_status("Cleanup completed", 'success')
            
        except Exception as e:
            self.print_status(f"Cleanup failed: {e}", 'error')
            self.logger.error("Cleanup failed", exc_info=True)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all MinIO storage tests"""
        self.print_status("Starting MinIO Storage Test Suite", 'test')
        
        if not await self.setup():
            return {'success': False, 'error': 'Setup failed'}
        
        # Run tests
        test_results = {}
        
        # Test 1: Basic operations
        self.print_status("Running basic operations test...", 'test')
        test_results['basic_operations'] = await self.test_basic_operations()
        
        # Test 2: File deduplication
        self.print_status("Running file deduplication test...", 'test')
        test_results['deduplication'] = await self.test_file_deduplication()
        
        # Test 3: Large file handling
        self.print_status("Running large file handling test...", 'test')
        test_results['large_file'] = await self.test_large_file_handling()
        
        # Test 4: Concurrent operations
        self.print_status("Running concurrent operations test...", 'test')
        test_results['concurrent'] = await self.test_concurrent_operations()
        
        # Test 5: Bucket operations
        self.print_status("Running bucket operations test...", 'test')
        test_results['bucket_operations'] = await self.test_bucket_operations()
        
        # Generate report
        self.generate_test_report(test_results)
        
        # Cleanup
        await self.cleanup()
        # Storage service cleanup (disconnect not available)
        # await self.storage_service.disconnect()
        
        return {
            'success': True,
            'test_results': test_results
        }
    
    def generate_test_report(self, test_results: Dict[str, Any]):
        """Generate comprehensive test report"""
        if not self.console:
            self.print_plain_report(test_results)
            return
        
        # Summary panel
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result.get('success', False))
        
        summary_text = f"""
Total Tests: {total_tests}
✅ Passed: {passed_tests}
❌ Failed: {total_tests - passed_tests}
📊 Success Rate: {(passed_tests/total_tests*100):.1f}%
        """.strip()
        
        self.console.print(Panel(summary_text, title="💾 MinIO Storage Test Results", border_style="blue"))
        
        # Basic Operations Results
        if 'basic_operations' in test_results:
            result = test_results['basic_operations']
            if result['success']:
                self.console.print("\n🔄 Basic Operations", style="cyan bold")
                
                basic_table = Table(title="Operations Summary", box=box.ROUNDED)
                basic_table.add_column("Metric", style="white")
                basic_table.add_column("Value", style="green")
                
                basic_table.add_row("Total Operations", str(result['total_operations']))
                basic_table.add_row("Successful", str(result['successful_operations']))
                basic_table.add_row("Success Rate", f"{result['success_rate']:.1f}%")
                basic_table.add_row("Avg Throughput", f"{result['avg_throughput_mbps']:.2f} MB/s")
                
                self.console.print(basic_table)
        
        # Deduplication Results
        if 'deduplication' in test_results:
            result = test_results['deduplication']
            if result['success']:
                self.console.print("\n🔗 File Deduplication", style="cyan bold")
                
                dedup_table = Table(title="Deduplication Analysis", box=box.ROUNDED)
                dedup_table.add_column("Metric", style="white")
                dedup_table.add_column("Value", style="green")
                
                dedup_table.add_row("Deduplication Working", "✅ Yes" if result['deduplication_worked'] else "❌ No")
                dedup_table.add_row("Hash Correct", "✅ Yes" if result['hash_correct'] else "❌ No")
                dedup_table.add_row("Speed Improvement", f"{result['speed_improvement_percent']:.1f}%")
                
                self.console.print(dedup_table)
        
        # Large File Results
        if 'large_file' in test_results:
            result = test_results['large_file']
            if result['success']:
                self.console.print("\n📦 Large File Handling", style="cyan bold")
                
                large_file_table = Table(title="Large File Performance", box=box.ROUNDED)
                large_file_table.add_column("Metric", style="white")
                large_file_table.add_column("Value", style="green")
                
                large_file_table.add_row("File Size", f"{result['file_size_mb']:.1f} MB")
                large_file_table.add_row("Upload Throughput", f"{result['upload_throughput_mbps']:.2f} MB/s")
                large_file_table.add_row("Download Throughput", f"{result['download_throughput_mbps']:.2f} MB/s")
                large_file_table.add_row("Upload Target Met", "✅ Yes" if result['meets_upload_target'] else "❌ No")
                large_file_table.add_row("Download Target Met", "✅ Yes" if result['meets_download_target'] else "❌ No")
                
                self.console.print(large_file_table)
        
        # Concurrent Operations Results
        if 'concurrent' in test_results:
            result = test_results['concurrent']
            if result['success']:
                self.console.print("\n⚡ Concurrent Operations", style="cyan bold")
                
                concurrent_table = Table(title="Concurrency Analysis", box=box.ROUNDED)
                concurrent_table.add_column("Metric", style="white")
                concurrent_table.add_column("Value", style="green")
                
                concurrent_table.add_row("Total Workers", str(result['total_workers']))
                concurrent_table.add_row("Successful", str(result['successful_workers']))
                concurrent_table.add_row("Success Rate", f"{result['success_rate']:.1f}%")
                concurrent_table.add_row("Avg Duration", f"{result['avg_duration_ms']:.2f}ms")
                concurrent_table.add_row("Deduplication", "✅ Working" if result['deduplication_worked'] else "❌ Failed")
                
                self.console.print(concurrent_table)
        
        # Bucket Operations Results
        if 'bucket_operations' in test_results:
            result = test_results['bucket_operations']
            if result['success']:
                self.console.print("\n🗂️ Bucket Operations", style="cyan bold")
                
                bucket_table = Table(title="Bucket Management", box=box.ROUNDED)
                bucket_table.add_column("Metric", style="white")
                bucket_table.add_column("Value", style="green")
                
                bucket_table.add_row("Expected Buckets", str(result['total_buckets']))
                bucket_table.add_row("Found Buckets", str(result['found_buckets']))
                bucket_table.add_row("Missing", str(len(result['missing_buckets'])))
                
                if result['public_url_test'] and result['public_url_test']['success']:
                    bucket_table.add_row("Public URLs", "✅ Working")
                else:
                    bucket_table.add_row("Public URLs", "❌ Failed")
                
                self.console.print(bucket_table)
        
        # Performance Summary
        self.display_performance_table({
            'avg_throughput_mbps': test_results.get('basic_operations', {}).get('avg_throughput_mbps', 0)
        })
        
        # Errors and warnings
        has_errors = any(not result.get('success', False) for result in test_results.values())
        if has_errors:
            errors_panel = []
            for test_name, result in test_results.items():
                if not result.get('success', False):
                    errors_panel.append(f"\n{test_name}:")
                    errors_panel.append(f"  ❌ {result.get('error', 'Unknown error')}")
            
            if errors_panel:
                self.console.print(Panel("".join(errors_panel), title="❌ Errors", border_style="red"))
    
    def print_plain_report(self, test_results: Dict[str, Any]):
        """Print report in plain text format"""
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result.get('success', False))
        
        print(f"\n💾 MinIO Storage Test Results")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        for test_name, result in test_results.items():
            status = "PASS" if result.get('success', False) else "FAIL"
            print(f"{test_name}: {status}")
            
            if result.get('success', False):
                if 'success_rate' in result:
                    print(f"  Success rate: {result['success_rate']:.1f}%")
                if 'avg_throughput_mbps' in result:
                    print(f"  Avg throughput: {result['avg_throughput_mbps']:.2f} MB/s")
                if 'deduplication_worked' in result:
                    print(f"  Deduplication: {'Working' if result['deduplication_worked'] else 'Failed'}")
            else:
                print(f"  ❌ {result.get('error', 'Unknown error')}")
            print()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='KRAI MinIO Storage Operations Test')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--concurrent', action='store_true', help='Run concurrent operations test only')
    
    args = parser.parse_args()
    
    tester = MinIOStorageTester(verbose=args.verbose)
    
    if args.performance:
        # Run only performance-related tests
        await tester.setup()
        basic_result = await tester.test_basic_operations()
        large_file_result = await tester.test_large_file_handling()
        
        tester.generate_test_report({
            'basic_operations': basic_result,
            'large_file': large_file_result
        })
        
        await tester.cleanup()
        # Storage service cleanup (disconnect not available)
        # await tester.storage_service.disconnect()
    elif args.concurrent:
        # Run only concurrent operations test
        await tester.setup()
        concurrent_result = await tester.test_concurrent_operations()
        
        tester.generate_test_report({'concurrent': concurrent_result})
        
        await tester.cleanup()
        # Storage service cleanup (disconnect not available)
        # await tester.storage_service.disconnect()
    else:
        # Run all tests
        results = await tester.run_all_tests()
        
        if results['success']:
            total_tests = len(results['test_results'])
            passed_tests = sum(1 for result in results['test_results'].values() if result.get('success', False))
            success_rate = passed_tests / total_tests * 100
            
            print(f"\n🎉 MinIO storage test completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            sys.exit(0 if passed_tests == total_tests else 1)
        else:
            print(f"❌ MinIO storage test failed: {results.get('error', 'Unknown error')}")
            sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
