"""
Shared fixtures for service testing.

Provides reusable fixtures for WebScrapingService, LinkEnrichmentService,
StructuredExtractionService, and ManufacturerCrawler tests.
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from typing import Dict, Any, List


# Pytest configuration
pytest_plugins = ['pytest_asyncio']


@pytest.fixture
def mock_db_client():
    """Mock Supabase client for database operations."""
    client = MagicMock()
    # Configure table() method to return chainable mock
    table_mock = MagicMock()
    table_mock.select.return_value = table_mock
    table_mock.insert.return_value = table_mock
    table_mock.update.return_value = table_mock
    table_mock.delete.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.in_.return_value = table_mock
    table_mock.neq.return_value = table_mock
    table_mock.lt.return_value = table_mock
    table_mock.lte.return_value = table_mock
    table_mock.limit.return_value = table_mock
    table_mock.order.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[], count=0)
    client.table.return_value = table_mock
    return client


@pytest.fixture
def mock_database_service(mock_db_client):
    """Mock database service with client."""
    service = MagicMock()
    service.client = mock_db_client
    service.service_client = mock_db_client
    return service


@pytest.fixture
def mock_config_service():
    """Mock ConfigService with scraping configuration."""
    config = MagicMock()
    config.get_scraping_config.return_value = {
        'backend': 'firecrawl',
        'firecrawl_api_url': 'http://localhost:3002',
        'firecrawl_llm_provider': 'ollama',
        'firecrawl_model_name': 'llama3.2:latest',
        'enable_link_enrichment': True,
        'enable_manufacturer_crawling': True,
        'max_concurrency': 2,
    }
    return config


@pytest.fixture
def mock_web_scraping_service():
    """WebScrapingService in mock mode (no network calls)."""
    from backend.services.web_scraping_service import create_web_scraping_service
    return create_web_scraping_service(backend='firecrawl', config_service=None)


@pytest.fixture
def mock_firecrawl_backend():
    """Mock FirecrawlBackend with predefined responses."""
    backend = MagicMock()
    backend.backend_name = 'firecrawl'
    backend.scrape_url = AsyncMock(return_value={
        'success': True,
        'backend': 'firecrawl',
        'content': '# Test Content\n\nThis is markdown content.',
        'html': '<html><body>Test</body></html>',
        'metadata': {'status_code': 200}
    })
    backend.crawl_site = AsyncMock(return_value={
        'success': True,
        'backend': 'firecrawl',
        'total': 2,
        'pages': [
            {'url': 'http://example.com', 'content': 'Page 1', 'metadata': {}},
            {'url': 'http://example.com/page2', 'content': 'Page 2', 'metadata': {}}
        ]
    })
    backend.extract_structured_data = AsyncMock(return_value={
        'success': True,
        'backend': 'firecrawl',
        'data': {'model_number': 'C750i'},
        'confidence': 0.85
    })
    backend.map_urls = AsyncMock(return_value={
        'success': True,
        'backend': 'firecrawl',
        'urls': ['http://example.com/page1', 'http://example.com/page2'],
        'total': 2
    })
    backend.health_check = AsyncMock(return_value={
        'status': 'healthy',
        'backend': 'firecrawl'
    })
    return backend


@pytest.fixture
def mock_beautifulsoup_backend():
    """Mock BeautifulSoupBackend with predefined responses."""
    backend = MagicMock()
    backend.backend_name = 'beautifulsoup'
    backend.scrape_url = AsyncMock(return_value={
        'success': True,
        'backend': 'beautifulsoup',
        'content': 'Plain text content',
        'html': '<html><body>Test</body></html>',
        'metadata': {'status_code': 200}
    })
    backend.crawl_site = AsyncMock(return_value={
        'success': True,
        'backend': 'beautifulsoup',
        'total': 1,
        'pages': [
            {'url': 'http://example.com', 'content': 'Plain text', 'metadata': {}}
        ]
    })
    backend.map_urls = AsyncMock(return_value={
        'success': True,
        'backend': 'beautifulsoup',
        'urls': ['http://example.com/page1'],
        'total': 1
    })
    backend.extract_structured_data = AsyncMock(return_value={
        'success': False,
        'error': 'Structured extraction requires Firecrawl'
    })
    backend.health_check = AsyncMock(return_value={
        'status': 'healthy',
        'backend': 'beautifulsoup'
    })
    return backend


@pytest.fixture
def extraction_schemas():
    """Load extraction schemas from JSON file."""
    schema_path = Path(__file__).parent.parent.parent / 'schemas' / 'extraction_schemas.json'
    
    # For integration/E2E tests, fail fast if schema file is missing
    if not schema_path.exists():
        raise FileNotFoundError(f"Extraction schemas file not found at {schema_path}. "
                              "This file is required for integration and E2E tests.")
    
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture
def mock_extraction_schemas():
    """Mock extraction schemas for unit tests (when real file not needed)."""
    return {
        'product_specs': {
            'schema': {
                'type': 'object',
                'properties': {
                    'model_number': {'type': 'string'},
                    'manufacturer': {'type': 'string'}
                }
            },
            'version': '1.0',
            'description': 'Product specifications'
        },
        'error_codes': {
            'schema': {
                'type': 'object',
                'properties': {
                    'error_codes': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'code': {'type': 'string'},
                                'description': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            'version': '1.0',
            'description': 'Error codes'
        },
        'service_manual': {
            'schema': {
                'type': 'object',
                'properties': {
                    'manual_type': {'type': 'string'},
                    'product_models': {'type': 'array'}
                }
            },
            'version': '1.0',
            'description': 'Service manual metadata'
        },
        'parts_list': {
            'schema': {
                'type': 'object',
                'properties': {
                    'parts': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'part_number': {'type': 'string'},
                                'part_name': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            'version': '1.0',
            'description': 'Parts list'
        },
        'troubleshooting': {
            'schema': {
                'type': 'object',
                'properties': {
                    'issues': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'symptom': {'type': 'string'},
                                'solution': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            'version': '1.0',
            'description': 'Troubleshooting guide'
        }
    }


@pytest.fixture
def sample_link_data():
    """Sample link record for testing."""
    return {
        'id': 'test-link-id-123',
        'url': 'http://example.com/product',
        'link_type': 'external',
        'scrape_status': 'pending',
        'document_id': 'test-doc-id',
        'manufacturer_id': 'test-mfr-id'
    }


@pytest.fixture
def sample_crawl_schedule():
    """Sample crawl schedule for testing."""
    return {
        'id': 'test-schedule-id',
        'manufacturer_id': 'test-mfr-id',
        'crawl_type': 'support_pages',
        'start_url': 'http://example.com/support',
        'max_pages': 10,
        'max_depth': 2,
        'enabled': True
    }


@pytest.fixture
def sample_manufacturer_urls():
    """Sample manufacturer URLs for testing."""
    return [
        'http://example.com/products/c750i',
        'http://example.com/products/c650i',
        'http://example.com/support/c750i/manual',
        'http://example.com/support/c750i/error-codes',
        'http://example.com/parts/c750i'
    ]


@pytest.fixture
def sample_research_results():
    """Sample research results for testing."""
    return {
        'manufacturer': 'Konica Minolta',
        'model': 'C750i',
        'specifications': {
            'model_number': 'C750i',
            'manufacturer': 'Konica Minolta',
            'print_speed': '75 ppm',
            'resolution': '1200 x 1200 dpi'
        },
        'sources': [
            {'url': 'http://example.com/c750i', 'content': 'Product page content'},
            {'url': 'http://example.com/c750i/specs', 'content': 'Specifications content'}
        ],
        'scraping_backend': 'firecrawl',
        'extraction_confidence': 0.85
    }


@pytest.fixture
def mock_tavily_response():
    """Mock Tavily search response for testing."""
    return {
        'results': [
            {
                'title': 'Konica Minolta C750i Specifications',
                'url': 'http://example.com/c750i/specs',
                'content': 'Detailed specifications for C750i',
                'score': 0.95
            },
            {
                'title': 'C750i Product Page',
                'url': 'http://example.com/c750i',
                'content': 'Official product page',
                'score': 0.90
            },
            {
                'title': 'C750i Support',
                'url': 'http://example.com/c750i/support',
                'content': 'Support and documentation',
                'score': 0.85
            }
        ]
    }


@pytest.fixture
def run_async():
    """Helper to run async functions in tests."""
    def _run(coro):
        return asyncio.run(coro)
    return _run


@pytest.fixture
def mock_batch_task_service():
    """Mock BatchTaskService for crawler testing."""
    service = MagicMock()
    service.create_task = AsyncMock(return_value='task-id-123')
    service.get_task_status = AsyncMock(return_value={'status': 'completed'})
    return service


@pytest.fixture
def mock_manufacturer_website():
    """Mock manufacturer website responses."""
    return {
        'product_page': {
            'url': 'http://example.com/products/c750i',
            'content': '# Konica Minolta C750i\n\n**Print Speed:** 75 ppm\n**Resolution:** 1200 x 1200 dpi',
            'metadata': {'status_code': 200, 'content_type': 'text/html'}
        },
        'support_page': {
            'url': 'http://example.com/support/c750i',
            'content': '# C750i Support\n\n## Error Codes\n- 900.01: Fuser error\n- 900.02: Lamp error',
            'metadata': {'status_code': 200, 'content_type': 'text/html'}
        },
        'manual_page': {
            'url': 'http://example.com/manuals/c750i.pdf',
            'content': '# Service Manual C750i\n\n**Type:** Service Manual\n**Models:** C750i, C650i',
            'metadata': {'status_code': 200, 'content_type': 'application/pdf'}
        },
        'parts_page': {
            'url': 'http://example.com/parts/c750i',
            'content': '# Parts List C750i\n\n- A03U: Fuser Unit\n- A04V: Transfer Belt',
            'metadata': {'status_code': 200, 'content_type': 'text/html'}
        }
    }


@pytest.fixture
def sample_crawled_pages():
    """Sample crawled pages for testing."""
    return [
        {
            'id': 'page-1',
            'crawl_job_id': 'job-1',
            'url': 'http://example.com/products/c750i',
            'title': 'C750i Product Page',
            'content': '# Konica Minolta C750i\n\nPrint Speed: 75 ppm',
            'content_hash': 'hash1',
            'page_type': 'product_page',
            'status': 'scraped',
            'scraped_at': '2024-01-01T10:00:00Z'
        },
        {
            'id': 'page-2',
            'crawl_job_id': 'job-1',
            'url': 'http://example.com/support/c750i',
            'title': 'C750i Support',
            'content': '# C750i Support\n\nError: 900.01 Fuser error',
            'content_hash': 'hash2',
            'page_type': 'error_code_page',
            'status': 'scraped',
            'scraped_at': '2024-01-01T10:01:00Z'
        }
    ]


@pytest.fixture
def sample_structured_extractions():
    """Sample structured extractions for testing."""
    return [
        {
            'id': 'extraction-1',
            'source_type': 'crawled_page',
            'source_id': 'page-1',
            'extraction_type': 'product_specs',
            'extracted_data': {
                'model_number': 'C750i',
                'manufacturer': 'Konica Minolta',
                'print_speed': '75 ppm',
                'resolution': '1200 x 1200 dpi'
            },
            'confidence': 0.85,
            'llm_provider': 'ollama',
            'llm_model': 'llama3.2:latest',
            'validation_status': 'pending',
            'extracted_at': '2024-01-01T10:02:00Z'
        },
        {
            'id': 'extraction-2',
            'source_type': 'crawled_page',
            'source_id': 'page-2',
            'extraction_type': 'error_codes',
            'extracted_data': {
                'error_codes': [
                    {'code': '900.01', 'description': 'Fuser error', 'severity': 'critical'},
                    {'code': '900.02', 'description': 'Lamp error', 'severity': 'warning'}
                ]
            },
            'confidence': 0.90,
            'llm_provider': 'ollama',
            'llm_model': 'llama3.2:latest',
            'validation_status': 'pending',
            'extracted_at': '2024-01-01T10:03:00Z'
        }
    ]


@pytest.fixture
def mock_link_enrichment_service(mock_database_service, mock_web_scraping_service):
    """Mock LinkEnrichmentService for testing."""
    from backend.services.link_enrichment_service import LinkEnrichmentService
    return LinkEnrichmentService(
        database_service=mock_database_service,
        web_scraping_service=mock_web_scraping_service
    )


@pytest.fixture
def mock_structured_extraction_service(mock_database_service, mock_web_scraping_service):
    """Mock StructuredExtractionService for testing."""
    from backend.services.structured_extraction_service import StructuredExtractionService
    return StructuredExtractionService(
        database_service=mock_database_service,
        web_scraping_service=mock_web_scraping_service
    )


@pytest.fixture
def mock_manufacturer_crawler(mock_database_service, mock_web_scraping_service, mock_batch_task_service):
    """Mock ManufacturerCrawler for testing."""
    from backend.services.manufacturer_crawler import ManufacturerCrawler
    return ManufacturerCrawler(
        database_service=mock_database_service,
        web_scraping_service=mock_web_scraping_service,
        batch_task_service=mock_batch_task_service
    )
