"""
Unit tests for ManufacturerCrawler.

Tests manufacturer crawling functionality including schedule management,
job execution, page processing, and content change detection.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import hashlib

from services.manufacturer_crawler import ManufacturerCrawler


pytest.mark.unit = pytest.mark.unit


class TestManufacturerCrawler:
    """Test ManufacturerCrawler functionality."""

    @pytest.fixture
    def mock_scraper(self):
        """Mock WebScrapingService."""
        scraper = MagicMock()
        scraper.crawl_site = AsyncMock(return_value={
            'success': True,
            'backend': 'firecrawl',
            'total': 5,
            'pages': [
                {
                    'url': 'http://example.com/product1',
                    'content': 'Product 1 content',
                    'metadata': {'title': 'Product 1'}
                },
                {
                    'url': 'http://example.com/product2',
                    'content': 'Product 2 content',
                    'metadata': {'title': 'Product 2'}
                }
            ]
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
    def mock_batch_task_service(self):
        """Mock BatchTaskService."""
        service = MagicMock()
        service.create_task = AsyncMock(return_value='batch-task-id-123')
        service.get_task_status = AsyncMock(return_value={'status': 'completed'})
        return service

    @pytest.fixture
    def mock_structured_extraction_service(self):
        """Mock StructuredExtractionService."""
        service = MagicMock()
        service.batch_extract = AsyncMock(return_value={
            'total': 2,
            'completed': 2,
            'failed': 0
        })
        return service

    @pytest.fixture
    def manufacturer_crawler(self, mock_scraper, mock_database_service, mock_batch_task_service):
        """Create ManufacturerCrawler instance for testing."""
        return ManufacturerCrawler(
            web_scraping_service=mock_scraper,
            database_service=mock_database_service,
            batch_task_service=mock_batch_task_service
        )

    @pytest.fixture
    def sample_crawl_schedule(self):
        """Sample crawl schedule for testing."""
        return {
            'id': 'schedule-id-123',
            'manufacturer_id': 'mfr-id-123',
            'crawl_type': 'support_pages',
            'start_url': 'http://example.com/support',
            'max_pages': 50,
            'max_depth': 3,
            'enabled': True,
            'cron_expression': '0 2 * * *',  # Daily at 2 AM
            'last_run_at': None,
            'next_run_at': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }

    @pytest.fixture
    def sample_crawl_job(self):
        """Sample crawl job for testing."""
        return {
            'id': 'job-id-123',
            'schedule_id': 'schedule-id-123',
            'manufacturer_id': 'mfr-id-123',
            'status': 'running',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': None,
            'pages_crawled': 0,
            'pages_failed': 0,
            'error_message': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }

    @pytest.fixture
    def sample_crawled_pages(self):
        """Sample crawled pages for testing."""
        return [
            {
                'id': 'page-1',
                'crawl_job_id': 'job-id-123',
                'url': 'http://example.com/product1',
                'title': 'Product 1',
                'content': '# Product 1\n\nSpecifications: ...',
                'content_hash': hashlib.sha256('Product 1 content'.encode()).hexdigest(),
                'page_type': 'product_page',
                'status': 'scraped',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'id': 'page-2',
                'crawl_job_id': 'job-id-123',
                'url': 'http://example.com/error-codes',
                'title': 'Error Codes',
                'content': '# Error Codes\n\n900.01: Fuser error',
                'content_hash': hashlib.sha256('Error codes content'.encode()).hexdigest(),
                'page_type': 'error_code_page',
                'status': 'scraped',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            }
        ]

    def test_crawler_initialization(self, mock_scraper, mock_database_service):
        """Test crawler initialization with correct config."""
        crawler = ManufacturerCrawler(
            web_scraping_service=mock_scraper,
            database_service=mock_database_service
        )
        
        assert crawler._scraper == mock_scraper
        assert crawler._database_service == mock_database_service
        assert crawler._enabled is False  # Default disabled
        assert crawler._config['crawler_max_concurrent_jobs'] == 1
        assert crawler._config['crawler_default_max_pages'] == 100

    def test_crawler_initialization_enabled(self, mock_scraper, mock_database_service):
        """Test crawler initialization when feature is enabled."""
        with patch('backend.services.manufacturer_crawler.ConfigService') as mock_config_class:
            mock_config = MagicMock()
            mock_config.get_scraping_config.return_value = {'enable_manufacturer_crawling': True}
            mock_config_class.return_value = mock_config
            
            crawler = ManufacturerCrawler(
                web_scraping_service=mock_scraper,
                database_service=mock_database_service,
                config_service=mock_config
            )
            
            assert crawler._enabled is True

    def test_crawler_initialization_with_optional_services(self, mock_scraper, mock_database_service, 
                                                         mock_structured_extraction_service, mock_batch_task_service):
        """Test crawler initialization with optional services."""
        crawler = ManufacturerCrawler(
            web_scraping_service=mock_scraper,
            database_service=mock_database_service,
            structured_extraction_service=mock_structured_extraction_service,
            batch_task_service=mock_batch_task_service
        )
        
        assert crawler._structured_extraction_service == mock_structured_extraction_service
        assert crawler._batch_task_service == mock_batch_task_service

    @pytest.mark.asyncio
    async def test_create_crawl_schedule_success(self, manufacturer_crawler, mock_db_client):
        """Test successful crawl schedule creation."""
        # Setup database response
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'new-schedule-id'}]
        )
        
        crawl_config = {
            'crawl_type': 'support_pages',
            'start_url': 'http://example.com/support',
            'max_pages': 50,
            'max_depth': 3,
            'cron_expression': '0 2 * * *'
        }
        
        result = await manufacturer_crawler.create_crawl_schedule('mfr-id-123', crawl_config)
        
        assert result == 'new-schedule-id'
        
        # Verify schedule was inserted
        mock_db_client.table.return_value.insert.return_value.execute.assert_called_once()
        
        call_args = mock_db_client.table.return_value.insert.return_value.execute.call_args
        insert_data = call_args[0][0] if call_args[0] else {}
        
        assert insert_data['manufacturer_id'] == 'mfr-id-123'
        assert insert_data['crawl_type'] == 'support_pages'
        assert insert_data['start_url'] == 'http://example.com/support'
        assert insert_data['enabled'] is True

    @pytest.mark.asyncio
    async def test_create_crawl_schedule_invalid_config(self, manufacturer_crawler):
        """Test crawl schedule creation with invalid config."""
        invalid_config = {
            'crawl_type': 'invalid_type',
            'start_url': 'not-a-url'
        }
        
        result = await manufacturer_crawler.create_crawl_schedule('mfr-id-123', invalid_config)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_create_crawl_schedule_database_error(self, manufacturer_crawler, mock_db_client):
        """Test crawl schedule creation with database error."""
        # Setup database to raise error
        mock_db_client.table.return_value.insert.return_value.execute.side_effect = Exception("DB Error")
        
        crawl_config = {
            'crawl_type': 'support_pages',
            'start_url': 'http://example.com/support'
        }
        
        result = await manufacturer_crawler.create_crawl_schedule('mfr-id-123', crawl_config)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_crawl_schedule_success(self, manufacturer_crawler, mock_db_client, sample_crawl_schedule):
        """Test successful crawl schedule update."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_schedule]
        )
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'schedule-id-123'}]
        )
        
        updates = {
            'max_pages': 100,
            'enabled': False
        }
        
        result = await manufacturer_crawler.update_crawl_schedule('schedule-id-123', updates)
        
        assert result is True
        
        # Verify schedule was updated
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_crawl_schedule_not_found(self, manufacturer_crawler, mock_db_client):
        """Test updating non-existent crawl schedule."""
        # Setup database response with no schedule
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await manufacturer_crawler.update_crawl_schedule('nonexistent-id', {'enabled': False})
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_crawl_schedule_success(self, manufacturer_crawler, mock_db_client, sample_crawl_schedule):
        """Test successful crawl schedule deletion."""
        # Setup database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_schedule]
        )
        mock_db_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'schedule-id-123'}]
        )
        
        result = await manufacturer_crawler.delete_crawl_schedule('schedule-id-123')
        
        assert result is True
        
        # Verify schedule was deleted
        mock_db_client.table.return_value.delete.return_value.eq.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_crawl_schedule_not_found(self, manufacturer_crawler, mock_db_client):
        """Test deleting non-existent crawl schedule."""
        # Setup database response with no schedule
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await manufacturer_crawler.delete_crawl_schedule('nonexistent-id')
        
        assert result is False

    @pytest.mark.asyncio
    async def test_list_crawl_schedules_all(self, manufacturer_crawler, mock_db_client, sample_crawl_schedule):
        """Test listing all crawl schedules."""
        # Setup database response
        mock_db_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_schedule]
        )
        
        result = await manufacturer_crawler.list_crawl_schedules()
        
        assert len(result) == 1
        assert result[0]['id'] == 'schedule-id-123'
        assert result[0]['manufacturer_id'] == 'mfr-id-123'

    @pytest.mark.asyncio
    async def test_list_crawl_schedules_by_manufacturer(self, manufacturer_crawler, mock_db_client, sample_crawl_schedule):
        """Test listing crawl schedules by manufacturer."""
        # Setup database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_schedule]
        )
        
        result = await manufacturer_crawler.list_crawl_schedules('mfr-id-123')
        
        assert len(result) == 1
        assert result[0]['manufacturer_id'] == 'mfr-id-123'

    @pytest.mark.asyncio
    async def test_get_crawl_schedule_success(self, manufacturer_crawler, mock_db_client, sample_crawl_schedule):
        """Test getting specific crawl schedule."""
        # Setup database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_schedule]
        )
        
        result = await manufacturer_crawler.get_crawl_schedule('schedule-id-123')
        
        assert result is not None
        assert result['id'] == 'schedule-id-123'
        assert result['manufacturer_id'] == 'mfr-id-123'

    @pytest.mark.asyncio
    async def test_get_crawl_schedule_not_found(self, manufacturer_crawler, mock_db_client):
        """Test getting non-existent crawl schedule."""
        # Setup database response with no schedule
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await manufacturer_crawler.get_crawl_schedule('nonexistent-id')
        
        assert result is None

    @pytest.mark.asyncio
    async def test_start_crawl_job_success(self, manufacturer_crawler, mock_db_client, mock_batch_task_service, sample_crawl_schedule):
        """Test successful crawl job start."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_schedule]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'new-job-id'}]
        )
        
        result = await manufacturer_crawler.start_crawl_job('schedule-id-123')
        
        assert result == 'new-job-id'
        
        # Verify job was created
        mock_db_client.table.return_value.insert.return_value.execute.assert_called_once()
        
        # Verify batch task was created
        mock_batch_task_service.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_crawl_job_schedule_not_found(self, manufacturer_crawler, mock_db_client):
        """Test starting crawl job for non-existent schedule."""
        # Setup database response with no schedule
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await manufacturer_crawler.start_crawl_job('nonexistent-id')
        
        assert result is None

    @pytest.mark.asyncio
    async def test_start_crawl_job_schedule_disabled(self, manufacturer_crawler, mock_db_client, sample_crawl_schedule):
        """Test starting crawl job for disabled schedule."""
        # Setup disabled schedule
        disabled_schedule = sample_crawl_schedule.copy()
        disabled_schedule['enabled'] = False
        
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[disabled_schedule]
        )
        
        result = await manufacturer_crawler.start_crawl_job('schedule-id-123')
        
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_crawl_job_success(self, manufacturer_crawler, mock_db_client, mock_scraper, sample_crawl_job, sample_crawled_pages):
        """Test successful crawl job execution."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'new-page-id'}]
        )
        
        # Setup scraper response
        mock_scraper.crawl_site.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'total': 2,
            'pages': [
                {
                    'url': 'http://example.com/product1',
                    'content': 'Product 1 content',
                    'metadata': {'title': 'Product 1'}
                },
                {
                    'url': 'http://example.com/product2',
                    'content': 'Product 2 content',
                    'metadata': {'title': 'Product 2'}
                }
            ]
        }
        
        result = await manufacturer_crawler.execute_crawl_job('job-id-123')
        
        assert result['success'] is True
        assert result['pages_crawled'] == 2
        assert result['pages_failed'] == 0
        
        # Verify job was updated with completion status
        update_calls = mock_db_client.table.return_value.update.return_value.eq.return_value.execute
        assert update_calls.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_crawl_job_not_found(self, manufacturer_crawler, mock_db_client):
        """Test executing non-existent crawl job."""
        # Setup database response with no job
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await manufacturer_crawler.execute_crawl_job('nonexistent-job-id')
        
        assert result['success'] is False
        assert result['error'] == 'job not found'

    @pytest.mark.asyncio
    async def test_execute_crawl_job_scraping_failure(self, manufacturer_crawler, mock_db_client, mock_scraper, sample_crawl_job):
        """Test crawl job execution with scraping failure."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        
        # Setup scraper to fail
        mock_scraper.crawl_site.return_value = {
            'success': False,
            'error': 'Connection timeout'
        }
        
        result = await manufacturer_crawler.execute_crawl_job('job-id-123')
        
        assert result['success'] is False
        assert result['error'] == 'Connection timeout'
        
        # Verify job was marked as failed
        update_calls = mock_db_client.table.return_value.update.return_value.eq.return_value.execute
        update_calls.assert_called()

    @pytest.mark.asyncio
    async def test_execute_crawl_job_firecrawl_fallback(self, manufacturer_crawler, mock_db_client, mock_scraper, sample_crawl_job):
        """Test crawl job execution with Firecrawl fallback."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'new-page-id'}]
        )
        
        # Setup scraper to fail with Firecrawl then succeed with BeautifulSoup
        firecrawl_error = Exception("Firecrawl unavailable")
        beautifulsoup_result = {
            'success': True,
            'backend': 'beautifulsoup',
            'total': 1,
            'pages': [
                {
                    'url': 'http://example.com/product1',
                    'content': 'Product 1 content',
                    'metadata': {'title': 'Product 1'}
                }
            ]
        }
        
        mock_scraper.crawl_site.side_effect = [firecrawl_error, beautifulsoup_result]
        
        result = await manufacturer_crawler.execute_crawl_job('job-id-123')
        
        assert result['success'] is True
        assert result['pages_crawled'] == 1
        assert result['backend'] == 'beautifulsoup'

    @pytest.mark.asyncio
    async def test_process_crawled_pages_with_extraction(self, manufacturer_crawler, mock_db_client, 
                                                         mock_structured_extraction_service, sample_crawled_pages):
        """Test processing crawled pages with structured extraction."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_crawled_pages
        )
        
        result = await manufacturer_crawler.process_crawled_pages('job-id-123')
        
        assert result['total_pages'] == 2
        assert result['processed_pages'] == 2
        assert result['extractions_created'] == 2
        
        # Verify structured extraction was called
        mock_structured_extraction_service.batch_extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_crawled_pages_no_extraction_service(self, manufacturer_crawler, mock_db_client, sample_crawled_pages):
        """Test processing crawled pages without extraction service."""
        # Create crawler without extraction service
        crawler = ManufacturerCrawler(
            web_scraping_service=manufacturer_crawler._scraper,
            database_service=manufacturer_crawler._database_service
        )
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_crawled_pages
        )
        
        result = await crawler.process_crawled_pages('job-id-123')
        
        assert result['total_pages'] == 2
        assert result['processed_pages'] == 2
        assert result['extractions_created'] == 0  # No extraction service

    @pytest.mark.asyncio
    async def test_process_crawled_pages_no_pages(self, manufacturer_crawler, mock_db_client):
        """Test processing crawled pages with no pages."""
        # Setup database response with no pages
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await manufacturer_crawler.process_crawled_pages('job-id-123')
        
        assert result['total_pages'] == 0
        assert result['processed_pages'] == 0
        assert result['extractions_created'] == 0

    @pytest.mark.asyncio
    async def test_detect_content_changes_with_changes(self, manufacturer_crawler, mock_db_client, sample_crawled_pages):
        """Test content change detection with actual changes."""
        # Create modified pages (different content hash)
        modified_pages = []
        for page in sample_crawled_pages:
            modified_page = page.copy()
            modified_page['content_hash'] = 'different-hash-123'
            modified_pages.append(modified_page)
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_crawled_pages  # Original pages
        )
        
        result = await manufacturer_crawler.detect_content_changes('mfr-id-123', modified_pages)
        
        assert len(result) == 2
        assert all(change['change_type'] == 'content_modified' for change in result)
        assert all('previous_hash' in change for change in result)

    @pytest.mark.asyncio
    async def test_detect_content_changes_new_pages(self, manufacturer_crawler, mock_db_client, sample_crawled_pages):
        """Test content change detection with new pages."""
        # Setup database response with no existing pages
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await manufacturer_crawler.detect_content_changes('mfr-id-123', sample_crawled_pages)
        
        assert len(result) == 2
        assert all(change['change_type'] == 'new_page' for change in result)
        assert all('previous_hash' not in change for change in result)

    @pytest.mark.asyncio
    async def test_detect_content_changes_no_changes(self, manufacturer_crawler, mock_db_client, sample_crawled_pages):
        """Test content change detection with no changes."""
        # Setup database response with identical pages
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_crawled_pages  # Same pages
        )
        
        result = await manufacturer_crawler.detect_content_changes('mfr-id-123', sample_crawled_pages)
        
        assert len(result) == 0  # No changes detected

    @pytest.mark.asyncio
    async def test_get_crawl_job_status_success(self, manufacturer_crawler, mock_db_client, sample_crawl_job):
        """Test getting crawl job status."""
        # Setup database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        
        result = await manufacturer_crawler.get_crawl_job_status('job-id-123')
        
        assert result is not None
        assert result['id'] == 'job-id-123'
        assert result['status'] == 'running'

    @pytest.mark.asyncio
    async def test_get_crawl_job_status_not_found(self, manufacturer_crawler, mock_db_client):
        """Test getting status of non-existent crawl job."""
        # Setup database response with no job
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await manufacturer_crawler.get_crawl_job_status('nonexistent-job-id')
        
        assert result is None

    @pytest.mark.asyncio
    async def test_list_crawl_jobs_all(self, manufacturer_crawler, mock_db_client, sample_crawl_job):
        """Test listing all crawl jobs."""
        # Setup database response
        mock_db_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        
        result = await manufacturer_crawler.list_crawl_jobs()
        
        assert len(result) == 1
        assert result[0]['id'] == 'job-id-123'

    @pytest.mark.asyncio
    async def test_list_crawl_jobs_by_schedule(self, manufacturer_crawler, mock_db_client, sample_crawl_job):
        """Test listing crawl jobs by schedule."""
        # Setup database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        
        result = await manufacturer_crawler.list_crawl_jobs(schedule_id='schedule-id-123')
        
        assert len(result) == 1
        assert result[0]['schedule_id'] == 'schedule-id-123'

    @pytest.mark.asyncio
    async def test_list_crawl_jobs_by_status(self, manufacturer_crawler, mock_db_client, sample_crawl_job):
        """Test listing crawl jobs by status."""
        # Setup database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        
        result = await manufacturer_crawler.list_crawl_jobs(status='running')
        
        assert len(result) == 1
        assert result[0]['status'] == 'running'

    @pytest.mark.asyncio
    async def test_retry_failed_job_success(self, manufacturer_crawler, mock_db_client, mock_batch_task_service, sample_crawl_job):
        """Test retrying failed crawl job."""
        # Setup failed job
        failed_job = sample_crawl_job.copy()
        failed_job['status'] = 'failed'
        failed_job['error_message'] = 'Connection timeout'
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[failed_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'retry-job-id'}]
        )
        
        result = await manufacturer_crawler.retry_failed_job('job-id-123')
        
        assert result == 'retry-job-id'
        
        # Verify new job was created
        mock_db_client.table.return_value.insert.return_value.execute.assert_called_once()
        
        # Verify batch task was created
        mock_batch_task_service.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_failed_job_not_failed(self, manufacturer_crawler, mock_db_client, sample_crawl_job):
        """Test retrying job that is not failed."""
        # Setup running job
        running_job = sample_crawl_job.copy()
        
        # Setup database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[running_job]
        )
        
        result = await manufacturer_crawler.retry_failed_job('job-id-123')
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_crawled_pages_success(self, manufacturer_crawler, mock_db_client, sample_crawled_pages):
        """Test getting crawled pages for job."""
        # Setup database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=sample_crawled_pages
        )
        
        result = await manufacturer_crawler.get_crawled_pages('job-id-123')
        
        assert len(result) == 2
        assert result[0]['id'] == 'page-1'
        assert result[1]['id'] == 'page-2'

    @pytest.mark.asyncio
    async def test_get_crawled_pages_with_pagination(self, manufacturer_crawler, mock_db_client, sample_crawled_pages):
        """Test getting crawled pages with pagination."""
        # Setup database response
        mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=sample_crawled_pages[:1]  # Return only first page
        )
        
        result = await manufacturer_crawler.get_crawled_pages('job-id-123', limit=1, offset=0)
        
        assert len(result) == 1
        assert result[0]['id'] == 'page-1'

    @pytest.mark.asyncio
    async def test_check_scheduled_crawls_due(self, manufacturer_crawler, mock_db_client, mock_batch_task_service):
        """Test checking for scheduled crawls that are due."""
        # Create schedule that is due to run
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        due_schedule = {
            'id': 'due-schedule-id',
            'manufacturer_id': 'mfr-id-123',
            'enabled': True,
            'next_run_at': past_time,
            'last_run_at': None
        }
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.lte.return_value.execute.return_value = MagicMock(
            data=[due_schedule]
        )
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'due-schedule-id'}]
        )
        
        result = await manufacturer_crawler.check_scheduled_crawls()
        
        assert len(result) == 1
        assert 'due-schedule-id' in result
        
        # Verify batch task was created for due schedule
        assert mock_batch_task_service.create_task.call_count == 1

    @pytest.mark.asyncio
    async def test_check_scheduled_crawls_not_due(self, manufacturer_crawler, mock_db_client):
        """Test checking for scheduled crawls that are not due."""
        # Create schedule that is not due to run
        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        future_schedule = {
            'id': 'future-schedule-id',
            'manufacturer_id': 'mfr-id-123',
            'enabled': True,
            'next_run_at': future_time,
            'last_run_at': None
        }
        
        # Setup database response (should return empty since we query for past times)
        mock_db_client.table.return_value.select.return_value.eq.return_value.lte.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await manufacturer_crawler.check_scheduled_crawls()
        
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_crawler_stats(self, manufacturer_crawler, mock_db_client):
        """Test getting crawler statistics."""
        # Setup database responses for various counts
        mock_db_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{'count': 5}]),   # total_schedules
            MagicMock(data=[{'count': 3}]),   # active_schedules
            MagicMock(data=[{'count': 20}]),  # total_jobs
            MagicMock(data=[{'count': 2}]),   # running_jobs
            MagicMock(data=[{'count': 15}]),  # completed_jobs
            MagicMock(data=[{'count': 3}]),   # failed_jobs
            MagicMock(data=[{'count': 500}]), # total_pages
            MagicMock(data=[{'avg_pages': 25}]) # avg_pages_per_job
        ]
        
        result = await manufacturer_crawler.get_crawler_stats()
        
        assert result['total_schedules'] == 5
        assert result['active_schedules'] == 3
        assert result['total_jobs'] == 20
        assert result['running_jobs'] == 2
        assert result['completed_jobs'] == 15
        assert result['failed_jobs'] == 3
        assert result['total_pages'] == 500
        assert result['avg_pages_per_job'] == 25

    @pytest.mark.asyncio
    async def test_get_crawler_stats_empty(self, manufacturer_crawler, mock_db_client):
        """Test getting crawler statistics from empty database."""
        # Setup database responses with zero counts
        mock_db_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{'count': 0}]),
            MagicMock(data=[{'count': 0}]),
            MagicMock(data=[{'count': 0}]),
            MagicMock(data=[{'count': 0}]),
            MagicMock(data=[{'count': 0}]),
            MagicMock(data=[{'count': 0}]),
            MagicMock(data=[{'avg_pages': 0}])
        ]
        
        result = await manufacturer_crawler.get_crawler_stats()
        
        assert result['total_schedules'] == 0
        assert result['active_schedules'] == 0
        assert result['total_jobs'] == 0
        assert result['running_jobs'] == 0
        assert result['completed_jobs'] == 0
        assert result['failed_jobs'] == 0
        assert result['total_pages'] == 0
        assert result['avg_pages_per_job'] == 0

    def test_validate_crawl_config_valid(self, manufacturer_crawler):
        """Test validation of valid crawl configuration."""
        valid_config = {
            'crawl_type': 'support_pages',
            'start_url': 'http://example.com/support',
            'max_pages': 50,
            'max_depth': 3
        }
        
        result = manufacturer_crawler._validate_crawl_config(valid_config)
        
        assert result is True

    def test_validate_crawl_config_invalid_type(self, manufacturer_crawler):
        """Test validation of invalid crawl type."""
        invalid_config = {
            'crawl_type': 'invalid_type',
            'start_url': 'http://example.com/support'
        }
        
        result = manufacturer_crawler._validate_crawl_config(invalid_config)
        
        assert result is False

    def test_validate_crawl_config_invalid_url(self, manufacturer_crawler):
        """Test validation of invalid URL."""
        invalid_config = {
            'crawl_type': 'support_pages',
            'start_url': 'not-a-url'
        }
        
        result = manufacturer_crawler._validate_crawl_config(invalid_config)
        
        assert result is False

    def test_validate_crawl_config_invalid_pages(self, manufacturer_crawler):
        """Test validation of invalid max_pages."""
        invalid_config = {
            'crawl_type': 'support_pages',
            'start_url': 'http://example.com/support',
            'max_pages': -1
        }
        
        result = manufacturer_crawler._validate_crawl_config(invalid_config)
        
        assert result is False

    def test_validate_crawl_config_invalid_depth(self, manufacturer_crawler):
        """Test validation of invalid max_depth."""
        invalid_config = {
            'crawl_type': 'support_pages',
            'start_url': 'http://example.com/support',
            'max_depth': -1
        }
        
        result = manufacturer_crawler._validate_crawl_config(invalid_config)
        
        assert result is False

    def test_calculate_next_run_time_daily(self, manufacturer_crawler):
        """Test calculating next run time for daily cron."""
        cron_expr = '0 2 * * *'  # Daily at 2 AM
        next_run = manufacturer_crawler._calculate_next_run_time(cron_expr)
        
        assert next_run is not None
        assert next_run > datetime.now(timezone.utc)

    def test_calculate_next_run_time_weekly(self, manufacturer_crawler):
        """Test calculating next run time for weekly cron."""
        cron_expr = '0 3 * * 1'  # Weekly on Monday at 3 AM
        next_run = manufacturer_crawler._calculate_next_run_time(cron_expr)
        
        assert next_run is not None
        assert next_run > datetime.now(timezone.utc)

    def test_calculate_next_run_time_invalid_cron(self, manufacturer_crawler):
        """Test calculating next run time for invalid cron expression."""
        cron_expr = 'invalid-cron'
        next_run = manufacturer_crawler._calculate_next_run_time(cron_expr)
        
        assert next_run is None

    def test_determine_page_type_from_url(self, manufacturer_crawler):
        """Test determining page type from URL."""
        # Test various URL patterns
        assert manufacturer_crawler._determine_page_type_from_url('http://example.com/product/c750a') == 'product_page'
        assert manufacturer_crawler._determine_page_type_from_url('http://example.com/products/c750a/specs') == 'product_page'
        assert manufacturer_crawler._determine_page_type_from_url('http://example.com/error-codes') == 'error_code_page'
        assert manufacturer_crawler._determine_page_type_from_url('http://example.com/manual.pdf') == 'manual_page'
        assert manufacturer_crawler._determine_page_type_from_url('http://example.com/parts-catalog') == 'parts_page'
        assert manufacturer_crawler._determine_page_type_from_url('http://example.com/troubleshooting') == 'troubleshooting_page'
        
        # Test generic URL
        assert manufacturer_crawler._determine_page_type_from_url('http://example.com/about') == 'other'

    def test_determine_page_type_from_content(self, manufacturer_crawler):
        """Test determining page type from content."""
        # Test content patterns
        assert manufacturer_crawler._determine_page_type_from_content('# Error Codes\n\n900.01: Fuser error') == 'error_code_page'
        assert manufacturer_crawler._determine_page_type_from_content('# Service Manual\n\nType: Service Manual') == 'manual_page'
        assert manufacturer_crawler._determine_page_type_from_content('# Parts List\n\nPart Number: A02') == 'parts_page'
        assert manufacturer_crawler._determine_page_type_from_content('# Troubleshooting\n\nProblem: Printer not working') == 'troubleshooting_page'
        assert manufacturer_crawler._determine_page_type_from_content('# Specifications\n\nModel: C750a') == 'product_page'
        
        # Test generic content
        assert manufacturer_crawler._determine_page_type_from_content('About our company') == 'other'

    @pytest.mark.asyncio
    async def test_update_job_status(self, manufacturer_crawler, mock_db_client, sample_crawl_job):
        """Test updating job status."""
        # Setup database response
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'job-id-123'}]
        )
        
        await manufacturer_crawler._update_job('job-id-123', {'status': 'completed'})
        
        # Verify job was updated
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()
        
        call_args = mock_db_client.table.return_value.update.return_value.eq.return_value.execute.call_args
        update_data = call_args[0][0] if call_args[0] else {}
        
        assert update_data['status'] == 'completed'
        assert 'completed_at' in update_data

    @pytest.mark.asyncio
    async def test_update_schedule_run_time(self, manufacturer_crawler, mock_db_client):
        """Test updating schedule run time."""
        # Setup database response
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'schedule-id-123'}]
        )
        
        await manufacturer_crawler._update_schedule_run('schedule-id-123')
        
        # Verify schedule was updated
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()
        
        call_args = mock_db_client.table.return_value.update.return_value.eq.return_value.execute.call_args
        update_data = call_args[0][0] if call_args[0] else {}
        
        assert 'last_run_at' in update_data
        assert 'next_run_at' in update_data

    @pytest.mark.asyncio
    async def test_persist_crawled_pages_success(self, manufacturer_crawler, mock_db_client, sample_crawled_pages):
        """Test persisting crawled pages successfully."""
        # Setup database response
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'new-page-id'}]
        )
        
        result = await manufacturer_crawler._persist_crawled_pages('job-id-123', 'mfr-id-123', sample_crawled_pages)
        
        assert result['total'] == 2
        assert result['inserted'] == 2
        assert result['updated'] == 0
        
        # Verify pages were inserted
        assert mock_db_client.table.return_value.insert.return_value.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_persist_crawled_pages_with_duplicates(self, manufacturer_crawler, mock_db_client, sample_crawled_pages):
        """Test persisting crawled pages with duplicates."""
        # Setup database to indicate duplicates exist
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'existing-page-id'}]  # Existing page
        )
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'updated-page-id'}]
        )
        
        result = await manufacturer_crawler._persist_crawled_pages('job-id-123', 'mfr-id-123', sample_crawled_pages)
        
        assert result['total'] == 2
        assert result['inserted'] == 0
        assert result['updated'] == 2

    def test_is_crawler_enabled_true(self, manufacturer_crawler):
        """Test checking if crawler is enabled when it is."""
        manufacturer_crawler._enabled = True
        
        result = manufacturer_crawler.is_crawler_enabled()
        
        assert result is True

    def test_is_crawler_enabled_false(self, manufacturer_crawler):
        """Test checking if crawler is enabled when it is disabled."""
        manufacturer_crawler._enabled = False
        
        result = manufacturer_crawler.is_crawler_enabled()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_disabled_crawler_operations(self, manufacturer_crawler):
        """Test that operations return gracefully when crawler is disabled."""
        manufacturer_crawler._enabled = False
        
        # These operations should return appropriate responses when disabled
        result1 = await manufacturer_crawler.start_crawl_job('schedule-id-123')
        assert result1 is None
        
        result2 = await manufacturer_crawler.execute_crawl_job('job-id-123')
        assert result2['success'] is False
        assert result2['error'] == 'crawler disabled'
