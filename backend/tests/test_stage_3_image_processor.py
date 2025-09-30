import asyncio
import os
import sys
import hashlib
import pymupdf as fitz  # PyMuPDF
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.config_service import ConfigService
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from services.ai_service import AIService
from processors.image_processor import ImageProcessor
from core.data_models import DocumentModel, DocumentType, ImageModel, ImageType
from core.base_processor import ProcessingContext

async def test_stage_3_image_processor():
    """Test Stage 3: Image Processor with OCR + AI Vision"""
    print("Testing Stage 3: Image Processor with OCR + AI Vision...")
    
    try:
        # Initialize services
        print("Initializing services...")
        config_service = ConfigService()
        
        # Database service
        supabase_url = os.getenv("SUPABASE_URL", "https://crujfdpqdjzcfqeyhang.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        await database_service.connect()
        
        # R2 Storage service
        r2_access_key_id = os.getenv("R2_ACCESS_KEY_ID")
        r2_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
        r2_endpoint_url = os.getenv("R2_ENDPOINT_URL")
        r2_public_url_documents = os.getenv("R2_PUBLIC_URL_DOCUMENTS")
        r2_public_url_error = os.getenv("R2_PUBLIC_URL_ERROR")
        r2_public_url_parts = os.getenv("R2_PUBLIC_URL_PARTS")
        
        storage_service = ObjectStorageService(
            r2_access_key_id=r2_access_key_id,
            r2_secret_access_key=r2_secret_access_key,
            r2_endpoint_url=r2_endpoint_url,
            r2_public_url_documents=r2_public_url_documents,
            r2_public_url_error=r2_public_url_error,
            r2_public_url_parts=r2_public_url_parts
        )
        await storage_service.connect()
        
        # AI service with correct Ollama URL
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ai_service = AIService(ollama_url)
        await ai_service.connect()
        
        # Initialize Image Processor
        image_processor = ImageProcessor(database_service, storage_service, ai_service)
        
        # PDF file path
        pdf_path = r"C:\Users\haast\Downloads\HP_X580_SM.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return False
        
        print(f"PDF file found: {pdf_path}")
        
        # Create document first
        print("Creating document in database...")
        document = DocumentModel(
            filename=os.path.basename(pdf_path),
            original_filename=os.path.basename(pdf_path),
            file_size=os.path.getsize(pdf_path),
            file_hash=hashlib.sha256(open(pdf_path, 'rb').read()).hexdigest(),
            document_type=DocumentType.SERVICE_MANUAL,
            manufacturer="HP",
            series="Color LaserJet Enterprise",
            models=["X580"],
            version="1.0",
            language="en"
        )
        
        created_doc = await database_service.create_document(document)
        doc_id = created_doc.id if hasattr(created_doc, 'id') else created_doc
        print(f"Document created: {doc_id}")
        
        # Create processing context
        context = ProcessingContext(
            document_id=doc_id,
            file_path=pdf_path,
            file_hash=hashlib.sha256(open(pdf_path, 'rb').read()).hexdigest(),
            document_type=DocumentType.SERVICE_MANUAL,
            manufacturer="HP",
            model="X580",
            series="Color LaserJet Enterprise",
            version="1.0",
            language="en",
            processing_config={"filename": os.path.basename(pdf_path)},
            file_size=os.path.getsize(pdf_path)
        )
        
        print("Starting Stage 3: Image Processor...")
        print("=" * 60)
        
        # Process images with OCR + AI Vision
        result = await image_processor.process(context)
        
        print("=" * 60)
        print("Stage 3 Image Processor Results:")
        print(f"Success: {result.success}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        if result.success:
            data = result.data
            print(f"Total images processed: {data.get('total_images', 0)}")
            print(f"OCR text extracted: {len(data.get('ocr_text', ''))} characters")
            print(f"AI descriptions: {len(data.get('ai_descriptions', []))}")
            
            # Show OCR text sample
            ocr_text = data.get('ocr_text', '')
            if ocr_text:
                print(f"\nOCR Text Sample (first 200 chars):")
                print(f"'{ocr_text[:200]}...'")
            
            # Show AI descriptions
            ai_descriptions = data.get('ai_descriptions', [])
            if ai_descriptions:
                print(f"\nAI Descriptions:")
                for i, desc in enumerate(ai_descriptions):
                    if isinstance(desc, dict):
                        print(f"  Image {i+1}: {desc.get('description', 'No description')[:100]}...")
                        print(f"    Confidence: {desc.get('confidence', 0):.2f}")
                        print(f"    Contains Text: {desc.get('contains_text', False)}")
                        print(f"    Tags: {desc.get('tags', [])}")
                    else:
                        print(f"  Image {i+1}: {str(desc)[:100]}...")
            
            # Verify database storage
            print(f"\nVerifying database storage...")
            try:
                # Check if images were saved to database
                # This would require a database query method
                print("Database verification would require additional query methods")
            except Exception as e:
                print(f"Database verification error: {e}")
                
        else:
            print(f"Image processing failed: {result.error}")
            return False
        
        print("\nStage 3 Image Processor test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Stage 3 Image Processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_stage_3_image_processor())
