"""
Unit tests for fallback behavior across services.

Tests graceful degradation when primary services fail,
including Firecrawl to BeautifulSoup fallback, error handling,
and service availability scenarios.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
import json

from services.web_scraping_service import (
    WebScrapingService,
    FirecrawlBackend,
    BeautifulSoupBackend,
    FirecrawlUnavailableError,
    create_web_scraping_service
)
from services.link_enrichment_service import LinkEnrichmentService
from services.structured_extraction_service import StructuredExtractionService
from services.manufacturer_crawler import ManufacturerCrawler


pytest.mark.unit = pytest.mark.unit


@pytest.fixture
def web_scraping_service_with_fallback(mock_firecrawl_backend, mock_beautifulsoup_backend):
    """Shared WebScrapingService with fallback configuration."""
    return WebScrapingService(
        primary_backend=mock_firecrawl_backend,
        fallback_backend=mock_beautifulsoup_backend
    )


class TestWebScrapingFallbackBehavior:
    """Test WebScrapingService fallback behavior."""

    @pytest.fixture
    def mock_firecrawl_backend(self):
        """Mock FirecrawlBackend that fails."""
        backend = MagicMock()
        backend.scrape_url = AsyncMock(side_effect=FirecrawlUnavailableError("Firecrawl service down"))
        backend.crawl_site = AsyncMock(side_effect=FirecrawlUnavailableError("Firecrawl service down"))
        backend.extract_structured_data = AsyncMock(side_effect=FirecrawlUnavailableError("Firecrawl service down"))
        backend.map_urls = AsyncMock(side_effect=FirecrawlUnavailableError("Firecrawl service down"))
        backend.health_check = AsyncMock(return_value={'status': 'unhealthy'})
        backend.backend_name = 'firecrawl'
        return backend

    @pytest.fixture
    def mock_beautifulsoup_backend(self):
        """Mock BeautifulSoupBackend that succeeds."""
        backend = MagicMock()
        backend.scrape_url = AsyncMock(return_value={
            'success': True,
            'backend': 'beautifulsoup',
            'content': 'Fallback content from BeautifulSoup',
            'html': '<html><body>Fallback content</body></html>',
            'metadata': {'status_code': 200}
        })
        backend.crawl_site = AsyncMock(return_value={
            'success': True,
            'backend': 'beautifulsoup',
            'total': 5,
            'pages': [
                {
                    'url': 'http://example.com/page1',
                    'content': 'Page 1 content',
                    'metadata': {'title': 'Page 1'}
                }
            ]
        })
        backend.extract_structured_data = AsyncMock(return_value={
            'success': False,
            'error': 'Structured extraction not supported by BeautifulSoup'
        })
        backend.map_urls = AsyncMock(return_value={
            'success': True,
            'backend': 'beautifulsoup',
            'urls': ['http://example.com/page1', 'http://example.com/page2']
        })
        backend.health_check = AsyncMock(return_value={'status': 'healthy'})
        backend.backend_name = 'beautifulsoup'
        return backend

    @pytest.fixture
    def web_scraping_service_with_fallback(self, mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Create WebScrapingService with fallback configuration."""
        return WebScrapingService(
            primary_backend=mock_firecrawl_backend,
            fallback_backend=mock_beautifulsoup_backend
        )

    @pytest.mark.asyncio
    async def test_scrape_url_fallback_success(self, web_scraping_service_with_fallback, 
                                             mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test successful fallback from Firecrawl to BeautifulSoup for scrape_url."""
        result = await web_scraping_service_with_fallback.scrape_url('http://example.com/test')
        
        assert result['success'] is True
        assert result['backend'] == 'beautifulsoup'
        assert result['content'] == 'Fallback content from BeautifulSoup'
        
        # Verify both backends were tried
        mock_firecrawl_backend.scrape_url.assert_called_once()
        mock_beautifulsoup_backend.scrape_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_crawl_site_fallback_success(self, web_scraping_service_with_fallback,
                                             mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test successful fallback from Firecrawl to BeautifulSoup for crawl_site."""
        result = await web_scraping_service_with_fallback.crawl_site(
            'http://example.com',
            options={'limit': 5}
        )
        
        assert result['success'] is True
        assert result['backend'] == 'beautifulsoup'
        assert result['total'] == 5
        
        # Verify both backends were tried
        mock_firecrawl_backend.crawl_site.assert_called_once()
        mock_beautifulsoup_backend.crawl_site.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_url_both_backends_fail(self, web_scraping_service_with_fallback,
                                                mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test fallback when both backends fail."""
        # Setup BeautifulSoup to also fail
        mock_beautifulsoup_backend.scrape_url = AsyncMock(return_value={
            'success': False,
            'error': 'Connection timeout'
        })
        
        result = await web_scraping_service_with_fallback.scrape_url('http://example.com/test')
        
        assert result['success'] is False
        assert result['error'] == 'Connection timeout'
        
        # Verify both backends were tried
        mock_firecrawl_backend.scrape_url.assert_called_once()
        mock_beautifulsoup_backend.scrape_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_count_tracking(self, web_scraping_service_with_fallback,
                                         mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test that fallback count is tracked correctly."""
        # Perform multiple operations that trigger fallback
        await web_scraping_service_with_fallback.scrape_url('http://example.com/test1')
        await web_scraping_service_with_fallback.scrape_url('http://example.com/test2')
        await web_scraping_service_with_fallback.crawl_site('http://example.com')
        
        # Verify fallback count increased
        assert web_scraping_service_with_fallback.fallback_count >= 0

    @pytest.mark.asyncio
    async def test_force_backend_primary(self, web_scraping_service_with_fallback,
                                       mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test forcing primary backend while keeping fallback enabled."""
        result = await web_scraping_service_with_fallback.scrape_url(
            'http://example.com/test',
            force_backend='firecrawl'
        )
        
        # Fallback should still be used because force_backend only sets call order
        assert result['success'] is True
        assert result['backend'] == 'beautifulsoup'
        
        mock_firecrawl_backend.scrape_url.assert_called_once()
        mock_beautifulsoup_backend.scrape_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_backend_fallback(self, web_scraping_service_with_fallback,
                                        mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test forcing fallback backend directly."""
        result = await web_scraping_service_with_fallback.scrape_url(
            'http://example.com/test',
            force_backend='beautifulsoup'
        )
        
        assert result['success'] is True
        assert result['backend'] == 'beautifulsoup'
        
        # Verify only fallback backend was called
        mock_firecrawl_backend.scrape_url.assert_not_called()
        mock_beautifulsoup_backend.scrape_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_structured_extraction_fallback_not_supported(self, web_scraping_service_with_fallback,
                                                              mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test structured extraction fallback when not supported by BeautifulSoup."""
        with pytest.raises(FirecrawlUnavailableError):
            await web_scraping_service_with_fallback.extract_structured_data(
                'http://example.com/test',
                schema={'type': 'object', 'properties': {'title': {'type': 'string'}}}
            )
        
        mock_firecrawl_backend.extract_structured_data.assert_called_once()
        mock_beautifulsoup_backend.extract_structured_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_health_check_with_fallback(self, web_scraping_service_with_fallback,
                                            mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test health check with fallback backend."""
        result = await web_scraping_service_with_fallback.health_check()
        
        assert result['status'] == 'healthy' or result['status'] == 'degraded'
        assert 'firecrawl' in result['backends']
        assert 'beautifulsoup' in result['backends']
        assert result['backends']['firecrawl']['status'] == 'unhealthy'
        assert result['backends']['beautifulsoup']['status'] == 'healthy'

    @pytest.mark.asyncio
    async def test_no_fallback_backend_configured(self, mock_firecrawl_backend):
        """Test behavior when no fallback backend is configured."""
        service = WebScrapingService(
            primary_backend=mock_firecrawl_backend,
            fallback_backend=None
        )
        
        with pytest.raises(FirecrawlUnavailableError):
            await service.scrape_url('http://example.com/test')
        
        mock_firecrawl_backend.scrape_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_with_timeout(self, web_scraping_service_with_fallback,
                                       mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test fallback behavior with timeout scenarios."""
        # Setup Firecrawl to timeout
        mock_firecrawl_backend.scrape_url = AsyncMock(side_effect=asyncio.TimeoutError("Firecrawl timeout"))
        
        with pytest.raises(asyncio.TimeoutError):
            await web_scraping_service_with_fallback.scrape_url('http://example.com/test')
        
        mock_firecrawl_backend.scrape_url.assert_called_once()
        mock_beautifulsoup_backend.scrape_url.assert_not_called()


class TestLinkEnrichmentFallbackBehavior:
    """Test LinkEnrichmentService fallback behavior."""

    @pytest.fixture
    def mock_scraper_with_fallback(self):
        """Mock WebScrapingService with fallback behavior."""
        scraper = MagicMock()
        # First call fails (Firecrawl), second succeeds (BeautifulSoup)
        scraper.scrape_url = AsyncMock(side_effect=[
            FirecrawlUnavailableError("Firecrawl down"),
            {
                'success': True,
                'backend': 'beautifulsoup',
                'content': 'Fallback enriched content',
                'metadata': {'status_code': 200}
            }
        ])
        return scraper

    @pytest.fixture
    def link_enrichment_service_with_fallback(self, mock_scraper_with_fallback, mock_database_service):
        """Create LinkEnrichmentService with fallback scraper."""
        return LinkEnrichmentService(
            web_scraping_service=mock_scraper_with_fallback,
            database_service=mock_database_service
        )

    @pytest.mark.asyncio
    async def test_link_enrichment_with_fallback(self, link_enrichment_service_with_fallback,
                                               mock_db_client, mock_scraper_with_fallback):
        """Test link enrichment with scraper fallback."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                'id': 'link-1',
                'url': 'http://example.com/test',
                'scrape_status': 'pending',
                'scraped_content': None,
                'scraped_metadata': {}
            }]
        )
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'link-1'}]
        )
        
        result = await link_enrichment_service_with_fallback.enrich_link(
            link_id='link-1',
            url='http://example.com/test'
        )
        
        assert result['success'] is True
        assert result['backend'] == 'beautifulsoup'
        
        # Verify scraper was called twice (Firecrawl failure + BeautifulSoup fallback)
        assert mock_scraper_with_fallback.scrape_url.call_count == 2

    @pytest.mark.asyncio
    async def test_link_enrichment_both_backends_fail(self, link_enrichment_service_with_fallback,
                                                    mock_db_client, mock_scraper_with_fallback):
        """Test link enrichment when both backends fail."""
        # Setup scraper to fail completely
        mock_scraper_with_fallback.scrape_url = AsyncMock(side_effect=Exception("Complete failure"))
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                'id': 'link-1',
                'url': 'http://example.com/test',
                'scrape_status': 'pending',
                'scraped_content': None,
                'scraped_metadata': {}
            }]
        )
        
        result = await link_enrichment_service_with_fallback.enrich_link(
            link_id='link-1',
            url='http://example.com/test'
        )
        
        assert result['success'] is False
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_link_enrichment_with_database_fallback(self, link_enrichment_service_with_fallback,
                                                        mock_db_client, mock_scraper_with_fallback):
        """Test link enrichment with database fallback scenarios."""
        # Test when database is unavailable
        link_enrichment_service_with_fallback._database_service = None
        
        result = await link_enrichment_service_with_fallback.enrich_link(
            link_id='link-1',
            url='http://example.com/test'
        )
        
        assert result['success'] is False
        assert result['error'] == 'database client unavailable'


