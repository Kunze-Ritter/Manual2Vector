"""
Optimized Batch Processing Pipeline with GPU/NPU acceleration
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from enhanced_progress_tracker import EnhancedProgressTracker

# Import optimization modules
from optimizations.gpu_npu_optimization import hardware_accelerator

# Import all services and processors
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from services.ai_service import AIService
from services.config_service import ConfigService
from services.features_service import FeaturesService

from processors.upload_processor import UploadProcessor
from processors.text_processor_optimized import OptimizedTextProcessor
from processors.image_processor import ImageProcessor
from processors.classification_processor import ClassificationProcessor
from processors.metadata_processor import MetadataProcessor
from processors.storage_processor import StorageProcessor
from processors.embedding_processor import EmbeddingProcessor
from processors.search_processor import SearchProcessor
from processors.link_extraction_processor import LinkExtractionProcessor

from core.base_processor import ProcessingContext

class OptimizedBatchPipeline:
    """
    Optimized batch processing pipeline with GPU/NPU acceleration
    """
    
    def __init__(self):
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        self.processors = {}
        self.progress_tracker = None
        
        # Get hardware optimization config
        self.hardware_config = hardware_accelerator.get_optimization_config()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("krai.optimized_batch")
        
    async def initialize_services(self):
        """Initialize all services with hardware optimization"""
        self.logger.info("Initializing optimized batch processing services...")
        
        # Load environment variables
        load_dotenv('../credentials.txt')
        
        # Initialize database service
        self.database_service = DatabaseService(
            supabase_url=os.getenv('SUPABASE_URL'),
            supabase_key=os.getenv('SUPABASE_ANON_KEY')
        )
        await self.database_service.connect()
        self.logger.info("Database service connected")
        
        # Initialize object storage service
        self.storage_service = ObjectStorageService(
            r2_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
            r2_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
            r2_endpoint_url=os.getenv('R2_ENDPOINT_URL'),
            r2_public_url_documents=os.getenv('R2_PUBLIC_URL_DOCUMENTS'),
            r2_public_url_error=os.getenv('R2_PUBLIC_URL_ERROR'),
            r2_public_url_parts=os.getenv('R2_PUBLIC_URL_PARTS')
        )
        await self.storage_service.connect()
        self.logger.info("Object storage service connected")
        
        # Initialize AI service
        self.ai_service = AIService(ollama_url=os.getenv('OLLAMA_URL', 'http://localhost:11434'))
        await self.ai_service.connect()
        self.logger.info("AI service connected")
        
        # Initialize config service
        self.config_service = ConfigService()
        self.logger.info("Config service initialized")
        
        # Initialize features service
        self.features_service = FeaturesService(self.ai_service, self.database_service)
        self.logger.info("Features service initialized")
        
        # Initialize all processors with hardware optimization
        self.processors = {
            'upload': UploadProcessor(self.database_service),
            'text': OptimizedTextProcessor(self.database_service, self.config_service),
            'image': ImageProcessor(self.database_service, self.storage_service, self.ai_service),
            'classification': ClassificationProcessor(self.database_service, self.ai_service, self.features_service),
            'metadata': MetadataProcessor(self.database_service, self.config_service),
            'storage': StorageProcessor(self.database_service, self.storage_service),
            'embedding': EmbeddingProcessor(self.database_service, self.ai_service),
            'search': SearchProcessor(self.database_service, self.ai_service),
            'links': LinkExtractionProcessor(self.database_service)  # New processor
        }
        self.logger.info("All processors initialized with hardware optimization")
    
    async def process_document_with_optimization(self, file_path: str) -> Dict[str, Any]:
        """Process a single document with hardware optimization"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            # Get file information
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            # Create processing context
            context = ProcessingContext(
                file_path=file_path,
                document_id="",
                file_hash="",
                document_type="",
                processing_config={
                    'filename': filename,
                    'file_size': file_size,
                    'hardware_config': self.hardware_config
                },
                file_size=file_size
            )
            
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.set_current_file(filename, file_size)
            
            results = {}
            stage_number = 1
            total_stages = 9  # Added link extraction
            
            # Stage 1: Upload Processor
            if self.progress_tracker:
                self.progress_tracker.update_stage("Upload", stage_number, total_stages)
            result1 = await self.processors['upload'].process(context)
            context.document_id = result1.data.get('document_id')
            context.file_hash = result1.data.get('file_hash', '')
            context.document_type = result1.data.get('document_type', '')
            results['upload'] = result1
            stage_number += 1
            
            # Stage 2: Text Processor (Optimized)
            if self.progress_tracker:
                self.progress_tracker.update_stage("Text Processing", stage_number, total_stages)
            result2 = await self.processors['text'].process(context)
            results['text'] = result2
            stage_number += 1
            
            # Stage 3: Image Processor
            if self.progress_tracker:
                self.progress_tracker.update_stage("Image Processing", stage_number, total_stages)
            result3 = await self.processors['image'].process(context)
            results['image'] = result3
            stage_number += 1
            
            # Stage 4: Classification Processor
            if self.progress_tracker:
                self.progress_tracker.update_stage("Classification", stage_number, total_stages)
            result4 = await self.processors['classification'].process(context)
            results['classification'] = result4
            stage_number += 1
            
            # Stage 5: Metadata Processor
            if self.progress_tracker:
                self.progress_tracker.update_stage("Metadata Extraction", stage_number, total_stages)
            result5 = await self.processors['metadata'].process(context)
            results['metadata'] = result5
            stage_number += 1
            
            # Stage 6: Link Extraction Processor (NEW)
            if self.progress_tracker:
                self.progress_tracker.update_stage("Link Extraction", stage_number, total_stages)
            result6 = await self.processors['links'].process(context)
            results['links'] = result6
            stage_number += 1
            
            # Stage 7: Storage Processor
            if self.progress_tracker:
                self.progress_tracker.update_stage("Storage", stage_number, total_stages)
            result7 = await self.processors['storage'].process(context)
            results['storage'] = result7
            stage_number += 1
            
            # Stage 8: Embedding Processor
            if self.progress_tracker:
                self.progress_tracker.update_stage("Embeddings", stage_number, total_stages)
            result8 = await self.processors['embedding'].process(context)
            results['embedding'] = result8
            stage_number += 1
            
            # Stage 9: Search Processor
            if self.progress_tracker:
                self.progress_tracker.update_stage("Search Index", stage_number, total_stages)
            result9 = await self.processors['search'].process(context)
            results['search'] = result9
            
            return {
                'success': True,
                'document_id': context.document_id,
                'filename': filename,
                'file_size': file_size,
                'results': results,
                'hardware_optimization': self.hardware_config
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'filename': os.path.basename(file_path)
            }
    
    async def process_batch_optimized(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple documents with hardware optimization"""
        self.logger.info(f"\nStarting optimized batch processing of {len(file_paths)} files...")
        self.logger.info(f"Hardware Configuration:")
        self.logger.info(f"  GPU Available: {self.hardware_config['gpu_available']}")
        self.logger.info(f"  NPU Available: {self.hardware_config['npu_available']}")
        self.logger.info(f"  Optimization Level: {self.hardware_config['optimization_level']}")
        
        if self.hardware_config['npu_available']:
            self.logger.info(f"  NPU Type: {self.hardware_config['npu_type']}")
        
        self.logger.info(f"Optimal Worker Counts:")
        for task_type, count in self.hardware_config['optimal_workers'].items():
            self.logger.info(f"  {task_type}: {count}")
        
        print("="*80)
        
        # Initialize progress tracker
        self.progress_tracker = EnhancedProgressTracker(total_files=len(file_paths))
        
        results = {
            'successful': [],
            'failed': [],
            'total_files': len(file_paths),
            'start_time': time.time(),
            'hardware_config': self.hardware_config
        }
        
        try:
            # Process files with hardware optimization
            for file_path in file_paths:
                try:
                    result = await self.process_document_with_optimization(file_path)
                    if result['success']:
                        results['successful'].append(result)
                    else:
                        results['failed'].append(result)
                except Exception as e:
                    results['failed'].append({
                        'success': False,
                        'error': str(e),
                        'filename': os.path.basename(file_path)
                    })
        
        finally:
            # Stop progress tracker
            if self.progress_tracker:
                self.progress_tracker.stop()
        
        # Calculate final statistics
        results['end_time'] = time.time()
        results['duration'] = results['end_time'] - results['start_time']
        results['success_rate'] = len(results['successful']) / len(file_paths) * 100
        
        return results
    
    def find_pdf_files(self, directory: str) -> List[str]:
        """Find all PDF files in directory"""
        pdf_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        return sorted(pdf_files)
    
    def print_optimized_batch_summary(self, results: Dict[str, Any]):
        """Print detailed optimized batch processing summary"""
        print(f"\n{'='*80}")
        print(f"OPTIMIZED BATCH PROCESSING SUMMARY")
        print(f"{'='*80}")
        print(f"Total Files: {results['total_files']}")
        print(f"Successful: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print(f"Total Duration: {results['duration']:.1f}s ({results['duration']/60:.1f}m)")
        print(f"Average per File: {results['duration']/results['total_files']:.1f}s")
        
        # Hardware optimization summary
        hw_config = results['hardware_config']
        print(f"")
        print(f"HARDWARE OPTIMIZATION:")
        print(f"  GPU Acceleration: {'Enabled' if hw_config['gpu_available'] else 'Disabled'}")
        print(f"  NPU Acceleration: {'Enabled' if hw_config['npu_available'] else 'Disabled'}")
        if hw_config['npu_available']:
            print(f"  NPU Type: {hw_config['npu_type']}")
        print(f"  Optimization Level: {hw_config['optimization_level']}")
        print(f"")
        
        if results['successful']:
            print(f"SUCCESSFUL FILES:")
            for result in results['successful']:
                file_size_mb = result['file_size'] / (1024 * 1024)
                print(f"  [OK] {result['filename']} ({file_size_mb:.1f}MB) - {result['document_id']}")
        
        if results['failed']:
            print(f"FAILED FILES:")
            for result in results['failed']:
                print(f"  [FAIL] {result['filename']} - {result['error']}")
        
        print(f"{'='*80}")

async def main():
    """Main function for optimized batch processing"""
    print("KR-AI-Engine Optimized Batch Processing Pipeline")
    print("="*60)
    
    # Initialize pipeline
    pipeline = OptimizedBatchPipeline()
    await pipeline.initialize_services()
    
    # Find PDF files in service_documents directory
    pdf_directory = "../service_documents"
    pdf_files = pipeline.find_pdf_files(pdf_directory)
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return
    
    print(f"Found {len(pdf_files)} PDF files:")
    total_size = 0
    for i, file_path in enumerate(pdf_files, 1):
        file_size = os.path.getsize(file_path)
        total_size += file_size
        file_size_mb = file_size / (1024 * 1024)
        print(f"  {i:2d}. {os.path.basename(file_path)} ({file_size_mb:.1f}MB)")
    
    total_size_gb = total_size / (1024 * 1024 * 1024)
    print(f"\nTotal size: {total_size_gb:.1f}GB")
    print(f"Estimated processing time: {len(pdf_files) * 2:.0f} minutes")
    
    # Ask user for confirmation
    response = input(f"\nProcess all {len(pdf_files)} files? (y/n): ").lower().strip()
    if response != 'y':
        print("Processing cancelled.")
        return
    
    # Process batch with optimization
    results = await pipeline.process_batch_optimized(pdf_files)
    
    # Print summary
    pipeline.print_optimized_batch_summary(results)

if __name__ == "__main__":
    asyncio.run(main())
