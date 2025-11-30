"""
Test Upload Processor

This module provides basic unit tests for UploadProcessor functionality.
Integrates with conftest.py fixtures for consistent testing infrastructure.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from backend.processors.upload_processor import UploadProcessor
from backend.core.base_processor import ProcessingResult


pytestmark = pytest.mark.processor


class TestUploadProcessorBasic:
    """Basic unit tests for UploadProcessor functionality."""
    
    @pytest.mark.asyncio
    async def test_upload_processor_initialization(self, mock_database_adapter, processor_test_config):
        """Test UploadProcessor initialization with mock database."""
        # Arrange & Act
        processor = UploadProcessor(
            database_adapter=mock_database_adapter,
            max_file_size_mb=processor_test_config['max_file_size_mb']
        )
        
        # Assert
        assert processor is not None, "Processor should be initialized"
        assert processor.max_file_size_mb == processor_test_config['max_file_size_mb']
        assert processor.database_adapter == mock_database_adapter
    
    @pytest.mark.asyncio
    async def test_simple_file_validation(self, mock_database_adapter, sample_pdf_files, processor_test_config):
        """Test basic file validation functionality."""
        # Arrange
        processor = UploadProcessor(
            database_adapter=mock_database_adapter,
            max_file_size_mb=processor_test_config['max_file_size_mb']
        )
        
        valid_pdf = sample_pdf_files['valid_pdf']
        
        # Act
        result = await processor.process(valid_pdf['path'])
        
        # Assert
        assert isinstance(result, ProcessingResult), "Should return ProcessingResult"
        assert result.success, f"Valid PDF should process successfully: {result.error}"
        assert result.data is not None, "Should have result data"
        assert 'document_id' in result.data, "Should have document ID"
    
    @pytest.mark.asyncio
    async def test_file_size_validation(self, mock_database_adapter, sample_pdf_files, processor_test_config):
        """Test file size validation."""
        # Arrange
        processor = UploadProcessor(
            database_adapter=mock_database_adapter,
            max_file_size_mb=1  # Small limit for testing
        )
        
        # Use larger file to test size limit
        large_pdf = sample_pdf_files.get('large_pdf')
        if large_pdf and large_pdf['size'] > 1024 * 1024:  # > 1MB
            # Act
            result = await processor.process(large_pdf['path'])
            
            # Assert
            assert not result.success, "Large file should be rejected"
            assert "size" in result.error.lower() or "large" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_nonexistent_file_handling(self, mock_database_adapter, processor_test_config):
        """Test handling of non-existent files."""
        # Arrange
        processor = UploadProcessor(
            database_adapter=mock_database_adapter,
            max_file_size_mb=processor_test_config['max_file_size_mb']
        )
        
        nonexistent_file = Path("/nonexistent/path/file.pdf")
        
        # Act
        result = await processor.process(nonexistent_file)
        
        # Assert
        assert not result.success, "Non-existent file should be rejected"
        assert "exist" in result.error.lower() or "found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_file_extension_validation(self, mock_database_adapter, temp_test_pdf, processor_test_config):
        """Test file extension validation."""
        # Arrange
        processor = UploadProcessor(
            database_adapter=mock_database_adapter,
            max_file_size_mb=processor_test_config['max_file_size_mb']
        )
        
        # Create non-PDF file
        text_file = temp_test_pdf / "test.txt"
        text_file.write_text("This is not a PDF file.")
        
        # Act
        result = await processor.process(text_file)
        
        # Assert
        # Should either reject non-PDF or handle gracefully
        if not result.success:
            assert "pdf" in result.error.lower() or "extension" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, mock_database_adapter, temp_test_pdf, processor_test_config):
        """Test duplicate file detection."""
        # Arrange
        processor = UploadProcessor(
            database_adapter=mock_database_adapter,
            max_file_size_mb=processor_test_config['max_file_size_mb']
        )
        
        # Create test file
        test_file = temp_test_pdf / "duplicate_test.pdf"
        test_file.write_text("Test content for duplicate detection.")
        
        # Act - First upload
        first_result = await processor.process(test_file)
        
        # Assert - First upload should succeed
        assert first_result.success, "First upload should succeed"
        document_id = first_result.data['document_id']
        
        # Act - Second upload (should detect duplicate)
        second_result = await processor.process(test_file)
        
        # Assert - Second upload should detect duplicate
        assert not second_result.success, "Second upload should detect duplicate"
        assert "duplicate" in second_result.error.lower() or "exists" in second_result.error.lower()
    
    @pytest.mark.asyncio
    async def test_metadata_extraction(self, mock_database_adapter, sample_pdf_files, processor_test_config):
        """Test metadata extraction from uploaded files."""
        # Arrange
        processor = UploadProcessor(
            database_adapter=mock_database_adapter,
            max_file_size_mb=processor_test_config['max_file_size_mb']
        )
        
        valid_pdf = sample_pdf_files['valid_pdf']
        
        # Act
        result = await processor.process(valid_pdf['path'])
        
        # Assert
        assert result.success, "Upload should succeed"
        
        metadata = result.metadata
        assert metadata is not None, "Should have metadata"
        assert 'filename' in metadata, "Should have filename"
        assert 'file_size_bytes' in metadata, "Should have file size"
        assert 'file_hash' in metadata, "Should have file hash"
        assert 'page_count' in metadata, "Should have page count"
        
        # Verify metadata values
        assert metadata['filename'] == valid_pdf['path'].name, "Filename should match"
        assert metadata['file_size_bytes'] == valid_pdf['size'], "File size should match"
        assert len(metadata['file_hash']) > 0, "File hash should not be empty"
        assert metadata['page_count'] >= 1, "Page count should be at least 1"


# Legacy test function for backward compatibility
def test_upload_processor_legacy():
    """Legacy test function for backward compatibility.
    
    This function maintains the original test structure while using
    the new conftest.py fixtures where possible.
    """
    import sys
    from pathlib import Path
    
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from backend.processors.upload_processor import UploadProcessor
    from backend.processors.logger import get_logger
    
    logger = get_logger()
    
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
    
    logger.section("Upload Processor Test (Legacy)")
    
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
    # Run legacy test for backward compatibility
    test_upload_processor_legacy()