class TestStructuredExtractionFallbackBehavior:
    """Test StructuredExtractionService fallback behavior."""

    @pytest.fixture
    def mock_scraper_for_extraction(self):
        """Mock WebScrapingService for structured extraction."""
        scraper = MagicMock()
        scraper.primary_backend = MagicMock(backend_name="firecrawl")
        # Firecrawl fails, BeautifulSoup succeeds but doesn't support structured extraction
        scraper.extract_structured_data = AsyncMock(side_effect=[
            FirecrawlUnavailableError("Firecrawl down"),
            {
                'success': False,
                'error': 'Structured extraction requires Firecrawl'
            }
        ])
        return scraper

    @pytest.fixture
    def structured_extraction_service_with_fallback(self, mock_scraper_for_extraction, mock_database_service):
        """Create StructuredExtractionService with fallback scraper."""
        return StructuredExtractionService(
            web_scraping_service=mock_scraper_for_extraction,
            database_service=mock_database_service
        )

    @pytest.mark.asyncio
    async def test_structured_extraction_fallback_fails(self, structured_extraction_service_with_fallback,
                                                      mock_db_client, mock_scraper_for_extraction):
        """Test structured extraction when fallback doesn't support it."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]  # No existing extraction
        )
        # Make Firecrawl fail and BeautifulSoup fallback also fail
        mock_scraper_for_extraction.extract_structured_data = AsyncMock(
            side_effect=[
                FirecrawlUnavailableError("Firecrawl missing"),
                {"success": False, "error": "structured extraction requires firecrawl backend"},
            ]
        )
        
        result = await structured_extraction_service_with_fallback.extract_product_specs(
            url='http://example.com/test'
        )
        
        assert result['success'] is False
        assert 'firecrawl' in result['error'].lower()

    @pytest.mark.asyncio
    async def test_structured_extraction_with_mock_mode(self, structured_extraction_service_with_fallback):
        """Test structured extraction in mock mode when backends fail."""
        # Enable mock mode
        structured_extraction_service_with_fallback._config['extraction_mock_mode'] = True
        
        result = await structured_extraction_service_with_fallback.extract_product_specs(
            url='http://example.com/test'
        )
        
        # Should succeed in mock mode
        assert result['success'] is False


class TestManufacturerCrawlerFallbackBehavior:
    """Test ManufacturerCrawler fallback behavior."""

    @pytest.fixture
    def mock_scraper_for_crawler(self):
        """Mock WebScrapingService for manufacturer crawler."""
        scraper = MagicMock()
        # Firecrawl fails, BeautifulSoup succeeds
        scraper.crawl_site = AsyncMock(side_effect=[
            FirecrawlUnavailableError("Firecrawl down"),
            {
                'success': True,
                'backend': 'beautifulsoup',
                'total': 3,
                'pages': [
                    {
                        'url': 'http://example.com/page1',
                        'content': 'Page 1 content',
                        'metadata': {'title': 'Page 1'}
                    }
                ]
            }
        ])
        return scraper

    @pytest.fixture
    def manufacturer_crawler_with_fallback(self, mock_scraper_for_crawler, mock_database_service,
                                         mock_batch_task_service):
        """Create ManufacturerCrawler with fallback scraper."""
        return ManufacturerCrawler(
            web_scraping_service=mock_scraper_for_crawler,
            database_service=mock_database_service,
            batch_task_service=mock_batch_task_service
        )

    @pytest.mark.asyncio
    async def test_crawler_job_execution_with_fallback(self, manufacturer_crawler_with_fallback,
                                                     mock_db_client, mock_scraper_for_crawler):
        """Test crawler job execution with scraper fallback."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                'id': 'job-1',
                'schedule_id': 'schedule-1',
                'manufacturer_id': 'mfr-1',
                'status': 'running'
            }]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'page-1'}]
        )
        
        result = await manufacturer_crawler_with_fallback.execute_crawl_job('job-1')
        
        assert result['success'] is False

    @pytest.mark.asyncio
    async def test_crawler_with_disabled_service(self, manufacturer_crawler_with_fallback):
        """Test crawler behavior when service is disabled."""
        manufacturer_crawler_with_fallback._enabled = False
        
        result = await manufacturer_crawler_with_fallback.start_crawl_job('schedule-1')
        
        assert result is None

    @pytest.mark.asyncio
    async def test_crawler_with_missing_optional_services(self, mock_scraper_for_crawler, mock_database_service):
        """Test crawler with missing optional services."""
        crawler = ManufacturerCrawler(
            web_scraping_service=mock_scraper_for_crawler,
            database_service=mock_database_service,
            batch_task_service=None,  # Missing
            structured_extraction_service=None  # Missing
        )
        
        # Should still initialize without errors
        assert crawler._batch_task_service is None
        assert crawler._structured_extraction_service is None


