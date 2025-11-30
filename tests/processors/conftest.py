"""
Processor Test Configuration and Fixtures

Comprehensive pytest fixtures for processor testing including:
- Mock DatabaseAdapter with all required methods
- Sample PDF files for various test scenarios  
- Temporary test PDF creation
- Mock StageTracker
- Processor test configuration
- Cleanup utilities

This module provides session- and function-scoped fixtures for
testing UploadProcessor, DocumentProcessor, and OptimizedTextProcessor.
"""

import os
import sys
import pytest
import asyncio
import logging
import tempfile
import hashlib
from typing import AsyncGenerator, Dict, Any, Generator, List, Optional
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
import json

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.services.database_adapter import DatabaseAdapter
from backend.processors.stage_tracker import StageTracker
from backend.core.base_processor import ProcessingContext, ProcessingResult
from backend.core.data_models import DocumentModel


# Test configuration
PROCESSOR_TEST_CONFIG = {
    'max_file_size_mb': 100,
    'allowed_extensions': ['.pdf'],
    'chunk_size': 1000,
    'chunk_overlap': 200,
    'enable_ocr_fallback': True,
    'enable_hierarchical_chunking': True,
    'pdf_engine': 'pymupdf',
    'structured_line_cap': 1000,
    'test_timeout': 600,
    'temp_dir_suffix': 'krai_processor_tests'
}


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def mock_database_adapter() -> AsyncGenerator[DatabaseAdapter, None]:
    """
    Mock DatabaseAdapter with all required methods for processor testing.
    
    Provides realistic mock responses for:
    - Document operations (create, get_by_hash, update)
    - Processing queue operations
    - RPC calls for StageTracker
    - Chunk operations
    - Generic query execution
    """
    
    class MockDatabaseAdapter(DatabaseAdapter):
        """Mock implementation of DatabaseAdapter for testing."""
        
        def __init__(self):
            # Skip ABC initialization to avoid abstract method errors
            self.documents = {}  # Mock storage
            self.chunks = {}    # Mock storage
            self.processing_queue = []  # Mock storage
            self.logger = logging.getLogger("mock_database_adapter")
        
        async def connect(self) -> None:
            """Mock connect - does nothing."""
            pass
        
        async def test_connection(self) -> bool:
            """Mock test connection - always returns True."""
            return True
        
        async def create_document(self, document: DocumentModel) -> str:
            """Mock create document with deduplication."""
            doc_id = str(uuid4())
            self.documents[doc_id] = {
                'id': doc_id,
                'filename': document.filename,
                'file_hash': document.file_hash,
                'file_size_bytes': document.file_size_bytes,
                'page_count': document.page_count,
                'document_type': document.document_type,
                'manufacturer': document.manufacturer,
                'model': document.model,
                'language': document.language,
                'title': document.title,
                'author': document.author,
                'creator': document.creator,
                'creation_date': document.creation_date,
                'status': 'uploaded',
                'created_at': document.created_at,
                'updated_at': document.updated_at
            }
            return doc_id
        
        async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
            """Mock get document by ID."""
            return self.documents.get(document_id)
        
        async def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
            """Mock get document by hash for deduplication."""
            for doc in self.documents.values():
                if doc.get('file_hash') == file_hash:
                    return doc
            return None
        
        async def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
            """Mock update document."""
            if document_id in self.documents:
                self.documents[document_id].update(updates)
                return True
            return False
        
        async def create_processing_queue_item(self, item) -> str:
            """Mock create processing queue item."""
            item_id = str(uuid4())
            self.processing_queue.append({
                'id': item_id,
                'document_id': item.document_id,
                'stage': item.stage,
                'status': 'pending',
                'created_at': item.created_at
            })
            return item_id
        
        async def create_chunk(self, chunk) -> str:
            """Mock create chunk."""
            chunk_id = str(uuid4())
            self.chunks[chunk_id] = {
                'id': chunk_id,
                'document_id': chunk.document_id,
                'chunk_index': chunk.chunk_index,
                'content': chunk.content,
                'content_hash': chunk.content_hash,
                'char_count': chunk.char_count,
                'page_start': chunk.page_start,
                'page_end': chunk.page_end,
                'chunk_type': chunk.chunk_type,
                'metadata': chunk.metadata or {},
                'created_at': chunk.created_at
            }
            return chunk_id
        
        async def create_chunk_async(self, chunk_data: Dict[str, Any]) -> str:
            """Mock create chunk from dictionary."""
            chunk_id = str(uuid4())
            self.chunks[chunk_id] = chunk_data
            return chunk_id
        
        async def get_chunk_by_document_and_index(self, document_id: str, chunk_index: int) -> Optional[Dict[str, Any]]:
            """Mock get chunk by document and index."""
            for chunk in self.chunks.values():
                if chunk.get('document_id') == document_id and chunk.get('chunk_index') == chunk_index:
                    return chunk
            return None
        
        async def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
            """Mock execute query - returns empty list for most queries."""
            # Handle specific queries for testing
            if 'vw_stage_statistics' in query:
                return [
                    {'stage_name': 'upload', 'pending_count': 0, 'processing_count': 0, 
                     'completed_count': 1, 'failed_count': 0, 'skipped_count': 0, 'avg_duration_seconds': 5.0},
                    {'stage_name': 'text_extraction', 'pending_count': 0, 'processing_count': 0, 
                     'completed_count': 1, 'failed_count': 0, 'skipped_count': 0, 'avg_duration_seconds': 15.0}
                ]
            elif 'vw_documents' in query and params:
                document_id = params[0]
                if document_id in self.documents:
                    return [{'stage_status': {'upload': 'completed', 'text_extraction': 'completed'}}]
            return []
        
        async def rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
            """Mock RPC calls for StageTracker."""
            params = params or {}
            
            if function_name == 'krai_core.start_stage':
                self.logger.info(f"Mock RPC: start_stage {params}")
                return True
            elif function_name == 'krai_core.update_stage_progress':
                self.logger.info(f"Mock RPC: update_stage_progress {params}")
                return True
            elif function_name == 'krai_core.complete_stage':
                self.logger.info(f"Mock RPC: complete_stage {params}")
                return True
            elif function_name == 'krai_core.fail_stage':
                self.logger.info(f"Mock RPC: fail_stage {params}")
                return True
            elif function_name == 'krai_core.skip_stage':
                self.logger.info(f"Mock RPC: skip_stage {params}")
                return True
            elif function_name == 'krai_core.get_document_progress':
                return 100.0  # Mock 100% progress
            elif function_name == 'krai_core.get_current_stage':
                return 'completed'
            elif function_name == 'krai_core.can_start_stage':
                return True
            else:
                self.logger.warning(f"Mock RPC: Unknown function {function_name}")
                return None
        
        # Implement other abstract methods with minimal functionality
        async def create_manufacturer(self, manufacturer) -> str:
            return str(uuid4())
        
        async def get_manufacturer_by_name(self, name: str) -> Optional[Dict[str, Any]]:
            return None
        
        async def create_product_series(self, series) -> str:
            return str(uuid4())
        
        async def get_product_series_by_name(self, name: str, manufacturer_id: str) -> Optional[Dict[str, Any]]:
            return None
        
        async def create_product(self, product) -> str:
            return str(uuid4())
        
        async def get_product_by_model(self, model_number: str, manufacturer_id: str) -> Optional[Dict[str, Any]]:
            return None
        
        async def create_image(self, image) -> str:
            return str(uuid4())
        
        async def get_image_by_hash(self, image_hash: str) -> Optional[Dict[str, Any]]:
            return None
        
        async def get_images_by_document(self, document_id: str) -> List[Dict[str, Any]]:
            return []
        
        async def create_intelligence_chunk(self, chunk) -> str:
            return str(uuid4())
        
        async def create_embedding(self, embedding) -> str:
            return str(uuid4())
        
        async def get_embedding_by_chunk_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
            return None
        
        async def get_embeddings_by_chunk_ids(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
            return []
        
        async def search_embeddings(self, query_embedding: List[float], limit: int = 10, 
                                  match_threshold: float = 0.7, match_count: int = 10) -> List[Dict[str, Any]]:
            return []
        
        async def create_error_code(self, error_code) -> str:
            return str(uuid4())
        
        async def log_search_analytics(self, analytics) -> str:
            return str(uuid4())
        
        async def update_processing_queue_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
            return True
        
        async def log_audit_event(self, event) -> str:
            return str(uuid4())
        
        async def get_system_status(self) -> Dict[str, Any]:
            return {'status': 'healthy'}
        
        async def count_chunks_by_document(self, document_id: str) -> int:
            return len([c for c in self.chunks.values() if c.get('document_id') == document_id])
        
        async def count_images_by_document(self, document_id: str) -> int:
            return 0
        
        async def check_embedding_exists(self, chunk_id: str) -> bool:
            return False
        
        async def count_links_by_document(self, document_id: str) -> int:
            return 0
        
        async def create_link(self, link_data: Dict[str, Any]) -> str:
            return str(uuid4())
        
        async def create_video(self, video_data: Dict[str, Any]) -> str:
            return str(uuid4())
        
        async def create_print_defect(self, defect) -> str:
            return str(uuid4())
    
    yield MockDatabaseAdapter()


@pytest.fixture(scope="function")
def sample_pdf_files() -> Dict[str, Dict[str, Any]]:
    """
    Dictionary with various test PDF scenarios for comprehensive testing.
    
    Returns:
        Dictionary containing different PDF test scenarios:
        - valid_pdf: Normal service manual PDF
        - corrupted_pdf: Corrupted PDF file
        - empty_pdf: PDF with no pages
        - large_pdf: PDF over size limit
        - ocr_required_pdf: Scanned PDF without text
        - multi_language_pdf: PDF with multiple languages
    """
    
    # Create temporary directory for test files
    temp_dir = Path(tempfile.mkdtemp(suffix=PROCESSOR_TEST_CONFIG['temp_dir_suffix']))
    
    test_files = {}
    
    # 1. Valid PDF - Create a minimal valid PDF
    valid_pdf_path = temp_dir / "valid_service_manual.pdf"
    try:
        # Create a simple PDF using PyMuPDF if available
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "This is a test service manual PDF.\n\nIt contains technical information.")
        page.insert_text((72, 120), "Manufacturer: TestCorp\nModel: C4080\nLanguage: English")
        doc.save(valid_pdf_path)
        doc.close()
        
        test_files['valid_pdf'] = {
            'path': valid_pdf_path,
            'size': valid_pdf_path.stat().st_size,
            'exists': True,
            'pages': 1,
            'description': 'Valid service manual PDF with text'
        }
    except ImportError:
        # Fallback: create a simple text file with .pdf extension
        valid_pdf_path.write_text("Mock PDF content for testing")
        test_files['valid_pdf'] = {
            'path': valid_pdf_path,
            'size': valid_pdf_path.stat().st_size,
            'exists': True,
            'pages': 1,
            'description': 'Mock PDF file (text-based)'
        }
    
    # 2. Corrupted PDF - invalid PDF content
    corrupted_pdf_path = temp_dir / "corrupted.pdf"
    corrupted_pdf_path.write_bytes(b"This is not a valid PDF file content\x00\x01\x02invalid")
    test_files['corrupted_pdf'] = {
        'path': corrupted_pdf_path,
        'size': corrupted_pdf_path.stat().st_size,
        'exists': True,
        'pages': 0,
        'description': 'Corrupted PDF file with invalid content'
    }
    
    # 3. Empty PDF - zero bytes
    empty_pdf_path = temp_dir / "empty.pdf"
    empty_pdf_path.write_bytes(b"")
    test_files['empty_pdf'] = {
        'path': empty_pdf_path,
        'size': 0,
        'exists': True,
        'pages': 0,
        'description': 'Empty PDF file (zero bytes)'
    }
    
    # 4. Large PDF - create a file larger than max size
    large_pdf_path = temp_dir / "large.pdf"
    large_content = "Large PDF content " * (1024 * 1024)  # ~16MB
    large_pdf_path.write_text(large_content)
    test_files['large_pdf'] = {
        'path': large_pdf_path,
        'size': large_pdf_path.stat().st_size,
        'exists': True,
        'pages': 1,
        'description': f'Large PDF file ({large_pdf_path.stat().st_size / (1024*1024):.1f} MB)'
    }
    
    # 5. OCR-required PDF - PDF with no extractable text (simulated)
    ocr_pdf_path = temp_dir / "ocr_required.pdf"
    # Write binary data that looks like PDF but has no text
    ocr_pdf_path.write_bytes(b"%PDF-1.4\n%âãÏÓ\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n")
    test_files['ocr_required_pdf'] = {
        'path': ocr_pdf_path,
        'size': ocr_pdf_path.stat().st_size,
        'exists': True,
        'pages': 1,
        'description': 'PDF requiring OCR (no extractable text)'
    }
    
    # 6. Multi-language PDF
    multi_lang_pdf_path = temp_dir / "multi_language.pdf"
    multi_lang_content = """English: This is a service manual.
Deutsch: Dies ist ein Servicehandbuch.
Français: Cececi est un manuel de service.
Español: Este es un manual de servicio."""
    multi_lang_pdf_path.write_text(multi_lang_content)
    test_files['multi_language_pdf'] = {
        'path': multi_lang_pdf_path,
        'size': multi_lang_pdf_path.stat().st_size,
        'exists': True,
        'pages': 1,
        'description': 'Multi-language PDF content'
    }
    
    yield test_files
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function") 
def temp_test_pdf() -> Generator[Path, None, None]:
    """
    Fixture for creating temporary test PDFs with PyMuPDF.
    
    Yields a temporary directory path where test PDFs can be created.
    Automatically cleans up after the test.
    """
    with tempfile.TemporaryDirectory(suffix=PROCESSOR_TEST_CONFIG['temp_dir_suffix']) as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="function")
