import asyncio
import os
import sys
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables from credentials.txt
load_dotenv('../credentials.txt')

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.config_service import ConfigService
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from services.ai_service import AIService
from services.features_service import FeaturesService

# Import all processors
from processors.upload_processor import UploadProcessor
from processors.text_processor import TextProcessor
from processors.image_processor import ImageProcessor
from processors.classification_processor import ClassificationProcessor
from processors.metadata_processor import MetadataProcessor
from processors.storage_processor import StorageProcessor
from processors.embedding_processor import EmbeddingProcessor
from processors.search_processor import SearchProcessor

from core.data_models import DocumentModel, DocumentType
from core.base_processor import ProcessingContext

class ProgressTracker:
    """Progress tracking with percentage and visual indicators"""
    
    def __init__(self, total_stages: int = 8):
        self.total_stages = total_stages
        self.current_stage = 0
        self.start_time = time.time()
        self.stage_times = {}
        
    def start_stage(self, stage_name: str, stage_number: int):
        """Start a new stage"""
        self.current_stage = stage_number
        self.stage_start_time = time.time()
        percentage = (stage_number - 1) / self.total_stages * 100
        
        print(f"\n{'='*80}")
        print(f"STAGE {stage_number}/8: {stage_name}")
        print(f"Progress: {percentage:.1f}% | {'#' * int(percentage/10):<10} {'-' * (10-int(percentage/10))}")
        print(f"{'='*80}")
        
        # Flush output immediately
        import sys
        sys.stdout.flush()
        
    def end_stage(self, success: bool = True, details: Dict = None):
        """End current stage"""
        stage_time = time.time() - self.stage_start_time
        self.stage_times[self.current_stage] = stage_time
        
        status = "SUCCESS" if success else "FAILED"
        percentage = self.current_stage / self.total_stages * 100
        
        print(f"\nStage {self.current_stage} completed: {status}")
        print(f"Time: {stage_time:.2f}s | Progress: {percentage:.1f}%")
        
        if details:
            for key, value in details.items():
                print(f"  {key}: {value}")
        
        print(f"{'#' * int(percentage/10):<10} {'-' * (10-int(percentage/10))}")
        
        # Flush output immediately
        import sys
        sys.stdout.flush()
        
    def get_summary(self):
        """Get final summary"""
        total_time = time.time() - self.start_time
        return {
            'total_time': total_time,
            'stage_times': self.stage_times,
            'average_stage_time': sum(self.stage_times.values()) / len(self.stage_times)
        }

