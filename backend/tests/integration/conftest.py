"""
KRAI Integration Test Configuration
===================================

Pytest configuration and fixtures for integration testing of the complete KRAI pipeline.
This module provides session-scoped fixtures for database, storage, AI services,
and environment isolation to ensure consistent and repeatable integration tests.
"""

import os
import sys
import pytest
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Generator
from pathlib import Path
from tempfile import TemporaryDirectory
import uuid

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.database_service_production import DatabaseService
from services.object_storage_service import ObjectStorageService
from services.storage_factory import create_storage_service
from services.ai_service import AIService
from services.config_service import ConfigService
from services.features_service import FeaturesService
from services.multimodal_search_service import MultimodalSearchService
from pipeline.master_pipeline import KRMasterPipeline

# Test configuration
TEST_CONFIG = {
    'test_db_name': 'krai_test',
    'test_buckets': {
        'documents': 'test-documents',
        'images': 'test-images',
        'videos': 'test-videos',
        'tables': 'test-tables',
        'temp': 'test-temp'
    },
    'cleanup_after_test': True,
    'preserve_test_data': False
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_database() -> AsyncGenerator[DatabaseService, None]:
    """
    Session-scoped database fixture for integration tests.
    
    Provides a clean database connection with test schema isolation.
    Automatically handles setup and teardown of test database.
    """
    # Load test environment
    from dotenv import load_dotenv
    test_env_path = Path(__file__).parent.parent.parent / ".env.test"
    if test_env_path.exists():
        load_dotenv(test_env_path)
    else:
        load_dotenv()  # Fallback to main .env
    
    # Initialize database service
    database_service = DatabaseService()
    
    try:
        # Connect to test database
        await database_service.connect()
        
        # Verify test database schema
        schemas = await database_service.execute_query(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'krai_%'"
        )
        
        if not schemas:
            pytest.skip("No KRAI schemas found in test database")
        
        logging.info(f"Connected to test database with schemas: {[s['schema_name'] for s in schemas]}")
        
        yield database_service
        
    except Exception as e:
        pytest.fail(f"Failed to setup test database: {e}")
    
    finally:
        # Cleanup test data if enabled
        if TEST_CONFIG['cleanup_after_test']:
            await _cleanup_test_data(database_service)
        
        await database_service.disconnect()

@pytest.fixture(scope="session")
async def test_storage() -> AsyncGenerator[ObjectStorageService, None]:
    """
    Session-scoped storage fixture for integration tests.
    
    Provides isolated storage buckets for test files.
    Automatically creates test buckets and cleans them up after tests.
    """
    # Initialize storage service
    storage_service = create_storage_service()
    
    try:
        await storage_service.connect()
        
        # Create test buckets
        for bucket_type, bucket_name in TEST_CONFIG['test_buckets'].items():
            try:
                await storage_service.create_bucket(bucket_name)
                logging.info(f"Created test bucket: {bucket_name}")
            except Exception as e:
                # Bucket might already exist
                logging.warning(f"Test bucket {bucket_name} already exists or failed to create: {e}")
        
        yield storage_service
        
    except Exception as e:
        pytest.fail(f"Failed to setup test storage: {e}")
    
    finally:
        # Cleanup test buckets if enabled
        if TEST_CONFIG['cleanup_after_test']:
            await _cleanup_test_buckets(storage_service)
        
        await storage_service.disconnect()

@pytest.fixture(scope="session")
async def test_ai_service() -> AsyncGenerator[AIService, None]:
    """
    Session-scoped AI service fixture for integration tests.
    
    Provides AI service connection for embedding generation and LLM calls.
    Uses test configuration to avoid affecting production metrics.
    """
    ai_service = AIService()
    
    try:
        await ai_service.connect()
        
        # Test basic embedding generation
        test_embedding = await ai_service.generate_embeddings("test query")
        if not test_embedding:
            pytest.fail("AI service failed to generate test embedding")
        
        logging.info("AI service connected and tested successfully")
        
        yield ai_service
        
    except Exception as e:
        pytest.fail(f"Failed to setup test AI service: {e}")
    
    finally:
        await ai_service.disconnect()

@pytest.fixture(scope="session")
async def test_pipeline(
    test_database: DatabaseService,
    test_storage: ObjectStorageService,
    test_ai_service: AIService
) -> AsyncGenerator[KRMasterPipeline, None]:
    """
    Session-scoped pipeline fixture for integration tests.
    
    Provides fully initialized master pipeline with test services.
    Ready for end-to-end processing tests.
    """
    pipeline = KRMasterPipeline()
    
    try:
        # Initialize pipeline with test services
        await pipeline.initialize_services()
        
        logging.info("Master pipeline initialized for integration tests")
        
        yield pipeline
        
    except Exception as e:
        pytest.fail(f"Failed to setup test pipeline: {e}")

@pytest.fixture(scope="session")
async def test_search_service(
    test_database: DatabaseService,
    test_ai_service: AIService
) -> AsyncGenerator[MultimodalSearchService, None]:
    """
    Session-scoped search service fixture for integration tests.
    
    Provides multimodal search service with test database and AI services.
    """
    search_service = MultimodalSearchService(
        database_service=test_database,
        ai_service=test_ai_service,
        default_threshold=0.5,
        default_limit=10
    )
    
    yield search_service

@pytest.fixture
def sample_test_document() -> Dict[str, Any]:
    """
    Fixture providing sample test document data.
    
    Returns a dictionary with test document metadata for processing tests.
    """
    return {
        'filename': 'test_manual.pdf',
        'file_path': str(Path(__file__).parent.parent.parent / 'service_documents' / 'test_manual.pdf'),
        'file_size': 1024000,  # 1MB
        'document_type': 'service_manual',
        'manufacturer': 'TestCorp',
        'model': 'C4080',
        'language': 'en'
    }

@pytest.fixture
def temporary_test_file() -> Generator[Path, None, None]:
    """
    Fixture providing a temporary file for test operations.
    
    Creates a temporary file that is automatically cleaned up after the test.
    """
    with TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / f"test_file_{uuid.uuid4().hex}.txt"
        temp_file.write_text("This is a test file for integration testing.")
        yield temp_file

@pytest.fixture
def test_queries() -> Dict[str, list]:
    """
    Fixture providing test queries for search functionality.
    
    Returns categorized test queries for different search scenarios.
    """
    return {
        'error_codes': ["error 900.01", "error 900.02", "error 920.00"],
        'components': ["fuser unit", "paper tray", "toner cartridge"],
        'procedures': ["maintenance procedures", "installation guide", "troubleshooting"],
        'general': ["technical specifications", "user manual", "warranty information"]
    }

async def _cleanup_test_data(database_service: DatabaseService):
    """Clean up test data from database."""
    try:
        # Clean up test documents
        await database_service.execute_query(
            "DELETE FROM krai_core.documents WHERE filename LIKE 'test_%'"
        )
        
        # Clean up test chunks
        await database_service.execute_query(
            "DELETE FROM krai_intelligence.chunks WHERE document_id IN "
            "(SELECT id FROM krai_core.documents WHERE filename LIKE 'test_%')"
        )
        
        # Clean up test embeddings
        await database_service.execute_query(
            "DELETE FROM krai_intelligence.embeddings_v2 WHERE document_id IN "
            "(SELECT id FROM krai_core.documents WHERE filename LIKE 'test_%')"
        )
        
        logging.info("Test data cleanup completed")
        
    except Exception as e:
        logging.warning(f"Test data cleanup failed: {e}")

async def _cleanup_test_buckets(storage_service: ObjectStorageService):
    """Clean up test storage buckets."""
    try:
        for bucket_name in TEST_CONFIG['test_buckets'].values():
            try:
                # List and delete all objects in bucket
                objects = await storage_service.list_objects(bucket_name)
                for obj in objects:
                    await storage_service.delete_object(bucket_name, obj['name'])
                
                # Delete bucket
                await storage_service.delete_bucket(bucket_name)
                logging.info(f"Cleaned up test bucket: {bucket_name}")
                
            except Exception as e:
                logging.warning(f"Failed to cleanup test bucket {bucket_name}: {e}")
        
    except Exception as e:
        logging.warning(f"Test bucket cleanup failed: {e}")

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "storage: mark test as requiring storage"
    )

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for all tests."""
    # Set test environment variables
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    yield
    
    # Cleanup environment variables
    os.environ.pop('TESTING', None)
    os.environ.pop('LOG_LEVEL', None)
