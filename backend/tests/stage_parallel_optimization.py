"""
Stage Parallel Optimization - Run different stages in parallel across different documents!
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Set
import logging

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

class StageParallelOptimizer:
    """
    Optimized pipeline that runs different stages in parallel across different documents
    """
    
    def __init__(self):
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        self.processors = {}
        
        # Setup logging (minimal)
        logging.basicConfig(level=logging.ERROR)  # Only show errors
        self.logger = logging.getLogger("krai.stage_parallel")
        
        # Stage queues for parallel processing
        self.stage_queues = {
            'upload': asyncio.Queue(),
            'text': asyncio.Queue(),
            'image': asyncio.Queue(),
            'classification': asyncio.Queue(),
            'metadata': asyncio.Queue(),
            'storage': asyncio.Queue(),
            'embedding': asyncio.Queue(),
            'search': asyncio.Queue()
        }
        
        # Processing stats
        self.stats = {
            'documents_uploaded': 0,
            'documents_upload_processed': 0,
            'documents_text_processed': 0,
            'documents_image_processed': 0,
            'documents_classification_processed': 0,
            'documents_metadata_processed': 0,
            'documents_storage_processed': 0,
            'documents_embedding_processed': 0,
            'documents_search_processed': 0,
            'start_time': time.time()
        }
        
    async def initialize_services(self):
        """Initialize all services"""
        print("Initializing Stage Parallel Optimizer...")
        
        # Load environment variables
        load_dotenv('../credentials.txt')
        
        # Initialize database service
        self.database_service = DatabaseService(
            supabase_url=os.getenv('SUPABASE_URL'),
            supabase_key=os.getenv('SUPABASE_ANON_KEY')
        )
        await self.database_service.connect()
        
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
        
        # Initialize AI service
        self.ai_service = AIService(ollama_url=os.getenv('OLLAMA_URL', 'http://localhost:11434'))
        await self.ai_service.connect()
        
        # Initialize config service
        self.config_service = ConfigService()
        
        # Initialize features service
        self.features_service = FeaturesService(self.ai_service, self.database_service)
        
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
        print("All services initialized - Ready for stage parallel optimization!")
    
    async def stage_worker(self, stage_name: str, worker_id: int):
        """Worker that processes documents for a specific stage"""
        print(f"Stage Worker {worker_id} started for {stage_name}")
        
        while True:
            try:
                # Get document from stage queue
                context = await asyncio.wait_for(self.stage_queues[stage_name].get(), timeout=30.0)
                
                if context is None:  # Shutdown signal
                    break
                
                # Process the document for this stage
                result = await self.processors[stage_name].process(context)
                
                # Update context with results from this stage
                if stage_name == 'upload' and result.data:
                    context.document_id = result.data.get('document_id', context.document_id)
                    context.file_hash = result.data.get('file_hash', context.file_hash)
                    context.document_type = result.data.get('document_type', context.document_type)
                
                # Update stats
                self.stats[f'documents_{stage_name}_processed'] += 1
                
                print(f"Stage {stage_name} Worker {worker_id}: Processed {os.path.basename(context.file_path)}")
                
                # If not the last stage, queue for next stage
                stage_order = ['upload', 'text', 'image', 'classification', 'metadata', 'storage', 'embedding', 'search']
                current_index = stage_order.index(stage_name)
                
                if current_index < len(stage_order) - 1:
                    next_stage = stage_order[current_index + 1]
                    await self.stage_queues[next_stage].put(context)
                else:
                    print(f"Document {os.path.basename(context.file_path)} completed all stages!")
                
                # Mark task as done
                self.stage_queues[stage_name].task_done()
                
            except asyncio.TimeoutError:
                print(f"Stage {stage_name} Worker {worker_id}: Timeout, stopping")
                break
            except Exception as e:
                print(f"Stage {stage_name} Worker {worker_id}: Error - {e}")
                continue
    
    async def start_stage_workers(self):
        """Start workers for each stage"""
        workers = []
        
        # Start multiple workers for each stage based on resource requirements
        stage_workers = {
            'upload': 2,      # Low resource
            'text': 4,        # Medium resource (CPU intensive)
            'image': 3,       # High resource (GPU intensive)
            'classification': 2,  # Medium resource (AI)
            'metadata': 2,    # Low resource
            'storage': 2,     # Low resource
            'embedding': 3,   # High resource (GPU intensive)
            'search': 2       # Medium resource
        }
        
        for stage_name, worker_count in stage_workers.items():
            for worker_id in range(worker_count):
                worker = asyncio.create_task(self.stage_worker(stage_name, worker_id + 1))
                workers.append(worker)
        
        print(f"Started {sum(stage_workers.values())} stage workers")
        return workers
    
    async def queue_documents(self, file_paths: List[str]):
        """Queue documents for processing"""
        print(f"Queuing {len(file_paths)} documents for processing...")
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
            
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
                    'file_size': file_size
                },
                file_size=file_size
            )
            
            # Queue for upload stage
            await self.stage_queues['upload'].put(context)
            self.stats['documents_uploaded'] += 1
            print(f"Queued: {filename}")
    
    async def monitor_progress(self):
        """Monitor and display progress"""
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds
            
            elapsed = time.time() - self.stats['start_time']
            
            print(f"\n--- Progress Update ({elapsed:.0f}s) ---")
            for stage, count in self.stats.items():
                if stage.startswith('documents_') and stage != 'documents_uploaded':
                    stage_name = stage.replace('documents_', '').replace('_processed', '')
                    print(f"  {stage_name}: {count} documents")
            
            # Check if all queues are empty
            all_empty = all(q.empty() for q in self.stage_queues.values())
            if all_empty:
                print("All queues empty - processing complete!")
                break
    
    async def shutdown_workers(self, workers):
        """Shutdown all workers"""
        print("Shutting down workers...")
        
        # Send shutdown signal to all queues
        for queue in self.stage_queues.values():
            await queue.put(None)  # Shutdown signal
        
        # Wait for workers to finish
        await asyncio.gather(*workers, return_exceptions=True)
        print("All workers shut down")
    
    async def process_batch_stage_parallel(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process documents with stage parallel optimization"""
        print(f"Starting stage parallel processing of {len(file_paths)} files...")
        
        # Start stage workers
        workers = await self.start_stage_workers()
        
        try:
            # Start monitoring task
            monitor_task = asyncio.create_task(self.monitor_progress())
            
            # Queue all documents
            await self.queue_documents(file_paths)
            
            # Wait for all uploads to be queued
            await self.stage_queues['upload'].join()
            
            # Wait for all stages to complete
            for stage_name in ['text', 'image', 'classification', 'metadata', 'storage', 'embedding', 'search']:
                await self.stage_queues[stage_name].join()
            
            # Cancel monitoring
            monitor_task.cancel()
            
        finally:
            # Shutdown workers
            await self.shutdown_workers(workers)
        
        # Calculate final statistics
        total_time = time.time() - self.stats['start_time']
        
        return {
            'success': True,
            'total_files': len(file_paths),
            'duration': total_time,
            'stats': self.stats
        }
    
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
    
    def print_optimization_summary(self, results: Dict[str, Any]):
        """Print stage parallel optimization summary"""
        print(f"\n{'='*80}")
        print(f"STAGE PARALLEL OPTIMIZATION COMPLETE!")
        print(f"{'='*80}")
        print(f"Total Files: {results['total_files']}")
        print(f"Duration: {results['duration']:.1f}s ({results['duration']/60:.1f}m)")
        print(f"Average per File: {results['duration']/results['total_files']:.1f}s")
        print(f"")
        
        print("Stage Processing Stats:")
        for stage, count in results['stats'].items():
            if stage.startswith('documents_') and stage != 'documents_uploaded':
                stage_name = stage.replace('documents_', '').replace('_processed', '')
                print(f"  {stage_name}: {count} documents")
        
        print(f"{'='*80}")

