"""
Shared fixtures for service testing.

Provides reusable fixtures for WebScrapingService, LinkEnrichmentService,
StructuredExtractionService, and ManufacturerCrawler tests.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services import web_scraping_service as ws


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


def create_mock_response(
    *,
    backend: str = 'firecrawl',
    success: bool = True,
    content: str = 'Mock content',
    html: str = '<html></html>',
    metadata: Optional[Dict[str, Any]] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Helper to create standardized mock responses for tests."""
    response = {
        'success': success,
        'backend': backend,
        'content': content,
        'html': html,
        'metadata': metadata or {},
    }
    response.update(extra)
    return response


async def simulate_network_delay(delay: float) -> None:
    """Simulate an async network delay for timeout/retry tests."""
    await asyncio.sleep(delay)


def assert_fallback_occurred(service: 'ws.WebScrapingService', expected: int = 1) -> None:
    """Assert helper that fallback count matches expectations."""
    assert service.fallback_count >= expected, (
        f"Expected at least {expected} fallbacks, got {service.fallback_count}"
    )


def _build_firecrawl_backend(
    *,
    proxy: Optional[Dict[str, str]] = None,
    timeout: float = 5.0,
    crawl_timeout: float = 10.0,
    retries: int = 3,
) -> Tuple['ws.FirecrawlBackend', MagicMock]:
    """Construct a FirecrawlBackend with a mocked client for deterministic tests."""
    with patch.object(ws, 'AsyncFirecrawl', MagicMock()):
        backend = ws.FirecrawlBackend(
            api_url='http://localhost:3002',
            timeout=timeout,
            crawl_timeout=crawl_timeout,
            retries=retries,
            proxy=proxy,
            mock_mode=False,
        )

    client = MagicMock()
    client.scrape = AsyncMock(
        return_value={'data': {'markdown': 'content', 'html': '<html>', 'metadata': {}}}
    )
    client.crawl = AsyncMock(return_value={'data': {'pages': []}})
    client.extract = AsyncMock(
        return_value={'data': {'data': {'field': 'value'}, 'confidence': 0.9}}
    )
    client.map = AsyncMock(return_value={'data': {'urls': ['http://example.com']}})
    client.start_crawl = AsyncMock(
        return_value={'id': 'crawl-id', 'status': 'running'}
    )
    client.get_crawl_status = AsyncMock(
        return_value={'status': 'completed', 'result': {'pages': []}}
    )
    backend._client = client
    return backend, client


@pytest.fixture
def mock_web_scraping_service():
    """WebScrapingService in mock mode (no network calls)."""
    with patch.dict(os.environ, {"SCRAPING_MOCK_MODE": "true"}):
        return ws.create_web_scraping_service(backend='firecrawl', config_service=None)


@pytest.fixture
def web_scraping_service_with_fallback(mock_firecrawl_backend, mock_beautifulsoup_backend):
    """Shared WebScrapingService with fallback configuration for tests."""
    return ws.WebScrapingService(
        primary_backend=mock_firecrawl_backend,
        fallback_backend=mock_beautifulsoup_backend,
    )


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
def mock_proxy_config():
    """Proxy configuration fixture."""
    return {
        'server': 'http://proxy.example.com:8080',
        'username': 'proxyuser',
        'password': 'proxypass'
    }


@pytest.fixture
def mock_proxy_firecrawl_backend(mock_proxy_config):
    """FirecrawlBackend with proxy configuration."""
    backend, client = _build_firecrawl_backend(proxy=mock_proxy_config)
    return backend


@pytest.fixture
def mock_proxy_error():
    """Simulate proxy connection error."""
    return httpx.ConnectError('Proxy connection failed')


@pytest.fixture
def mock_timeout_config():
    """Custom timeout configuration for tests."""
    return {
        'scrape_timeout': 0.01,
        'crawl_timeout': 0.02
    }


@pytest.fixture
def mock_timeout_firecrawl_backend():
    """FirecrawlBackend with very short timeouts."""
    backend, client = _build_firecrawl_backend(timeout=0.01, crawl_timeout=0.02)
    client.scrape.side_effect = asyncio.TimeoutError("scrape timeout")
    client.crawl.side_effect = asyncio.TimeoutError("crawl timeout")
    return backend


