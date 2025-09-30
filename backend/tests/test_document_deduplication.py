import asyncio
import os
import sys
import hashlib
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

from services.database_service import DatabaseService
from core.data_models import DocumentModel, DocumentType

async def test_document_deduplication():
    """Test document deduplication based on file_hash"""
    print("Testing Document Deduplication")
    print("=" * 50)
    
    try:
        # Initialize database service
        supabase_url = os.getenv("SUPABASE_URL", "https://crujfdpqdjzcfqeyhang.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        database_service = DatabaseService(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        await database_service.connect()
        print("Database connected")
        
        # Create test document
        test_hash = hashlib.sha256(b"test_document_content").hexdigest()
        print(f"Test hash: {test_hash[:16]}...")
        
        document1 = DocumentModel(
            filename="test_document.pdf",
            original_filename="test_document.pdf",
            file_size=1024,
            file_hash=test_hash,
            document_type=DocumentType.SERVICE_MANUAL,
            language="en",
            processing_status="pending",
            manufacturer="Test",
            model="Test Model",
            series="Test Series",
            version="1.0"
        )
        
        # First upload - should create new document
        print("\n1. First upload...")
        doc_id_1 = await database_service.create_document(document1)
        print(f"   Created document: {doc_id_1}")
        
        # Second upload with same hash - should return existing document
        print("\n2. Second upload with same hash...")
        document2 = DocumentModel(
            filename="test_document_copy.pdf",  # Different filename
            original_filename="test_document_copy.pdf",
            file_size=2048,  # Different size
            file_hash=test_hash,  # Same hash
            document_type=DocumentType.SERVICE_MANUAL,
            language="en",
            processing_status="pending",
            manufacturer="Test",
            model="Test Model",
            series="Test Series",
            version="1.0"
        )
        
        doc_id_2 = await database_service.create_document(document2)
        print(f"   Returned document: {doc_id_2}")
        
        # Verify deduplication worked
        if doc_id_1 == doc_id_2:
            print("\nSUCCESS: Deduplication worked!")
            print(f"   Same document ID returned: {doc_id_1}")
        else:
            print("\nFAILED: Deduplication failed!")
            print(f"   Different IDs: {doc_id_1} vs {doc_id_2}")
        
        # Third upload with different hash - should create new document
        print("\n3. Third upload with different hash...")
        different_hash = hashlib.sha256(b"different_document_content").hexdigest()
        print(f"   Different hash: {different_hash[:16]}...")
        
        document3 = DocumentModel(
            filename="different_document.pdf",
            original_filename="different_document.pdf",
            file_size=1024,
            file_hash=different_hash,
            document_type=DocumentType.SERVICE_MANUAL,
            language="en",
            processing_status="pending",
            manufacturer="Test",
            model="Test Model",
            series="Test Series",
            version="1.0"
        )
        
        doc_id_3 = await database_service.create_document(document3)
        print(f"   Created new document: {doc_id_3}")
        
        # Verify different document was created
        if doc_id_3 != doc_id_1:
            print("\nSUCCESS: Different document created!")
            print(f"   New document ID: {doc_id_3}")
        else:
            print("\nFAILED: Same document ID returned for different hash!")
        
        print("\n" + "=" * 50)
        print("Deduplication Test Summary:")
        print(f"Document 1 (original): {doc_id_1}")
        print(f"Document 2 (duplicate): {doc_id_2}")
        print(f"Document 3 (different): {doc_id_3}")
        
        if doc_id_1 == doc_id_2 and doc_id_3 != doc_id_1:
            print("ALL TESTS PASSED: Deduplication working correctly!")
            return True
        else:
            print("SOME TESTS FAILED: Deduplication needs fixing!")
            return False
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_document_deduplication())
