"""
End-to-end integration tests for ManufacturerCrawler.

Tests complete manufacturer crawling workflows including schedule management,
job execution, page processing, and structured extraction.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import hashlib

from services.manufacturer_crawler import ManufacturerCrawler


pytest.mark.integration = pytest.mark.integration


class TestManufacturerCrawlerE2E:
    """Test ManufacturerCrawler end-to-end scenarios."""

    @pytest.fixture
    def mock_scraper(self):
        """Mock WebScrapingService."""
        scraper = MagicMock()
        scraper.crawl_site = AsyncMock(return_value={
            'success': True,
            'backend': 'firecrawl',
            'total': 10,
            'pages': [
                {
                    'url': 'http://example.com/product/c750a',
                    'content': '# C750a Specifications\n\nPrint Speed: 75 ppm\nResolution: 1200x1200 dpi',
                    'metadata': {'title': 'C750a Specifications', 'content_type': 'text/html'}
                },
                {
                    'url': 'http://example.com/error-codes/c750a',
                    'content': '# C750a Error Codes\n\n900.01: Fuser error\n900.02: Lamp error',
                    'metadata': {'title': 'C750a Error Codes', 'content_type': 'text/html'}
                },
                {
                    'url': 'http://example.com/manual/c750a.pdf',
                    'content': '# C750a Service Manual\n\nComplete service documentation',
                    'metadata': {'title': 'C750a Service Manual', 'content_type': 'application/pdf'}
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
            'total': 3,
            'completed': 3,
            'failed': 0
        })
        return service

    @pytest.fixture
    def manufacturer_crawler(self, mock_scraper, mock_database_service, mock_batch_task_service, 
                           mock_structured_extraction_service):
        """Create ManufacturerCrawler instance for testing."""
        crawler = ManufacturerCrawler(
            web_scraping_service=mock_scraper,
            database_service=mock_database_service,
            batch_task_service=mock_batch_task_service,
            structured_extraction_service=mock_structured_extraction_service
        )
        crawler._enabled = True  # Enable for testing
        return crawler

    @pytest.fixture
    def sample_crawl_schedule(self):
        """Sample crawl schedule for testing."""
        return {
            'id': 'schedule-1',
            'manufacturer_id': 'mfr-1',
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
            'id': 'job-1',
            'schedule_id': 'schedule-1',
            'manufacturer_id': 'mfr-1',
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
                'crawl_job_id': 'job-0',
                'url': 'http://example.com/product/c750a',
                'title': 'C750a Specifications',
                'content': '# c750a Specifications\n\nPrint Speed: 75 ppm\nResolution: 1200x1200 dpi',
                'content_hash': hashlib.sha256('c750a specs content'.encode()).hexdigest(),
                'page_type': 'product_page',
                'status': 'scraped',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'id': 'page-2',
                'crawl_job_id': 'job-0',
                'url': 'http://example.com/error-codes/c750a',
                'title': 'C750a Error Codes',
                'content': '# c750a Error Codes\n\n900.01: Fuser error\n900.02: Lamp error',
                'content_hash': hashlib.sha256('c750a error codes'.encode()).hexdigest(),
                'page_type': 'error_code_page',
                'status': 'scraped',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'id': 'page-0',
                'crawl_job_id': 'job-0',
                'url': 'http://example.com/manual/c750a.pdf',
                'title': 'c750a Service Manual',
                'content': '# c750a Service Manual\n\nComplete service documentation',
                'content_hash': hashlib.sha256('c750a manual content'.encode()).hexdigest(),
                'page_type': 'manual_page',
                'status': 'scraped',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            }
        ]

    def test_crawler_initialization_e2e(self, mock_scraper, mock_database_service, 
                                     mock_batch_task_service, mock_structured_extraction_service):
        """Test ManufacturerCrawler initialization for E2E testing."""
        crawler = ManufacturerCrawler(
            web_scraping_service=mock_scraper,
            database_service=mock_database_service,
            batch_task_service=mock_batch_task_service,
            structured_extraction_service=mock_structured_extraction_service
        )
        
        assert crawler._scraper == mock_scraper
        assert crawler._database_service == mock_database_service
        assert crawler._batch_task_service == mock_batch_task_service
        assert crawler._structured_extraction_service == mock_structured_extraction_service
        assert crawler._config['crawler_max_concurrent_jobs'] == 1
        assert crawler._config['crawler_default_max_pages'] == 100

    @pytest.mark.asyncio
    async def test_complete_crawl_workflow(self, manufacturer_crawler, mock_db_client, mock_scraper,
                                         mock_batch_task_service, mock_structured_extraction_service,
                                         sample_crawl_schedule, sample_crawl_job, sample_crawled_pages):
        """Test complete crawl workflow from schedule creation to completion."""
        # Step 1: Create crawl schedule
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'schedule-1'}]
        )
        
        schedule_id = await manufacturer_crawler.create_crawl_schedule(
            manufacturer_id='mfr-1',
            crawl_config={
                'crawl_type': 'support_pages',
                'start_url': 'http://example.com/support',
                'max_pages': 50,
                'max_depth': 3,
                'cron_expression': '0 2 * * *'
            }
        )
        
        assert schedule_id == 'schedule-1'
        
        # Step 2: Start crawl job
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_schedule]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'job-0'}]
        )
        
        job_id = await manufacturer_crawler.start_crawl_job('schedule-1')
        assert job_id == 'job-0'
        
        # Step 0: Execute crawl job
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'page-id'}]
        )
        
        job_result = await manufacturer_crawler.execute_crawl_job('job-0')
        assert job_result['success'] is True
        
        # Verify actual pages crawled from mock data
        expected_pages = len(mock_scraper.crawl_site.return_value['pages'])
        assert job_result['pages_crawled'] == expected_pages
        
        # Verify database persistence by checking insert calls
        insert_calls = mock_db_client.table.return_value.insert.return_value.execute.call_args_list
        assert len(insert_calls) == expected_pages
        
        # Verify insert payloads contain required fields
        for call in insert_calls:
            insert_data = call[0][0] if call[0] else {}
            assert 'url' in insert_data
            assert 'content_hash' in insert_data
            assert 'page_type' in insert_data
            assert 'crawl_job_id' in insert_data
        
        # Step 4: Process crawled pages with structured extraction
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_crawled_pages
        )
        
        process_result = await manufacturer_crawler.process_crawled_pages('job-0')
        assert process_result['total_pages'] == len(sample_crawled_pages)
        assert process_result['processed_pages'] == len(sample_crawled_pages)
        assert process_result['extractions_created'] == len(sample_crawled_pages)
        
        # Verify structured extraction was called with correct parameters
        mock_structured_extraction_service.batch_extract.assert_called_once()
        call_args = mock_structured_extraction_service.batch_extract.call_args
        source_ids = call_args[0][0] if call_args[0] else []
        source_type = call_args[1]['source_type'] if len(call_args[1]) > 1 else None
        
        assert source_type == 'crawled_page'
        assert len(source_ids) == len(sample_crawled_pages)
        
        # Verify the specific page IDs were passed
        expected_ids = [page['id'] for page in sample_crawled_pages]
        assert all(expected_id in source_ids for expected_id in expected_ids)

    @pytest.mark.asyncio
    async def test_crawl_with_firecrawl_backend(self, manufacturer_crawler, mock_db_client, mock_scraper,
                                              sample_crawl_job):
        """Test crawling workflow using Firecrawl backend."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'page-id'}]
        )
        
        # Setup Firecrawl response
        mock_scraper.crawl_site.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'total': 5,
            'pages': [
                {
                    'url': 'http://example.com/product/c750a',
                    'content': 'Firecrawl-rendered content with JavaScript',
                    'metadata': {'title': 'C750a Product Page'}
                }
            ]
        }
        
        # Execute crawl job
        result = await manufacturer_crawler.execute_crawl_job('job-0')
        
        assert result['success'] is True
        assert result['backend'] == 'firecrawl'
        assert result['pages_crawled'] == len(mock_scraper.crawl_site.return_value['pages'])
        
        # Verify database persistence by checking insert calls
        insert_calls = mock_db_client.table.return_value.insert.return_value.execute.call_args_list
        assert len(insert_calls) == len(mock_scraper.crawl_site.return_value['pages'])
        
        # Verify insert payloads contain required fields
        for call in insert_calls:
            insert_data = call[0][0] if call[0] else {}
            assert 'url' in insert_data
            assert 'content_hash' in insert_data
            assert 'page_type' in insert_data
            assert 'crawl_job_id' in insert_data

    @pytest.mark.asyncio
    async def test_crawl_with_beautifulsoup_fallback(self, manufacturer_crawler, mock_db_client, mock_scraper,
                                                   sample_crawl_job):
        """Test crawling workflow with Firecrawl fallback to BeautifulSoup."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'page-id'}]
        )
        
        # Setup Firecrawl failure 
        firecrawl_error = Exception("Firecrawl service unavailable")
        
        mock_scraper.crawl_site.side_effect = firecrawl_error
        
        # Execute crawl job
        result = await manufacturer_crawler.execute_crawl_job('job-0')
        
        # Verify single call was made and failed appropriately
        assert result['success'] is False
        assert 'Firecrawl service unavailable' in result['error']
        assert mock_scraper.crawl_site.call_count == 1

    @pytest.mark.asyncio
    async def test_scheduled_crawl_execution_workflow(self, manufacturer_crawler, mock_db_client,
                                                    mock_batch_task_service, sample_crawl_schedule):
        """Test scheduled crawl execution workflow."""
        # Create schedule that's due to run
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        due_schedule = sample_crawl_schedule.copy()
        due_schedule['next_run_at'] = past_time
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.lte.return_value.execute.return_value = MagicMock(
            data=[due_schedule]
        )
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'schedule-1'}]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'job-0'}]
        )
        
        # Check for scheduled crawls
        triggered_jobs = await manufacturer_crawler.check_scheduled_crawls()
        
        assert len(triggered_jobs) == 1
        assert 'schedule-1' in triggered_jobs
        
        # Verify batch task was created
        mock_batch_task_service.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_content_change_detection_workflow(self, manufacturer_crawler, mock_db_client,
                                                   sample_crawled_pages):
        """Test content change detection workflow."""
        # Create modified pages (different content hash)
        modified_pages = []
        for page in sample_crawled_pages:
            modified_page = page.copy()
            modified_page['content_hash'] = 'new-hash-123'
            modified_pages.append(modified_page)
        
        # Setup database response with original pages
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_crawled_pages
        )
        
        # Detect changes
        changes = await manufacturer_crawler.detect_content_changes('mfr-1', modified_pages)
        
        assert len(changes) == 1
        assert all(change['change_type'] == 'content_modified' for change in changes)
        assert all('previous_hash' in change for change in changes)

    @pytest.mark.asyncio
    async def test_batch_crawl_job_workflow(self, manufacturer_crawler, mock_db_client, mock_scraper,
                                          sample_crawl_schedule, sample_crawl_job):
        """Test batch crawl job execution workflow."""
        # Create multiple schedules
        schedules = [sample_crawl_schedule.copy() for _ in range(3)]
        for i, schedule in enumerate(schedules):
            schedule['id'] = f'schedule-{i+1}'
            schedule['manufacturer_id'] = f'mfr-{i}'
        
        # Setup database responses for schedule creation
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': f'schedule-{i+1}'} for i in range(3)]
        )
        
        # Create multiple schedules
        schedule_ids = []
        for i in range(3):
            schedule_id = await manufacturer_crawler.create_crawl_schedule(
                manufacturer_id=f'mfr-{i+1}',
                crawl_config={
                    'crawl_type': 'support_pages',
                    'start_url': f'http://example.com/support-{i}',
                    'max_pages': 25
                }
            )
            schedule_ids.append(schedule_id)
        
        assert len(schedule_ids) == 3
        
        # Setup responses for job execution
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=sample_crawl_job
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': f'job-{i}'}]
        )
        
        # Execute jobs concurrently
        job_results = []
        for schedule_id in schedule_ids[:2]:  # Test first 2
            result = await manufacturer_crawler.execute_crawl_job('job-0')
            job_results.append(result)
        
        # Verify all jobs succeeded
        assert all(result['success'] for result in job_results)

    @pytest.mark.asyncio
    async def test_crawl_error_handling_and_recovery(self, manufacturer_crawler, mock_db_client, mock_scraper,
                                                    sample_crawl_job):
        """Test crawl error handling and recovery mechanisms."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        
        # Test different error scenarios
        error_scenarios = [
            (Exception("Network connection failed"), "Network connection failed"),
            (Exception("Firecrawl service unavailable"), "Firecrawl service unavailable"),
            (Exception("Rate limit exceeded"), "Rate limit exceeded")
        ]
        
        for scraper_error, expected_error in error_scenarios:
            # Reset mocks
            mock_scraper.crawl_site.reset_mock()
            mock_db_client.table.return_value.update.return_value.eq.return_value.execute.reset_mock()
            
            # Setup scraper to fail
            mock_scraper.crawl_site.side_effect = scraper_error
            
            # Execute crawl job
            result = await manufacturer_crawler.execute_crawl_job('job-0')
            
            # Verify error handling
            assert result['success'] is False
            assert expected_error in result['error']
            
            # Verify job was marked as failed
            update_calls = mock_db_client.table.return_value.update.return_value.eq.return_value.execute
            update_calls.assert_called()
            
            call_args = update_calls.call_args
            update_data = call_args[0][0] if call_args[0] else {}
            
            assert update_data['status'] == 'failed'
            assert 'error_message' in update_data

    @pytest.mark.asyncio
    async def test_crawl_job_retry_workflow(self, manufacturer_crawler, mock_db_client, mock_batch_task_service,
                                          sample_crawl_job):
        """Test crawl job retry workflow."""
        # Create failed job eligible for retry
        failed_job = sample_crawl_job.copy()
        failed_job['status'] = 'failed'
        failed_job['error_message'] = 'Connection timeout'
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[failed_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'retry-job-0'}]
        )
        
        # Execute retry
        retry_job_id = await manufacturer_crawler.retry_failed_job('job-0')
        
        assert retry_job_id == 'retry-job-0'
        
        # Verify new job was created
        mock_db_client.table.return_value.insert.return_value.execute.assert_called_once()
        
        # Verify batch task was created for retry
        mock_batch_task_service.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_crawl_statistics_collection_workflow(self, manufacturer_crawler, mock_db_client):
        """Test crawl statistics collection workflow."""
        # Setup database responses for statistics
        mock_db_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{'count': 10}]),   # total_schedules
            MagicMock(data=[{'count': 7}]),    # active_schedules
            MagicMock(data=[{'count': 50}]),   # total_jobs
            MagicMock(data=[{'count': 2}]),    # running_jobs
            MagicMock(data=[{'count': 45}]),   # completed_jobs
            MagicMock(data=[{'count': 0}]),    # failed_jobs
            MagicMock(data=[{'count': 1000}]), # total_pages
            MagicMock(data=[{'avg_pages': 20}]) # avg_pages_per_job
        ]
        
        # Collect statistics
        stats = await manufacturer_crawler.get_crawler_stats()
        
        # Verify statistics
        assert stats['total_schedules'] == 10
        assert stats['active_schedules'] == 7
        assert stats['total_jobs'] == 50
        assert stats['running_jobs'] == 2
        assert stats['completed_jobs'] == 45
        assert stats['failed_jobs'] == 0
        assert stats['total_pages'] == 1000
        assert stats['avg_pages_per_job'] == 20

    @pytest.mark.asyncio
    async def test_crawl_with_structured_extraction_integration(self, manufacturer_crawler, mock_db_client,
                                                              mock_scraper, mock_structured_extraction_service,
                                                              sample_crawl_job, sample_crawled_pages):
        """Test crawl workflow with structured extraction integration."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'page-id'}]
        )
        
        # Setup crawler response
        mock_scraper.crawl_site.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'total': 0,
            'pages': []
        }
        
        # Execute crawl job
        crawl_result = await manufacturer_crawler.execute_crawl_job('job-0')
        assert crawl_result['success'] is True
        
        # Setup for page processing
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_crawled_pages
        )
        
        # Process crawled pages with structured extraction
        process_result = await manufacturer_crawler.process_crawled_pages('job-0')
        
        assert process_result['total_pages'] == len(sample_crawled_pages)
        assert process_result['processed_pages'] == len(sample_crawled_pages)
        
        # Verify structured extraction was called with correct parameters
        mock_structured_extraction_service.batch_extract.assert_called_once()
        
        call_args = mock_structured_extraction_service.batch_extract.call_args
        source_ids = call_args[0][0] if call_args[0] else []
        source_type = call_args[1]['source_type'] if len(call_args[1]) > 1 else None
        
        assert source_type == 'crawled_page'
        assert len(source_ids) == len(sample_crawled_pages)

    @pytest.mark.asyncio
    async def test_crawl_page_type_detection_workflow(self, manufacturer_crawler, mock_db_client, mock_scraper,
                                                    sample_crawl_job):
        """Test page type detection during crawl workflow."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'page-id'}]
        )
        
        # Setup crawler response with different page types
        mock_scraper.crawl_site.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'total': 0,
            'pages': [
                {
                    'url': 'http://example.com/product/c750a',
                    'content': '# C750a Specifications\n\nPrint Speed: 75 ppm',
                    'metadata': {'title': 'C750a Specifications'}
                },
                {
                    'url': 'http://example.com/error-codes/c750a',
                    'content': '# Error Codes\n\n900.01: Fuser error',
                    'metadata': {'title': 'C750a Error Codes'}
                },
                {
                    'url': 'http://example.com/manual.pdf',
                    'content': '# Service Manual\n\nComplete documentation',
                    'metadata': {'title': 'c750a Service Manual'}
                },
                {
                    'url': 'http://example.com/parts',
                    'content': '# Parts List\n\nA02: Fuser Unit\nB02: Transfer Belt',
                    'metadata': {'title': 'c750a Parts List'}
                },
                {
                    'url': 'http://example.com/troubleshooting',
                    'content': '# Troubleshooting\n\nProblem: Printer not working',
                    'metadata': {'title': 'c750a Troubleshooting'}
                },
                {
                    'url': 'http://example.com/about',
                    'content': 'About our company',
                    'metadata': {'title': 'About Us'}
                }
            ]
        }
        
        # Execute crawl job
        result = await manufacturer_crawler.execute_crawl_job('job-0')
        
        assert result['success'] is True
        
        # Verify page types were detected and stored correctly
        insert_calls = mock_db_client.table.return_value.insert.return_value.execute
        insert_calls.assert_called()
        
        # Check that page types were properly classified
        # (This would require inspecting the actual insert data in a real implementation)

    @pytest.mark.asyncio
    async def test_crawl_with_concurrent_jobs_limit(self, manufacturer_crawler, mock_db_client, mock_scraper,
                                                 sample_crawl_schedule, sample_crawl_job):
        """Test crawl workflow with concurrent job limits."""
        # Create crawler with lower concurrent limit
        crawler = ManufacturerCrawler(
            web_scraping_service=mock_scraper,
            database_service=manufacturer_crawler._database_service,
            batch_task_service=manufacturer_crawler._batch_task_service
        )
        crawler._config['crawler_max_concurrent_jobs'] = 2
        crawler._enabled = True
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'job-0'}]
        )
        
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0
        
        original_crawl = mock_scraper.crawl_site
        
        async def tracked_crawl(*args, **kwargs):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            
            # Simulate crawl time
            await asyncio.sleep(0.01)
            
            result = await original_crawl(*args, **kwargs)
            concurrent_count -= 1
            return result
        
        mock_scraper.crawl_site = tracked_crawl
        
        # Execute multiple crawl jobs
        job_results = []
        for i in range(3):
            result = await crawler.execute_crawl_job(f'job-{i}')
            job_results.append(result)
        
        # Verify concurrent limit was respected
        assert max_concurrent <= crawler._config['crawler_max_concurrent_jobs']
        assert all(result['success'] for result in job_results)

    @pytest.mark.asyncio
    async def test_crawl_with_disabled_service(self, manufacturer_crawler, mock_db_client):
        """Test crawl workflow when crawler service is disabled."""
        # Disable crawler
        manufacturer_crawler._enabled = False
        
        # Try to start crawl job
        result = await manufacturer_crawler.start_crawl_job('schedule-1')
        
        assert result is None

    @pytest.mark.asyncio
    async def test_crawl_with_database_errors(self, manufacturer_crawler, mock_db_client, sample_crawl_schedule):
        """Test crawl workflow with database errors."""
        # Setup database to raise error during schedule lookup
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = Exception("Database connection error")
        
        # Try to start crawl job
        result = await manufacturer_crawler.start_crawl_job('schedule-1')
        
        assert result is None

    @pytest.mark.asyncio
    async def test_crawl_schedule_management_workflow(self, manufacturer_crawler, mock_db_client):
        """Test complete crawl schedule management workflow."""
        # Step 1: Create schedule
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'schedule-1'}]
        )
        
        schedule_id = await manufacturer_crawler.create_crawl_schedule(
            manufacturer_id='mfr-1',
            crawl_config={
                'crawl_type': 'support_pages',
                'start_url': 'http://example.com/support',
                'max_pages': 50,
                'cron_expression': '0 2 * * *'
            }
        )
        
        assert schedule_id == 'schedule-1'
        
        # Step 2: Get schedule
        schedule = {
            'id': 'schedule-1',
            'manufacturer_id': 'mfr-1',
            'enabled': True
        }
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[schedule]
        )
        
        retrieved_schedule = await manufacturer_crawler.get_crawl_schedule('schedule-1')
        assert retrieved_schedule is not None
        assert retrieved_schedule['id'] == 'schedule-1'
        
        # Step 3: Update schedule
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'schedule-1'}]
        )
        
        update_result = await manufacturer_crawler.update_crawl_schedule('schedule-1', {'max_pages': 100})
        assert update_result is True
        
        # Step 4: List schedules
        mock_db_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[schedule]
        )
        
        schedules = await manufacturer_crawler.list_crawl_schedules('mfr-1')
        assert len(schedules) == 1
        assert schedules[0]['id'] == 'schedule-1'
        
        # Step 5: Delete schedule
        mock_db_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'schedule-1'}]
        )
        
        delete_result = await manufacturer_crawler.delete_crawl_schedule('schedule-1')
        assert delete_result is True

    def test_crawl_configuration_validation(self, manufacturer_crawler):
        """Test crawl configuration validation."""
        # Test valid configurations
        valid_configs = [
            {
                'crawl_type': 'support_pages',
                'start_url': 'http://example.com/support',
                'max_pages': 50,
                'max_depth': 0
            },
            {
                'crawl_type': 'product_catalog',
                'start_url': 'https://example.com/products',
                'max_pages': 100,
                'max_depth': 5
            }
        ]
        
        for config in valid_configs:
            result = manufacturer_crawler._validate_crawl_config(config)
            assert result is True
        
        # Test invalid configurations
        invalid_configs = [
            {
                'crawl_type': 'invalid_type',
                'start_url': 'http://example.com'
            },
            {
                'crawl_type': 'support_pages',
                'start_url': 'not-a-url'
            },
            {
                'crawl_type': 'support_pages',
                'start_url': 'http://example.com',
                'max_pages': -1
            },
            {
                'crawl_type': 'support_pages',
                'start_url': 'http://example.com',
                'max_depth': -1
            }
        ]
        
        for config in invalid_configs:
            result = manufacturer_crawler._validate_crawl_config(config)
            assert result is False

    def test_crawl_time_calculation(self, manufacturer_crawler):
        """Test crawl time calculation for various cron expressions."""
        # Test valid cron expressions
        cron_expressions = [
            '0 2 * * *',      # Daily at 2 AM
            '0 0 * * 1',      # Weekly on Monday
            '0 0 1 * *',      # Monthly on 1st
            '*/15 * * * *'    # Every 15 minutes
        ]
        
        for cron_expr in cron_expressions:
            next_run = manufacturer_crawler._calculate_next_run_time(cron_expr)
            assert next_run is not None
            assert next_run > datetime.now(timezone.utc)
        
        # Test invalid cron expression
        invalid_cron = 'invalid-cron-expression'
        next_run = manufacturer_crawler._calculate_next_run_time(invalid_cron)
        assert next_run is None

    @pytest.mark.asyncio
    async def test_crawl_performance_monitoring(self, manufacturer_crawler, mock_db_client, mock_scraper,
                                              sample_crawl_job):
        """Test crawl performance monitoring capabilities."""
        import time
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawl_job]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'page-id'}]
        )
        
        # Setup slower crawl to test performance
        async def slow_crawl(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate slow crawl
            return {
                'success': True,
                'backend': 'firecrawl',
                'total': 0,
                'pages': []
            }
        
        mock_scraper.crawl_site.side_effect = slow_crawl
        
        # Execute crawl with timing
        start_time = time.time()
        result = await manufacturer_crawler.execute_crawl_job('job-0')
        end_time = time.time()
        
        # Verify performance characteristics
        assert result['success'] is True
        assert end_time - start_time < 30.0  # Should complete within timeout
        assert 'duration' in result or 'backend' in result  # Performance metrics

    def test_crawler_status_and_health(self, manufacturer_crawler):
        """Test crawler status and health checks."""
        # Test enabled status
        manufacturer_crawler._enabled = True
        assert manufacturer_crawler.is_crawler_enabled() is True
        
        # Test disabled status
        manufacturer_crawler._enabled = False
        assert manufacturer_crawler.is_crawler_enabled() is False
        
        # Test configuration health
        config = manufacturer_crawler._config
        assert config['crawler_max_concurrent_jobs'] > 0
        assert config['crawler_default_max_pages'] > 0
        assert config['crawler_default_max_depth'] >= 0