@pytest.fixture
def mock_slow_response():
    """Async function to simulate slow responses."""
    async def _slow():
        await asyncio.sleep(0.05)
        return {'data': {'markdown': 'slow', 'html': '<p>slow</p>'}}
    return _slow


@pytest.fixture
def mock_unhealthy_firecrawl_backend():
    """Firecrawl backend that reports unhealthy."""
    backend = MagicMock()
    backend.backend_name = 'firecrawl'
    backend.health_check = AsyncMock(return_value={'status': 'unavailable', 'backend': 'firecrawl'})
    backend.scrape_url = AsyncMock(side_effect=ws.FirecrawlUnavailableError("unhealthy"))
    backend.crawl_site = AsyncMock(side_effect=ws.FirecrawlUnavailableError("unhealthy"))
    backend.extract_structured_data = AsyncMock(side_effect=ws.FirecrawlUnavailableError("unhealthy"))
    backend.map_urls = AsyncMock(side_effect=ws.FirecrawlUnavailableError("unhealthy"))
    return backend


@pytest.fixture
def mock_degraded_firecrawl_backend():
    """Firecrawl backend that returns degraded health."""
    backend = MagicMock()
    backend.backend_name = 'firecrawl'
    backend.health_check = AsyncMock(return_value={'status': 'degraded', 'backend': 'firecrawl'})
    backend.scrape_url = AsyncMock(return_value=create_mock_response(backend='firecrawl', success=False, error='degraded'))
    backend.crawl_site = AsyncMock(return_value={'success': False, 'error': 'degraded'})
    backend.extract_structured_data = AsyncMock(return_value={'success': False, 'error': 'degraded'})
    backend.map_urls = AsyncMock(return_value={'success': False, 'error': 'degraded'})
    return backend


@pytest.fixture
def mock_health_check_response():
    """Sample health check responses."""
    return {
        'healthy': {'status': 'healthy', 'backend': 'firecrawl'},
        'degraded': {'status': 'degraded', 'backend': 'firecrawl', 'details': {'status_code': 500}},
        'unavailable': {'status': 'unavailable', 'backend': 'firecrawl', 'error': 'connection failed'}
    }


@pytest.fixture(scope="session")
def firecrawl_service_available():
    """Check if real firecrawl service is reachable (session-scoped)."""
    url = os.getenv('FIRECRAWL_API_URL', 'http://localhost:9004')
    try:
        resp = httpx.get(f"{url}/health", timeout=2.0)
        return resp.status_code == 200
    except Exception:
        return False


@pytest.fixture
def real_firecrawl_service(firecrawl_service_available):
    """Real Firecrawl service fixture with skip logic."""
    if not firecrawl_service_available:
        pytest.skip("Firecrawl service not available")
    api_url = os.getenv('FIRECRAWL_API_URL', 'http://localhost:9004')
    return ws.FirecrawlBackend(api_url=api_url, mock_mode=False)


@pytest.fixture
def integration_test_urls():
    """Common URLs for integration testing."""
    return {
        'example': 'http://example.com',
        'httpbin': 'http://httpbin.org/get'
    }


@pytest.fixture
def mock_switchable_service(mock_firecrawl_backend, mock_beautifulsoup_backend):
    """WebScrapingService with switchable backends."""
    return ws.WebScrapingService(primary_backend=mock_firecrawl_backend, fallback_backend=mock_beautifulsoup_backend)


@pytest.fixture
def mock_backend_switch_logger():
    """Capture logging for backend switching."""
    logger = MagicMock()
    return logger


@pytest.fixture
def performance_metrics():
    """Performance metrics collector."""
    metrics: Dict[str, List[float]] = {'latency': [], 'throughput': []}
    return metrics


@pytest.fixture
def mock_concurrent_requests():
    """Simulate concurrent requests list."""
    return [AsyncMock(return_value=create_mock_response()) for _ in range(5)]


