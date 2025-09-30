"""
Quick Batch Test - Simplified version for testing multiple PDFs
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

# Import services (without complex optimizations)
from services.database_service import DatabaseService
from services.ai_service import AIService
from services.config_service import ConfigService

from processors.upload_processor import UploadProcessor
from processors.text_processor_optimized import OptimizedTextProcessor

from core.base_processor import ProcessingContext

class QuickBatchTest:
    """
    Quick batch test for multiple PDFs - simplified version
    """
    
    def __init__(self):
        self.database_service = None
        self.ai_service = None
        self.config_service = None
        self.processors = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("krai.quick_batch")
        
    async def initialize_services(self):
        """Initialize only essential services"""
        self.logger.info("Initializing quick batch services...")
        
        # Load environment variables
        load_dotenv('../credentials.txt')
        
        # Initialize database service
        self.database_service = DatabaseService(
            supabase_url=os.getenv('SUPABASE_URL'),
            supabase_key=os.getenv('SUPABASE_ANON_KEY')
        )
        await self.database_service.connect()
        self.logger.info("Database service connected")
        
        # Initialize AI service
        self.ai_service = AIService(ollama_url=os.getenv('OLLAMA_URL', 'http://localhost:11434'))
        await self.ai_service.connect()
        self.logger.info("AI service connected")
        
        # Initialize config service
        self.config_service = ConfigService()
        self.logger.info("Config service initialized")
        
        # Initialize only essential processors
        self.processors = {
            'upload': UploadProcessor(self.database_service),
            'text': OptimizedTextProcessor(self.database_service, self.config_service),
        }
        self.logger.info("Essential processors initialized")
    
    async def quick_process_document(self, file_path: str) -> Dict[str, Any]:
        """Quick process a single document (upload + text only)"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            # Get file information
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            self.logger.info(f"Processing: {filename} ({file_size/1024/1024:.1f}MB)")
            
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
            
            # Stage 1: Upload Processor
            self.logger.info(f"  Upload: {filename}")
            result1 = await self.processors['upload'].process(context)
            context.document_id = result1.data.get('document_id')
            context.file_hash = result1.data.get('file_hash', '')
            context.document_type = result1.data.get('document_type', '')
            results['upload'] = result1
            
            # Stage 2: Text Processor (Optimized)
            self.logger.info(f"  Text Processing: {filename}")
            result2 = await self.processors['text'].process(context)
            results['text'] = result2
            
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
    
    async def quick_batch_process(self, file_paths: List[str]) -> Dict[str, Any]:
        """Quick batch process multiple documents"""
        self.logger.info(f"\nStarting quick batch processing of {len(file_paths)} files...")
        print("="*60)
        
        results = {
            'successful': [],
            'failed': [],
            'total_files': len(file_paths),
            'start_time': time.time()
        }
        
        # Process files sequentially for stability
        for i, file_path in enumerate(file_paths, 1):
            filename = os.path.basename(file_path)
            print(f"\n[{i}/{len(file_paths)}] Processing: {filename}")
            
            try:
                result = await self.quick_process_document(file_path)
                if result['success']:
                    results['successful'].append(result)
                    print(f"  ✓ Success: {result['document_id']}")
                else:
                    results['failed'].append(result)
                    print(f"  ✗ Failed: {result['error']}")
            except Exception as e:
                results['failed'].append({
                    'success': False,
                    'error': str(e),
                    'filename': filename
                })
                print(f"  ✗ Exception: {e}")
        
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
    
    def print_quick_summary(self, results: Dict[str, Any]):
        """Print quick batch processing summary"""
        print(f"\n{'='*60}")
        print(f"QUICK BATCH PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Total Files: {results['total_files']}")
        print(f"Successful: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print(f"Total Duration: {results['duration']:.1f}s ({results['duration']/60:.1f}m)")
        print(f"Average per File: {results['duration']/results['total_files']:.1f}s")
        print(f"")
        
        if results['successful']:
            print(f"SUCCESSFUL FILES:")
            for result in results['successful']:
                file_size_mb = result['file_size'] / (1024 * 1024)
                print(f"  ✓ {result['filename']} ({file_size_mb:.1f}MB) - {result['document_id']}")
        
        if results['failed']:
            print(f"FAILED FILES:")
            for result in results['failed']:
                print(f"  ✗ {result['filename']} - {result['error']}")
        
        print(f"{'='*60}")

async def main():
    """Main function for quick batch testing"""
    print("KR-AI-Engine Quick Batch Test")
    print("="*40)
    
    # Initialize pipeline
    pipeline = QuickBatchTest()
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
    print(f"Estimated processing time: {len(pdf_files) * 1:.0f} minutes")
    
    # Ask user for confirmation
    response = input(f"\nProcess all {len(pdf_files)} files? (y/n): ").lower().strip()
    if response != 'y':
        print("Processing cancelled.")
        return
    
    # Process batch
    results = await pipeline.quick_batch_process(pdf_files)
    
    # Print summary
    pipeline.print_quick_summary(results)

if __name__ == "__main__":
    asyncio.run(main())
