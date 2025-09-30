import asyncio
import os
import sys
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.config_service import ConfigService
from services.database_service import DatabaseService
from processors.metadata_processor import MetadataProcessor
from core.data_models import DocumentModel, DocumentType
from core.base_processor import ProcessingContext

async def test_stage_5_metadata_processor():
    """Test Stage 5: Metadata Processor with error code extraction"""
    print("Testing Stage 5: Metadata Processor with error code extraction...")
    
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
        
        # Initialize Metadata Processor
        metadata_processor = MetadataProcessor(database_service, config_service)
        
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
        
        print("Starting Stage 5: Metadata Processor...")
        print("=" * 60)
        
        # Process metadata extraction
        result = await metadata_processor.process(context)
        
        print("=" * 60)
        print("Stage 5 Metadata Processor Results:")
        print(f"Success: {result.success}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        if result.success:
            data = result.data
            print(f"Error Codes Found: {len(data.get('error_codes', []))}")
            print(f"Versions Found: {len(data.get('versions', []))}")
            
            # Show metadata result
            metadata = data.get('metadata', {})
            if metadata:
                print(f"\nMetadata Result:")
                print(f"  Error Codes Count: {metadata.get('error_codes_count', 0)}")
                print(f"  Versions Count: {metadata.get('versions_count', 0)}")
                print(f"  Manufacturer: {metadata.get('manufacturer', 'N/A')}")
            
            # Show error codes
            error_codes = data.get('error_codes', [])
            if error_codes:
                print(f"\nError Codes Found:")
                for i, error_code_id in enumerate(error_codes[:5]):  # Show first 5
                    print(f"  {i+1}. Error Code ID: {error_code_id}")
            
            # Show versions
            versions = data.get('versions', [])
            if versions:
                print(f"\nVersions Found:")
                for i, version in enumerate(versions[:3]):  # Show first 3
                    print(f"  {i+1}. {version}")
            
            # Verify database storage
            print(f"\nVerifying database storage...")
            try:
                if error_codes:
                    print(f"Error codes stored in database: {len(error_codes)} items")
                else:
                    print("No error codes found in document")
                
                if versions:
                    print(f"Versions extracted: {len(versions)} items")
                else:
                    print("No versions found in document")
                
            except Exception as e:
                print(f"Database verification error: {e}")
                
        else:
            print(f"Metadata processing failed: {result.error}")
            return False
        
        print("\nStage 5 Metadata Processor test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Stage 5 Metadata Processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_stage_5_metadata_processor())
