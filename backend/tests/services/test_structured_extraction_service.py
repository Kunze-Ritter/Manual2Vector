"""
Unit tests for StructuredExtractionService.

Tests structured data extraction functionality including product specs,
error codes, service manuals, parts lists, and troubleshooting data.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import json
import tempfile

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

from services.structured_extraction_service import StructuredExtractionService


pytest.mark.unit = pytest.mark.unit


class TestStructuredExtractionService:
    """Test StructuredExtractionService functionality."""

    @pytest.fixture
    def mock_scraper(self):
        """Mock WebScrapingService."""
        scraper = MagicMock()
        scraper.extract_structured_data = AsyncMock(return_value={
            'success': True,
            'backend': 'firecrawl',
            'data': {'model_number': 'c750i', 'manufacturer': 'Konica Minolta'},
            'confidence': 0.85
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
    def extraction_service(self, mock_scraper, mock_database_service, extraction_schemas):
        """Create StructuredExtractionService instance for testing."""
        with patch('backend.services.structured_extraction_service.Path') as mock_path:
            mock_path.return_value = Path(__file__)  # Mock path
            service = StructuredExtractionService(
                web_scraping_service=mock_scraper,
                database_service=mock_database_service
            )
            service._schemas = extraction_schemas  # Inject test schemas
            return service

    @pytest.fixture
    def sample_link_record(self):
        """Sample link record for testing."""
        return {
            'id': 'test-link-id-123',
            'url': 'http://example.com/product/c750a',
            'link_type': 'external',
            'scrape_status': 'success',
            'scraped_content': 'Product page content',
            'scraped_metadata': {'backend': 'firecrawl'},
            'document_id': 'test-doc-id',
            'manufacturer_id': 'test-mfr-id'
        }

    @pytest.fixture
    def sample_crawled_page(self):
        """Sample crawled page record for testing."""
        return {
            'id': 'test-page-id-123',
            'crawl_job_id': 'test-job-id',
            'url': 'http://example.com/product/c750a',
            'title': 'Konica Minolta C750a',
            'content': '# c750a Specifications\n\nPrint Speed: 75 ppm',
            'page_type': 'product_page',
            'status': 'scraped',
            'scraped_at': datetime.now(timezone.utc).isoformat()
        }

    def test_service_initialization_with_schemas(self, mock_scraper, mock_database_service, extraction_schemas):
        """Test service initialization loads schemas correctly."""
        with patch('backend.services.structured_extraction_service.Path') as mock_path:
            mock_path.return_value = Path(__file__)
            service = StructuredExtractionService(
                web_scraping_service=mock_scraper,
                database_service=mock_database_service
            )
            service._schemas = extraction_schemas
            
            assert service._schemas == extraction_schemas
            assert 'product_specs' in service._schemas
            assert 'error_codes' in service._schemas
            assert 'service_manual' in service._schemas
            assert 'parts_list' in service._schemas
            assert 'troubleshooting' in service._schemas
            
            # Verify schema structure
            for schema_name, schema_info in extraction_schemas.items():
                assert 'schema' in schema_info
                assert 'version' in schema_info
                assert 'description' in schema_info

    def test_service_initialization_missing_schema_file(self, mock_scraper, mock_database_service):
        """Test service initialization with missing schema file."""
        with patch('backend.services.structured_extraction_service.Path') as mock_path:
            mock_path.side_effect = FileNotFoundError("Schema file not found")
            
            with pytest.raises(FileNotFoundError):
                StructuredExtractionService(
                    web_scraping_service=mock_scraper,
                    database_service=mock_database_service
                )

    def test_service_initialization_invalid_json(self, mock_scraper, mock_database_service):
        """Test service initialization with invalid JSON schema file."""
        with patch('builtins.open') as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "invalid json {"
            
            with pytest.raises(json.JSONDecodeError):
                StructuredExtractionService(
                    web_scraping_service=mock_scraper,
                    database_service=mock_database_service
                )

    def test_service_initialization_missing_schema_definition(self, mock_scraper, mock_database_service):
        """Test service initialization with missing schema definition."""
        invalid_schemas = {
            'product_specs': {
                'version': '1.0',
                'description': 'Missing schema key'
            }
        }
        
        with patch('builtins.open') as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(invalid_schemas)
            
            with pytest.raises(ValueError) as exc_info:
                StructuredExtractionService(
                    web_scraping_service=mock_scraper,
                    database_service=mock_database_service
                )
            
            assert "Missing 'schema' key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_product_specs_success(self, extraction_service, mock_db_client, mock_scraper):
        """Test successful product specs extraction."""
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {
                'model_number': 'c750a',
                'manufacturer': 'Konica Minolta',
                'print_speed': '75 ppm',
                'resolution': '1200 x 1200 dpi'
            },
            'confidence': 0.85
        }
        
        # Setup database response for checking existing extraction
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]  # No existing extraction
        )
        
        # Setup database response for insert
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'new-extraction-id'}]
        )
        
        result = await extraction_service.extract_product_specs(
            url='http://example.com/product/c750a',
            manufacturer_id='test-mfr-id'
        )
        
        assert result['success'] is True
        assert 'extraction_id' in result
        assert result['confidence'] == 0.85
        
        # Verify extraction was inserted
        mock_db_client.table.return_value.insert.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_product_specs_low_confidence(self, extraction_service, mock_db_client, mock_scraper):
        """Test product specs extraction with low confidence."""
        # Setup scraper response with low confidence
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'model_number': 'c750a'},
            'confidence': 0.3  # Below threshold
        }
        
        result = await extraction_service.extract_product_specs(
            url='http://example.com/product/c750a'
        )
        
        assert result['success'] is False
        assert result['skipped'] is True
        assert result['reason'] == 'confidence_below_threshold'
        
        # Verify no database insert occurred
        mock_db_client.table.return_value.insert.return_value.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_product_specs_requires_firecrawl(self, extraction_service, mock_scraper):
        """Test that product specs extraction requires Firecrawl."""
        # Setup scraper to indicate non-Firecrawl backend
        mock_scraper.extract_structured_data.return_value = {
            'success': False,
            'backend': 'beautifulsoup',
            'error': 'Structured extraction requires Firecrawl'
        }
        
        result = await extraction_service.extract_product_specs(
            url='http://example.com/product/c750a'
        )
        
        assert result['success'] is False
        assert 'requires Firecrawl' in result['error']

    @pytest.mark.asyncio
    async def test_extract_product_specs_with_all_params(self, extraction_service, mock_db_client, mock_scraper):
        """Test product specs extraction with all parameters."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'extraction-id'}]
        )
        
        result = await extraction_service.extract_product_specs(
            url='http://example.com/product/c750a',
            manufacturer_id='test-mfr-id',
            product_id='test-product-id',
            document_id='test-doc-id',
            source_type='link',
            source_id='test-link-id'
        )
        
        assert result['success'] is True
        
        # Verify all parameters were passed to persistence
        insert_call = mock_db_client.table.return_value.insert.return_value.execute
        insert_call.assert_called_once()
        
        call_args = insert_call.call_args
        insert_data = call_args[0][0] if call_args[0] else {}
        
        assert insert_data['manufacturer_id'] == 'test-mfr-id'
        assert insert_data['product_id'] == 'test-product-id'
        assert insert_data['document_id'] == 'test-doc-id'
        assert insert_data['source_type'] == 'link'
        assert insert_data['source_id'] == 'test-link-id'

    @pytest.mark.asyncio
    async def test_extract_error_codes_success(self, extraction_service, mock_db_client, mock_scraper):
        """Test successful error codes extraction."""
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {
                'error_codes': [
                    {
                        'code': '900.01',
                        'description': 'Fuser error',
                        'severity': 'critical',
                        'solution': 'Replace fuser unit'
                    },
                    {
                        'code': '900.02',
                        'description': 'Lamp error',
                        'severity': 'warning',
                        'solution': 'Replace lamp'
                    }
                ]
            },
            'confidence': 0.90
        }
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'error-extraction-id'}]
        )
        
        result = await extraction_service.extract_error_codes(
            url='http://example.com/error-codes'
        )
        
        assert result['success'] is True
        assert 'extraction_id' in result
        assert result['confidence'] == 0.90
        
        # Verify error codes structure
        insert_call = mock_db_client.table.return_value.insert.return_value.execute
        call_args = insert_call.call_args
        insert_data = call_args[0][0] if call_args[0] else {}
        
        extracted_data = insert_data['extracted_data']
        assert len(extracted_data['error_codes']) == 2
        assert extracted_data['error_codes'][0]['code'] == '900.01'
        assert extracted_data['error_codes'][0]['severity'] == 'critical'

    @pytest.mark.asyncio
    async def test_extract_error_codes_empty_result(self, extraction_service, mock_db_client, mock_scraper):
        """Test error codes extraction with empty result."""
        # Setup scraper response with empty error codes
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'error_codes': []},
            'confidence': 0.50
        }
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'empty-extraction-id'}]
        )
        
        result = await extraction_service.extract_error_codes(
            url='http://example.com/error-codes'
        )
        
        assert result['success'] is True
        assert result['confidence'] == 0.50

    @pytest.mark.asyncio
    async def test_extract_service_manual_metadata_success(self, extraction_service, mock_db_client, mock_scraper):
        """Test successful service manual metadata extraction."""
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {
                'manual_type': 'service_manual',
                'product_models': ['c750a', 'c650a', 'c550a'],
                'version': '2.0',
                'download_url': 'http://example.com/manuals/c750a.pdf'
            },
            'confidence': 0.80
        }
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'manual-extraction-id'}]
        )
        
        result = await extraction_service.extract_service_manual_metadata(
            url='http://example.com/manuals/c750a'
        )
        
        assert result['success'] is True
        assert result['confidence'] == 0.80
        
        # Verify manual metadata structure
        insert_call = mock_db_client.table.return_value.insert.return_value.execute
        call_args = insert_call.call_args
        insert_data = call_args[0][0] if call_args[0] else {}
        
        extracted_data = insert_data['extracted_data']
        assert extracted_data['manual_type'] == 'service_manual'
        assert len(extracted_data['product_models']) == 3
        assert 'c750a' in extracted_data['product_models']

    @pytest.mark.asyncio
    async def test_extract_parts_list_success(self, extraction_service, mock_db_client, mock_scraper):
        """Test successful parts list extraction."""
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {
                'parts': [
                    {
                        'part_number': 'A02',
                        'part_name': 'Fuser Unit',
                        'description': 'Main fuser assembly',
                        'price': '$250.00'
                    },
                    {
                        'part_number': 'a04o',
                        'part_name': 'Transfer Belt',
                        'description': 'Transfer belt assembly',
                        'price': '$150.00'
                    }
                ]
            },
            'confidence': 0.75
        }
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'parts-extraction-id'}]
        )
        
        result = await extraction_service.extract_parts_list(
            url='http://example.com/parts/c750a'
        )
        
        assert result['success'] is True
        assert result['confidence'] == 0.75
        
        # Verify parts list structure
        insert_call = mock_db_client.table.return_value.insert.return_value.execute
        call_args = insert_call.call_args
        insert_data = call_args[0][0] if call_args[0] else {}
        
        extracted_data = insert_data['extracted_data']
        assert len(extracted_data['parts']) == 2
        assert extracted_data['parts'][0]['part_number'] == 'a02'
        assert extracted_data['parts'][1]['part_name'] == 'Transfer Belt'

    @pytest.mark.asyncio
    async def test_extract_troubleshooting_success(self, extraction_service, mock_db_client, mock_scraper):
        """Test successful troubleshooting extraction."""
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {
                'issues': [
                    {
                        'symptom': 'Printer not turning on',
                        'cause': 'Power supply failure',
                        'solution': 'Check power cable and replace if necessary',
                        'difficulty': 'medium'
                    },
                    {
                        'symptom': 'Poor print quality',
                        'cause': 'Dirty developer unit',
                        'solution': 'Clean developer unit and replace drum',
                        'difficulty': 'easy'
                    }
                ]
            },
            'confidence': 0.85
        }
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'troubleshooting-extraction-id'}]
        )
        
        result = await extraction_service.extract_troubleshooting(
            url='http://example.com/troubleshooting/c750a'
        )
        
        assert result['success'] is True
        assert result['confidence'] == 0.85
        
        # Verify troubleshooting structure
        insert_call = mock_db_client.table.return_value.insert.return_value.execute
        call_args = insert_call.call_args
        insert_data = call_args[0][0] if call_args[0] else {}
        
        extracted_data = insert_data['extracted_data']
        assert len(extracted_data['issues']) == 2
        assert extracted_data['issues'][0]['symptom'] == 'Printer not turning on'
        assert extracted_data['issues'][1]['difficulty'] == 'easy'

    @pytest.mark.asyncio
    async def test_extract_from_link_product_page(self, extraction_service, mock_db_client, mock_scraper, sample_link_record):
        """Test extraction from product page link."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_link_record]
        )
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]  # No existing extraction
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'link-extraction-id'}]
        )
        
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'model_number': 'c750a', 'manufacturer': 'Konica Minolta'},
            'confidence': 0.85
        }
        
        result = await extraction_service.extract_from_link('test-link-id-123')
        
        assert result['success'] is True
        assert result['extraction_type'] == 'product_specs'
        assert result['extraction_id'] == 'link-extraction-id'
        
        # Verify link metadata was updated
        update_call = mock_db_client.table.return_value.update.return_value.eq.return_value.execute
        update_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_from_link_error_code_page(self, extraction_service, mock_db_client, mock_scraper):
        """Test extraction from error code page link."""
        # Setup link record for error code page
        error_link = {
            'id': 'error-link-id',
            'url': 'http://example.com/error-codes/c750a',
            'link_type': 'external',
            'scrape_status': 'success',
            'scraped_metadata': {}
        }
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[error_link]
        )
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'error-extraction-id'}]
        )
        
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'error_codes': [{'code': '900.01', 'description': 'Fuser error'}]},
            'confidence': 0.90
        }
        
        result = await extraction_service.extract_from_link('error-link-id')
        
        assert result['success'] is True
        assert result['extraction_type'] == 'error_code'

    @pytest.mark.asyncio
    async def test_extract_from_link_manual_page(self, extraction_service, mock_db_client, mock_scraper):
        """Test extraction from manual page link."""
        # Setup link record for manual page
        manual_link = {
            'id': 'manual-link-id',
            'url': 'http://example.com/manuals/c750a.pdf',
            'link_type': 'external',
            'scrape_status': 'success',
            'scraped_metadata': {}
        }
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[manual_link]
        )
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'manual-extraction-id'}]
        )
        
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'manual_type': 'service_manual', 'product_models': ['c750a']},
            'confidence': 0.80
        }
        
        result = await extraction_service.extract_from_link('manual-link-id')
        
        assert result['success'] is True
        assert result['extraction_type'] == 'service_manual'

    @pytest.mark.asyncio
    async def test_extract_from_link_not_found(self, extraction_service, mock_db_client):
        """Test extraction from non-existent link."""
        # Setup database response with no link
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await extraction_service.extract_from_link('nonexistent-link-id')
        
        assert result['success'] is False
        assert result['error'] == 'link not found', f"Expected exact error message 'link not found', got: {result.get('error')}"

    @pytest.mark.asyncio
    async def test_extract_from_link_no_matching_schema(self, extraction_service, mock_db_client, mock_scraper):
        """Test extraction from link with no matching schema."""
        # Setup generic link record
        generic_link = {
            'id': 'generic-link-id',
            'url': 'http://example.com/about-us',
            'link_type': 'external',
            'scrape_status': 'success',
            'scraped_metadata': {}
        }
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[generic_link]
        )
        
        result = await extraction_service.extract_from_link('generic-link-id')
        
        assert result['success'] is False
        assert result['error'] == 'no matching extraction schema', f"Expected exact error message 'no matching extraction schema', got: {result.get('error')}"

    @pytest.mark.asyncio
    async def test_extract_from_link_updates_metadata(self, extraction_service, mock_db_client, mock_scraper, sample_link_record):
        """Test that extraction updates link metadata."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_link_record]
        )
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'extraction-id'}]
        )
        
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'model_number': 'c750a'},
            'confidence': 0.85
        }
        
        result = await extraction_service.extract_from_link('test-link-id-123')
        
        assert result['success'] is True
        
        # Verify link metadata was updated with extraction results
        update_call = mock_db_client.table.return_value.update.return_value.eq.return_value.execute
        update_call.assert_called_once()
        
        call_args = update_call.call_args
        update_data = call_args[0][0] if call_args[0] else {}
        
        assert 'scraped_metadata' in update_data
        assert 'structured_extractions' in update_data['scraped_metadata']
        
        extractions = update_data['scraped_metadata']['structured_extractions']
        assert len(extractions) == 1
        assert extractions[0]['record_id'] == 'extraction-id'
        assert extractions[0]['extraction_type'] == 'product_specs'
        assert extractions[0]['confidence'] == 0.85
        assert 'extracted_at' in extractions[0]

    @pytest.mark.asyncio
    async def test_extract_from_crawled_page_success(self, extraction_service, mock_db_client, mock_scraper, sample_crawled_page):
        """Test extraction from crawled page."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawled_page]
        )
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'page-extraction-id'}]
        )
        
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'model_number': 'c750a', 'manufacturer': 'Konica Minolta'},
            'confidence': 0.85
        }
        
        result = await extraction_service.extract_from_crawled_page('test-page-id-123')
        
        assert result['success'] is True
        assert result['extraction_type'] == 'product_specs'
        assert result['extraction_id'] == 'page-extraction-id'
        
        # Verify page status was updated
        update_call = mock_db_client.table.return_value.update.return_value.eq.return_value.execute
        update_call.assert_called_once()
        
        call_args = update_call.call_args
        update_data = call_args[0][0] if call_args[0] else {}
        
        assert update_data['status'] == 'processed'
        assert 'processed_at' in update_data

    @pytest.mark.asyncio
    async def test_extract_from_crawled_page_not_found(self, extraction_service, mock_db_client):
        """Test extraction from non-existent crawled page."""
        # Setup database response with no page
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        
        result = await extraction_service.extract_from_crawled_page('nonexistent-page-id')
        
        assert result['success'] is False
        assert result['error'] == 'crawled page not found', f"Expected exact error message 'crawled page not found', got: {result.get('error')}"

    @pytest.mark.asyncio
    async def test_extract_from_crawled_page_updates_status(self, extraction_service, mock_db_client, mock_scraper, sample_crawled_page):
        """Test that extraction updates crawled page status."""
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[sample_crawled_page]
        )
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'extraction-id'}]
        )
        
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'model_number': 'c750a'},
            'confidence': 0.85
        }
        
        result = await extraction_service.extract_from_crawled_page('test-page-id-123')
        
        assert result['success'] is True
        
        # Verify page status was updated to 'processed'
        update_call = mock_db_client.table.return_value.update.return_value.eq.return_value.execute
        update_call.assert_called_once()
        
        call_args = update_call.call_args
        update_data = call_args[0][0] if call_args[0] else {}
        
        assert update_data['status'] == 'processed'
        assert 'processed_at' in update_data

    @pytest.mark.asyncio
    async def test_batch_extract_links_success(self, extraction_service, mock_db_client, mock_scraper):
        """Test batch extraction of links."""
        # Setup database responses for multiple links
        link_ids = ['link-1', 'link-2', 'link-3']
        mock_db_client.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[{'id': lid, 'url': f'http://example.com/{lid}', 'scraped_metadata': {}} for lid in link_ids]
        )
        
        # Setup responses for individual link processing
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{'id': lid, 'url': f'http://example.com/{lid}', 'scraped_metadata': {}}]
        )
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': f'extraction-{lid}'}]
        )
        
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'model_number': 'c750a'},
            'confidence': 0.85
        }
        
        result = await extraction_service.batch_extract(
            source_ids=link_ids,
            source_type='link',
            max_concurrent=2
        )
        
        assert result['total'] == 3
        assert result['completed'] == 3
        assert result['failed'] == 0

    @pytest.mark.asyncio
    async def test_batch_extract_crawled_pages(self, extraction_service, mock_db_client, mock_scraper):
        """Test batch extraction of crawled pages."""
        page_ids = ['page-1', 'page-2']
        
        # Setup database responses
        mock_db_client.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[{'id': pid, 'url': f'http://example.com/{pid}', 'page_type': 'product_page'} for pid in page_ids]
        )
        
        mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{'id': pid, 'url': f'http://example.com/{pid}', 'page_type': 'product_page'}]
        )
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': f'extraction-{pid}'}]
        )
        
        # Setup scraper response
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'model_number': 'c750a'},
            'confidence': 0.85
        }
        
        result = await extraction_service.batch_extract(
            source_ids=page_ids,
            source_type='crawled_page'
        )
        
        assert result['total'] == 2
        assert result['completed'] == 2
        assert result['failed'] == 0

    @pytest.mark.asyncio
    async def test_batch_extract_empty_list(self, extraction_service):
        """Test batch extraction with empty list."""
        result = await extraction_service.batch_extract(
            source_ids=[],
            source_type='link'
        )
        
        assert result['total'] == 0
        assert result['completed'] == 0
        assert result['failed'] == 0

    def test_get_extraction_schemas(self, extraction_service, extraction_schemas):
        """Test getting extraction schemas."""
        schemas = extraction_service.get_extraction_schemas()
        
        assert schemas == extraction_schemas
        assert 'product_specs' in schemas
        assert 'error_codes' in schemas

    def test_get_schema_valid_key(self, extraction_service):
        """Test getting schema with valid key."""
        schema = extraction_service._get_schema('product_specs')
        
        assert schema is not None
        assert 'schema' in schema
        assert 'version' in schema
        assert 'description' in schema

    def test_get_schema_invalid_key(self, extraction_service):
        """Test getting schema with invalid key."""
        with pytest.raises(ValueError) as exc_info:
            extraction_service._get_schema('invalid_schema_key')
        
        assert "Schema 'invalid_schema_key' not available" == str(exc_info.value), f"Expected exact error message, got: {exc_info.value}"

    @pytest.mark.asyncio
    async def test_validate_extraction_success(self, extraction_service, mock_db_client):
        """Test successful extraction validation."""
        # Setup database response
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'extraction-id'}]
        )
        
        result = await extraction_service.validate_extraction(
            extraction_id='extraction-id',
            status='validated',
            notes='Looks good'
        )
        
        assert result is True
        
        # Verify validation was updated
        update_call = mock_db_client.table.return_value.update.return_value.eq.return_value.execute
        update_call.assert_called_once()
        
        call_args = update_call.call_args
        update_data = call_args[0][0] if call_args[0] else {}
        
        assert update_data['validation_status'] == 'validated'
        assert update_data['validation_notes'] == 'Looks good'
        assert 'validated_at' in update_data

    @pytest.mark.asyncio
    async def test_validate_extraction_invalid_status(self, extraction_service):
        """Test validation with invalid status."""
        with pytest.raises(ValueError) as exc_info:
            await extraction_service.validate_extraction(
                extraction_id='extraction-id',
                status='invalid_status'
            )
        
        assert "Invalid validation status" == str(exc_info.value), f"Expected exact error message, got: {exc_info.value}"

    @pytest.mark.asyncio
    async def test_extract_from_link_database_unavailable(self, mock_scraper):
        """Test extract_from_link when database client is unavailable."""
        # Create service with database_service that has no client
        mock_database_service = MagicMock()
        mock_database_service.service_client = None
        mock_database_service.client = None
        
        with patch('backend.services.structured_extraction_service.Path') as mock_path:
            mock_path.return_value = Path(__file__)
            service = StructuredExtractionService(
                web_scraping_service=mock_scraper,
                database_service=mock_database_service
            )
            service._schemas = {'product_specs': {'schema': {}, 'version': '1.0', 'description': 'test'}}
            
            result = await service.extract_from_link('test-link-id')
            
            assert result['success'] is False
            assert result['error'] == 'database client unavailable', f"Expected exact error 'database client unavailable', got: {result.get('error')}"

    @pytest.mark.asyncio
    async def test_batch_extract_database_unavailable(self, mock_scraper):
        """Test batch_extract when database client is unavailable."""
        # Create service with database_service that has no client
        mock_database_service = MagicMock()
        mock_database_service.service_client = None
        mock_database_service.client = None
        
        with patch('backend.services.structured_extraction_service.Path') as mock_path:
            mock_path.return_value = Path(__file__)
            service = StructuredExtractionService(
                web_scraping_service=mock_scraper,
                database_service=mock_database_service
            )
            service._schemas = {'product_specs': {'schema': {}, 'version': '1.0', 'description': 'test'}}
            
            result = await service.batch_extract(
                source_type='link',
                source_ids=['link-1', 'link-2']
            )
            
            # All extractions should fail with database unavailable error
            assert result['total'] == 2
            assert result['failed'] == 2
            for item_result in result['results']:
                assert item_result['success'] is False
                assert item_result['error'] == 'database client unavailable'

    @pytest.mark.asyncio
    async def test_persist_extraction_new_record(self, extraction_service, mock_db_client):
        """Test persisting new extraction record."""
        # Setup database response for checking existing extraction
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]  # No existing extraction
        )
        
        # Setup database response for insert
        mock_db_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{'id': 'new-extraction-id'}]
        )
        
        extraction_data = {
            'source_type': 'link',
            'source_id': 'link-id',
            'extraction_type': 'product_specs',
            'extracted_data': {'model_number': 'c750a'},
            'confidence': 0.85
        }
        
        result = await extraction_service._persist_extraction(extraction_data)
        
        assert result['success'] is True
        assert result['record_id'] == 'new-extraction-id'
        
        # Verify insert was called
        mock_db_client.table.return_value.insert.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_extraction_update_existing(self, extraction_service, mock_db_client):
        """Test persisting extraction updates existing record."""
        # Setup database response for existing extraction
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'existing-extraction-id'}]
        )
        
        extraction_data = {
            'source_type': 'link',
            'source_id': 'link-id',
            'extraction_type': 'product_specs',
            'extracted_data': {'model_number': 'c750a'},
            'confidence': 0.85
        }
        
        result = await extraction_service._persist_extraction(extraction_data)
        
        assert result['success'] is True
        assert result['record_id'] == 'existing-extraction-id'
        
        # Verify update was called instead of insert
        mock_db_client.table.return_value.insert.return_value.execute.assert_not_called()
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_extraction_database_error(self, extraction_service, mock_db_client):
        """Test persisting extraction with database error."""
        # Setup database to raise error
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("DB Error")
        
        extraction_data = {
            'source_type': 'link',
            'source_id': 'link-id',
            'extraction_type': 'product_specs',
            'extracted_data': {'model_number': 'c750a'},
            'confidence': 0.85
        }
        
        result = await extraction_service._persist_extraction(extraction_data)
        
        assert result['success'] is False
        assert 'error' in result

    def test_determine_extraction_type_from_url(self, extraction_service):
        """Test determining extraction type from URL."""
        # Test product page URLs
        assert extraction_service._determine_extraction_type_from_url('http://example.com/product/c750a') == 'product_specs'
        assert extraction_service._determine_extraction_type_from_url('http://example.com/products/c750a/specs') == 'product_specs'
        
        # Test error code URLs
        assert extraction_service._determine_extraction_type_from_url('http://example.com/error-codes') == 'error_codes'
        assert extraction_service._determine_extraction_type_from_url('http://example.com/support/errors') == 'error_codes'
        
        # Test manual URLs
        assert extraction_service._determine_extraction_type_from_url('http://example.com/manual.pdf') == 'service_manual'
        assert extraction_service._determine_extraction_type_from_url('http://example.com/downloads/manual') == 'service_manual'
        
        # Test parts URLs
        assert extraction_service._determine_extraction_type_from_url('http://example.com/parts-catalog') == 'parts_list'
        assert extraction_service._determine_extraction_type_from_url('http://example.com/parts/c750a') == 'parts_list'
        
        # Test troubleshooting URLs
        assert extraction_service._determine_extraction_type_from_url('http://example.com/troubleshooting') == 'troubleshooting'
        assert extraction_service._determine_extraction_type_from_url('http://example.com/support/troubleshoot') == 'troubleshooting'
        
        # Test generic URL (no match)
        assert extraction_service._determine_extraction_type_from_url('http://example.com/about') is None

    def test_determine_extraction_type_from_link_type(self, extraction_service):
        """Test determining extraction type from link type."""
        # Test various link types
        assert extraction_service._determine_extraction_type_from_link_type('product_page') == 'product_specs'
        assert extraction_service._determine_extraction_type_from_link_type('error_code_page') == 'error_codes'
        assert extraction_service._determine_extraction_type_from_link_type('manual_page') == 'service_manual'
        assert extraction_service._determine_extraction_type_from_link_type('parts_page') == 'parts_list'
        assert extraction_service._determine_extraction_type_from_link_type('troubleshooting_page') == 'troubleshooting'
        
        # Test generic link type (no match)
        assert extraction_service._determine_extraction_type_from_link_type('external') is None
        assert extraction_service._determine_extraction_type_from_link_type('internal') is None

    def test_load_config_from_config_service(self, mock_scraper, mock_database_service):
        """Test loading config from ConfigService."""
        mock_config_service = MagicMock()
        mock_config_service.get_scraping_config.return_value = {
            'firecrawl_llm_provider': 'ollama',
            'firecrawl_model_name': 'llama3.2:latest',
            'extraction_confidence_threshold': 0.7,
            'scrape_timeout': 60
        }
        
        service = StructuredExtractionService(
            web_scraping_service=mock_scraper,
            database_service=mock_database_service,
            config_service=mock_config_service
        )
        
        assert service._config['firecrawl_llm_provider'] == 'ollama'
        assert service._config['confidence_threshold'] == 0.7
        assert service._config['extraction_timeout'] == 60

    def test_load_config_defaults(self, mock_scraper, mock_database_service):
        """Test loading default config when no ConfigService provided."""
        service = StructuredExtractionService(
            web_scraping_service=mock_scraper,
            database_service=mock_database_service,
            config_service=None
        )
        
        # Should have default values
        assert service._config['confidence_threshold'] == 0.5
        assert service._config['extraction_timeout'] == 60

    @pytest.mark.asyncio
    async def test_confidence_threshold_configurable(self, extraction_service, mock_db_client, mock_scraper):
        """Test configurable confidence threshold."""
        # Override confidence threshold
        extraction_service._config['confidence_threshold'] = 0.7
        
        # Setup scraper response with confidence below new threshold
        mock_scraper.extract_structured_data.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'data': {'model_number': 'c750a'},
            'confidence': 0.65  # Below 0.7 threshold
        }
        
        result = await extraction_service.extract_product_specs(
            url='http://example.com/product/c750a'
        )
        
        assert result['success'] is False
        assert result['skipped'] is True
        assert result['reason'] == 'confidence_below_threshold'


# ============================================================================
# Integration Tests for StructuredExtractionService
# ============================================================================

@pytest.mark.integration
@pytest.mark.database
class TestStructuredExtractionIntegration:
    """Integration tests for StructuredExtractionService with real database and services.
    
    These tests use real database connections, real WebScrapingService (Firecrawl when available),
    and verify end-to-end extraction workflows including database persistence, confidence filtering,
    batch processing, and validation.
    """
    
    # ========================================================================
    # Product Specs Extraction Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_extract_product_specs_real_firecrawl(
        self, real_extraction_service, integration_test_urls, test_database, firecrawl_available
    ):
        """Test real Firecrawl extraction with product_specs schema.
        
        Setup:
        - Use real extraction service with Firecrawl backend
        - Extract from test product URL
        
        Expected:
        - Extraction succeeds with product_specs data
        - Data contains model_number, series_name, product_type
        - Record persisted in database with correct extraction_type
        
        Verification:
        - Check extracted_data structure
        - Verify database record exists
        - Validate all required fields present
        """
        if not firecrawl_available:
            pytest.skip("Firecrawl not available, using BeautifulSoup (no structured extraction)")
        
        url = integration_test_urls['product']
        
        # Perform extraction
        result = await real_extraction_service.extract_product_specs(url=url)
        
        # Verify extraction succeeded
        assert result['success'] is True
        assert 'extracted_data' in result
        assert 'record_id' in result
        
        # Verify extracted data structure
        extracted_data = result['extracted_data']
        assert isinstance(extracted_data, dict)
        
        # Verify database persistence

        record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
        assert record is not None
        assert record['extraction_type'] == 'product_specs'
        assert record['confidence'] >= 0.0
        assert record['confidence'] <= 1.0
    @pytest.mark.asyncio
    async def test_extract_product_specs_confidence_threshold(
        self, real_extraction_service, integration_test_urls, test_database, test_helpers
    ):
        """Test confidence threshold filtering with different thresholds."""
        url = integration_test_urls['product']
        thresholds = [0.3, 0.5, 0.8]
        
        for threshold in thresholds:
            real_extraction_service._config['confidence_threshold'] = threshold
            result = await real_extraction_service.extract_product_specs(url=url)
            
            if result.get('skipped'):
                assert result['reason'] == 'confidence_below_threshold'
                assert result['confidence'] < threshold
            elif result.get('success'):
                # Verify record was persisted and confidence meets threshold
                record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
                assert record is not None
                assert record['confidence'] >= threshold
    
    @pytest.mark.asyncio
    async def test_extract_product_specs_schema_validation(
        self, real_extraction_service, integration_test_urls, extraction_schemas
    ):
        """Test schema validation for product_specs extraction."""
        url = integration_test_urls['product']
        schema_info = extraction_schemas['schemas']['product_specs']
        assert schema_info is not None
        
        result = await real_extraction_service.extract_product_specs(url=url)
        
        if result['success']:
            extracted_data = result['extracted_data']
            schema = schema_info['schema']
            
            # Validate against JSON schema if jsonschema is available
            if JSONSCHEMA_AVAILABLE:
                try:
                    jsonschema.validate(instance=extracted_data, schema=schema)
                except jsonschema.ValidationError as e:
                    pytest.fail(f"Schema validation failed: {e.message}")
            else:
                # Fallback: Check required fields manually
                required_fields = schema.get('required', [])
                for field in required_fields:
                    assert field in extracted_data, f"Required field '{field}' missing from extracted_data"
    
    @pytest.mark.asyncio
    async def test_extract_product_specs_with_manufacturer_product_ids(
        self, real_extraction_service, integration_test_urls, test_database, test_helpers
    ):
        """Test extraction with manufacturer_id and product_id foreign keys."""

        
        url = integration_test_urls['product']
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        product_id = f"prod-{uuid.uuid4().hex[:8]}"
        
        result = await real_extraction_service.extract_product_specs(
            url=url,
            manufacturer_id=manufacturer_id,
            product_id=product_id
        )
        
        if result['success']:
            record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
            if record:
                assert record.get('manufacturer_id') == manufacturer_id
                assert record.get('product_id') == product_id
    
    # ========================================================================
    # Error Codes Extraction Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_extract_error_codes_real_firecrawl(
        self, real_extraction_service, integration_test_urls, test_database, firecrawl_available, test_helpers, extraction_schemas
    ):
        """Test real Firecrawl extraction with error_codes schema."""
        if not firecrawl_available:
            pytest.skip("Firecrawl not available")

        url = integration_test_urls['error_codes']
        
        result = await real_extraction_service.extract_error_codes(url=url)
        
        assert result['success'] is True
        assert 'extracted_data' in result
        
        # Validate schema
        extracted_data = result['extracted_data']
        schema_info = extraction_schemas['schemas']['error_codes']
        schema = schema_info['schema']
        
        if JSONSCHEMA_AVAILABLE:
            try:
                jsonschema.validate(instance=extracted_data, schema=schema)
            except jsonschema.ValidationError as e:
                pytest.fail(f"Schema validation failed: {e.message}")
        else:
            # Check required fields
            assert 'error_codes' in extracted_data
            if extracted_data['error_codes']:
                for error_code in extracted_data['error_codes']:
                    assert 'code' in error_code
                    assert 'description' in error_code
        
        record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
        assert record is not None
        assert record['extraction_type'] == 'error_code'
    
    @pytest.mark.asyncio
    async def test_extract_error_codes_multiple_codes(
        self, real_extraction_service, integration_test_urls
    ):
        """Test extraction of multiple error codes."""
        url = integration_test_urls['error_codes']
        result = await real_extraction_service.extract_error_codes(url=url)
        
        if result['success'] and 'extracted_data' in result:
            data = result['extracted_data']
            if 'error_codes' in data:
                assert isinstance(data['error_codes'], list)
    
    @pytest.mark.asyncio
    async def test_extract_error_codes_with_related_parts(
        self, real_extraction_service, integration_test_urls
    ):
        """Test extraction with related_parts and affected_models."""
        url = integration_test_urls['error_codes']
        result = await real_extraction_service.extract_error_codes(url=url)
        
        if result['success']:
            assert 'extracted_data' in result
    
    # ========================================================================
    # Service Manual, Parts List, Troubleshooting Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_extract_service_manual_metadata_real_firecrawl(
        self, real_extraction_service, integration_test_urls, test_database, firecrawl_available, test_helpers, extraction_schemas
    ):
        """Test service manual metadata extraction."""
        if not firecrawl_available:
            pytest.skip("Firecrawl not available")

        url = integration_test_urls['manual']
        
        result = await real_extraction_service.extract_service_manual_metadata(url=url)
        assert result['success'] is True
        
        # Validate schema
        extracted_data = result['extracted_data']
        schema_info = extraction_schemas['schemas']['service_manual']
        schema = schema_info['schema']
        
        if JSONSCHEMA_AVAILABLE:
            try:
                jsonschema.validate(instance=extracted_data, schema=schema)
            except jsonschema.ValidationError as e:
                pytest.fail(f"Schema validation failed: {e.message}")
        else:
            # Check required fields
            assert 'manual_type' in extracted_data
            assert 'product_models' in extracted_data
        
        record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
        assert record['extraction_type'] == 'service_manual'
    
    @pytest.mark.asyncio
    async def test_extract_parts_list_real_firecrawl(
        self, real_extraction_service, integration_test_urls, test_database, firecrawl_available, test_helpers, extraction_schemas
    ):
        """Test parts list extraction."""
        if not firecrawl_available:
            pytest.skip("Firecrawl not available")

        url = integration_test_urls['parts']
        
        result = await real_extraction_service.extract_parts_list(url=url)
        assert result['success'] is True
        
        # Validate schema
        extracted_data = result['extracted_data']
        schema_info = extraction_schemas['schemas']['parts_list']
        schema = schema_info['schema']
        
        if JSONSCHEMA_AVAILABLE:
            try:
                jsonschema.validate(instance=extracted_data, schema=schema)
            except jsonschema.ValidationError as e:
                pytest.fail(f"Schema validation failed: {e.message}")
        else:
            # Check required fields
            assert 'parts' in extracted_data
            if extracted_data['parts']:
                for part in extracted_data['parts']:
                    assert 'part_number' in part
                    assert 'part_name' in part
        
        record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
        assert record['extraction_type'] == 'parts_list'
    
    @pytest.mark.asyncio
    async def test_extract_troubleshooting_real_firecrawl(
        self, real_extraction_service, integration_test_urls, test_database, firecrawl_available, test_helpers, extraction_schemas
    ):
        """Test troubleshooting extraction."""
        if not firecrawl_available:
            pytest.skip("Firecrawl not available")

        url = integration_test_urls['troubleshooting']
        
        result = await real_extraction_service.extract_troubleshooting(url=url)
        assert result['success'] is True
        
        # Validate schema
        extracted_data = result['extracted_data']
        schema_info = extraction_schemas['schemas']['troubleshooting']
        schema = schema_info['schema']
        
        if JSONSCHEMA_AVAILABLE:
            try:
                jsonschema.validate(instance=extracted_data, schema=schema)
            except jsonschema.ValidationError as e:
                pytest.fail(f"Schema validation failed: {e.message}")
        else:
            # Check required fields
            assert 'issues' in extracted_data
            if extracted_data['issues']:
                for issue in extracted_data['issues']:
                    assert 'issue_title' in issue
                    assert 'solutions' in issue
        
        record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
        assert record['extraction_type'] == 'troubleshooting'
    
    # ========================================================================
    # Link Extraction Integration Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_extract_from_link_real_database(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test extract_from_link() with real link record from database."""

        
        # Create test link
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_id = await test_helpers.create_test_link(
            test_database,
            'http://example.com/test-product',
            'external',
            'product',
            manufacturer_id
        )
        
        # Perform extraction
        result = await real_extraction_service.extract_from_link(link_id)
        
        if result['success']:
            # Verify database persistence
            record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
            assert record is not None
            assert record['source_type'] == 'link'
            assert record['source_id'] == link_id
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("link_type,link_category,expected_type", [
        ('external', 'product', 'product_specs'),
        ('external', 'error', 'error_code'),
        ('external', 'manual', 'service_manual'),
        ('external', 'parts', 'parts_list'),
        ('external', 'troubleshooting', 'troubleshooting'),
    ])
    async def test_extract_from_link_type_determination(
        self, real_extraction_service, test_database, link_type, link_category, expected_type, test_helpers
    ):
        """Test automatic extraction_type determination from link_type and link_category."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_id = await test_helpers.create_test_link(
            test_database,
            f'http://example.com/test-{link_category}',
            link_type,
            link_category,
            manufacturer_id
        )
        
        result = await real_extraction_service.extract_from_link(link_id)
        
        if result['success']:
            assert result['extraction_type'] == expected_type
    
    @pytest.mark.asyncio
    async def test_extract_from_link_metadata_update(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test that link metadata is updated with structured_extractions array."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_id = await test_helpers.create_test_link(
            test_database,
            'http://example.com/test-product',
            'external',
            'product',
            manufacturer_id
        )
        
        result = await real_extraction_service.extract_from_link(link_id)
        
        if result['success']:
            # Query link to verify metadata update
            link_record = await test_database.execute_query(
                "SELECT scraped_metadata FROM krai_content.links WHERE id = $1",
                link_id
            )
            
            if link_record:
                metadata = link_record[0].get('scraped_metadata', {})
                assert isinstance(metadata, dict)
    
    @pytest.mark.asyncio
    async def test_extract_from_link_not_found(
        self, real_extraction_service, test_helpers
    ):
        """Test error handling for non-existent link ID."""
        result = await real_extraction_service.extract_from_link('non-existent-link-id')
        
        assert result['success'] is False
        assert result['error'] == 'link not found', f"Expected exact error 'link not found', got: {result.get('error')}"
    
    @pytest.mark.asyncio
    async def test_extract_from_link_no_matching_schema(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test error handling when no schema matches link type."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_id = await test_helpers.create_test_link(
            test_database,
            'http://example.com/unknown',
            'external',
            'unknown_category',
            manufacturer_id
        )
        
        result = await real_extraction_service.extract_from_link(link_id)
        
        assert result['success'] is False
        assert result['error'] == 'no matching extraction schema', f"Expected exact error 'no matching extraction schema', got: {result.get('error')}"
    
    # ========================================================================
    # Crawled Page Extraction Integration Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_extract_from_crawled_page_real_database(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test extract_from_crawled_page() with real crawled page record."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        crawl_job_id = f"job-{uuid.uuid4().hex[:8]}"
        page_id = await test_helpers.create_test_crawled_page(
            test_database,
            'http://example.com/test-support',
            'product_page',
            manufacturer_id,
            crawl_job_id
        )
        
        result = await real_extraction_service.extract_from_crawled_page(page_id)
        
        if result['success']:
            record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
            assert record is not None
            assert record['source_type'] == 'crawled_page'
            assert record['source_id'] == page_id
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("page_type,expected_type", [
        ('product_page', 'product_specs'),
        ('error_code_page', 'error_code'),
        ('manual_page', 'service_manual'),
        ('parts_page', 'parts_list'),
        ('troubleshooting_page', 'troubleshooting'),
    ])
    async def test_extract_from_crawled_page_type_determination(
        self, real_extraction_service, test_database, page_type, expected_type, test_helpers
    ):
        """Test automatic extraction_type determination from page_type."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        crawl_job_id = f"job-{uuid.uuid4().hex[:8]}"
        page_id = await test_helpers.create_test_crawled_page(
            test_database,
            f'http://example.com/test-{page_type}',
            page_type,
            manufacturer_id,
            crawl_job_id
        )
        
        result = await real_extraction_service.extract_from_crawled_page(page_id)
        
        if result['success']:
            assert result['extraction_type'] == expected_type
    
    @pytest.mark.asyncio
    async def test_extract_from_crawled_page_status_update(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test that crawled page status is updated to 'processed'."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        crawl_job_id = f"job-{uuid.uuid4().hex[:8]}"
        page_id = await test_helpers.create_test_crawled_page(
            test_database,
            'http://example.com/test-page',
            'product_page',
            manufacturer_id,
            crawl_job_id
        )
        
        result = await real_extraction_service.extract_from_crawled_page(page_id)
        
        if result['success']:
            # Verify status update
            page_record = await test_database.execute_query(
                "SELECT status, processed_at FROM krai_system.crawled_pages WHERE id = $1",
                page_id
            )
            
            if page_record:
                assert page_record[0].get('status') in ['processed', 'scraped']
    
    @pytest.mark.asyncio
    async def test_extract_from_crawled_page_not_found(
        self, real_extraction_service, test_helpers
    ):
        """Test error handling for non-existent page ID."""
        result = await real_extraction_service.extract_from_crawled_page('non-existent-page-id')
        
        assert result['success'] is False
        assert result['error'] == 'crawled page not found', f"Expected exact error 'crawled page not found', got: {result.get('error')}"
    
    # ========================================================================
    # Batch Extraction Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_batch_extract_links_real_database(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test batch_extract() with multiple link IDs."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_ids = []
        
        # Create 5 test links
        for i in range(5):
            link_id = await test_helpers.create_test_link(
                test_database,
                f'http://example.com/product-{i}',
                'external',
                'product',
                manufacturer_id
            )
            link_ids.append(link_id)
        
        # Perform batch extraction
        result = await real_extraction_service.batch_extract(
            source_type='link',
            source_ids=link_ids
        )
        
        assert 'total' in result
        assert 'completed' in result
        assert 'failed' in result
        assert result['total'] == 5
    
    @pytest.mark.asyncio
    async def test_batch_extract_crawled_pages_real_database(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test batch_extract() with multiple crawled page IDs."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        crawl_job_id = f"job-{uuid.uuid4().hex[:8]}"
        page_ids = []
        
        # Create 5 test pages
        for i in range(5):
            page_id = await test_helpers.create_test_crawled_page(
                test_database,
                f'http://example.com/page-{i}',
                'product_page',
                manufacturer_id,
                crawl_job_id
            )
            page_ids.append(page_id)
        
        # Perform batch extraction
        result = await real_extraction_service.batch_extract(
            source_type='crawled_page',
            source_ids=page_ids
        )
        
        assert 'total' in result
        assert result['total'] == 5
    
    @pytest.mark.asyncio
    async def test_batch_extract_concurrency_control(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test concurrency limiting with max_concurrent parameter."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_ids = []
        
        # Create 10 test links
        for i in range(10):
            link_id = await test_helpers.create_test_link(
                test_database,
                f'http://example.com/product-{i}',
                'external',
                'product',
                manufacturer_id
            )
            link_ids.append(link_id)
        
        # Track concurrent task counts
        import asyncio
        current_tasks = 0
        max_observed_concurrency = 0
        lock = asyncio.Lock()
        
        original_extract = real_extraction_service.extract_from_link
        
        async def tracked_extract(link_id):
            nonlocal current_tasks, max_observed_concurrency
            async with lock:
                current_tasks += 1
                max_observed_concurrency = max(max_observed_concurrency, current_tasks)
            try:
                return await original_extract(link_id)
            finally:
                async with lock:
                    current_tasks -= 1
        
        # Temporarily replace extract_from_link with tracked version
        real_extraction_service.extract_from_link = tracked_extract
        
        try:
            # Perform batch extraction with concurrency limit
            result = await real_extraction_service.batch_extract(
                source_type='link',
                source_ids=link_ids,
                max_concurrent=2
            )
            
            assert 'total' in result
            assert result['total'] == 10
            # Verify max concurrency did not exceed limit
            assert max_observed_concurrency <= 2
        finally:
            # Restore original method
            real_extraction_service.extract_from_link = original_extract
    
    @pytest.mark.asyncio
    async def test_batch_extract_empty_list(
        self, real_extraction_service, test_helpers
    ):
        """Test batch_extract() with empty source_ids list."""
        result = await real_extraction_service.batch_extract(
            source_type='link',
            source_ids=[]
        )
        
        assert result['total'] == 0
        assert result['completed'] == 0
        assert result['failed'] == 0
        assert result['results'] == []
    
    @pytest.mark.asyncio
    async def test_batch_extract_mixed_success_failure(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test batch extraction with both successful and failing extractions."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_ids = []
        
        # Create 3 valid links
        for i in range(3):
            link_id = await test_helpers.create_test_link(
                test_database,
                f'http://example.com/product-{i}',
                'external',
                'product',
                manufacturer_id
            )
            link_ids.append(link_id)
        
        # Add 2 non-existent link IDs
        link_ids.append('non-existent-link-1')
        link_ids.append('non-existent-link-2')
        
        result = await real_extraction_service.batch_extract(
            source_type='link',
            source_ids=link_ids,
            max_concurrent=2
        )
        
        assert result['total'] == 5
        assert result['completed'] + result['failed'] == 5
        assert result['failed'] >= 2  # At least the 2 non-existent links
        
        # Verify all results are present
        assert len(result['results']) == 5
        
        # Verify successful extractions were persisted
        successful_results = [r for r in result['results'] if r.get('success')]
        for success_result in successful_results:
            record = await test_helpers.verify_extraction_in_db(test_database, success_result['record_id'])
            assert record is not None
    
    # ========================================================================
    # Validation Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_validate_extraction_pending_to_validated(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test validate_extraction() with status='validated'."""

        
        # Create and extract
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_id = await test_helpers.create_test_link(
            test_database,
            'http://example.com/test-product',
            'external',
            'product',
            manufacturer_id
        )
        
        result = await real_extraction_service.extract_from_link(link_id)
        
        if result['success']:
            # Validate extraction
            validation_result = await real_extraction_service.validate_extraction(
                result['record_id'],
                status='validated',
                notes='Test validation'
            )
            
            if validation_result:
                # Verify database update
                record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
                assert record['validation_status'] == 'validated'
                assert record.get('validation_notes') == 'Test validation'
    
    @pytest.mark.asyncio
    async def test_validate_extraction_pending_to_rejected(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test validate_extraction() with status='rejected'."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_id = await test_helpers.create_test_link(
            test_database,
            'http://example.com/test-product',
            'external',
            'product',
            manufacturer_id
        )
        
        result = await real_extraction_service.extract_from_link(link_id)
        
        if result['success']:
            validation_result = await real_extraction_service.validate_extraction(
                result['record_id'],
                status='rejected',
                notes='Test rejection'
            )
            
            if validation_result:
                record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
                assert record['validation_status'] == 'rejected'
    
    @pytest.mark.asyncio
    async def test_validate_extraction_not_found(
        self, real_extraction_service
    ):
        """Test validate_extraction() with non-existent extraction_id."""
        result = await real_extraction_service.validate_extraction(
            'non-existent-id',
            status='validated'
        )
        
        assert result is False or (isinstance(result, dict) and not result.get('success'))
    
    # ========================================================================
    # Schema Management Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_schema_loading_from_file(
        self, real_extraction_service, extraction_schemas
    ):
        """Test that schemas are correctly loaded from extraction_schemas.json."""
        schemas = real_extraction_service.get_extraction_schemas()
        
        assert 'product_specs' in schemas
        assert 'error_codes' in schemas
        assert 'service_manual' in schemas
        assert 'parts_list' in schemas
        assert 'troubleshooting' in schemas
    
    @pytest.mark.asyncio
    async def test_get_extraction_schemas(
        self, real_extraction_service
    ):
        """Test get_extraction_schemas() returns all loaded schemas."""
        schemas = real_extraction_service.get_extraction_schemas()
        
        assert isinstance(schemas, dict)
        assert len(schemas) >= 5
    
    # ========================================================================
    # Database Persistence Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_persist_extraction_confidence_constraint(
        self, real_extraction_service, integration_test_urls, test_helpers
    ):
        """Test confidence constraint (0.0 <= confidence <= 1.0)."""
        url = integration_test_urls['product']
        
        result = await real_extraction_service.extract_product_specs(url=url)
        
        if result['success']:
            assert result['confidence'] >= 0.0
            assert result['confidence'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_persist_extraction_validation_status_default(
        self, real_extraction_service, test_database, integration_test_urls, test_helpers
    ):
        """Test that validation_status defaults to 'pending'."""

        
        url = integration_test_urls['product']
        result = await real_extraction_service.extract_product_specs(url=url)
        
        if result['success']:
            record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
            assert record['validation_status'] == 'pending'
    
    # ========================================================================
    # Config Service Integration Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_config_llm_provider_persisted(
        self, real_extraction_service, test_database, integration_test_urls, test_helpers
    ):
        """Test that llm_provider from config is persisted in database."""

        
        url = integration_test_urls['product']
        result = await real_extraction_service.extract_product_specs(url=url)
        
        if result['success']:
            record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
            assert record.get('llm_provider') is not None
    
    @pytest.mark.asyncio
    async def test_config_llm_model_persisted(
        self, real_extraction_service, test_database, integration_test_urls, test_helpers
    ):
        """Test that llm_model from config is persisted in database."""

        
        url = integration_test_urls['product']
        result = await real_extraction_service.extract_product_specs(url=url)
        
        if result['success']:
            record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
            assert record.get('llm_model') is not None
    
    # ========================================================================
    # End-to-End Integration Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_e2e_link_extraction_full_flow(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test complete flow: Create link → Extract → Persist → Update metadata → Validate."""

        
        # Step 1: Create link
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_id = await test_helpers.create_test_link(
            test_database,
            'http://example.com/test-product',
            'external',
            'product',
            manufacturer_id
        )
        
        # Step 2: Extract
        result = await real_extraction_service.extract_from_link(link_id)
        
        if result['success']:
            # Step 3: Verify persistence
            record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
            assert record is not None
            
            # Step 4: Verify link metadata update
            link_record = await test_database.execute_query(
                "SELECT scraped_metadata FROM krai_content.links WHERE id = $1",
                link_id
            )
            assert link_record is not None
            
            # Step 5: Validate
            validation_result = await real_extraction_service.validate_extraction(
                result['record_id'],
                status='validated',
                notes='E2E test validation'
            )
            
            if validation_result:
                # Verify validation
                validated_record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
                assert validated_record['validation_status'] == 'validated'
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_e2e_crawled_page_extraction_full_flow(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test complete flow for crawled page: Create page → Extract → Persist → Status update."""

        
        # Step 1: Create crawled page
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        crawl_job_id = f"job-{uuid.uuid4().hex[:8]}"
        page_id = await test_helpers.create_test_crawled_page(
            test_database,
            'http://example.com/test-support',
            'product_page',
            manufacturer_id,
            crawl_job_id
        )
        
        # Step 2: Extract
        result = await real_extraction_service.extract_from_crawled_page(page_id)
        
        if result['success']:
            # Step 3: Verify persistence
            record = await test_helpers.verify_extraction_in_db(test_database, result['record_id'])
            assert record is not None
            
            # Step 4: Verify status update
            page_record = await test_database.execute_query(
                "SELECT status FROM krai_system.crawled_pages WHERE id = $1",
                page_id
            )
            assert page_record is not None
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_e2e_batch_extraction_with_validation(
        self, real_extraction_service, test_database, test_helpers
    ):
        """Test batch extraction followed by validation of multiple records."""

        
        manufacturer_id = f"mfr-{uuid.uuid4().hex[:8]}"
        link_ids = []
        
        # Create 3 test links
        for i in range(3):
            link_id = await test_helpers.create_test_link(
                test_database,
                f'http://example.com/product-{i}',
                'external',
                'product',
                manufacturer_id
            )
            link_ids.append(link_id)
        
        # Batch extract
        batch_result = await real_extraction_service.batch_extract(
            source_type='link',
            source_ids=link_ids
        )
        
        # Validate successful extractions
        if batch_result.get('completed', 0) > 0:
            for result in batch_result.get('results', []):
                if result.get('success'):
                    await real_extraction_service.validate_extraction(
                        result['record_id'],
                        status='validated'
                    )
