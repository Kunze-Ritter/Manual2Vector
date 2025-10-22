"""
Test Upload Processor
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.processors.upload_processor import UploadProcessor, BatchUploadProcessor
from backend.processors.logger import get_logger

logger = get_logger()


def test_upload_processor():
    """Test upload processor with AccurioPress PDF"""
    
    # Mock Supabase client for testing (we'll use real one later)
    class MockSupabase:
        def table(self, name):
            return self
        
        def select(self, *args):
            return self
        
        def eq(self, field, value):
            return self
        
        def execute(self):
            # Return empty result (no duplicates)
            class Result:
                data = []
            return Result()
        
        def insert(self, data):
            logger.info(f"[MOCK] Would insert: {data.get('filename', 'unknown')}")
            return self
        
        def update(self, data):
            logger.info(f"[MOCK] Would update document")
            return self
    
    # Test file
    pdf_path = Path("c:/Users/haast/Docker/KRAI-minimal/AccurioPress_C4080_C4070_C84hc_C74hc_AccurioPrint_C4065_C4065P_SM_EN_20250127.pdf")
    
    if not pdf_path.exists():
        logger.error(f"Test PDF not found: {pdf_path}")
        return
    
    logger.section("Upload Processor Test")
    
    # Initialize processor with mock
    processor = UploadProcessor(
        supabase_client=MockSupabase(),
        max_file_size_mb=500
    )
    
    # Test upload
    logger.info("Testing file upload...")
    result = processor.process_upload(pdf_path)
    
    # Check results
    print("\n=== RESULTS ===")
    
    if result['success']:
        print("✓ Upload successful!")
        print(f"  Document ID: {result['document_id']}")
        print(f"  Status: {result['status']}")
        print(f"  File hash: {result['file_hash'][:16]}...")
        
        metadata = result.get('metadata', {})
        print(f"\n  Metadata:")
        print(f"    Filename: {metadata.get('filename')}")
        print(f"    Pages: {metadata.get('page_count')}")
        print(f"    Size: {metadata.get('file_size_bytes', 0) / (1024*1024):.1f} MB")
        print(f"    Title: {metadata.get('title', 'N/A')}")
    else:
        print(f"✗ Upload failed: {result['error']}")
    
    # Test validation
    print("\n=== VALIDATION TESTS ===")
    
    # Test 1: Non-existent file
    print("\nTest 1: Non-existent file")
    fake_path = Path("nonexistent.pdf")
    result = processor.process_upload(fake_path)
    if not result['success']:
        print("  ✓ Correctly rejected non-existent file")
    else:
        print("  ✗ Should have rejected non-existent file")
    
    # Test 2: Valid file (should pass)
    print("\nTest 2: Valid PDF")
    result = processor.process_upload(pdf_path)
    if result['success']:
        print("  ✓ Correctly accepted valid PDF")
    else:
        print("  ✗ Should have accepted valid PDF")


if __name__ == "__main__":
    test_upload_processor()