async def main():
    """Main function for stage parallel optimization"""
    print("Stage Parallel Optimization Pipeline")
    print("="*50)
    print("This pipeline runs different stages in parallel across documents!")
    print("Maximum CPU/GPU utilization with stage-level parallelization!")
    print("="*50)
    
    # Initialize pipeline
    pipeline = StageParallelOptimizer()
    await pipeline.initialize_services()
    
    # Find PDF files
    pdf_directory = "../service_documents"
    
    # Ask user how many files to process
    print("\nOptions:")
    print("1. Test with 3 files (quick test)")
    print("2. Test with 5 files (medium test)")
    print("3. Process all files (full batch)")
    
    choice = input("\nChoose option (1/2/3): ").strip()
    
    if choice == "1":
        pdf_files = pipeline.find_pdf_files(pdf_directory, limit=3)
    elif choice == "2":
        pdf_files = pipeline.find_pdf_files(pdf_directory, limit=5)
    elif choice == "3":
        pdf_files = pipeline.find_pdf_files(pdf_directory)
    else:
        pdf_files = pipeline.find_pdf_files(pdf_directory, limit=3)
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return
    
    print(f"\nSelected {len(pdf_files)} files for stage parallel processing")
    print("This will maximize hardware utilization!")
    
    # Ask user for confirmation
    response = input(f"\nStart stage parallel processing? (y/n): ").lower().strip()
    if response != 'y':
        print("Processing cancelled.")
        return
    
    # Process batch with stage parallel optimization
    results = await pipeline.process_batch_stage_parallel(pdf_files)
    
    # Print summary
    pipeline.print_optimization_summary(results)

if __name__ == "__main__":
    asyncio.run(main())