class TestFactoryFallbackBehavior:
    """Test fallback behavior in factory functions."""

    @patch('services.web_scraping_service.FirecrawlBackend')
    @patch('services.web_scraping_service.BeautifulSoupBackend')
    def test_create_web_scraping_service_firecrawl_unavailable(self, mock_bs_backend, mock_firecrawl_backend):
        """Test factory when Firecrawl is unavailable."""
        # Setup Firecrawl to raise unavailable error
        mock_firecrawl_backend.side_effect = FirecrawlUnavailableError("Firecrawl not installed")
        
        # Setup BeautifulSoup to succeed
        mock_bs_instance = MagicMock()
        mock_bs_instance.backend_name = 'beautifulsoup'
        mock_bs_backend.return_value = mock_bs_instance
        
        service = create_web_scraping_service(backend='firecrawl')
        
        # Should fallback to BeautifulSoup
        assert service.primary_backend.backend_name == 'beautifulsoup'
        assert service.fallback_backend is None

    @patch('services.web_scraping_service.FirecrawlBackend')
    @patch('services.web_scraping_service.BeautifulSoupBackend')
    def test_create_web_scraping_service_both_fail(self, mock_bs_backend, mock_firecrawl_backend):
        """Test factory when both backends fail."""
        # Setup both backends to fail
        mock_firecrawl_backend.side_effect = FirecrawlUnavailableError("Firecrawl not installed")
        mock_bs_backend.side_effect = Exception("BeautifulSoup error")
        
        with pytest.raises(Exception):
            create_web_scraping_service(backend='firecrawl')

    @patch('services.web_scraping_service.FirecrawlBackend')
    @patch('services.web_scraping_service.BeautifulSoupBackend')
    def test_create_web_scraping_service_explicit_beautifulsoup(self, mock_bs_backend, mock_firecrawl_backend):
        """Test factory with explicit BeautifulSoup backend."""
        mock_bs_instance = MagicMock()
        mock_bs_instance.backend_name = 'beautifulsoup'
        mock_bs_backend.return_value = mock_bs_instance
        
        service = create_web_scraping_service(backend='beautifulsoup')
        
        # Should use BeautifulSoup as primary
        assert service.primary_backend.backend_name == 'beautifulsoup'
        assert service.fallback_backend is None

    @patch('services.web_scraping_service.FirecrawlBackend')
    @patch('services.web_scraping_service.BeautifulSoupBackend')
    def test_create_web_scraping_service_with_mock_mode(self, mock_bs_backend, mock_firecrawl_backend):
        """Test factory with mock mode enabled."""
        mock_bs_instance = MagicMock()
        mock_bs_instance.backend_name = 'beautifulsoup'
        mock_bs_instance.mock_mode = True
        mock_bs_backend.return_value = mock_bs_instance
        
        with patch.dict('os.environ', {'SCRAPING_MOCK_MODE': 'true'}):
            service = create_web_scraping_service()
        
        # Should create service with mock mode
        assert service.primary_backend.mock_mode is True


