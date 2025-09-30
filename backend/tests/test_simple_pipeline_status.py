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

async def test_pipeline_with_simple_status():
    """Test pipeline with simple status updates"""
    print("KR-AI-Engine Pipeline Test - PRODUCTION MODE")
    print("=" * 60)
    
    # PDF file path
    pdf_path = r"C:\Users\haast\Downloads\HP_X580_SM.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return False
    
    try:
        # Initialize services
        print("1/8 - Initializing services...")
        config_service = ConfigService()
        
        # Database service
        supabase_url = os.getenv("SUPABASE_URL", "https://crujfdpqdjzcfqeyhang.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        await database_service.connect()
        print("   Database connected")
        
        # Object Storage service
        storage_service = ObjectStorageService(
            r2_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            r2_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            r2_endpoint_url=os.getenv("R2_ENDPOINT_URL"),
            r2_public_url_documents=os.getenv("R2_PUBLIC_URL_DOCUMENTS"),
            r2_public_url_error=os.getenv("R2_PUBLIC_URL_ERROR"),
            r2_public_url_parts=os.getenv("R2_PUBLIC_URL_PARTS")
        )
        await storage_service.connect()
        print("   R2 Storage connected")
        
        # AI service
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ai_service = AIService(ollama_url)
        await ai_service.connect()
        print("   AI Service connected")
        
        # Features service
        features_service = FeaturesService(ai_service, database_service)
        
        # Initialize processors
        upload_processor = UploadProcessor(database_service)
        text_processor = TextProcessor(database_service, config_service)
        image_processor = ImageProcessor(database_service, storage_service, ai_service)
        classification_processor = ClassificationProcessor(database_service, ai_service, features_service)
        metadata_processor = MetadataProcessor(database_service, config_service)
        storage_processor = StorageProcessor(database_service, storage_service)
        embedding_processor = EmbeddingProcessor(database_service, ai_service)
        search_processor = SearchProcessor(database_service, ai_service)
        
        print("   All processors initialized")
        print()
        
        # Create processing context
        file_hash = hashlib.sha256(open(pdf_path, 'rb').read()).hexdigest()
        context = ProcessingContext(
            document_id="",
            file_path=pdf_path,
            file_hash=file_hash,
            document_type=DocumentType.SERVICE_MANUAL,
            manufacturer="HP",
            model="X580",
            series="Color LaserJet Enterprise",
            version="1.0",
            language="en",
            processing_config={"filename": os.path.basename(pdf_path)},
            file_size=os.path.getsize(pdf_path)
        )
        
        pipeline_start = time.time()
        
        # Stage 1: Upload
        print("2/8 - Upload Processor...")
        stage_start = time.time()
        upload_result = await upload_processor.process(context)
        context.document_id = upload_result.data['document_id']
        print(f"   Document uploaded: {context.document_id}")
        print(f"   Time: {time.time() - stage_start:.1f}s")
        print()
        
        # Stage 2: Text Processing
        print("3/8 - Text Processor...")
        stage_start = time.time()
        text_result = await text_processor.process(context)
        print(f"   Pages: {text_result.data.get('total_pages', 0)}")
        print(f"   Chunks: {len(text_result.data.get('chunks', []))}")
        print(f"   Time: {time.time() - stage_start:.1f}s")
        print()
        
        # Stage 3: Image Processing
        print("4/8 - Image Processor...")
        stage_start = time.time()
        image_result = await image_processor.process(context)
        print(f"   Images processed: {len(image_result.data.get('processed_images', []))}")
        print(f"   Images uploaded: {len(image_result.data.get('uploaded_images', []))}")
        print(f"   Time: {time.time() - stage_start:.1f}s")
        print()
        
        # Stage 4: Classification
        print("5/8 - Classification Processor...")
        stage_start = time.time()
        classification_result = await classification_processor.process(context)
        print(f"   Manufacturer ID: {classification_result.data.get('manufacturer_id', 'N/A')}")
        print(f"   Time: {time.time() - stage_start:.1f}s")
        print()
        
        # Stage 5: Metadata
        print("6/8 - Metadata Processor...")
        stage_start = time.time()
        metadata_result = await metadata_processor.process(context)
        print(f"   Error codes: {len(metadata_result.data.get('error_codes', []))}")
        print(f"   Time: {time.time() - stage_start:.1f}s")
        print()
        
        # Stage 6: Storage
        print("7/8 - Storage Processor...")
        stage_start = time.time()
        storage_result = await storage_processor.process(context)
        print(f"   Storage URLs: {len(storage_result.data.get('storage_urls', []))}")
        print(f"   Time: {time.time() - stage_start:.1f}s")
        print()
        
        # Stage 7: Embeddings
        print("8/8 - Embedding Processor...")
        stage_start = time.time()
        embedding_result = await embedding_processor.process(context)
        print(f"   Embeddings: {embedding_result.data.get('vector_count', 0)}")
        print(f"   Time: {time.time() - stage_start:.1f}s")
        print()
        
        # Final Summary
        total_time = time.time() - pipeline_start
        print("PIPELINE COMPLETED!")
        print("=" * 60)
        print(f"Document ID: {context.document_id}")
        print(f"Total Time: {total_time:.1f}s")
        print(f"Success: All stages completed")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_pipeline_with_simple_status())
