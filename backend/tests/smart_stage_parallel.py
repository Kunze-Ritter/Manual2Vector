"""
Smart Stage Parallel Pipeline - Different PDFs in different stages simultaneously!
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import multiprocessing as mp

# Import simple monitoring
try:
    from simple_monitor import update_stage_status, start_monitoring, print_status
except ImportError:
    def update_stage_status(stage_name, doc_name="", completed=False):
        pass
    def start_monitoring(total_docs):
        pass
    def print_status():
        pass

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

class SmartStageParallelPipeline:
    """
    Smart pipeline that runs different PDFs in different stages simultaneously
    PDF1→Stage1, PDF2→Stage2, PDF3→Stage3, etc.
    """
    
    def __init__(self):
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        self.processors = {}
        
        # Setup logging (minimal)
        logging.basicConfig(level=logging.ERROR)
        self.logger = logging.getLogger("krai.smart_stage_parallel")
        
        # Stage queues - each stage has its own queue
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
            'documents_processed': 0,
            'total_chunks': 0,
            'total_images': 0,
            'total_links': 0,
            'start_time': time.time(),
            'stage_stats': {
                'upload': 0,
                'text': 0,
                'image': 0,
                'classification': 0,
                'metadata': 0,
                'storage': 0,
                'embedding': 0,
                'search': 0
            }
        }
        
        self.logger.info("Smart Stage Parallel Pipeline initialized")
        
    async def initialize_services(self):
        """Initialize all services"""
        print("Initializing Smart Stage Parallel Pipeline...")
        
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
        print("All services initialized - Ready for smart stage parallel processing!")
    
    async def stage_worker(self, stage_name: str, worker_id: int):
        """Worker that processes documents for a specific stage"""
        print(f"Stage Worker {worker_id} started for {stage_name}")
        
        while True:
            try:
                # Get document from stage queue
                context = await asyncio.wait_for(self.stage_queues[stage_name].get(), timeout=60.0)
                
                if context is None:  # Shutdown signal
                    break
                
                filename = os.path.basename(context.file_path)
                print(f"[{stage_name.upper()}] Processing: {filename}")
                
                # Update monitoring
                update_stage_status(stage_name, filename, False)
                
                # Process the document for this stage
                result = await self.processors[stage_name].process(context)
                
                # Update context with results from this stage
                if result.data:
                    context.document_id = result.data.get('document_id', context.document_id)
                    context.file_hash = result.data.get('file_hash', context.file_hash)
                    context.document_type = result.data.get('document_type', context.document_type)
                
                # Update stats
                self.stats['stage_stats'][stage_name] += 1
                
                # Update global stats
                if stage_name == 'text' and result.data:
                    chunks_count = result.data.get('chunks_created', 0)
                    self.stats['total_chunks'] += chunks_count
                elif stage_name == 'image' and result.data:
                    images_count = result.data.get('images_processed', 0)
                    self.stats['total_images'] += images_count
                
                print(f"[{stage_name.upper()}] Completed: {filename}")
                
                # Update monitoring - stage completed
                update_stage_status(stage_name, filename, True)
                
                # If not the last stage, queue for next stage
                stage_order = ['upload', 'text', 'image', 'classification', 'metadata', 'storage', 'embedding', 'search']
                current_index = stage_order.index(stage_name)
                
                if current_index < len(stage_order) - 1:
                    next_stage = stage_order[current_index + 1]
                    await self.stage_queues[next_stage].put(context)
                    print(f"[{stage_name.upper()}] Queued {filename} for {next_stage}")
                else:
                    self.stats['documents_processed'] += 1
                    print(f"[COMPLETE] {filename} finished all stages!")
                
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
        
        # Start workers for each stage based on resource requirements
        stage_workers = {
            'upload': 2,      # Low resource
            'text': 3,        # Medium resource (CPU intensive)
            'image': 2,       # High resource (GPU intensive)
            'classification': 2,  # Medium resource (AI)
            'metadata': 2,    # Low resource
            'storage': 2,     # Low resource
            'embedding': 2,   # High resource (GPU intensive)
            'search': 2       # Medium resource
        }
        
        for stage_name, worker_count in stage_workers.items():
            for worker_id in range(worker_count):
                worker = asyncio.create_task(self.stage_worker(stage_name, worker_id + 1))
                workers.append(worker)
        
        print(f"Started {sum(stage_workers.values())} stage workers")
        return workers
    
    async def smart_distribute_documents(self, file_paths: List[str]):
        """Smart distribution: Start documents in different stages"""
        print(f"Smart distributing {len(file_paths)} documents across stages...")
        
        stage_order = ['upload', 'text', 'image', 'classification', 'metadata', 'storage', 'embedding', 'search']
        
        # ALWAYS start with upload stage first to get document_id
        for i, file_path in enumerate(file_paths):
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
            
            # ALWAYS start with upload stage to get document_id
            print(f"Document {i+1}: {filename} starting at upload")
            await self.stage_queues['upload'].put(context)
    
    async def monitor_progress(self):
        """Monitor and display progress"""
        while True:
            await asyncio.sleep(10)  # Update every 10 seconds
            
            # Use simple monitor for status display
            print_status()
            
            # Check if all queues are empty
            all_empty = all(q.empty() for q in self.stage_queues.values())
            if all_empty and self.stats['documents_processed'] > 0:
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
    
    async def process_batch_smart_parallel(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process documents with smart stage parallel optimization"""
        print(f"Starting smart stage parallel processing of {len(file_paths)} files...")
        print("Different PDFs will run in different stages simultaneously!")
        print("This will maximize hardware utilization!")
        
        # Start monitoring
        start_monitoring(len(file_paths))
        
        # Start stage workers
        workers = await self.start_stage_workers()
        
        try:
            # Start monitoring task
            monitor_task = asyncio.create_task(self.monitor_progress())
            
            # Smart distribute documents across stages
            await self.smart_distribute_documents(file_paths)
            
            # Wait for all stages to complete
            for stage_name in self.stage_queues.keys():
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
    
    def print_smart_summary(self, results: Dict[str, Any]):
        """Print smart stage parallel summary"""
        print(f"\n{'='*80}")
        print(f"SMART STAGE PARALLEL PROCESSING COMPLETE!")
        print(f"{'='*80}")
        print(f"Total Files: {results['total_files']}")
        print(f"Duration: {results['duration']:.1f}s ({results['duration']/60:.1f}m)")
        print(f"Average per File: {results['duration']/results['total_files']:.1f}s")
        print(f"")
        
        print("Stage Processing Stats:")
        for stage, count in results['stats']['stage_stats'].items():
            print(f"  {stage}: {count} documents")
        
        print(f"")
        print(f"Processing Results:")
        print(f"  Total Documents: {results['stats']['documents_processed']}")
        print(f"  Total Chunks: {results['stats']['total_chunks']}")
        print(f"  Total Images: {results['stats']['total_images']}")
        print(f"  Total Links: {results['stats']['total_links']}")
        print(f"{'='*80}")

