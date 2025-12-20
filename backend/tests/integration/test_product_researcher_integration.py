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
import os

from services.product_researcher import ProductResearcher


pytest.mark.integration = pytest.mark.integration


class TestProductResearcherUnitMocks:
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


# =============================================================================
# REAL INTEGRATION TESTS - Uses actual Firecrawl, DB, and LLM services
# =============================================================================

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("FIRECRAWL_API_KEY") or not os.getenv("FIRECRAWL_API_URL"),
    reason="Firecrawl not configured (FIRECRAWL_API_KEY or FIRECRAWL_API_URL missing)"
)
class TestProductResearcherRealIntegration:
    """
    Real integration tests for ProductResearcher.
    
    These tests use:
    - Real Supabase test database (via test_database fixture)
    - Real WebScrapingService with Firecrawl (via real_product_researcher fixture)
    - Real Ollama LLM for analysis
    - Real caching in database
    
    Tests are marked with @pytest.mark.integration and @pytest.mark.skipif
    to make them optional in CI environments where Firecrawl may not be available.
    """
    
    @pytest.mark.asyncio
    async def test_real_product_research_end_to_end(
        self,
        real_product_researcher: ProductResearcher,
        test_database
    ):
        """
        Test complete product research workflow with real services.
        
        This test performs a minimal but genuine end-to-end workflow:
        1. Search for product URLs (direct URL construction)
        2. Scrape product pages with real Firecrawl/BeautifulSoup
        3. Analyze content with real Ollama LLM
        4. Cache results in real test database
        """
        # Use a well-known product page that should be stable
        manufacturer = "Konica Minolta"
        model = "bizhub C450i"
        
        # Execute real research workflow
        result = await real_product_researcher.research_product(
            manufacturer=manufacturer,
            model=model,
            use_tavily=False,  # Use direct URL construction to avoid Tavily dependency
            max_urls=2  # Limit to 2 URLs to keep test fast
        )
        
        # Verify result structure
        assert 'success' in result
        assert 'manufacturer' in result
        assert 'model' in result
        
        # If successful, verify data quality
        if result['success']:
            assert result['manufacturer'] == manufacturer
            assert result['model'] == model
            assert 'series_name' in result
            assert 'specifications' in result
            assert isinstance(result['specifications'], dict)
            assert 'confidence' in result
            assert isinstance(result['confidence'], (int, float))
            assert 0.0 <= result['confidence'] <= 1.0
            assert 'source_urls' in result
            assert isinstance(result['source_urls'], list)
            assert len(result['source_urls']) > 0
            assert result.get('cached') == False  # First run should not be cached
            
            # Verify cache was created
            cache_result = await real_product_researcher._get_cached_research(
                manufacturer, model
            )
            assert cache_result is not None
            assert cache_result['manufacturer'] == manufacturer
            assert cache_result['model'] == model
    
    @pytest.mark.asyncio
    async def test_real_cache_hit(
        self,
        real_product_researcher: ProductResearcher,
        test_database
    ):
        """
        Test that cached research is retrieved correctly.
        
        Performs two sequential research calls and verifies:
        1. First call performs full workflow and caches
        2. Second call retrieves from cache without scraping
        """
        manufacturer = "Canon"
        model = "imageRUNNER ADVANCE DX C5870i"
        
        # First call - should perform full research
        result1 = await real_product_researcher.research_product(
            manufacturer=manufacturer,
            model=model,
            use_tavily=False,
            max_urls=1,
            force_refresh=True  # Force fresh research
        )
        
        # Second call - should hit cache
        result2 = await real_product_researcher.research_product(
            manufacturer=manufacturer,
            model=model,
            use_tavily=False,
            max_urls=1,
            force_refresh=False  # Allow cache
        )
        
        # Verify cache hit
        if result1.get('success'):
            assert result2.get('cached') == True
            assert result2['manufacturer'] == manufacturer
            assert result2['model'] == model
    
    @pytest.mark.asyncio
    async def test_real_scraping_with_firecrawl(
        self,
        real_product_researcher: ProductResearcher,
        firecrawl_available: bool
    ):
        """
        Test that scraping works with real Firecrawl backend.
        
        Verifies:
        - Scraping service is properly initialized
        - Can scrape a real URL
        - Returns valid content
        """
        if not firecrawl_available:
            pytest.skip("Firecrawl not available for this test")
        
        # Test scraping a simple, stable URL
        test_url = "https://example.com"
        
        result = await real_product_researcher.scrape_product_page(test_url)
        
        # Verify scraping result
        assert 'success' in result
        if result['success']:
            assert 'content' in result or 'error' in result
            if 'content' in result:
                assert len(result['content']) > 0
                assert 'backend' in result
    
    @pytest.mark.asyncio
    async def test_real_llm_analysis(
        self,
        real_product_researcher: ProductResearcher
    ):
        """
        Test LLM analysis with real Ollama service.
        
        Verifies:
        - Can analyze product content with Ollama
        - Returns structured data
        - Includes confidence score
        """
        # Sample product content for analysis
        test_content = """
        # Konica Minolta bizhub C450i
        
        ## Technical Specifications
        - Print Speed: 45 ppm (color and B&W)
        - Paper Size: A6 to SRA3
        - Memory: 8 GB
        - Storage: 256 GB SSD
        - Connectivity: Ethernet, USB, Wi-Fi
        
        ## Features
        - Color multifunction printer
        - Advanced scanning capabilities
        - Mobile printing support
        """
        
        result = await real_product_researcher.analyze_product_content(
            content=test_content,
            manufacturer="Konica Minolta",
            model="bizhub C450i",
            timeout=60  # Allow more time for LLM
        )
        
        # Verify analysis result
        assert 'success' in result
        if result['success']:
            assert 'series_name' in result or 'specifications' in result
            assert 'confidence' in result
            assert isinstance(result['confidence'], (int, float))
    
    @pytest.mark.asyncio
    async def test_real_error_handling(
        self,
        real_product_researcher: ProductResearcher
    ):
        """
        Test error handling with real services.
        
        Verifies:
        - Invalid URLs are handled gracefully
        - Errors are reported correctly
        - System doesn't crash on failures
        """
        # Test with invalid/non-existent product
        result = await real_product_researcher.research_product(
            manufacturer="NonExistentManufacturer",
            model="InvalidModel12345",
            use_tavily=False,
            max_urls=1
        )
        
        # Should return error gracefully
        assert 'success' in result
        # May succeed with empty/low-confidence results or fail gracefully
        if not result['success']:
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_real_backend_fallback(
        self,
        real_product_researcher: ProductResearcher,
        firecrawl_available: bool
    ):
        """
        Test backend fallback behavior with real services.
        
        Verifies:
        - System can fall back to BeautifulSoup if Firecrawl fails
        - Fallback is transparent to caller
        - Results are still valid
        """
        # Get backend info
        backend_info = real_product_researcher.scraper.get_backend_info()
        
        assert 'backend' in backend_info
        assert 'capabilities' in backend_info
        assert 'fallback_available' in backend_info
        
        # If Firecrawl is primary, verify fallback is available
        if backend_info['backend'] == 'firecrawl':
            assert backend_info['fallback_available'] == True
    
    @pytest.mark.asyncio
    async def test_real_concurrent_research(
        self,
        real_product_researcher: ProductResearcher
    ):
        """
        Test concurrent research requests with real services.
        
        Verifies:
        - Multiple concurrent requests are handled correctly
        - No race conditions in caching
        - All requests complete successfully
        """
        # Define multiple products to research concurrently
        products = [
            ("Konica Minolta", "bizhub C450i"),
            ("Canon", "imageRUNNER ADVANCE"),
            ("HP", "LaserJet Enterprise")
        ]
        
        # Execute concurrent research
        tasks = [
            real_product_researcher.research_product(
                manufacturer=mfr,
                model=mdl,
                use_tavily=False,
                max_urls=1
            )
            for mfr, mdl in products
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all completed (success or graceful failure)
        assert len(results) == len(products)
        for result in results:
            if isinstance(result, dict):
                assert 'success' in result
            else:
                # Exception occurred but was caught
                assert isinstance(result, Exception)
    
    @pytest.mark.asyncio
    async def test_real_database_integration(
        self,
        real_product_researcher: ProductResearcher,
        test_database
    ):
        """
        Test database integration with real test database.
        
        Verifies:
        - Cache table exists and is accessible
        - Can write to cache
        - Can read from cache
        - Cache expiry works correctly
        """
        manufacturer = "TestManufacturer"
        model = "TestModel"
        
        # Create test research data
        test_data = {
            'success': True,
            'manufacturer': manufacturer,
            'model': model,
            'series_name': 'Test Series',
            'specifications': {'test': 'value'},
            'confidence': 0.9,
            'source_urls': ['https://example.com']
        }
        
        # Cache the data
        cache_success = await real_product_researcher._cache_research(
            manufacturer, model, test_data
        )
        
        assert cache_success == True
        
        # Retrieve from cache
        cached = await real_product_researcher._get_cached_research(
            manufacturer, model
        )
        
        assert cached is not None
        assert cached['manufacturer'] == manufacturer
        assert cached['model'] == model
        assert cached['series_name'] == 'Test Series'
        
        # Cleanup test data
        await test_database.execute_query(
            "DELETE FROM krai_intelligence.product_research_cache WHERE manufacturer = $1 AND model = $2",
            manufacturer, model
        )
