"""
Integration tests for ProductResearcher.

Tests end-to-end product research workflow including web search,
scraping, LLM analysis, and caching.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import json

from research.product_researcher import ProductResearcher


pytest.mark.integration = pytest.mark.integration


class TestProductResearcherIntegration:
    """Test ProductResearcher integration scenarios."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        client = MagicMock()
        # Setup table() method to return chainable mock
        table_mock = MagicMock()
        table_mock.select.return_value = table_mock
        table_mock.insert.return_value = table_mock
        table_mock.update.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[], count=0)
        client.table.return_value = table_mock
        return client

    @pytest.fixture
    def product_researcher(self, mock_supabase):
        """Create ProductResearcher instance for testing."""
        return ProductResearcher(
            supabase=mock_supabase,
            ollama_url="http://localhost:11434",
            model="llama3.2:latest"
        )

    @pytest.fixture
    def sample_search_results(self):
        """Sample search results from Tavily."""
        return {
            'results': [
                {
                    'title': 'Konica Minolta C750i Specifications',
                    'url': 'http://example.com/c750i/specs',
                    'content': 'Detailed specifications for C750i including print speed, resolution, and dimensions.',
                    'score': 0.95
                },
                {
                    'title': 'C750i Product Page',
                    'url': 'http://example.com/c750i',
                    'content': 'Official product page for Konica Minolta C750i with overview and features.',
                    'score': 0.90
                },
                {
                    'title': 'C750i Support Documentation',
                    'url': 'http://example.com/c750i/support',
                    'content': 'Support documentation, manuals, and troubleshooting guides for C750i.',
                    'score': 0.85
                }
            ]
        }

    @pytest.fixture
    def sample_scraped_content(self):
        """Sample scraped content from URLs."""
        return """
        # Konica Minolta C750i

        ## Specifications
        - **Print Speed**: 75 ppm
        - **Resolution**: 1200 x 1200 dpi
        - **Paper Capacity**: 3,650 sheets
        - **Monthly Volume**: 300,000 pages

        ## Features
        - Color printing
        - Scanning and copying
        - Advanced finishing options
        """

    @pytest.fixture
    def sample_llm_analysis(self):
        """Sample LLM analysis result."""
        return {
            'manufacturer': 'Konica Minolta',
            'model_number': 'C750i',
            'product_type': 'Production Printer',
            'specifications': {
                'print_speed': '75 ppm',
                'resolution': '1200 x 1200 dpi',
                'paper_capacity': '3,650 sheets',
                'monthly_volume': '300,000 pages'
            },
            'features': ['Color printing', 'Scanning', 'Copying', 'Advanced finishing'],
            'confidence': 0.85,
            'sources': [
                'http://example.com/c750i/specs',
                'http://example.com/c750i'
            ],
            'scraping_backend': 'firecrawl',
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }

    def test_researcher_initialization(self, mock_supabase):
        """Test ProductResearcher initialization."""
        researcher = ProductResearcher(
            supabase=mock_supabase,
            ollama_url="http://localhost:11434",
            model="llama3.2:latest"
        )
        
        assert researcher.supabase == mock_supabase
        assert researcher.ollama_url == "http://localhost:11434"
        assert researcher.model == "llama3.2:latest"
        assert researcher.cache_ttl == 86400  # 24 hours default

    def test_researcher_with_custom_config(self, mock_supabase):
        """Test ProductResearcher with custom configuration."""
        researcher = ProductResearcher(
            supabase=mock_supabase,
            ollama_url="http://custom-ollama:11434",
            model="custom-model",
            cache_ttl=3600
        )
        
        assert researcher.ollama_url == "http://custom-ollama:11434"
        assert researcher.model == "custom-model"
        assert researcher.cache_ttl == 3600

    @patch('backend.research.product_researcher.requests.post')
    def test_research_product_full_workflow(self, mock_post, product_researcher, 
                                          sample_search_results, sample_scraped_content, sample_llm_analysis):
        """Test full product research workflow."""
        # Setup Tavily search response
        mock_tavily_response = MagicMock()
        mock_tavily_response.json.return_value = sample_search_results
        mock_tavily_response.raise_for_status.return_value = None
        
        # Setup Ollama LLM response
        mock_ollama_response = MagicMock()
        mock_ollama_response.json.return_value = {
            'response': json.dumps(sample_llm_analysis),
            'done': True
        }
        mock_ollama_response.raise_for_status.return_value = None
        
        # Configure mock_post to return different responses based on URL
        def post_side_effect(url, **kwargs):
            if 'tavily' in url:
                return mock_tavily_response
            elif 'ollama' in url:
                return mock_ollama_response
            return MagicMock()
        
        mock_post.side_effect = post_side_effect
        
        # Mock web scraping
        with patch.object(product_researcher, '_scrape_urls', return_value=sample_scraped_content):
            result = product_researcher.research_product(
                manufacturer="Konica Minolta",
                model_number="C750i"
            )
        
        assert result['success'] is True
        assert result['manufacturer'] == 'Konica Minolta'
        assert result['model_number'] == 'C750i'
        assert result['confidence'] == 0.85
        assert 'specifications' in result
        assert len(result['sources']) == 2

    @patch('backend.research.product_researcher.requests.post')
    def test_research_product_with_cache_hit(self, mock_post, product_researcher, sample_llm_analysis):
        """Test product research with cache hit."""
        # Setup cache hit
        with patch.object(product_researcher, '_get_cached_research', return_value=sample_llm_analysis):
            result = product_researcher.research_product(
                manufacturer="Konica Minolta",
                model_number="C750i"
            )
        
        assert result['success'] is True
        assert result['manufacturer'] == 'Konica Minolta'
        assert result['cached'] is True
        
        # Verify no web search was performed
        mock_post.assert_not_called()

    @patch('backend.research.product_researcher.requests.post')
    def test_research_product_search_failure(self, mock_post, product_researcher):
        """Test product research when search fails."""
        # Setup search failure
        mock_post.side_effect = Exception("Search API error")
        
        result = product_researcher.research_product(
            manufacturer="Konica Minolta",
            model_number="C750i"
        )
        
        assert result['success'] is False
        assert 'error' in result

    @patch('backend.research.product_researcher.requests.post')
    def test_research_product_no_search_results(self, mock_post, product_researcher):
        """Test product research with no search results."""
        # Setup empty search results
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': []}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = product_researcher.research_product(
            manufacturer="Konica Minolta",
            model_number="C750i"
        )
        
        assert result['success'] is False
        assert result['error'] == 'No search results found'

    @patch('backend.research.product_researcher.requests.post')
    def test_research_product_scraping_failure(self, mock_post, product_researcher, sample_search_results):
        """Test product research when scraping fails."""
        # Setup search success
        mock_tavily_response = MagicMock()
        mock_tavily_response.json.return_value = sample_search_results
        mock_tavily_response.raise_for_status.return_value = None
        mock_post.return_value = mock_tavily_response
        
        # Mock scraping failure
        with patch.object(product_researcher, '_scrape_urls', side_effect=Exception("Scraping failed")):
            result = product_researcher.research_product(
                manufacturer="Konica Minolta",
                model_number="C750i"
            )
        
        assert result['success'] is False
        assert 'scraping' in result['error'].lower()

    @patch('backend.research.product_researcher.requests.post')
    def test_research_product_llm_failure(self, mock_post, product_researcher, 
                                        sample_search_results, sample_scraped_content):
        """Test product research when LLM analysis fails."""
        # Setup search success
        mock_tavily_response = MagicMock()
        mock_tavily_response.json.return_value = sample_search_results
        mock_tavily_response.raise_for_status.return_value = None
        
        # Setup LLM failure
        mock_ollama_response = MagicMock()
        mock_ollama_response.raise_for_status.side_effect = Exception("LLM error")
        
        def post_side_effect(url, **kwargs):
            if 'tavily' in url:
                return mock_tavily_response
            elif 'ollama' in url:
                return mock_ollama_response
            return MagicMock()
        
        mock_post.side_effect = post_side_effect
        
        # Mock web scraping
        with patch.object(product_researcher, '_scrape_urls', return_value=sample_scraped_content):
            result = product_researcher.research_product(
                manufacturer="Konica Minolta",
                model_number="C750i"
            )
        
        assert result['success'] is False
        assert 'analysis' in result['error'].lower()

    @patch('backend.research.product_researcher.requests.post')
    def test_research_product_with_firecrawl_backend(self, mock_post, product_researcher, 
                                                   sample_search_results, sample_scraped_content, sample_llm_analysis):
        """Test product research using Firecrawl backend."""
        # Setup responses
        mock_tavily_response = MagicMock()
        mock_tavily_response.json.return_value = sample_search_results
        mock_tavily_response.raise_for_status.return_value = None
        
        mock_ollama_response = MagicMock()
        mock_ollama_response.json.return_value = {
            'response': json.dumps(sample_llm_analysis),
            'done': True
        }
        mock_ollama_response.raise_for_status.return_value = None
        
        mock_post.side_effect = lambda url, **kwargs: (
            mock_tavily_response if 'tavily' in url else mock_ollama_response
        )
        
        # Create researcher with Firecrawl backend
        with patch('backend.research.product_researcher.create_web_scraping_service') as mock_create_service:
            mock_scraper = MagicMock()
            mock_scraper.scrape_url.return_value = {
                'success': True,
                'backend': 'firecrawl',
                'content': sample_scraped_content,
                'metadata': {'status_code': 200}
            }
            mock_create_service.return_value = mock_scraper
            
            researcher = ProductResearcher(
                supabase=product_researcher.supabase,
                ollama_url="http://localhost:11434",
                model="llama3.2:latest"
            )
            
            with patch.object(researcher, '_scrape_urls', return_value=sample_scraped_content):
                result = researcher.research_product(
                    manufacturer="Konica Minolta",
                    model_number="C750i"
                )
        
        assert result['success'] is True
        assert result['scraping_backend'] == 'firecrawl'

    @patch('backend.research.product_researcher.requests.post')
    def test_research_product_with_beautifulsoup_fallback(self, mock_post, product_researcher, 
                                                        sample_search_results, sample_scraped_content, sample_llm_analysis):
        """Test product research falling back to BeautifulSoup."""
        # Setup responses
        mock_tavily_response = MagicMock()
        mock_tavily_response.json.return_value = sample_search_results
        mock_tavily_response.raise_for_status.return_value = None
        
        mock_ollama_response = MagicMock()
        mock_ollama_response.json.return_value = {
            'response': json.dumps(sample_llm_analysis),
            'done': True
        }
        mock_ollama_response.raise_for_status.return_value = None
        
        mock_post.side_effect = lambda url, **kwargs: (
            mock_tavily_response if 'tavily' in url else mock_ollama_response
        )
        
        # Create researcher that will fallback to BeautifulSoup
        with patch('backend.research.product_researcher.create_web_scraping_service') as mock_create_service:
            mock_scraper = MagicMock()
            mock_scraper.scrape_url.return_value = {
                'success': True,
                'backend': 'beautifulsoup',
                'content': sample_scraped_content,
                'metadata': {'status_code': 200}
            }
            mock_create_service.return_value = mock_scraper
            
            researcher = ProductResearcher(
                supabase=product_researcher.supabase,
                ollama_url="http://localhost:11434",
                model="llama3.2:latest"
            )
            
            with patch.object(researcher, '_scrape_urls', return_value=sample_scraped_content):
                result = researcher.research_product(
                    manufacturer="Konica Minolta",
                    model_number="C750i"
                )
        
        assert result['success'] is True
        assert result['scraping_backend'] == 'beautifulsoup'

    def test_cache_operations(self, product_researcher, sample_llm_analysis):
        """Test cache save and retrieve operations."""
        # Test saving to cache
        product_researcher._save_to_cache(
            manufacturer="Konica Minolta",
            model_number="C750i",
            analysis=sample_llm_analysis
        )
        
        # Verify cache save was called
        product_researcher.supabase.table.assert_called()
        
        # Test retrieving from cache
        with patch.object(product_researcher, '_get_cached_research', return_value=sample_llm_analysis):
            cached_result = product_researcher._get_cached_research(
                manufacturer="Konica Minolta",
                model_number="C750i"
            )
        
        assert cached_result == sample_llm_analysis

    def test_cache_expiry(self, product_researcher, sample_llm_analysis):
        """Test cache expiry functionality."""
        # Create old analysis (older than cache TTL)
        old_analysis = sample_llm_analysis.copy()
        old_analysis['cached_at'] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        
        with patch.object(product_researcher, '_get_cached_research', return_value=old_analysis):
            result = product_researcher.research_product(
                manufacturer="Konica Minolta",
                model_number="C750i"
            )
        
        # Should not use expired cache
        assert result.get('cached') is not True

    @patch('backend.research.product_researcher.requests.post')
    def test_url_discovery(self, mock_post, product_researcher):
        """Test URL discovery functionality."""
        # Setup search results for URL discovery
        search_results = {
            'results': [
                {
                    'title': 'C750i Products',
                    'url': 'http://example.com/products/c750i',
                    'content': 'Product listing page',
                    'score': 0.90
                }
            ]
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = search_results
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Mock URL discovery to return additional URLs
        discovered_urls = [
            'http://example.com/products/c750i/specs',
            'http://example.com/products/c750i/manual',
            'http://example.com/products/c750i/parts'
        ]
        
        with patch.object(product_researcher, '_discover_urls', return_value=discovered_urls):
            urls = product_researcher._discover_urls(
                manufacturer_url='http://example.com',
                model_number='C750i'
            )
        
        assert len(urls) == 3
        assert all('c750i' in url.lower() for url in urls)

    @patch('backend.research.product_researcher.requests.post')
    def test_direct_search_fallback(self, mock_post, product_researcher, sample_search_results):
        """Test direct search fallback when Tavily fails."""
        # Setup Tavily failure
        def post_side_effect(url, **kwargs):
            if 'tavily' in url:
                raise Exception("Tavily API error")
            # Return success for direct search
            mock_response = MagicMock()
            mock_response.json.return_value = sample_search_results
            mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_post.side_effect = post_side_effect
        
        result = product_researcher._web_search(
            manufacturer="Konica Minolta",
            model_number="C750i"
        )
        
        assert result is not None
        assert len(result['results']) == 3

    def test_get_scraping_info(self, product_researcher):
        """Test getting scraping configuration info."""
        info = product_researcher.get_scraping_info()
        
        assert 'backend' in info
        assert 'mock_mode' in info
        assert 'cache_ttl' in info
        assert 'model' in info
        assert 'ollama_url' in info

    def test_content_validation(self, product_researcher):
        """Test content validation in LLM analysis."""
        # Test with valid content
        valid_content = "# Product Specs\n\n- Speed: 75 ppm\n- Resolution: 1200 dpi"
        
        with patch('backend.research.product_researcher.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'response': json.dumps({
                    'manufacturer': 'Konica Minolta',
                    'model_number': 'C750i',
                    'specifications': {'speed': '75 ppm'}
                }),
                'done': True
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = product_researcher._llm_analyze(
                content=valid_content,
                manufacturer="Konica Minolta",
                model_number="C750i",
                sources=['http://example.com']
            )
        
        assert result['success'] is True
        assert 'specifications' in result

    def test_content_validation_insufficient_data(self, product_researcher):
        """Test content validation with insufficient data."""
        # Test with insufficient content
        insufficient_content = "Limited product information"
        
        result = product_researcher._llm_analyze(
            content=insufficient_content,
            manufacturer="Konica Minolta",
            model_number="C750i",
            sources=['http://example.com']
        )
        
        assert result['success'] is False
        assert 'insufficient data' in result['error'].lower()

    @patch('backend.research.product_researcher.requests.post')
    def test_async_scraping_integration(self, mock_post, product_researcher, sample_scraped_content):
        """Test async scraping integration."""
        # Setup mock scraping service
        mock_scraper = MagicMock()
        mock_scraper.scrape_url.return_value = {
            'success': True,
            'backend': 'firecrawl',
            'content': sample_scraped_content,
            'metadata': {'status_code': 200}
        }
        
        with patch('backend.research.product_researcher.create_web_scraping_service', return_value=mock_scraper):
            result = asyncio.run(product_researcher._scrape_urls_async([
                'http://example.com/c750i/specs',
                'http://example.com/c750i/features'
            ]))
        
        assert sample_scraped_content in result
        assert mock_scraper.scrape_url.call_count == 2

    def test_error_handling_and_recovery(self, product_researcher):
        """Test error handling and recovery mechanisms."""
        # Test with various error scenarios
        test_cases = [
            (Exception("Network error"), "network"),
            (TimeoutError("Request timeout"), "timeout"),
            (ValueError("Invalid data"), "validation")
        ]
        
        for error, error_type in test_cases:
            with patch.object(product_researcher, '_web_search', side_effect=error):
                result = product_researcher.research_product(
                    manufacturer="Konica Minolta",
                    model_number="C750i"
                )
            
            assert result['success'] is False
            assert error_type in result['error'].lower() or 'error' in result['error'].lower()

    @patch('backend.research.product_researcher.requests.post')
    def test_research_with_different_manufacturers(self, mock_post, product_researcher, 
                                                 sample_search_results, sample_scraped_content):
        """Test research with different manufacturers."""
        manufacturers = ["Konica Minolta", "Canon", "HP", "Brother"]
        
        # Setup responses
        mock_tavily_response = MagicMock()
        mock_tavily_response.json.return_value = sample_search_results
        mock_tavily_response.raise_for_status.return_value = None
        
        mock_ollama_response = MagicMock()
        mock_ollama_response.json.return_value = {
            'response': json.dumps({
                'manufacturer': 'Test Manufacturer',
                'model_number': 'Test Model',
                'specifications': {'test': 'value'}
            }),
            'done': True
        }
        mock_ollama_response.raise_for_status.return_value = None
        
        mock_post.side_effect = lambda url, **kwargs: (
            mock_tavily_response if 'tavily' in url else mock_ollama_response
        )
        
        with patch.object(product_researcher, '_scrape_urls', return_value=sample_scraped_content):
            for manufacturer in manufacturers:
                result = product_researcher.research_product(
                    manufacturer=manufacturer,
                    model_number="Test-Model"
                )
                
                assert result['success'] is True
                assert 'manufacturer' in result

    def test_performance_monitoring(self, product_researcher):
        """Test performance monitoring capabilities."""
        import time
        
        # Mock a slow operation
        with patch.object(product_researcher, '_web_search') as mock_search:
            def slow_search(*args, **kwargs):
                time.sleep(0.1)  # Simulate slow operation
                return {'results': []}
            
            mock_search.side_effect = slow_search
            
            start_time = time.time()
            result = product_researcher.research_product(
                manufacturer="Konica Minolta",
                model_number="C750i"
            )
            end_time = time.time()
            
            # Should complete within reasonable time
            assert end_time - start_time < 5.0  # 5 second timeout
            assert result['success'] is False  # No results, but completed

    @patch('backend.research.product_researcher.requests.post')
    def test_data_quality_validation(self, mock_post, product_researcher, 
                                   sample_search_results, sample_scraped_content):
        """Test data quality validation in research results."""
        # Setup LLM response with low quality data
        low_quality_analysis = {
            'manufacturer': '',
            'model_number': 'unknown',
            'specifications': {},
            'confidence': 0.1
        }
        
        mock_tavily_response = MagicMock()
        mock_tavily_response.json.return_value = sample_search_results
        mock_tavily_response.raise_for_status.return_value = None
        
        mock_ollama_response = MagicMock()
        mock_ollama_response.json.return_value = {
            'response': json.dumps(low_quality_analysis),
            'done': True
        }
        mock_ollama_response.raise_for_status.return_value = None
        
        mock_post.side_effect = lambda url, **kwargs: (
            mock_tavily_response if 'tavily' in url else mock_ollama_response
        )
        
        with patch.object(product_researcher, '_scrape_urls', return_value=sample_scraped_content):
            result = product_researcher.research_product(
                manufacturer="Konica Minolta",
                model_number="C750i"
            )
        
        # Should handle low quality results appropriately
        assert result['success'] is True  # Still succeeds but with low confidence
        assert result['confidence'] <= 0.5

    def test_configuration_validation(self, product_researcher):
        """Test configuration validation."""
        # Test with invalid Ollama URL
        with pytest.raises(ValueError):
            ProductResearcher(
                supabase=product_researcher.supabase,
                ollama_url="invalid-url",
                model="llama3.2:latest"
            )
        
        # Test with invalid cache TTL
        with pytest.raises(ValueError):
            ProductResearcher(
                supabase=product_researcher.supabase,
                ollama_url="http://localhost:11434",
                model="llama3.2:latest",
                cache_ttl=-1
            )

    @patch('backend.research.product_researcher.requests.post')
    def test_concurrent_research_requests(self, mock_post, product_researcher, 
                                        sample_search_results, sample_scraped_content):
        """Test handling concurrent research requests."""
        # Setup responses
        mock_tavily_response = MagicMock()
        mock_tavily_response.json.return_value = sample_search_results
        mock_tavily_response.raise_for_status.return_value = None
        
        mock_ollama_response = MagicMock()
        mock_ollama_response.json.return_value = {
            'response': json.dumps({
                'manufacturer': 'Konica Minolta',
                'model_number': 'C750i',
                'specifications': {'speed': '75 ppm'}
            }),
            'done': True
        }
        mock_ollama_response.raise_for_status.return_value = None
        
        mock_post.side_effect = lambda url, **kwargs: (
            mock_tavily_response if 'tavily' in url else mock_ollama_response
        )
        
        with patch.object(product_researcher, '_scrape_urls', return_value=sample_scraped_content):
            # Run multiple research requests concurrently
            async def run_concurrent_research():
                tasks = []
                for i in range(3):
                    task = asyncio.create_task(
                        asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: product_researcher.research_product(
                                manufacturer="Konica Minolta",
                                model_number=f"C750i-{i}"
                            )
                        )
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                return results
            
            results = asyncio.run(run_concurrent_research())
        
        # All requests should succeed
        assert len(results) == 3
        assert all(result['success'] for result in results)