@pytest.fixture
def mock_partial_failure_backend():
    """Backend that partially fails to trigger fallback scenarios."""
    backend = MagicMock()
    backend.backend_name = 'firecrawl'
    backend.scrape_url = AsyncMock(return_value={'success': False, 'backend': 'firecrawl', 'error': 'partial failure'})
    backend.crawl_site = AsyncMock(return_value={'success': True, 'backend': 'firecrawl', 'total': 1, 'pages': [{'url': 'http://example.com', 'content': 'partial', 'metadata': {}}]})
    backend.map_urls = AsyncMock(return_value={'success': False, 'backend': 'firecrawl', 'error': 'partial failure'})
    backend.extract_structured_data = AsyncMock(side_effect=ws.FirecrawlUnavailableError("partial failure"))
    backend.health_check = AsyncMock(return_value={'status': 'degraded', 'backend': 'firecrawl'})
    return backend


@pytest.fixture
def mock_rate_limited_backend():
    """Backend simulating rate limiting."""
    backend = MagicMock()
    backend.backend_name = 'firecrawl'
    backend.scrape_url = AsyncMock(return_value={'success': False, 'backend': 'firecrawl', 'error': '429 Too Many Requests'})
    backend.crawl_site = AsyncMock(return_value={'success': False, 'backend': 'firecrawl', 'error': '429 Too Many Requests'})
    backend.extract_structured_data = AsyncMock(return_value={'success': False, 'backend': 'firecrawl', 'error': '429 Too Many Requests'})
    backend.map_urls = AsyncMock(return_value={'success': False, 'backend': 'firecrawl', 'error': '429 Too Many Requests'})
    backend.health_check = AsyncMock(return_value={'status': 'degraded', 'backend': 'firecrawl', 'details': {'status_code': 429}})
    return backend


@pytest.fixture
def mock_circuit_breaker():
    """Simple circuit breaker state holder."""
    return {'open': True, 'opened_at': time.time()}


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
    from services.link_enrichment_service import LinkEnrichmentService
    return LinkEnrichmentService(
        database_service=mock_database_service,
        web_scraping_service=mock_web_scraping_service
    )


@pytest.fixture
def mock_structured_extraction_service(mock_database_service, mock_web_scraping_service):
    """Mock StructuredExtractionService for testing."""
    from services.structured_extraction_service import StructuredExtractionService
    return StructuredExtractionService(
        database_service=mock_database_service,
        web_scraping_service=mock_web_scraping_service
    )


@pytest.fixture
def mock_manufacturer_crawler(mock_database_service, mock_web_scraping_service, mock_batch_task_service):
    """Mock ManufacturerCrawler for testing."""
    from services.manufacturer_crawler import ManufacturerCrawler
    return ManufacturerCrawler(
        database_service=mock_database_service,
        web_scraping_service=mock_web_scraping_service,
        batch_task_service=mock_batch_task_service
    )


# ============================================================================
# Integration Test Fixtures for StructuredExtractionService
# ============================================================================

# Import or define test_database fixture for integration tests
@pytest.fixture(scope="function")
async def test_database():
    """Async test database fixture for integration tests.
    
    Provides a DatabaseService instance connected to the test database.
    Function-scoped to ensure each test gets a fresh connection in the correct event loop.
    """
    from services.database_service import DatabaseService
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Load test environment
    test_env_path = Path(__file__).parent.parent.parent / ".env.test"
    if test_env_path.exists():
        load_dotenv(test_env_path)
    else:
        load_dotenv()
    
    # Initialize database service
    database_service = DatabaseService()
    
    # Connect asynchronously
    await database_service.connect()
    
    yield database_service
    
    # Cleanup: Close connection
    try:
        await database_service.close()
    except AttributeError:
        # Fallback if close() doesn't exist
        try:
            await database_service.disconnect()
        except AttributeError:
            pass

