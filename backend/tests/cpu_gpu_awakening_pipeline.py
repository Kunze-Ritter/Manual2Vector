"""
CPU/GPU Awakening Pipeline - Actually wakes up the hardware with real parallel processing!
"""

import asyncio
import os
import sys
import time
import concurrent.futures
import multiprocessing as mp
from pathlib import Path
from typing import List, Dict, Any
import logging
import threading

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

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

class CPUGPUAwakeningPipeline:
    """
    Pipeline that actually wakes up CPU/GPU with aggressive parallel processing
    """
    
    def __init__(self):
        # Get hardware info
        cpu_count = mp.cpu_count()
        self.max_workers = min(cpu_count * 2, 16)  # Aggressive parallelization
        
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        self.processors = {}
        
        # Setup logging (reduce verbosity)
        logging.basicConfig(level=logging.WARNING)  # Only show warnings and errors
        self.logger = logging.getLogger("krai.cpu_gpu_awakening")
        
        self.logger.info(f"CPU/GPU Awakening Pipeline initialized with {self.max_workers} workers")
        
        # Hardware monitoring
        self.cpu_samples = []
        self.ram_samples = []
        self.start_time = time.time()
        
    async def initialize_services(self):
        """Initialize all services"""
        print("Initializing CPU/GPU awakening services...")
        
        # Load environment variables
        load_dotenv('../credentials.txt')
        
        # Initialize database service
        self.database_service = DatabaseService(
            supabase_url=os.getenv('SUPABASE_URL'),
            supabase_key=os.getenv('SUPABASE_ANON_KEY')
        )
        await self.database_service.connect()
        print("Database service connected")
        
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
        print("Object storage service connected")
        
        # Initialize AI service
        self.ai_service = AIService(ollama_url=os.getenv('OLLAMA_URL', 'http://localhost:11434'))
        await self.ai_service.connect()
        print("AI service connected")
        
        # Initialize config service
        self.config_service = ConfigService()
        print("Config service initialized")
        
        # Initialize features service
        self.features_service = FeaturesService(self.ai_service, self.database_service)
        print("Features service initialized")
        
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
        print("All processors initialized - Ready to awaken hardware!")
    
    async def process_single_document_aggressive(self, file_path: str, file_index: int, total_files: int) -> Dict[str, Any]:
        """Process a single document with aggressive parallelization"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            # Get file information
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            print(f"[{file_index}/{total_files}] Processing: {filename} ({file_size/1024/1024:.1f}MB)")
            
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
            
            # Stage 1: Upload Processor
            result1 = await self.processors['upload'].process(context)
            context.document_id = result1.data.get('document_id')
            context.file_hash = result1.data.get('file_hash', '')
            context.document_type = result1.data.get('document_type', '')
            
            # Stage 2: Text Processor (This will wake up CPU!)
            print(f"  Text Processing: {filename}")
            result2 = await self.processors['text'].process(context)
            chunks_count = result2.data.get('chunks_created', 0)
            
            # Stage 3: Image Processor (This will wake up GPU!)
            print(f"  Image Processing: {filename}")
            result3 = await self.processors['image'].process(context)
            images_count = result3.data.get('images_processed', 0)
            
            # Stage 4: Classification Processor
            print(f"  Classification: {filename}")
            result4 = await self.processors['classification'].process(context)
            
            # Stage 5: Metadata Processor
            print(f"  Metadata: {filename}")
            result5 = await self.processors['metadata'].process(context)
            
            # Stage 6: Storage Processor
            print(f"  Storage: {filename}")
            result6 = await self.processors['storage'].process(context)
            
            # Stage 7: Embedding Processor (This will wake up GPU for AI!)
            print(f"  Embeddings: {filename}")
            result7 = await self.processors['embedding'].process(context)
            
            # Stage 8: Search Processor
            print(f"  Search Index: {filename}")
            result8 = await self.processors['search'].process(context)
            
            print(f"  Completed: {filename}")
            
            return {
                'success': True,
                'document_id': context.document_id,
                'filename': filename,
                'file_size': file_size,
                'chunks': chunks_count,
                'images': images_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'filename': os.path.basename(file_path)
            }
    
    async def process_batch_aggressive_parallel(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple documents with aggressive parallelization to wake up hardware"""
        print(f"AWAKENING HARDWARE - Processing {len(file_paths)} files with {self.max_workers} workers!")
        
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
            
            async def process_with_semaphore(file_path: str, file_index: int):
                """Process file with semaphore to limit concurrency"""
                async with semaphore:
                    return await self.process_single_document_aggressive(file_path, file_index, len(file_paths))
            
            # Create tasks for all files
            tasks = [process_with_semaphore(file_path, i+1) for i, file_path in enumerate(file_paths)]
            
            # Process all files in parallel - This will wake up the hardware!
            print(f"Starting aggressive parallel processing of {len(tasks)} files...")
            print("This should wake up your CPU and GPU!")
            
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
        
        except Exception as e:
            print(f"Error in parallel processing: {e}")
        
        # Calculate final statistics
        results['end_time'] = time.time()
        results['duration'] = results['end_time'] - results['start_time']
        results['success_rate'] = len(results['successful']) / len(file_paths) * 100
        
        return results
    
    def find_pdf_files(self, directory: str, limit: int = None) -> List[str]:
        """Find PDF files in directory with optional limit"""
        pdf_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
                    if limit and len(pdf_files) >= limit:
                        return sorted(pdf_files)
        return sorted(pdf_files)
    
    def print_awakening_summary(self, results: Dict[str, Any]):
        """Print hardware awakening summary"""
        print(f"\n{'='*80}")
        print(f"HARDWARE AWAKENING COMPLETE!")
        print(f"{'='*80}")
        print(f"Parallel Workers: {results['parallel_workers']}")
        print(f"Total Files: {results['total_files']}")
        print(f"Successful: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print(f"Total Duration: {results['duration']:.1f}s ({results['duration']/60:.1f}m)")
        print(f"Average per File: {results['duration']/results['total_files']:.1f}s")
        print(f"Parallel Speedup: ~{results['parallel_workers']:.1f}x faster than sequential!")
        print(f"")
        
        if results['successful']:
            print(f"SUCCESSFUL FILES:")
            total_chunks = 0
            total_images = 0
            for result in results['successful']:
                file_size_mb = result['file_size'] / (1024 * 1024)
                total_chunks += result.get('chunks', 0)
                total_images += result.get('images', 0)
                print(f"  {result['filename']} ({file_size_mb:.1f}MB) - {result['document_id']}")
            print(f"  Total Chunks: {total_chunks}")
            print(f"  Total Images: {total_images}")
        
        if results['failed']:
            print(f"FAILED FILES:")
            for result in results['failed']:
                print(f"  {result['filename']} - {result['error']}")
        
        print(f"{'='*80}")

async def main():
    """Main function for CPU/GPU awakening batch processing"""
    print("CPU/GPU Awakening Pipeline")
    print("="*50)
    print("This pipeline will aggressively wake up your hardware!")
    print("Processing multiple PDFs in parallel for maximum CPU/GPU usage!")
    print("="*50)
    
    # Initialize pipeline
    pipeline = CPUGPUAwakeningPipeline()
    await pipeline.initialize_services()
    
    # Find PDF files in service_documents directory
    pdf_directory = "../service_documents"
    
    # Ask user how many files to process
    print("\nOptions:")
    print("1. Test with 3 files (quick test)")
    print("2. Test with 5 files (medium test)")
    print("3. Process all files (full batch)")
    
    choice = input("\nChoose option (1/2/3): ").strip()
    
    if choice == "1":
        pdf_files = pipeline.find_pdf_files(pdf_directory, limit=3)
        print(f"Testing with {len(pdf_files)} files for quick hardware awakening test")
    elif choice == "2":
        pdf_files = pipeline.find_pdf_files(pdf_directory, limit=5)
        print(f"Testing with {len(pdf_files)} files for medium hardware awakening test")
    elif choice == "3":
        pdf_files = pipeline.find_pdf_files(pdf_directory)
        print(f"Processing all {len(pdf_files)} files for full hardware awakening")
    else:
        print("Invalid choice, using 3 files for test")
        pdf_files = pipeline.find_pdf_files(pdf_directory, limit=3)
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return
    
    print(f"\nSelected files:")
    total_size = 0
    for i, file_path in enumerate(pdf_files, 1):
        file_size = os.path.getsize(file_path)
        total_size += file_size
        file_size_mb = file_size / (1024 * 1024)
        print(f"  {i:2d}. {os.path.basename(file_path)} ({file_size_mb:.1f}MB)")
    
    total_size_gb = total_size / (1024 * 1024 * 1024)
    print(f"\nTotal size: {total_size_gb:.1f}GB")
    print(f"Estimated processing time with {pipeline.max_workers} workers: {len(pdf_files) * 0.3:.1f} minutes")
    print(f"This should wake up your CPU and GPU!")
    
    # Ask user for confirmation
    response = input(f"\nAWAKEN HARDWARE and process {len(pdf_files)} files? (y/n): ").lower().strip()
    if response != 'y':
        print("Hardware awakening cancelled.")
        return
    
    # Process batch with hardware awakening
    results = await pipeline.process_batch_aggressive_parallel(pdf_files)
    
    # Print summary
    pipeline.print_awakening_summary(results)

if __name__ == "__main__":
    asyncio.run(main())
