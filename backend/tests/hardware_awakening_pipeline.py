"""
Hardware Awakening Pipeline - Wake up CPU/GPU/NPU and process multiple PDFs in parallel!
"""

import asyncio
import os
import sys
import time
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any
import logging
import multiprocessing as mp

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from perfect_progress_tracker import PerfectProgressTracker

# Import services
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

from core.base_processor import ProcessingContext

class HardwareAwakeningPipeline:
    """
    Pipeline that actually wakes up and uses CPU/GPU/NPU for parallel processing
    """
    
    def __init__(self, max_workers: int = None):
        # Determine optimal worker count based on hardware
        cpu_count = mp.cpu_count()
        self.max_workers = max_workers or min(cpu_count, 8)  # Cap at 8 for stability
        
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        self.processors = {}
        self.progress_tracker = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("krai.hardware_awakening")
        
        self.logger.info(f"Hardware Awakening Pipeline initialized with {self.max_workers} workers")
    
    async def initialize_services(self):
        """Initialize all services"""
        self.logger.info("Initializing hardware awakening services...")
        
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
        
        # Initialize all processors
        self.processors = {
            'upload': UploadProcessor(self.database_service),
            'text': OptimizedTextProcessor(self.database_service, self.config_service),
            'image': ImageProcessor(self.database_service, self.storage_service, self.ai_service),
            'classification': ClassificationProcessor(self.database_service, self.ai_service, self.features_service),
            'metadata': MetadataProcessor(self.database_service, self.config_service),
            'storage': StorageProcessor(self.database_service, self.storage_service),
            'embedding': EmbeddingProcessor(self.database_service, self.ai_service),
            'search': SearchProcessor(self.database_service, self.ai_service)
        }
        self.logger.info("All processors initialized - Hardware ready to awaken!")
    
    async def process_single_document_parallel(self, file_path: str, progress_tracker: PerfectProgressTracker) -> Dict[str, Any]:
        """Process a single document with full pipeline"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            # Get file information
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            # Set file info in progress tracker
            progress_tracker.set_current_file(filename, file_size)
            
            # Create processing context
            context = ProcessingContext(
                file_path=file_path,
                document_id="",
                file_hash="",
                document_type="",
                processing_config={
                    'filename': filename,
                    'file_size': file_size
                },
                file_size=file_size
            )
            
            results = {}
            stage_number = 1
            total_stages = 8
            
            # Stage 1: Upload Processor
            progress_tracker.update_stage("Upload", 0)
            result1 = await self.processors['upload'].process(context)
            context.document_id = result1.data.get('document_id')
            context.file_hash = result1.data.get('file_hash', '')
            context.document_type = result1.data.get('document_type', '')
            results['upload'] = result1
            progress_tracker.update_stage("Upload", 100)
            stage_number += 1
            
            # Stage 2: Text Processor (Optimized) - This will wake up CPU!
            progress_tracker.update_stage("Text Processing", 0)
            result2 = await self.processors['text'].process(context)
            results['text'] = result2
            chunks_count = result2.data.get('chunks_created', 0)
            progress_tracker.update_chunks(chunks_count)
            progress_tracker.update_stage("Text Processing", 100)
            stage_number += 1
            
            # Stage 3: Image Processor - This will wake up GPU!
            progress_tracker.update_stage("Image Processing", 0)
            result3 = await self.processors['image'].process(context)
            results['image'] = result3
            images_count = result3.data.get('images_processed', 0)
            progress_tracker.update_images(images_count)
            progress_tracker.update_stage("Image Processing", 100)
            stage_number += 1
            
            # Stage 4: Classification Processor
            progress_tracker.update_stage("Classification", 0)
            result4 = await self.processors['classification'].process(context)
            results['classification'] = result4
            progress_tracker.update_stage("Classification", 100)
            stage_number += 1
            
            # Stage 5: Metadata Processor
            progress_tracker.update_stage("Metadata Extraction", 0)
            result5 = await self.processors['metadata'].process(context)
            results['metadata'] = result5
            progress_tracker.update_stage("Metadata Extraction", 100)
            stage_number += 1
            
            # Stage 6: Storage Processor
            progress_tracker.update_stage("Storage", 0)
            result6 = await self.processors['storage'].process(context)
            results['storage'] = result6
            progress_tracker.update_stage("Storage", 100)
            stage_number += 1
            
            # Stage 7: Embedding Processor - This will wake up GPU for AI!
            progress_tracker.update_stage("Embeddings", 0)
            result7 = await self.processors['embedding'].process(context)
            results['embedding'] = result7
            progress_tracker.update_stage("Embeddings", 100)
            stage_number += 1
            
            # Stage 8: Search Processor
            progress_tracker.update_stage("Search Index", 0)
            result8 = await self.processors['search'].process(context)
            results['search'] = result8
            progress_tracker.update_stage("Search Index", 100)
            
            # Mark file as completed
            progress_tracker.file_completed()
            
            return {
                'success': True,
                'document_id': context.document_id,
                'filename': filename,
                'file_size': file_size,
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'filename': os.path.basename(file_path)
            }
    
    async def process_batch_parallel_awakening(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple documents in parallel to awaken hardware"""
        self.logger.info(f"AWAKENING HARDWARE - Processing {len(file_paths)} files in parallel!")
        self.logger.info(f"Using {self.max_workers} parallel workers to maximize CPU/GPU usage")
        
        # Initialize perfect progress tracker
        self.progress_tracker = PerfectProgressTracker(total_files=len(file_paths))
        
        results = {
            'successful': [],
            'failed': [],
            'total_files': len(file_paths),
            'start_time': time.time(),
            'parallel_workers': self.max_workers
        }
        
        try:
            # Create semaphore to limit concurrent processing
            semaphore = asyncio.Semaphore(self.max_workers)
            
            async def process_with_semaphore(file_path: str):
                """Process file with semaphore to limit concurrency"""
                async with semaphore:
                    return await self.process_single_document_parallel(file_path, self.progress_tracker)
            
            # Create tasks for all files
            tasks = [process_with_semaphore(file_path) for file_path in file_paths]
            
            # Process all files in parallel
            self.logger.info(f"Starting parallel processing of {len(tasks)} files...")
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(completed_tasks):
                if isinstance(result, Exception):
                    results['failed'].append({
                        'success': False,
                        'error': str(result),
                        'filename': os.path.basename(file_paths[i])
                    })
                elif result['success']:
                    results['successful'].append(result)
                else:
                    results['failed'].append(result)
        
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
    
    def print_hardware_awakening_summary(self, results: Dict[str, Any]):
        """Print hardware awakening summary"""
        print(f"\n{'='*120}")
        print(f"🔥 HARDWARE AWAKENING COMPLETE!")
        print(f"{'='*120}")
        print(f"⚡ Parallel Workers: {results['parallel_workers']}")
        print(f"📊 Total Files: {results['total_files']}")
        print(f"✅ Successful: {len(results['successful'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        print(f"📈 Success Rate: {results['success_rate']:.1f}%")
        print(f"⏱️  Total Duration: {results['duration']:.1f}s ({results['duration']/60:.1f}m)")
        print(f"🚀 Average per File: {results['duration']/results['total_files']:.1f}s")
        print(f"⚡ Parallel Speedup: ~{results['parallel_workers']:.1f}x faster than sequential!")
        print(f"")
        
        if results['successful']:
            print(f"✅ SUCCESSFUL FILES:")
            for result in results['successful']:
                file_size_mb = result['file_size'] / (1024 * 1024)
                print(f"   🎯 {result['filename']} ({file_size_mb:.1f}MB) - {result['document_id']}")
        
        if results['failed']:
            print(f"❌ FAILED FILES:")
            for result in results['failed']:
                print(f"   💥 {result['filename']} - {result['error']}")
        
        print(f"{'='*120}")

async def main():
    """Main function for hardware awakening batch processing"""
    print("KR-AI-Engine Hardware Awakening Pipeline")
    print("="*60)
    print("This pipeline will wake up your CPU/GPU/NPU!")
    print("Processing multiple PDFs in parallel for maximum performance!")
    print("="*60)
    
    # Initialize pipeline
    pipeline = HardwareAwakeningPipeline(max_workers=6)  # Use 6 workers to wake up hardware
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
        print(f"   {i:2d}. {os.path.basename(file_path)} ({file_size_mb:.1f}MB)")
    
    total_size_gb = total_size / (1024 * 1024 * 1024)
    print(f"\nTotal size: {total_size_gb:.1f}GB")
    print(f"Estimated processing time with {pipeline.max_workers} workers: {len(pdf_files) * 0.5:.0f} minutes")
    print(f"This will wake up your hardware and use all available CPU/GPU power!")
    
    # Ask user for confirmation
    response = input(f"\nAWAKEN HARDWARE and process all {len(pdf_files)} files? (y/n): ").lower().strip()
    if response != 'y':
        print("Hardware awakening cancelled.")
        return
    
    # Process batch with hardware awakening
    results = await pipeline.process_batch_parallel_awakening(pdf_files)
    
    # Print summary
    pipeline.print_hardware_awakening_summary(results)

if __name__ == "__main__":
    asyncio.run(main())