@pytest.fixture(scope="function")
async def real_extraction_service(test_database, firecrawl_service_available):
    """Real StructuredExtractionService with real WebScrapingService and DatabaseService.
    
    Uses Firecrawl backend if available, otherwise BeautifulSoup.
    Function-scoped to match test_database scope and avoid event loop conflicts.
    """
    from services.structured_extraction_service import StructuredExtractionService
    from services.web_scraping_service import WebScrapingService, FirecrawlBackend, BeautifulSoupBackend
    from services.config_service import ConfigService
    
    # Create web scraping service
    if firecrawl_service_available:
        try:
            api_url = os.getenv("FIRECRAWL_API_URL", "http://krai-firecrawl-api:3002")
            llm_provider = os.getenv("LLM_PROVIDER", "ollama")
            model_name = os.getenv("MODEL_NAME", "llama3.2:latest")
            embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
            timeout = float(os.getenv("FIRECRAWL_TIMEOUT", "30.0"))
            crawl_timeout = float(os.getenv("FIRECRAWL_CRAWL_TIMEOUT", "300.0"))
            
            primary = FirecrawlBackend(
                api_url=api_url,
                llm_provider=llm_provider,
                model_name=model_name,
                embedding_model=embedding_model,
                timeout=timeout,
                crawl_timeout=crawl_timeout,
                mock_mode=False
            )
        except Exception:
            primary = BeautifulSoupBackend(mock_mode=False)
    else:
        primary = BeautifulSoupBackend(mock_mode=False)
    
    fallback = BeautifulSoupBackend(mock_mode=False)
    
    web_scraping = WebScrapingService(
        primary_backend=primary,
        fallback_backend=fallback,
    )
    
    # Create config service
    config_service = ConfigService()
    
    # Create extraction service
    service = StructuredExtractionService(
        web_scraping_service=web_scraping,
        database_service=test_database,
        config_service=config_service
    )
    
    return service


@pytest.fixture
async def test_link_data(test_database):
    """Create test link record in database.
    
    Returns dictionary with link data for tests.
    Automatically cleaned up after test.
    """
    link_id = f"test-link-{uuid.uuid4().hex[:8]}"
    link_data = {
        'id': link_id,
        'url': 'http://example.com/test-product',
        'link_type': 'external',
        'link_category': 'product',
        'manufacturer_id': f"mfr-{uuid.uuid4().hex[:8]}",
        'scrape_status': 'pending',
        'scraped_metadata': {}
    }
    
    # Insert link into database
    await test_database.execute_query(
        """
        INSERT INTO krai_content.links (id, url, link_type, link_category, manufacturer_id, scrape_status, scraped_metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        link_data['id'], link_data['url'], link_data['link_type'], link_data['link_category'],
        link_data['manufacturer_id'], link_data['scrape_status'], json.dumps(link_data['scraped_metadata'])
    )
    
    yield link_data
    
    # Cleanup
    await test_database.execute_query(
        "DELETE FROM krai_content.links WHERE id = $1",
        link_id
    )


@pytest.fixture
async def test_crawled_page_data(test_database):
    """Create test crawled page record in database.
    
    Returns dictionary with page data for tests.
    Automatically cleaned up after test.
    """
    page_id = f"test-page-{uuid.uuid4().hex[:8]}"
    crawl_job_id = f"test-job-{uuid.uuid4().hex[:8]}"
    page_data = {
        'id': page_id,
        'crawl_job_id': crawl_job_id,
        'url': 'http://example.com/test-support',
        'page_type': 'support_page',
        'manufacturer_id': f"mfr-{uuid.uuid4().hex[:8]}",
        'status': 'scraped',
        'title': 'Test Support Page',
        'content': 'Test content for extraction'
    }
    
    # Insert page into database
    await test_database.execute_query(
        """
        INSERT INTO krai_system.crawled_pages (id, crawl_job_id, url, page_type, manufacturer_id, status, title, content)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        page_data['id'], page_data['crawl_job_id'], page_data['url'], page_data['page_type'],
        page_data['manufacturer_id'], page_data['status'], page_data['title'], page_data['content']
    )
    
    yield page_data
    
    # Cleanup
    await test_database.execute_query(
        "DELETE FROM krai_system.crawled_pages WHERE id = $1",
        page_id
    )