def mock_stage_tracker(mock_database_adapter: DatabaseAdapter) -> StageTracker:
    """
    Mock StageTracker with all stage tracking methods.
    
    Provides a real StageTracker instance connected to the mock database adapter.
    All RPC calls are mocked and logged.
    """
    return StageTracker(database_adapter=mock_database_adapter)


@pytest.fixture(scope="function")
def processor_test_config() -> Dict[str, Any]:
    """
    Configuration for processor tests.
    
    Returns a dictionary with test configuration including:
    - File size limits
    - Allowed extensions  
    - Chunking parameters
    - OCR settings
    - PDF engine selection
    """
    return PROCESSOR_TEST_CONFIG.copy()


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_documents(mock_database_adapter: DatabaseAdapter):
    """
    Autouse fixture for cleaning up test documents after each test.
    
    Automatically clears the mock database adapter's storage after each test
    to ensure test isolation.
    """
    yield
    
    # Cleanup mock storage
    mock_database_adapter.documents.clear()
    mock_database_adapter.chunks.clear()
    mock_database_adapter.processing_queue.clear()


@pytest.fixture(scope="function")
def processing_context() -> ProcessingContext:
    """
    Create a basic ProcessingContext for testing.
    
    Returns a ProcessingContext with minimal required fields for processor testing.
    """
    return ProcessingContext(
        document_id=str(uuid4()),
        file_path=Path("/tmp/test.pdf"),
        metadata={}
    )


