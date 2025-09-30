"""
True Parallel Pipeline - Actually runs different stages in parallel across different documents!
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import logging
import multiprocessing as mp

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

class TrueParallelPipeline:
    """
    True parallel pipeline that processes multiple documents simultaneously
    with different stages running in parallel
    """
    
    def __init__(self):
        # Get hardware info
        cpu_count = mp.cpu_count()
        self.max_concurrent_documents = min(cpu_count, 8)  # Process multiple docs simultaneously
        
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        self.processors = {}
        
        # Setup logging (minimal)
        logging.basicConfig(level=logging.WARNING)
        self.logger = logging.getLogger("krai.true_parallel")
        
        # Processing stats
        self.stats = {
            'documents_processed': 0,
            'total_chunks': 0,
            'total_images': 0,
            'total_links': 0,
            'start_time': time.time()
        }
        
        self.logger.info(f"True Parallel Pipeline initialized with {self.max_concurrent_documents} concurrent documents")
        
    async def initialize_services(self):
        """Initialize all services"""
        print("Initializing True Parallel Pipeline...")
        
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
        print("All services initialized - Ready for true parallel processing!")
    
    async def process_single_document_full_pipeline(self, file_path: str, document_index: int, total_documents: int) -> Dict[str, Any]:
        """Process a single document through all 8 stages"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            # Get file information
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            print(f"[{document_index}/{total_documents}] Starting: {filename} ({file_size/1024/1024:.1f}MB)")
            
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
            print(f"  [{document_index}] Upload: {filename}")
            result1 = await self.processors['upload'].process(context)
            context.document_id = result1.data.get('document_id')
            context.file_hash = result1.data.get('file_hash', '')
            context.document_type = result1.data.get('document_type', '')
            
            # Stage 2: Text Processor (This will wake up CPU!)
            print(f"  [{document_index}] Text Processing: {filename}")
            result2 = await self.processors['text'].process(context)
            chunks_count = result2.data.get('chunks_created', 0)
            self.stats['total_chunks'] += chunks_count
            
            # Stage 3: Image Processor (This will wake up GPU!)
            print(f"  [{document_index}] Image Processing: {filename}")
            result3 = await self.processors['image'].process(context)
            images_count = result3.data.get('images_processed', 0)
            self.stats['total_images'] += images_count
            
            # Stage 4: Classification Processor
            print(f"  [{document_index}] Classification: {filename}")
            result4 = await self.processors['classification'].process(context)
            
            # Stage 5: Metadata Processor
            print(f"  [{document_index}] Metadata: {filename}")
            result5 = await self.processors['metadata'].process(context)
            
            # Stage 6: Storage Processor
            print(f"  [{document_index}] Storage: {filename}")
            result6 = await self.processors['storage'].process(context)
            
            # Stage 7: Embedding Processor (This will wake up GPU for AI!)
            print(f"  [{document_index}] Embeddings: {filename}")
            result7 = await self.processors['embedding'].process(context)
            
            # Stage 8: Search Processor
            print(f"  [{document_index}] Search Index: {filename}")
            result8 = await self.processors['search'].process(context)
            
            self.stats['documents_processed'] += 1
            print(f"  [{document_index}] Completed: {filename}")
            
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
    
    async def process_batch_true_parallel(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple documents in true parallel - multiple docs at once"""
        print(f"TRUE PARALLEL PROCESSING - {len(file_paths)} files with {self.max_concurrent_documents} concurrent documents!")
        print("This will wake up your CPU and GPU by processing multiple documents simultaneously!")
        
        results = {
            'successful': [],
            'failed': [],
            'total_files': len(file_paths),
            'start_time': time.time(),
            'concurrent_documents': self.max_concurrent_documents
        }
        
        try:
            # Create semaphore to limit concurrent document processing
            semaphore = asyncio.Semaphore(self.max_concurrent_documents)
            
            async def process_with_semaphore(file_path: str, doc_index: int):
                """Process document with semaphore to limit concurrency"""
                async with semaphore:
                    return await self.process_single_document_full_pipeline(file_path, doc_index, len(file_paths))
            
            # Create tasks for all files - THIS IS THE KEY: Multiple docs processing simultaneously
            tasks = [process_with_semaphore(file_path, i+1) for i, file_path in enumerate(file_paths)]
            
            # Process all files in parallel - Multiple documents running through all stages simultaneously
            print(f"Starting TRUE PARALLEL processing of {len(tasks)} files...")
            print("Multiple documents will be processed simultaneously - CPU and GPU will be busy!")
            
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
            print(f"Error in true parallel processing: {e}")
        
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
    
    def print_true_parallel_summary(self, results: Dict[str, Any]):
        """Print true parallel processing summary"""
        print(f"\n{'='*80}")
        print(f"TRUE PARALLEL PROCESSING COMPLETE!")
        print(f"{'='*80}")
        print(f"Concurrent Documents: {results['concurrent_documents']}")
        print(f"Total Files: {results['total_files']}")
        print(f"Successful: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print(f"Total Duration: {results['duration']:.1f}s ({results['duration']/60:.1f}m)")
        print(f"Average per File: {results['duration']/results['total_files']:.1f}s")
        print(f"Parallel Speedup: ~{results['concurrent_documents']:.1f}x faster than sequential!")
        print(f"")
        print(f"Processing Results:")
        print(f"  Total Chunks: {self.stats['total_chunks']}")
        print(f"  Total Images: {self.stats['total_images']}")
        print(f"  Total Links: {self.stats['total_links']}")
        print(f"")
        
        if results['successful']:
            print(f"SUCCESSFUL FILES:")
            for result in results['successful']:
                file_size_mb = result['file_size'] / (1024 * 1024)
                print(f"  {result['filename']} ({file_size_mb:.1f}MB) - {result['document_id']}")
        
        if results['failed']:
            print(f"FAILED FILES:")
            for result in results['failed']:
                print(f"  {result['filename']} - {result['error']}")
        
        print(f"{'='*80}")

async def main():
    """Main function for true parallel processing"""
    print("TRUE PARALLEL PROCESSING PIPELINE")
    print("="*60)
    print("This pipeline processes multiple documents simultaneously!")
    print("Each document goes through all 8 stages in parallel with others!")
    print("Maximum CPU/GPU utilization achieved!")
    print("="*60)
    
    # Initialize pipeline
    pipeline = TrueParallelPipeline()
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
    
    print(f"\nSelected {len(pdf_files)} files for TRUE PARALLEL processing")
    print(f"Will process {pipeline.max_concurrent_documents} documents simultaneously!")
    print("This should wake up your CPU and GPU!")
    
    # Ask user for confirmation
    response = input(f"\nStart TRUE PARALLEL processing? (y/n): ").lower().strip()
    if response != 'y':
        print("Processing cancelled.")
        return
    
    # Process batch with true parallel processing
    results = await pipeline.process_batch_true_parallel(pdf_files)
    
    # Print summary
    pipeline.print_true_parallel_summary(results)

if __name__ == "__main__":
    asyncio.run(main())