async def main():
    """Main function for smart stage parallel processing"""
    print("SMART STAGE PARALLEL PROCESSING PIPELINE")
    print("="*60)
    print("Different PDFs run in different stages simultaneously!")
    print("PDF1->Stage1, PDF2->Stage2, PDF3->Stage3, etc.")
    print("Maximum hardware utilization achieved!")
    print("="*60)
    
    # Initialize pipeline
    pipeline = SmartStageParallelPipeline()
    await pipeline.initialize_services()
    
    # Find PDF files
    pdf_directory = "../service_documents"
    
    # Ask user how many files to process
    print("\nOptions:")
    print("1. Test with 8 files (perfect for 8 stages)")
    print("2. Test with 16 files (2x perfect)")
    print("3. Process all files (full batch)")
    
    choice = input("\nChoose option (1/2/3): ").strip()
    
    if choice == "1":
        pdf_files = pipeline.find_pdf_files(pdf_directory, limit=8)
    elif choice == "2":
        pdf_files = pipeline.find_pdf_files(pdf_directory, limit=16)
    elif choice == "3":
        pdf_files = pipeline.find_pdf_files(pdf_directory)
    else:
        pdf_files = pipeline.find_pdf_files(pdf_directory, limit=8)
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return
    
    print(f"\nSelected {len(pdf_files)} files for smart stage parallel processing")
    print("Different PDFs will start in different stages!")
    print("This should wake up your hardware!")
    
    # Ask user for confirmation
    response = input(f"\nStart smart stage parallel processing? (y/n): ").lower().strip()
    if response != 'y':
        print("Processing cancelled.")
        return
    
    # Process batch with smart stage parallel processing
    results = await pipeline.process_batch_smart_parallel(pdf_files)
    
    # Print summary
    pipeline.print_smart_summary(results)

if __name__ == "__main__":
    asyncio.run(main())