@pytest.fixture(scope="function")
def sample_document_metadata() -> Dict[str, Any]:
    """
    Sample document metadata for testing.
    
    Returns realistic metadata that would be extracted from a service manual PDF.
    """
    return {
        'filename': 'test_service_manual.pdf',
        'file_size_bytes': 2048576,  # 2MB
        'page_count': 25,
        'document_type': 'service_manual',
        'manufacturer': 'TestCorp',
        'model': 'C4080',
        'language': 'en',
        'title': 'Test Service Manual',
        'author': 'TestCorp Technical Documentation',
        'creator': 'PDF Generator',
        'creation_date': '2024-01-15T10:30:00Z',
        'file_hash': hashlib.sha256(b"test content").hexdigest()
    }


# Pytest configuration for processor tests
def pytest_configure(config):
    """Configure pytest with processor-specific markers."""
    config.addinivalue_line("markers", "processor: Tests for processor components")
    config.addinivalue_line("markers", "upload: Tests for UploadProcessor")
    config.addinivalue_line("markers", "text: Tests for TextProcessor")
    config.addinivalue_line("markers", "document: Tests for DocumentProcessor")
    config.addinivalue_line("markers", "chunking: Tests for chunking functionality")
    config.addinivalue_line("markers", "extraction: Tests for text extraction")
    config.addinivalue_line("markers", "stage_tracking: Tests for stage tracking")


@pytest.fixture(scope="function")
def mock_websocket_callback():
    """
    Mock WebSocket callback for StageTracker testing.
    
    Returns an AsyncMock that can be used to verify WebSocket events
    are sent during stage tracking.
    """
    callback = AsyncMock()
    return callback