class CompletePipelineProcessor:
    """Complete 8-Stage Pipeline Processor with Progress Tracking"""
    
    def __init__(self):
        self.logger = None
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        
        # Initialize all processors
        self.upload_processor = None
        self.text_processor = None
        self.image_processor = None
        self.classification_processor = None
        self.metadata_processor = None
        self.storage_processor = None
        self.embedding_processor = None
        self.search_processor = None
        
        self.results = {}
        self.context = None
        self.progress = ProgressTracker()
    
    async def initialize_services(self):
        """Initialize all services and processors"""
        print("KR-AI-Engine PRODUCTION Pipeline - Initializing...")
        print("=" * 80)
        
        # Initialize core services
        self.config_service = ConfigService()
        
        # Database service
        supabase_url = os.getenv("SUPABASE_URL", "https://crujfdpqdjzcfqeyhang.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        print("Connecting to Supabase database...")
        self.database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        await self.database_service.connect()
        
        # Object Storage service
        print("Connecting to Cloudflare R2...")
        self.storage_service = ObjectStorageService(
            r2_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            r2_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            r2_endpoint_url=os.getenv("R2_ENDPOINT_URL"),
            r2_public_url_documents=os.getenv("R2_PUBLIC_URL_DOCUMENTS"),
            r2_public_url_error=os.getenv("R2_PUBLIC_URL_ERROR"),
            r2_public_url_parts=os.getenv("R2_PUBLIC_URL_PARTS")
        )
        await self.storage_service.connect()
        
        # AI service
        print("Connecting to Ollama AI service...")
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ai_service = AIService(ollama_url)
        await self.ai_service.connect()
        
        # Features service
        self.features_service = FeaturesService(self.ai_service, self.database_service)
        
        # Initialize all processors
        print("Initializing processing stages...")
        self.upload_processor = UploadProcessor(self.database_service)
        self.text_processor = TextProcessor(self.database_service, self.config_service)
        self.image_processor = ImageProcessor(self.database_service, self.storage_service, self.ai_service)
        self.classification_processor = ClassificationProcessor(self.database_service, self.ai_service, self.features_service)
        self.metadata_processor = MetadataProcessor(self.database_service, self.config_service)
        self.storage_processor = StorageProcessor(self.database_service, self.storage_service)
        self.embedding_processor = EmbeddingProcessor(self.database_service, self.ai_service)
        self.search_processor = SearchProcessor(self.database_service, self.ai_service)
        
        print("All services and processors initialized successfully!")
        print()
    
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process document through complete 8-stage pipeline with progress tracking"""
        print(f"Processing Document: {os.path.basename(file_path)}")
        print(f"File Path: {file_path}")
        print(f"File Size: {os.path.getsize(file_path):,} bytes")
        print()
        
        # Flush output to ensure it's visible immediately
        import sys
        sys.stdout.flush()
        
        # Create processing context
        file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
        self.context = ProcessingContext(
            document_id="",  # Will be set by upload processor
            file_path=file_path,
            file_hash=file_hash,
            document_type=DocumentType.SERVICE_MANUAL,
            manufacturer="HP",
            model="X580",
            series="Color LaserJet Enterprise",
            version="1.0",
            language="en",
            processing_config={"filename": os.path.basename(file_path)},
            file_size=os.path.getsize(file_path)
        )
        
        try:
            # Stage 1: Upload Processor
            self.progress.start_stage("Upload Processor", 1)
            upload_result = await self.upload_processor.process(self.context)
            self.context.document_id = upload_result.data['document_id']
            self.results['stage_1_upload'] = {
                'success': upload_result.success,
                'document_id': self.context.document_id
            }
            self.progress.end_stage(upload_result.success, {
                'Document ID': self.context.document_id
            })
            
            # Stage 2: Text Processor
            self.progress.start_stage("Text Processor", 2)
            print("Extracting text from PDF...")
            import sys
            sys.stdout.flush()
            text_result = await self.text_processor.process(self.context)
            self.results['stage_2_text'] = {
                'success': text_result.success,
                'chunks_created': len(text_result.data.get('chunks', [])),
                'total_pages': text_result.data.get('total_pages', 0)
            }
            self.progress.end_stage(text_result.success, {
                'Pages': text_result.data.get('total_pages', 0),
                'Chunks': len(text_result.data.get('chunks', []))
            })
            
            # Stage 3: Image Processor
            self.progress.start_stage("Image Processor", 3)
            print("Extracting and processing images...")
            import sys
            sys.stdout.flush()
            image_result = await self.image_processor.process(self.context)
            self.results['stage_3_image'] = {
                'success': image_result.success,
                'images_processed': len(image_result.data.get('processed_images', [])),
                'images_uploaded': len(image_result.data.get('uploaded_images', []))
            }
            self.progress.end_stage(image_result.success, {
                'Images Processed': len(image_result.data.get('processed_images', [])),
                'Images Uploaded': len(image_result.data.get('uploaded_images', []))
            })
            
            # Stage 4: Classification Processor
            self.progress.start_stage("Classification Processor", 4)
            print("Classifying document with AI...")
            import sys
            sys.stdout.flush()
            classification_result = await self.classification_processor.process(self.context)
            self.results['stage_4_classification'] = {
                'success': classification_result.success,
                'manufacturer_id': classification_result.data.get('manufacturer_id'),
                'series_id': classification_result.data.get('series_id'),
                'product_id': classification_result.data.get('product_id')
            }
            self.progress.end_stage(classification_result.success, {
                'Manufacturer ID': classification_result.data.get('manufacturer_id', 'N/A'),
                'Series ID': classification_result.data.get('series_id', 'N/A')
            })
            
            # Stage 5: Metadata Processor
            self.progress.start_stage("Metadata Processor", 5)
            metadata_result = await self.metadata_processor.process(self.context)
            self.results['stage_5_metadata'] = {
                'success': metadata_result.success,
                'error_codes_found': len(metadata_result.data.get('error_codes', [])),
                'versions_found': len(metadata_result.data.get('versions', []))
            }
            self.progress.end_stage(metadata_result.success, {
                'Error Codes': len(metadata_result.data.get('error_codes', [])),
                'Versions': len(metadata_result.data.get('versions', []))
            })
            
            # Stage 6: Storage Processor
            self.progress.start_stage("Storage Processor", 6)
            storage_result = await self.storage_processor.process(self.context)
            self.results['stage_6_storage'] = {
                'success': storage_result.success,
                'storage_urls': len(storage_result.data.get('storage_urls', []))
            }
            self.progress.end_stage(storage_result.success, {
                'Storage URLs': len(storage_result.data.get('storage_urls', []))
            })
            
            # Stage 7: Embedding Processor
            self.progress.start_stage("Embedding Processor", 7)
            embedding_result = await self.embedding_processor.process(self.context)
            self.results['stage_7_embedding'] = {
                'success': embedding_result.success,
                'embeddings_created': embedding_result.data.get('vector_count', 0)
            }
            self.progress.end_stage(embedding_result.success, {
                'Embeddings Created': embedding_result.data.get('vector_count', 0)
            })
            
            # Stage 8: Search Processor
            self.progress.start_stage("Search Processor", 8)
            search_result = await self.search_processor.process(self.context)
            self.results['stage_8_search'] = {
                'success': search_result.success,
                'search_index_created': search_result.data.get('search_index', {}).get('index_created', False)
            }
            self.progress.end_stage(search_result.success, {
                'Search Index': search_result.data.get('search_index', {}).get('index_type', 'N/A')
            })
            
            # Final Summary
            summary = self.progress.get_summary()
            self.results['pipeline_summary'] = {
                'total_processing_time': summary['total_time'],
                'all_stages_successful': all(stage['success'] for stage in self.results.values() if isinstance(stage, dict) and 'success' in stage),
                'document_id': self.context.document_id,
                'average_stage_time': summary['average_stage_time']
            }
            
            print(f"\n{'='*80}")
            print("PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"{'='*80}")
            print(f"Document ID: {self.context.document_id}")
            print(f"Total Processing Time: {summary['total_time']:.2f}s")
            print(f"Average Stage Time: {summary['average_stage_time']:.2f}s")
            print(f"All Stages: {'SUCCESS' if self.results['pipeline_summary']['all_stages_successful'] else 'FAILED'}")
            print(f"{'#' * 10} 100% COMPLETE {'#' * 10}")
            
            return self.results
            
        except Exception as e:
            print(f"\nPipeline failed at stage {self.progress.current_stage}: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

async def test_complete_pipeline():
    """Test the complete 8-stage pipeline with progress tracking"""
    print("KR-AI-Engine Complete Pipeline Test - PRODUCTION MODE")
    print("=" * 80)
    
    # PDF file path
    pdf_path = r"C:\Users\haast\Downloads\HP_X580_SM.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return False
    
    try:
        # Initialize pipeline processor
        pipeline = CompletePipelineProcessor()
        await pipeline.initialize_services()
        
        # Process document through complete pipeline
        results = await pipeline.process_document(pdf_path)
        
        if 'error' in results:
            print(f"Pipeline failed: {results['error']}")
            return False
        
        # Print detailed results
        print("\nDETAILED PIPELINE RESULTS:")
        print("=" * 80)
        
        stage_names = {
            'stage_1_upload': 'Upload Processor',
            'stage_2_text': 'Text Processor', 
            'stage_3_image': 'Image Processor',
            'stage_4_classification': 'Classification Processor',
            'stage_5_metadata': 'Metadata Processor',
            'stage_6_storage': 'Storage Processor',
            'stage_7_embedding': 'Embedding Processor',
            'stage_8_search': 'Search Processor'
        }
        
        for stage_name, stage_result in results.items():
            if isinstance(stage_result, dict) and 'success' in stage_result:
                stage_display = stage_names.get(stage_name, stage_name.upper())
                status = "SUCCESS" if stage_result['success'] else "FAILED"
                print(f"{stage_display}: {status}")
        
        print()
        print("PIPELINE TEST COMPLETED!")
        print(f"Total Time: {results['pipeline_summary']['total_processing_time']:.2f}s")
        print(f"Success: {results['pipeline_summary']['all_stages_successful']}")
        
        return results['pipeline_summary']['all_stages_successful']
        
    except Exception as e:
        print(f"Complete pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())