@pytest.fixture
async def cleanup_extraction_data(test_database):
    """Cleanup fixture for structured extractions (manual use for integration tests).
    
    Runs after each test to clean up test data from:
    - krai_intelligence.structured_extractions
    - krai_content.links (test links)
    - krai_system.crawled_pages (test pages)
    
    Note: Not autouse to avoid requiring test_database for unit tests.
    Integration tests should explicitly request this fixture.
    """
    yield
    
    try:
        # Delete test extractions
        await test_database.execute_query(
            "DELETE FROM krai_intelligence.structured_extractions WHERE source_id LIKE $1",
            ('test-%',)
        )
        
        # Delete test links
        await test_database.execute_query(
            "DELETE FROM krai_content.links WHERE id LIKE $1",
            ('test-%',)
        )
        
        # Delete test crawled pages
        await test_database.execute_query(
            "DELETE FROM krai_system.crawled_pages WHERE id LIKE $1",
            ('test-%',)
        )
    except Exception as exc:
        logging.warning(f"Failed to cleanup extraction test data: {exc}")


# ============================================================================
# Helper Functions for Integration Tests
# ============================================================================

class IntegrationTestHelpers:
    """Helper class for integration tests - provides reusable test data creation and verification."""
    
    @staticmethod
    async def create_test_link(database_service, url: str, link_type: str, link_category: str, manufacturer_id: str) -> str:
        """Create test link record and return ID.
        
        Note: link_category and manufacturer_id are accepted for API compatibility
        but not stored in DB (columns don't exist in current schema).
        Creates a test document first to satisfy foreign key constraint.
        """
        # Generate proper UUIDs
        link_id = uuid.uuid4()
        document_id = uuid.uuid4()
        
        # First create a test document to satisfy foreign key constraint
        await database_service.execute_query(
            """
            INSERT INTO krai_core.documents 
            (id, filename, storage_path, created_at)
            VALUES ($1, $2, $3, NOW())
            """,
            (document_id, f"test_doc_{link_id}.pdf", f"/test/{link_id}.pdf")
        )
        
        # Now create the link
        await database_service.execute_query(
            """
            INSERT INTO krai_content.links 
            (id, document_id, url, link_type, page_number, description, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """,
            (link_id, document_id, url, link_type, 1, f"Test link - {link_category}")
        )
        return str(link_id)
    
    @staticmethod
    async def create_test_crawled_page(database_service, url: str, page_type: str, manufacturer_id: str) -> str:
        """Create test crawled page record and return ID.
        
        Note: krai_system.crawled_pages table may not exist yet.
        This will raise an error if the table doesn't exist - tests should skip gracefully.
        """
        page_id = f"test-{uuid.uuid4().hex[:8]}"
        try:
            await database_service.execute_query(
                """
                INSERT INTO krai_system.crawled_pages (id, url, page_type, status, created_at)
                VALUES ($1, $2, $3, 'pending', NOW())
                """,
                (page_id, url, page_type)
            )
            return page_id
        except Exception as e:
            # Table might not exist - raise with clear message
            raise RuntimeError(f"Failed to create test crawled page - table may not exist: {e}") from e
    
    @staticmethod
    async def verify_extraction_in_db(database_service, extraction_id: str):
        """Verify extraction exists in database and return record."""
        result = await database_service.execute_query(
            "SELECT * FROM krai_intelligence.structured_extractions WHERE id = $1",
            (extraction_id,)
        )
        return result[0] if result else None
    
    @staticmethod
    async def wait_for_extraction(database_service, source_type: str, source_id: str, timeout: int = 30):
        """Wait for extraction to appear in database."""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            result = await database_service.execute_query(
                "SELECT * FROM krai_intelligence.structured_extractions WHERE source_type = $1 AND source_id = $2",
                (source_type, source_id)
            )
            if result:
                return result[0]
            await asyncio.sleep(0.5)
        return None
    
    @staticmethod
    async def get_extraction_by_source(database_service, source_type: str, source_id: str):
        """Get extraction by source type and ID."""
        result = await database_service.execute_query(
            "SELECT * FROM krai_intelligence.structured_extractions WHERE source_type = $1 AND source_id = $2",
            (source_type, source_id)
        )
        return result[0] if result else None


