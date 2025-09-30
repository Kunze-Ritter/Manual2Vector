#!/usr/bin/env python3
"""
Complete Pipeline Test with Advanced Progress Tracking
Tests the full 8-stage KR-AI-Engine pipeline with the most advanced progress tracking
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from tests.enhanced_progress_tracker import EnhancedProgressTracker
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from services.ai_service import AIService
from services.config_service import ConfigService
from services.features_service import FeaturesService

# Import all processors
from processors.upload_processor import UploadProcessor
from processors.text_processor_optimized import OptimizedTextProcessor
from processors.image_processor import ImageProcessor
from processors.classification_processor import ClassificationProcessor
from processors.metadata_processor import MetadataProcessor
from processors.storage_processor import StorageProcessor
from processors.embedding_processor import EmbeddingProcessor
from processors.search_processor import SearchProcessor

from core.base_processor import ProcessingContext
from core.data_models import DocumentModel

class AdvancedPipelineProcessor:
    """
    Complete 8-Stage Pipeline Processor with Advanced Progress Tracking
    
    Features:
    - Real-time progress updates with ETA
    - Detailed stage information
    - Error handling and recovery
    - Performance metrics
    - Thread-safe progress tracking
    """
    
    def __init__(self):
        self.logger = None
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        
        # Initialize processors
        self.processors = {}
        self.progress_tracker = None
    
    async def initialize_services(self):
        """Initialize all services in production mode"""
        print("Initializing services in PRODUCTION mode...")
        
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
        print("All processors initialized")
    
    async def process_document(self, file_path: str) -> Dict:
        """
        Process document through complete 8-stage pipeline with advanced progress tracking
        
        Args:
            file_path: Path to the document to process
            
        Returns:
            Dict with processing results and metrics
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Initialize progress tracker
        self.progress_tracker = EnhancedProgressTracker(total_files=1)
        
        try:
            # Get file information
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            # Set file info in progress tracker
            self.progress_tracker.set_current_file(filename, file_size)
            
            # Create processing context
            context = ProcessingContext(
                    file_path=file_path,
                    document_id="",  # Will be set by upload processor
                    file_hash="",  # Will be set by upload processor
                    document_type="",  # Will be set by upload processor
                    processing_config={
                        'filename': filename,
                        'file_size': file_size
                    },
                    file_size=file_size
                )
            
            results = {}
            
            # Stage 1: Upload Processor
            self.progress_tracker.start_stage(1, {
                "file": filename,
                "size": f"{file_size:,} bytes",
                "stage": "Document upload and validation"
            })
            
            try:
                    result1 = await self.processors['upload'].process(context)
                    context.document_id = result1.data.get('document_id')
                    results['upload'] = result1
                    
                    # Update progress tracker with document ID
                    self.progress_tracker.set_current_file(filename, file_size, context.document_id)
                    
                    self.progress_tracker.end_stage(1, success=True, details={
                        "document_id": context.document_id,
                        "file_hash": result1.data.get('file_hash', 'N/A')[:16] + "...",
                        "document_type": result1.data.get('document_type', 'N/A')
                    })
            except Exception as e:
                self.progress_tracker.end_stage(1, success=False, error_message=str(e))
                raise
            
            # Stage 2: Text Processor
            self.progress_tracker.start_stage(2, {
                "stage": "Text extraction and chunking",
                "document_id": context.document_id
            })
            
            try:
                result2 = await self.processors['text'].process(context)
                results['text'] = result2
                
                chunk_count = len(result2.outputs.get('chunks', []))
                self.progress_tracker.end_stage(2, success=True, details={
                    "chunks_created": chunk_count,
                    "text_length": result2.outputs.get('text_length', 'N/A')
                })
            except Exception as e:
                self.progress_tracker.end_stage(2, success=False, error_message=str(e))
                raise
            
            # Stage 3: Image Processor
            self.progress_tracker.start_stage(3, {
                "stage": "Image extraction and AI analysis",
                "document_id": context.document_id
            })
            
            try:
                result3 = await self.processors['image'].process(context)
                results['image'] = result3
                
                image_count = len(result3.outputs.get('images', []))
                self.progress_tracker.end_stage(3, success=True, details={
                    "images_extracted": image_count,
                    "ai_analysis": "completed"
                })
            except Exception as e:
                self.progress_tracker.end_stage(3, success=False, error_message=str(e))
                raise
            
            # Stage 4: Classification Processor
            self.progress_tracker.start_stage(4, {
                "stage": "Document classification",
                "document_id": context.document_id
            })
            
            try:
                result4 = await self.processors['classification'].process(context)
                results['classification'] = result4
                
                self.progress_tracker.end_stage(4, success=True, details={
                    "manufacturer": result4.outputs.get('manufacturer', 'N/A'),
                    "product_series": result4.outputs.get('product_series', 'N/A'),
                    "product": result4.outputs.get('product', 'N/A')
                })
            except Exception as e:
                self.progress_tracker.end_stage(4, success=False, error_message=str(e))
                raise
            
            # Stage 5: Metadata Processor
            self.progress_tracker.start_stage(5, {
                "stage": "Metadata extraction",
                "document_id": context.document_id
            })
            
            try:
                result5 = await self.processors['metadata'].process(context)
                results['metadata'] = result5
                
                error_count = len(result5.outputs.get('error_codes', []))
                self.progress_tracker.end_stage(5, success=True, details={
                    "error_codes_found": error_count,
                    "metadata_extracted": "completed"
                })
            except Exception as e:
                self.progress_tracker.end_stage(5, success=False, error_message=str(e))
                raise
            
            # Stage 6: Storage Processor
            self.progress_tracker.start_stage(6, {
                "stage": "Object storage operations",
                "document_id": context.document_id
            })
            
            try:
                result6 = await self.processors['storage'].process(context)
                results['storage'] = result6
                
                self.progress_tracker.end_stage(6, success=True, details={
                    "storage_operations": "completed",
                    "images_stored": result6.outputs.get('images_stored', 0)
                })
            except Exception as e:
                self.progress_tracker.end_stage(6, success=False, error_message=str(e))
                raise
            
            # Stage 7: Embedding Processor
            self.progress_tracker.start_stage(7, {
                "stage": "Vector embedding generation",
                "document_id": context.document_id
            })
            
            try:
                result7 = await self.processors['embedding'].process(context)
                results['embedding'] = result7
                
                embedding_count = len(result7.outputs.get('embeddings', []))
                self.progress_tracker.end_stage(7, success=True, details={
                    "embeddings_created": embedding_count,
                    "model": result7.outputs.get('model_name', 'N/A')
                })
            except Exception as e:
                self.progress_tracker.end_stage(7, success=False, error_message=str(e))
                raise
            
            # Stage 8: Search Processor
            self.progress_tracker.start_stage(8, {
                "stage": "Search index creation",
                "document_id": context.document_id
            })
            
            try:
                result8 = await self.processors['search'].process(context)
                results['search'] = result8
                
                self.progress_tracker.end_stage(8, success=True, details={
                    "search_index": "created",
                    "analytics": "tracked"
                })
            except Exception as e:
                self.progress_tracker.end_stage(8, success=False, error_message=str(e))
                raise
            
            # Get final summary
            summary = self.progress_tracker.get_summary()
            
            # Print final summary
            self.progress_tracker.print_final_summary()
            
            return {
                'success': True,
                'document_id': context.document_id,
                'results': results,
                'summary': summary
            }
            
        except Exception as e:
            print(f"\nPipeline failed: {e}")
            if self.progress_tracker:
                self.progress_tracker.print_final_summary()
            raise
        finally:
            if self.progress_tracker:
                self.progress_tracker.stop()

async def test_complete_pipeline():
    """Test the complete pipeline with advanced progress tracking"""
    print("KR-AI-Engine Complete Pipeline Test")
    print("=" * 60)
    
    # Initialize processor
    processor = AdvancedPipelineProcessor()
    
    try:
        # Initialize all services
        await processor.initialize_services()
        
        # Test with HP manual
        test_file = "../HP_X580_SM.pdf"
        
        if not os.path.exists(test_file):
            print(f"Test file not found: {test_file}")
            print("Please ensure HP_X580_SM.pdf is in the parent directory")
            return
        
        print(f"\nProcessing document: {test_file}")
        print("This will test ALL 8 stages with real-time progress tracking")
        
        # Process the document
        result = await processor.process_document(test_file)
        
        if result['success']:
            print(f"\nPIPELINE COMPLETED SUCCESSFULLY!")
            print(f"Document ID: {result['document_id']}")
            print(f"Total Time: {result['summary']['total_time']:.2f}s")
            print(f"Success Rate: {result['summary']['success_rate']:.1f}%")
        else:
            print(f"\nPipeline failed!")
            
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())