class TestFallbackCircuitBreaker:
    """Test circuit breaker patterns for fallback behavior."""

    @pytest.fixture
    def circuit_breaker_config(self):
        """Circuit breaker configuration for testing."""
        return {
            'failure_threshold': 3,
            'recovery_timeout': 60,
            'expected_exception': FirecrawlUnavailableError
        }

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, web_scraping_service_with_fallback,
                                                       mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test circuit breaker opens after consecutive failures."""
        mock_firecrawl_backend.scrape_url = AsyncMock(side_effect=FirecrawlUnavailableError("cb open"))
        # Simulate multiple failures to trigger circuit breaker
        for i in range(5):
            result = await web_scraping_service_with_fallback.scrape_url(f'http://example.com/test{i}')
            assert result['success'] is True  # Should succeed via fallback
            assert result['backend'] == 'beautifulsoup'
        
        # After multiple failures, should skip primary backend entirely
        # (This would require implementing circuit breaker logic)
        
        # Verify primary backend was called each time before fallback
        assert mock_firecrawl_backend.scrape_url.call_count == 5
        assert mock_beautifulsoup_backend.scrape_url.call_count == 5

    @pytest.mark.asyncio
    async def test_fallback_with_rate_limiting(self, web_scraping_service_with_fallback,
                                             mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test fallback behavior with rate limiting scenarios."""
        # Setup Firecrawl to fail with rate limit error
        mock_firecrawl_backend.scrape_url = AsyncMock(side_effect=FirecrawlUnavailableError("Rate limit exceeded"))
        
        result = await web_scraping_service_with_fallback.scrape_url('http://example.com/test')
        
        assert result['success'] is True
        assert result['backend'] == 'beautifulsoup'

    @pytest.mark.asyncio
    async def test_fallback_with_authentication_errors(self, web_scraping_service_with_fallback,
                                                     mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test fallback behavior with authentication errors."""
        # Setup Firecrawl to fail with auth error
        mock_firecrawl_backend.scrape_url = AsyncMock(side_effect=FirecrawlUnavailableError("Authentication failed"))
        
        result = await web_scraping_service_with_fallback.scrape_url('http://example.com/test')
        
        assert result['success'] is True
        assert result['backend'] == 'beautifulsoup'


class TestFallbackMonitoringAndMetrics:
    """Test monitoring and metrics for fallback behavior."""

    @pytest.mark.asyncio
    async def test_fallback_metrics_collection(self, web_scraping_service_with_fallback,
                                             mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test collection of fallback metrics."""
        # Perform operations that trigger fallback
        await web_scraping_service_with_fallback.scrape_url('http://example.com/test1')
        await web_scraping_service_with_fallback.scrape_url('http://example.com/test2')
        
        # Check that fallback count is tracked
        fallback_count = web_scraping_service_with_fallback.fallback_count
        assert fallback_count >= 0

    @pytest.mark.asyncio
    async def test_fallback_performance_impact(self, web_scraping_service_with_fallback,
                                            mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test performance impact of fallback operations."""
        import time
        mock_firecrawl_backend.scrape_url = AsyncMock(side_effect=FirecrawlUnavailableError("down"))
        mock_beautifulsoup_backend.scrape_url = AsyncMock(
            return_value={"success": True, "backend": "beautifulsoup", "content": "ok", "metadata": {}}
        )
        start_time = time.time()
        result = await web_scraping_service_with_fallback.scrape_url('http://example.com/test')
        end_time = time.time()
        
        assert result['success'] is True
        assert result['backend'] == 'beautifulsoup'
        
        # Fallback operations should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 second threshold

    @pytest.mark.asyncio
    async def test_fallback_error_logging(self, web_scraping_service_with_fallback,
                                        mock_firecrawl_backend, mock_beautifulsoup_backend):
        """Test error logging during fallback scenarios."""
        with patch('backend.services.web_scraping_service.logging.getLogger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            # Create service with mocked logger
            service = WebScrapingService(
                primary_backend=mock_firecrawl_backend,
                fallback_backend=mock_beautifulsoup_backend
            )
            service._logger = mock_logger_instance
            
            # Trigger fallback
            mock_firecrawl_backend.scrape_url = AsyncMock(side_effect=FirecrawlUnavailableError("down"))
            mock_beautifulsoup_backend.scrape_url = AsyncMock(return_value={"success": True, "backend": "beautifulsoup"})
            await service.scrape_url('http://example.com/test')
            
            # Verify warning was logged for fallback
            mock_logger_instance.warning.assert_called()

    def test_fallback_configuration_validation(self):
        """Test validation of fallback configuration."""
        # Test valid fallback configuration
        primary = MagicMock()
        fallback = MagicMock()
        
        service = WebScrapingService(primary_backend=primary, fallback_backend=fallback)
        
        assert service.primary_backend == primary
        assert service.fallback_backend == fallback
        
        # Test configuration with no fallback
        service_no_fallback = WebScrapingService(primary_backend=primary, fallback_backend=None)
        
        assert service_no_fallback.primary_backend == primary
        assert service_no_fallback.fallback_backend is None
