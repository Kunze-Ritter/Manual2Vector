"""
Unit tests for LinkEnrichmentService.

Tests link enrichment functionality including single link enrichment,
batch processing, retry logic, and statistics tracking.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import hashlib

from services.link_enrichment_service import LinkEnrichmentService
from services.web_scraping_service import FirecrawlUnavailableError


pytest.mark.unit = pytest.mark.unit


class TestLinkEnrichmentService:
    """Test LinkEnrichmentService functionality."""

    @pytest.fixture
    def mock_scraper(self):
        """Mock WebScrapingService."""
        scraper = MagicMock()
        scraper.scrape_url = AsyncMock(return_value={
            'success': True,
            'backend': 'firecrawl',
            'content': 'Test scraped content',
            'html': '<html><body>Test</body></html>',
            'metadata': {'status_code': 200}
        })
        return scraper

    @pytest.fixture
    def mock_database_service(self, mock_db_client):
        """Mock database service."""
        service = MagicMock()
        service.client = mock_db_client
        service.service_client = mock_db_client
        return service

    @pytest.fixture
    def link_enrichment_service(self, mock_scraper, mock_database_service):
        """Create LinkEnrichmentService instance for testing."""
        return LinkEnrichmentService(
            web_scraping_service=mock_scraper,
            database_service=mock_database_service
        )

    @pytest.fixture
    def sample_link_record(self):
        """Sample link record for testing."""
        return {
            'id': 'test-link-id-123',
            'url': 'http://example.com/product',
            'link_type': 'external',
            'scrape_status': 'pending',
            'scraped_content': None,
            'content_hash': None,
            'scraped_metadata': {},
            'document_id': 'test-doc-id',
            'manufacturer_id': 'test-mfr-id'
        }

    @pytest.fixture
    def enriched_link_record(self):
        """Sample enriched link record."""
        content = 'Test scraped content'
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return {
            'id': 'test-link-id-456',
            'url': 'http://example.com/product',
            'link_type': 'external',
            'scrape_status': 'success',
            'scraped_content': content,
            'content_hash': content_hash,
            'scraped_metadata': {'backend': 'firecrawl', 'status_code': 200},
            'document_id': 'test-doc-id',
            'manufacturer_id': 'test-mfr-id'
        }

    def test_service_initialization(self, mock_scraper, mock_database_service):
        """Test service initialization with correct config."""
        service = LinkEnrichmentService(
            web_scraping_service=mock_scraper,
            database_service=mock_database_service
        )
        
        assert service._scraper == mock_scraper
        assert service._database_service == mock_database_service
        assert service._enabled is True
        assert service._max_concurrent_enrichments == 3
        assert service._enrichment_timeout == 30
        assert service._retry_failed_after_hours == 24

    def test_service_disabled_by_config(self, mock_scraper, mock_database_service):
        """Test service when disabled by configuration."""
        with patch('backend.services.link_enrichment_service.ConfigService') as mock_config_class:
            mock_config = MagicMock()
            mock_config.get_scraping_config.return_value = {'enable_link_enrichment': False}
            mock_config_class.return_value = mock_config
            
            service = LinkEnrichmentService(
                web_scraping_service=mock_scraper,
                database_service=mock_database_service,
                config_service=mock_config
            )
            
            assert service._enabled is False

    @pytest.mark.asyncio
    async def test_enrich_link_success(self, link_enrichment_service, mock_db_client, sample_link_record):
        """Test successful link enrichment."""
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_link_record]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='test-link-id-123',
            url='http://example.com/product'
        )
        
        assert result['success'] is True
        assert result['link_id'] == 'test-link-id-123'
        assert 'content_length' in result
        assert 'backend' in result
        
        # Verify database update was called
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_enrich_link_already_enriched_skip(self, link_enrichment_service, mock_db_client, enriched_link_record):
        """Test skipping already enriched link."""
        # Setup mock database response for enriched link
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[enriched_link_record]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='test-link-id-456',
            url='http://example.com/product',
            force_refresh=False
        )
        
        assert result['success'] is True
        assert result['skipped'] is True
        assert result['link_id'] == 'test-link-id-456'
        
        # Verify database update was NOT called
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_enrich_link_force_refresh(self, link_enrichment_service, mock_db_client, enriched_link_record):
        """Test force refresh of already enriched link."""
        # Setup mock database response for enriched link
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[enriched_link_record]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='test-link-id-456',
            url='http://example.com/product',
            force_refresh=True
        )
        
        assert result['success'] is True
        assert result['link_id'] == 'test-link-id-456'
        
        # Verify database update WAS called for force refresh
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_enrich_link_not_found(self, link_enrichment_service, mock_db_client):
        """Test enrichment when link record not found."""
        # Setup mock database response with no data
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='nonexistent-link-id',
            url='http://example.com/product'
        )
        
        assert result['success'] is False
        assert result['error'] == 'link record not found'
        assert result['link_id'] == 'nonexistent-link-id'

    @pytest.mark.asyncio
    async def test_enrich_link_scrape_failure(self, link_enrichment_service, mock_db_client, mock_scraper, sample_link_record):
        """Test enrichment when scraping fails."""
        # Setup scraper to fail
        mock_scraper.scrape_url.return_value = {
            'success': False,
            'error': 'Connection timeout'
        }
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_link_record]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='test-link-id-123',
            url='http://example.com/product'
        )
        
        assert result['success'] is False
        assert result['error'] == 'Connection timeout'
        assert result['link_id'] == 'test-link-id-123'
        
        # Verify link was marked as failed
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_enrich_link_timeout(self, link_enrichment_service, mock_db_client, mock_scraper, sample_link_record):
        """Test enrichment timeout handling."""
        # Setup scraper to timeout
        mock_scraper.scrape_url = AsyncMock(side_effect=asyncio.TimeoutError("Timeout"))
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_link_record]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='test-link-id-123',
            url='http://example.com/product'
        )
        
        assert result['success'] is False
        assert result['error'] == 'timeout'
        assert result['link_id'] == 'test-link-id-123'

    @pytest.mark.asyncio
    async def test_enrich_link_firecrawl_fallback(self, link_enrichment_service, mock_db_client, mock_scraper, sample_link_record):
        """Test Firecrawl fallback to BeautifulSoup."""
        # Setup scraper to fail with Firecrawl then succeed with BeautifulSoup
        firecrawl_error = FirecrawlUnavailableError("Firecrawl down")
        beautifulsoup_result = {
            'success': True,
            'backend': 'beautifulsoup',
            'content': 'BeautifulSoup content',
            'html': '<html><body>Test</body></html>',
            'metadata': {'status_code': 200}
        }
        
        mock_scraper.scrape_url.side_effect = [firecrawl_error, beautifulsoup_result]
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_link_record]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='test-link-id-123',
            url='http://example.com/product'
        )
        
        assert result['success'] is True
        assert result['backend'] == 'beautifulsoup'
        assert result['link_id'] == 'test-link-id-123'
        
        # Verify scraper was called twice (Firecrawl failure + BeautifulSoup fallback)
        assert mock_scraper.scrape_url.call_count == 2

    @pytest.mark.asyncio
    async def test_enrich_link_empty_content(self, link_enrichment_service, mock_db_client, mock_scraper, sample_link_record):
        """Test enrichment when scraper returns empty content."""
        # Setup scraper to return success but no content
        mock_scraper.scrape_url.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'content': None,
            'html': '<html></html>',
            'metadata': {'status_code': 200}
        }
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_link_record]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='test-link-id-123',
            url='http://example.com/product'
        )
        
        assert result['success'] is False
        assert result['error'] == 'empty content'
        assert result['link_id'] == 'test-link-id-123'

    @pytest.mark.asyncio
    async def test_enrich_link_content_hash_calculation(self, link_enrichment_service, mock_db_client, mock_scraper, sample_link_record):
        """Test content hash calculation and storage."""
        test_content = 'Test scraped content for hashing'
        expected_hash = hashlib.sha256(test_content.encode()).hexdigest()
        
        # Setup scraper to return specific content
        mock_scraper.scrape_url.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'content': test_content,
            'html': '<html><body>Test</body></html>',
            'metadata': {'status_code': 200}
        }
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_link_record]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='test-link-id-123',
            url='http://example.com/product'
        )
        
        assert result['success'] is True
        
        # Verify content hash was calculated and stored
        update_call = mock_db_client.table.return_value.update.return_value.eq.return_value.execute
        update_call.assert_called_once()
        
        # Get the update data from the call
        call_args = update_call.call_args
        update_data = call_args[0][0] if call_args[0] else {}
        
        assert update_data.get('content_hash') == expected_hash

    @pytest.mark.asyncio
    async def test_enrich_links_batch_success(self, link_enrichment_service, mock_db_client, sample_link_record):
        """Test successful batch enrichment."""
        # Setup mock database response for multiple links
        link_ids = ['link-1', 'link-2', 'link-3']
        mock_db_client.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[sample_link_record for _ in link_ids]
        )
        
        result = await link_enrichment_service.enrich_links_batch(link_ids)
        
        assert result['total'] == 3
        assert result['enriched'] == 3
        assert result['failed'] == 0
        assert result['skipped'] == 0

    @pytest.mark.asyncio
    async def test_enrich_links_batch_mixed_results(self, link_enrichment_service, mock_db_client, mock_scraper):
        """Test batch enrichment with mixed results."""
        # Setup different link records
        pending_link = {'id': 'link-1', 'scrape_status': 'pending', 'scraped_content': None, 'content_hash': None}
        enriched_link = {'id': 'link-2', 'scrape_status': 'success', 'scraped_content': 'content', 'content_hash': 'hash'}
        failed_link = {'id': 'link-3', 'scrape_status': 'pending', 'scraped_content': None, 'content_hash': None}
        
        # Setup scraper to fail for one link
        async def scrape_side_effect(url):
            if 'link-3' in url:
                return {'success': False, 'error': 'Connection failed'}
            return {'success': True, 'content': 'Success', 'metadata': {}}
        
        mock_scraper.scrape_url.side_effect = scrape_side_effect
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[pending_link, enriched_link, failed_link]
        )
        
        result = await link_enrichment_service.enrich_links_batch(['link-1', 'link-2', 'link-3'])
        
        assert result['total'] == 3
        assert result['enriched'] == 1  # Only pending_link succeeds
        assert result['skipped'] == 1   # enriched_link is skipped
        assert result['failed'] == 1    # failed_link fails

    @pytest.mark.asyncio
    async def test_enrich_links_batch_empty_list(self, link_enrichment_service):
        """Test batch enrichment with empty link list."""
        result = await link_enrichment_service.enrich_links_batch([])
        
        assert result['total'] == 0
        assert result['enriched'] == 0
        assert result['failed'] == 0
        assert result['skipped'] == 0

    @pytest.mark.asyncio
    async def test_enrich_links_batch_concurrency_limit(self, link_enrichment_service, mock_db_client, sample_link_record):
        """Test batch enrichment respects concurrency limit."""
        # Create service with low concurrency limit
        service = LinkEnrichmentService(
            web_scraping_service=link_enrichment_service._scraper,
            database_service=link_enrichment_service._database_service
        )
        service._max_concurrent_enrichments = 2
        
        # Setup mock database response for many links
        link_ids = [f'link-{i}' for i in range(10)]
        mock_db_client.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[sample_link_record for _ in link_ids]
        )
        
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0
        
        original_scrape = link_enrichment_service._scraper.scrape_url
        
        async def tracked_scrape(url):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)  # Small delay to allow concurrency
            concurrent_count -= 1
            return await original_scrape(url)
        
        link_enrichment_service._scraper.scrape_url = tracked_scrape
        
        result = await service.enrich_links_batch(link_ids)
        
        assert result['total'] == 10
        assert max_concurrent <= 2  # Should not exceed concurrency limit

    @pytest.mark.asyncio
    async def test_enrich_document_links_success(self, link_enrichment_service, mock_db_client, sample_link_record):
        """Test successful document links enrichment."""
        # Setup mock database response for document links
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[sample_link_record for _ in range(5)]
        )
        
        result = await link_enrichment_service.enrich_document_links('test-doc-id')
        
        assert result['total'] == 5
        assert result['enriched'] == 5
        assert result['failed'] == 0
        assert result['skipped'] == 0

    @pytest.mark.asyncio
    async def test_enrich_document_links_no_pending(self, link_enrichment_service, mock_db_client):
        """Test document enrichment with no pending links."""
        # Setup mock database response with no links
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await link_enrichment_service.enrich_document_links('empty-doc-id')
        
        assert result['total'] == 0
        assert result['enriched'] == 0
        assert result['failed'] == 0
        assert result['skipped'] == 0

    @pytest.mark.asyncio
    async def test_refresh_stale_links(self, link_enrichment_service, mock_db_client):
        """Test refreshing stale links."""
        # Create stale link record (older than 90 days)
        stale_date = datetime.now(timezone.utc) - timedelta(days=100)
        stale_link = {
            'id': 'stale-link-1',
            'scrape_status': 'success',
            'scraped_at': stale_date.isoformat(),
            'content_hash': 'old_hash'
        }
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.lt.return_value.execute.return_value = MagicMock(
            data=[stale_link]
        )
        
        result = await link_enrichment_service.refresh_stale_links(days_old=90)
        
        assert result['total'] == 1
        assert result['refreshed'] == 1

    @pytest.mark.asyncio
    async def test_refresh_stale_links_custom_threshold(self, link_enrichment_service, mock_db_client):
        """Test refreshing stale links with custom threshold."""
        # Create link older than 30 days but newer than 90 days
        recent_date = datetime.now(timezone.utc) - timedelta(days=45)
        recent_link = {
            'id': 'recent-link-1',
            'scrape_status': 'success',
            'scraped_at': recent_date.isoformat(),
            'content_hash': 'recent_hash'
        }
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.lt.return_value.execute.return_value = MagicMock(
            data=[recent_link]
        )
        
        result = await link_enrichment_service.refresh_stale_links(days_old=30)
        
        assert result['total'] == 1
        assert result['refreshed'] == 1

    @pytest.mark.asyncio
    async def test_retry_failed_links_within_budget(self, link_enrichment_service, mock_db_client):
        """Test retrying failed links within retry budget."""
        # Create failed link with retry_count < 3
        failed_link = {
            'id': 'failed-link-1',
            'scrape_status': 'failed',
            'scraped_metadata': {'retry_count': 2},
            'scraped_at': (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()  # More than 24h ago
        }
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.lt.return_value.execute.return_value = MagicMock(
            data=[failed_link]
        )
        
        result = await link_enrichment_service.retry_failed_links(max_retries=3)
        
        assert result['total'] == 1
        assert result['retried'] == 1

    @pytest.mark.asyncio
    async def test_retry_failed_links_exceeded_budget(self, link_enrichment_service, mock_db_client):
        """Test not retrying links that exceeded retry budget."""
        # Create failed link with retry_count >= 3
        exhausted_link = {
            'id': 'exhausted-link-1',
            'scrape_status': 'failed',
            'scraped_metadata': {'retry_count': 3},
            'scraped_at': (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        }
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.lt.return_value.execute.return_value = MagicMock(
            data=[exhausted_link]
        )
        
        result = await link_enrichment_service.retry_failed_links(max_retries=3)
        
        assert result['total'] == 1
        assert result['retried'] == 0  # Not retried due to exceeded budget

    @pytest.mark.asyncio
    async def test_retry_failed_links_time_threshold(self, link_enrichment_service, mock_db_client):
        """Test not retrying recently failed links."""
        # Create recently failed link (less than 24 hours ago)
        recent_failed_link = {
            'id': 'recent-failed-1',
            'scrape_status': 'failed',
            'scraped_metadata': {'retry_count': 1},
            'scraped_at': (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()  # Less than 24h ago
        }
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.lt.return_value.execute.return_value = MagicMock(
            data=[recent_failed_link]
        )
        
        result = await link_enrichment_service.retry_failed_links()
        
        assert result['total'] == 0  # No links returned due to time threshold

    @pytest.mark.asyncio
    async def test_get_enrichment_stats(self, link_enrichment_service, mock_db_client):
        """Test getting enrichment statistics."""
        # Setup mock database responses for various counts
        mock_db_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{'count': 100}]),  # total_links
            MagicMock(data=[{'count': 70}]),   # enriched_links
            MagicMock(data=[{'count': 20}]),   # pending_links
            MagicMock(data=[{'count': 10}]),   # failed_links
            MagicMock(data=[{'avg_length': 1500}]),  # average_content_length
            MagicMock(data=[{'backend': 'firecrawl', 'count': 50}, {'backend': 'beautifulsoup', 'count': 20}])  # backend_distribution
        ]
        
        result = await link_enrichment_service.get_enrichment_stats()
        
        assert result['total_links'] == 100
        assert result['enriched_links'] == 70
        assert result['pending_links'] == 20
        assert result['failed_links'] == 10
        assert result['average_content_length'] == 1500
        assert 'backend_distribution' in result
        assert result['backend_distribution']['firecrawl'] == 50
        assert result['backend_distribution']['beautifulsoup'] == 20

    @pytest.mark.asyncio
    async def test_get_enrichment_stats_empty_database(self, link_enrichment_service, mock_db_client):
        """Test getting enrichment statistics from empty database."""
        # Setup mock database responses with zero counts
        mock_db_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{'count': 0}]),
            MagicMock(data=[{'count': 0}]),
            MagicMock(data=[{'count': 0}]),
            MagicMock(data=[{'count': 0}]),
            MagicMock(data=[{'avg_length': 0}]),
            MagicMock(data=[])
        ]
        
        result = await link_enrichment_service.get_enrichment_stats()
        
        assert result['total_links'] == 0
        assert result['enriched_links'] == 0
        assert result['pending_links'] == 0
        assert result['failed_links'] == 0
        assert result['average_content_length'] == 0
        assert result['backend_distribution'] == {}

    def test_database_client_unavailable(self, mock_scraper):
        """Test behavior when database client is unavailable."""
        # Create service with None database client
        service = LinkEnrichmentService(
            web_scraping_service=mock_scraper,
            database_service=MagicMock(client=None)
        )
        
        # This should be handled gracefully in actual implementation
        assert service._get_db_client() is None

    @pytest.mark.asyncio
    async def test_database_update_failure(self, link_enrichment_service, mock_db_client, mock_scraper, sample_link_record):
        """Test handling of database update failure."""
        # Setup database to fail on update
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("DB Error")
        
        # Setup mock database response for select
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_link_record]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='test-link-id-123',
            url='http://example.com/product'
        )
        
        # Should still return success (scraping worked) but log the error
        assert result['success'] is True

    def test_service_disabled_error(self, mock_scraper, mock_database_service):
        """Test service returns error when disabled."""
        with patch('backend.services.link_enrichment_service.ConfigService') as mock_config_class:
            mock_config = MagicMock()
            mock_config.get_scraping_config.return_value = {'enable_link_enrichment': False}
            mock_config_class.return_value = mock_config
            
            service = LinkEnrichmentService(
                web_scraping_service=mock_scraper,
                database_service=mock_database_service,
                config_service=mock_config
            )
            
            # Test that enrich_link returns disabled error
            result = asyncio.run(service.enrich_link('test-id', 'http://example.com'))
            
            assert result['success'] is False
            assert result['error'] == 'link enrichment disabled'

    @pytest.mark.asyncio
    async def test_enrich_links_batch_force_refresh(self, link_enrichment_service, mock_db_client, enriched_link_record):
        """Test batch enrichment with force refresh."""
        # Setup mock database response for enriched links
        mock_db_client.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[enriched_link_record for _ in range(3)]
        )
        
        result = await link_enrichment_service.enrich_links_batch(
            ['link-1', 'link-2', 'link-3'],
            force_refresh=True
        )
        
        assert result['total'] == 3
        assert result['enriched'] == 3  # All should be enriched due to force_refresh
        assert result['skipped'] == 0

    @pytest.mark.asyncio
    async def test_enrich_link_retry_count_increment(self, link_enrichment_service, mock_db_client, mock_scraper, sample_link_record):
        """Test that retry count is incremented on failure."""
        # Setup scraper to fail
        mock_scraper.scrape_url.return_value = {
            'success': False,
            'error': 'Connection failed'
        }
        
        # Setup link record with existing retry count
        sample_link_record['scraped_metadata'] = {'retry_count': 2}
        
        # Setup mock database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_link_record]
        )
        
        result = await link_enrichment_service.enrich_link(
            link_id='test-link-id-123',
            url='http://example.com/product'
        )
        
        assert result['success'] is False
        
        # Verify retry count was incremented
        update_call = mock_db_client.table.return_value.update.return_value.eq.return_value.execute
        update_call.assert_called_once()
        
        call_args = update_call.call_args
        update_data = call_args[0][0] if call_args[0] else {}
        scraped_metadata = update_data.get('scraped_metadata', {})
        
        assert scraped_metadata.get('retry_count') == 3