@pytest.fixture
def test_helpers():
    """Fixture providing integration test helper functions."""
    return IntegrationTestHelpers()


# Backward compatibility - keep old function definitions
async def create_test_link(database_service, url: str, link_type: str, link_category: str, manufacturer_id: str) -> str:
    """Create test link record and return ID.
    
    Args:
        database_service: DatabaseService instance
        url: Link URL
        link_type: Type of link (e.g., 'external')
        link_category: Category (e.g., 'product', 'error', 'manual')
        manufacturer_id: Manufacturer ID
    
    Returns:
        Link ID
    """
    link_id = f"test-link-{uuid.uuid4().hex[:8]}"
    
    await database_service.execute_query(
        """
        INSERT INTO krai_content.links (id, url, link_type, link_category, manufacturer_id, scrape_status, scraped_metadata)
        VALUES ($1, $2, $3, $4, $5, 'pending', '{}')
        """,
        link_id, url, link_type, link_category, manufacturer_id
    )
    
    return link_id


async def create_test_crawled_page(database_service, url: str, page_type: str, manufacturer_id: str, crawl_job_id: str) -> str:
    """Create test crawled page record and return ID.
    
    Args:
        database_service: DatabaseService instance
        url: Page URL
        page_type: Type of page (e.g., 'product_page', 'support_page')
        manufacturer_id: Manufacturer ID
        crawl_job_id: Crawl job ID
    
    Returns:
        Page ID
    """
    page_id = f"test-page-{uuid.uuid4().hex[:8]}"
    
    await database_service.execute_query(
        """
        INSERT INTO krai_system.crawled_pages (id, crawl_job_id, url, page_type, manufacturer_id, status, title, content)
        VALUES ($1, $2, $3, $4, $5, 'scraped', 'Test Page', 'Test content')
        """,
        page_id, crawl_job_id, url, page_type, manufacturer_id
    )
    
    return page_id


async def wait_for_extraction(database_service, source_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Wait for extraction to appear in database.
    
    Args:
        database_service: DatabaseService instance
        source_id: Source ID to wait for
        timeout: Timeout in seconds
    
    Returns:
        Extraction record or None if timeout
    """
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = await database_service.execute_query(
            "SELECT * FROM krai_intelligence.structured_extractions WHERE source_id = $1",
            source_id
        )
        
        if result:
            return result[0]
        
        await asyncio.sleep(0.5)
    
    return None


async def verify_extraction_in_db(database_service, extraction_id: str) -> Optional[Dict[str, Any]]:
    """Verify extraction exists in database and return record.
    
    Args:
        database_service: DatabaseService instance
        extraction_id: Extraction record ID
    
    Returns:
        Extraction record or None
    """
    result = await database_service.execute_query(
        "SELECT * FROM krai_intelligence.structured_extractions WHERE id = $1",
        extraction_id
    )
    
    return result[0] if result else None


async def get_extraction_by_source(database_service, source_type: str, source_id: str) -> Optional[Dict[str, Any]]:
    """Get extraction by source type and ID.
    
    Args:
        database_service: DatabaseService instance
        source_type: Source type ('link' or 'crawled_page')
        source_id: Source ID
    
    Returns:
        Extraction record or None
    """
    result = await database_service.execute_query(
        "SELECT * FROM krai_intelligence.structured_extractions WHERE source_type = $1 AND source_id = $2",
        source_type, source_id
    )
    
    return result[0] if result else None


@pytest.fixture
def integration_test_urls():
    """Test URLs for integration testing.
    
    Provides URLs for different extraction types.
    """
    return {
        'product': 'http://example.com/products/test-model',
        'error_codes': 'http://example.com/support/error-codes',
        'manual': 'http://example.com/manuals/test-manual.pdf',
        'parts': 'http://example.com/parts/test-model',
        'troubleshooting': 'http://example.com/support/troubleshooting'
    }
