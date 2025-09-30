import asyncio
import os
import sys
import hashlib
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Disable all logging to prevent console spam
logging.disable(logging.CRITICAL)

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

def print_status(stage: int, total: int, name: str, details: str = ""):
    """Print status with progress bar"""
    percentage = (stage / total) * 100
    progress_bar = "#" * int(percentage / 5) + "-" * (20 - int(percentage / 5))
    print(f"[{stage:2d}/{total}] {name:20s} [{progress_bar}] {percentage:5.1f}% {details}")
    sys.stdout.flush()

async def test_pipeline_clean():
    """Test pipeline with clean output"""
    print("KR-AI-Engine Pipeline Test - PRODUCTION MODE")
    print("=" * 70)
    
    # PDF file path
    pdf_path = r"C:\Users\haast\Downloads\HP_X580_SM.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return False
    
    try:
        print_status(0, 8, "Initializing", "Services...")
        
        # Initialize services
        config_service = ConfigService()
        
        # Database service
        supabase_url = os.getenv("SUPABASE_URL", "https://crujfdpqdjzcfqeyhang.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        await database_service.connect()
        
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
        
        # AI service
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ai_service = AIService(ollama_url)
        await ai_service.connect()
        
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
        
        print_status(1, 8, "Services Ready", "All connected")
        
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
        print_status(2, 8, "Upload", "Processing...")
        stage_start = time.time()
        upload_result = await upload_processor.process(context)
        context.document_id = upload_result.data['document_id']
        print_status(2, 8, "Upload", f"Done ({time.time() - stage_start:.1f}s)")
        
        # Stage 2: Text Processing
        print_status(3, 8, "Text Extract", "Processing...")
        stage_start = time.time()
        text_result = await text_processor.process(context)
        pages = text_result.data.get('total_pages', 0)
        chunks = len(text_result.data.get('chunks', []))
        print_status(3, 8, "Text Extract", f"{pages} pages, {chunks} chunks ({time.time() - stage_start:.1f}s)")
        
        # Stage 3: Image Processing
        print_status(4, 8, "Images", "Processing...")
        stage_start = time.time()
        image_result = await image_processor.process(context)
        img_count = len(image_result.data.get('processed_images', []))
        img_uploaded = len(image_result.data.get('uploaded_images', []))
        print_status(4, 8, "Images", f"{img_count} processed, {img_uploaded} uploaded ({time.time() - stage_start:.1f}s)")
        
        # Stage 4: Classification
        print_status(5, 8, "Classification", "Processing...")
        stage_start = time.time()
        classification_result = await classification_processor.process(context)
        manufacturer_id = classification_result.data.get('manufacturer_id', 'N/A')
        print_status(5, 8, "Classification", f"Done ({time.time() - stage_start:.1f}s)")
        
        # Stage 5: Metadata
        print_status(6, 8, "Metadata", "Processing...")
        stage_start = time.time()
        metadata_result = await metadata_processor.process(context)
        error_codes = len(metadata_result.data.get('error_codes', []))
        print_status(6, 8, "Metadata", f"{error_codes} error codes ({time.time() - stage_start:.1f}s)")
        
        # Stage 6: Storage
        print_status(7, 8, "Storage", "Processing...")
        stage_start = time.time()
        storage_result = await storage_processor.process(context)
        storage_urls = len(storage_result.data.get('storage_urls', []))
        print_status(7, 8, "Storage", f"{storage_urls} URLs ({time.time() - stage_start:.1f}s)")
        
        # Stage 7: Embeddings
        print_status(8, 8, "Embeddings", "Processing...")
        stage_start = time.time()
        embedding_result = await embedding_processor.process(context)
        embeddings = embedding_result.data.get('vector_count', 0)
        print_status(8, 8, "Embeddings", f"{embeddings} vectors ({time.time() - stage_start:.1f}s)")
        
        # Final Summary
        total_time = time.time() - pipeline_start
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"Document ID: {context.document_id}")
        print(f"Total Time: {total_time:.1f}s")
        print(f"Pages: {pages}")
        print(f"Chunks: {chunks}")
        print(f"Images: {img_count}")
        print(f"Error Codes: {error_codes}")
        print(f"Embeddings: {embeddings}")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_pipeline_clean())
