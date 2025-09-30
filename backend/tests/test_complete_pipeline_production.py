import asyncio
import os
import sys
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

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

class CompletePipelineProcessor:
    """Complete 8-Stage Pipeline Processor for PRODUCTION"""
    
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
    
    async def initialize_services(self):
        """Initialize all services and processors"""
        print("Initializing KR-AI-Engine PRODUCTION Pipeline...")
        print("=" * 80)
        
        # Initialize core services
        self.config_service = ConfigService()
        
        # Database service
        supabase_url = os.getenv("SUPABASE_URL", "https://crujfdpqdjzcfqeyhang.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        self.database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        await self.database_service.connect()
        
        # Object Storage service
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
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ai_service = AIService(ollama_url)
        await self.ai_service.connect()
        
        # Features service
        self.features_service = FeaturesService(self.ai_service, self.database_service)
        
        # Initialize all processors
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
        """Process document through complete 8-stage pipeline"""
        print(f"Processing Document: {os.path.basename(file_path)}")
        print(f"File Path: {file_path}")
        print(f"File Size: {os.path.getsize(file_path):,} bytes")
        print()
        
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
        
        pipeline_start_time = time.time()
        
        try:
            # Stage 1: Upload Processor
            print("STAGE 1: Upload Processor")
            print("   -> krai_core.documents (Database only)")
            stage_start = time.time()
            
            upload_result = await self.upload_processor.process(self.context)
            self.context.document_id = upload_result.data['document_id']
            self.results['stage_1_upload'] = {
                'success': upload_result.success,
                'processing_time': time.time() - stage_start,
                'document_id': self.context.document_id
            }
            
            print(f"   Document uploaded: {self.context.document_id}")
            print(f"   Processing time: {time.time() - stage_start:.2f}s")
            print()
            
            # Stage 2: Text Processor
            print("STAGE 2: Text Processor")
            print("   -> krai_content.chunks + krai_intelligence.chunks")
            stage_start = time.time()
            
            text_result = await self.text_processor.process(self.context)
            self.results['stage_2_text'] = {
                'success': text_result.success,
                'processing_time': time.time() - stage_start,
                'chunks_created': len(text_result.data.get('chunks', [])),
                'total_pages': text_result.data.get('total_pages', 0)
            }
            
            print(f"   Text extracted and chunked")
            print(f"   Pages processed: {text_result.data.get('total_pages', 0)}")
            print(f"   Chunks created: {len(text_result.data.get('chunks', []))}")
            print(f"   Processing time: {time.time() - stage_start:.2f}s")
            print()
            
            # Stage 3: Image Processor
            print("STAGE 3: Image Processor")
            print("   -> krai_content.images (Object Storage)")
            stage_start = time.time()
            
            image_result = await self.image_processor.process(self.context)
            self.results['stage_3_image'] = {
                'success': image_result.success,
                'processing_time': time.time() - stage_start,
                'images_processed': len(image_result.data.get('processed_images', [])),
                'images_uploaded': len(image_result.data.get('uploaded_images', []))
            }
            
            print(f"   Images extracted and processed")
            print(f"   Images processed: {len(image_result.data.get('processed_images', []))}")
            print(f"   Images uploaded to R2: {len(image_result.data.get('uploaded_images', []))}")
            print(f"   Processing time: {time.time() - stage_start:.2f}s")
            print()
            
            # Stage 4: Classification Processor
            print("STAGE 4: Classification Processor")
            print("   -> krai_core.manufacturers, products, product_series")
            stage_start = time.time()
            
            classification_result = await self.classification_processor.process(self.context)
            self.results['stage_4_classification'] = {
                'success': classification_result.success,
                'processing_time': time.time() - stage_start,
                'manufacturer_id': classification_result.data.get('manufacturer_id'),
                'series_id': classification_result.data.get('series_id'),
                'product_id': classification_result.data.get('product_id')
            }
            
            print(f"   Document classified")
            print(f"   Manufacturer ID: {classification_result.data.get('manufacturer_id', 'N/A')}")
            print(f"   Series ID: {classification_result.data.get('series_id', 'N/A')}")
            print(f"   Processing time: {time.time() - stage_start:.2f}s")
            print()
            
            # Stage 5: Metadata Processor
            print("STAGE 5: Metadata Processor")
            print("   -> krai_intelligence.error_codes")
            stage_start = time.time()
            
            metadata_result = await self.metadata_processor.process(self.context)
            self.results['stage_5_metadata'] = {
                'success': metadata_result.success,
                'processing_time': time.time() - stage_start,
                'error_codes_found': len(metadata_result.data.get('error_codes', [])),
                'versions_found': len(metadata_result.data.get('versions', []))
            }
            
            print(f"   Metadata extracted")
            print(f"   Error codes found: {len(metadata_result.data.get('error_codes', []))}")
            print(f"   Versions found: {len(metadata_result.data.get('versions', []))}")
            print(f"   Processing time: {time.time() - stage_start:.2f}s")
            print()
            
            # Stage 6: Storage Processor
            print("STAGE 6: Storage Processor")
            print("   -> Cloudflare R2 (NUR Bilder)")
            stage_start = time.time()
            
            storage_result = await self.storage_processor.process(self.context)
            self.results['stage_6_storage'] = {
                'success': storage_result.success,
                'processing_time': time.time() - stage_start,
                'storage_urls': len(storage_result.data.get('storage_urls', []))
            }
            
            print(f"   Storage processing completed")
            print(f"   Storage URLs: {len(storage_result.data.get('storage_urls', []))}")
            print(f"   Processing time: {time.time() - stage_start:.2f}s")
            print()
            
            # Stage 7: Embedding Processor
            print("STAGE 7: Embedding Processor")
            print("   -> krai_intelligence.embeddings")
            stage_start = time.time()
            
            embedding_result = await self.embedding_processor.process(self.context)
            self.results['stage_7_embedding'] = {
                'success': embedding_result.success,
                'processing_time': time.time() - stage_start,
                'embeddings_created': embedding_result.data.get('vector_count', 0)
            }
            
            print(f"   Vector embeddings generated")
            print(f"   Embeddings created: {embedding_result.data.get('vector_count', 0)}")
            print(f"   Processing time: {time.time() - stage_start:.2f}s")
            print()
            
            # Stage 8: Search Processor
            print("STAGE 8: Search Processor")
            print("   -> Semantic Search + Analytics")
            stage_start = time.time()
            
            search_result = await self.search_processor.process(self.context)
            self.results['stage_8_search'] = {
                'success': search_result.success,
                'processing_time': time.time() - stage_start,
                'search_index_created': search_result.data.get('search_index', {}).get('index_created', False)
            }
            
            print(f"   Search index created")
            print(f"   Search index: {search_result.data.get('search_index', {}).get('index_type', 'N/A')}")
            print(f"   Processing time: {time.time() - stage_start:.2f}s")
            print()
            
            # Pipeline Summary
            total_time = time.time() - pipeline_start_time
            self.results['pipeline_summary'] = {
                'total_processing_time': total_time,
                'all_stages_successful': all(stage['success'] for stage in self.results.values() if isinstance(stage, dict) and 'success' in stage),
                'document_id': self.context.document_id
            }
            
            print("PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"Document ID: {self.context.document_id}")
            print(f"Total Processing Time: {total_time:.2f}s")
            print(f"All Stages: {'SUCCESS' if self.results['pipeline_summary']['all_stages_successful'] else 'FAILED'}")
            print()
            
            return self.results
            
        except Exception as e:
            print(f"Pipeline failed at stage: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

async def test_complete_pipeline():
    """Test the complete 8-stage pipeline in PRODUCTION mode"""
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
        print("DETAILED PIPELINE RESULTS:")
        print("=" * 80)
        
        for stage_name, stage_result in results.items():
            if isinstance(stage_result, dict) and 'success' in stage_result:
                status = "SUCCESS" if stage_result['success'] else "FAILED"
                time_taken = stage_result.get('processing_time', 0)
                print(f"{stage_name.upper()}: {status} ({time_taken:.2f}s)")
                
                # Show specific results for each stage
                if stage_name == 'stage_1_upload':
                    print(f"  Document ID: {stage_result.get('document_id', 'N/A')}")
                elif stage_name == 'stage_2_text':
                    print(f"  Chunks: {stage_result.get('chunks_created', 0)}")
                    print(f"  Pages: {stage_result.get('total_pages', 0)}")
                elif stage_name == 'stage_3_image':
                    print(f"  Images: {stage_result.get('images_processed', 0)}")
                    print(f"  Uploaded: {stage_result.get('images_uploaded', 0)}")
                elif stage_name == 'stage_4_classification':
                    print(f"  Manufacturer: {stage_result.get('manufacturer_id', 'N/A')}")
                    print(f"  Series: {stage_result.get('series_id', 'N/A')}")
                elif stage_name == 'stage_5_metadata':
                    print(f"  Error Codes: {stage_result.get('error_codes_found', 0)}")
                    print(f"  Versions: {stage_result.get('versions_found', 0)}")
                elif stage_name == 'stage_7_embedding':
                    print(f"  Embeddings: {stage_result.get('embeddings_created', 0)}")
                elif stage_name == 'stage_8_search':
                    print(f"  Search Index: {stage_result.get('search_index_created', False)}")
        
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
