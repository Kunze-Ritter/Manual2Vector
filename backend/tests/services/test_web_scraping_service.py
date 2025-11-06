"""
Comprehensive unit tests for WebScrapingService.

Tests FirecrawlBackend, BeautifulSoupBackend, and WebScrapingService including
fallback behavior, error handling, and factory functions.
"""

import pytest
import asyncio
import httpx
from unittest.mock import MagicMock, AsyncMock, patch
import os

from services.web_scraping_service import (
    FirecrawlBackend,
    BeautifulSoupBackend,
    WebScrapingService,
    FirecrawlUnavailableError,
    create_web_scraping_service,
    WebScraperBackend,
)


pytest.mark.unit = pytest.mark.unit
pytest.mark.firecrawl = pytest.mark.firecrawl


class TestFirecrawlBackend:
    """Test FirecrawlBackend functionality."""

    @pytest.mark.asyncio
    async def test_firecrawl_scrape_url_success(self):
        """Test successful URL scraping with Firecrawl."""
        backend = FirecrawlBackend(api_url="http://localhost:3002", mock_mode=True)
        result = await backend.scrape_url("http://example.com")
        
        assert result["success"] is True
        assert result["backend"] == "firecrawl"
        assert "Mock content" in result["content"]
        assert "html" in result
        assert "metadata" in result
        assert result["metadata"]["url"] == "http://example.com"

    @pytest.mark.asyncio
    async def test_firecrawl_scrape_url_with_options(self):
        """Test URL scraping with custom options."""
        backend = FirecrawlBackend(api_url="http://localhost:3002", mock_mode=True)
        options = {"formats": ["markdown"], "waitFor": 1000}
        result = await backend.scrape_url("http://example.com", options)
        
        assert result["success"] is True
        assert result["backend"] == "firecrawl"

    @pytest.mark.asyncio
    async def test_firecrawl_crawl_site_success(self):
        """Test successful site crawling with Firecrawl."""
        backend = FirecrawlBackend(api_url="http://localhost:3002", mock_mode=True)
        result = await backend.crawl_site("http://example.com", {"limit": 5})
        
        assert result["success"] is True
        assert result["backend"] == "firecrawl"
        assert result["total"] == 1
        assert len(result["pages"]) == 1
        assert "url" in result["pages"][0]
        assert "content" in result["pages"][0]
        assert "metadata" in result["pages"][0]

    @pytest.mark.asyncio
    async def test_firecrawl_extract_structured_data_success(self):
        """Test successful structured data extraction with Firecrawl."""
        backend = FirecrawlBackend(api_url="http://localhost:3002", mock_mode=True)
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "price": {"type": "number"}
            }
        }
        result = await backend.extract_structured_data("http://example.com", schema)
        
        assert result["success"] is True
        assert result["backend"] == "firecrawl"
        assert result["data"]["mock"] is True
        assert result["confidence"] == 1.0

    @pytest.mark.asyncio
    async def test_firecrawl_map_urls_success(self):
        """Test successful URL mapping with Firecrawl."""
        backend = FirecrawlBackend(api_url="http://localhost:3002", mock_mode=True)
        result = await backend.map_urls("http://example.com")
        
        assert result["success"] is True
        assert result["backend"] == "firecrawl"
        assert len(result["urls"]) == 2
        assert result["total"] == 2
        assert "http://example.com" in result["urls"]

    @pytest.mark.asyncio
    async def test_firecrawl_health_check_mock(self):
        """Test health check in mock mode."""
        backend = FirecrawlBackend(api_url="http://localhost:3002", mock_mode=True)
        result = await backend.health_check()
        
        assert result["status"] == "mock"
        assert result["backend"] == "firecrawl"

    def test_firecrawl_unavailable_error(self):
        """Test FirecrawlUnavailableError when SDK is not available."""
        with patch('backend.services.web_scraping_service.AsyncFirecrawl', None):
            with pytest.raises(FirecrawlUnavailableError) as exc_info:
                FirecrawlBackend(api_url="http://localhost:3002", mock_mode=False)
            
            assert "firecrawl-py SDK is not installed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_firecrawl_connection_error(self):
        """Test connection error handling."""
        backend = FirecrawlBackend(api_url="http://localhost:3002", mock_mode=False)
        backend._client = MagicMock()
        backend._client.scrape = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        
        with pytest.raises(FirecrawlUnavailableError):
            await backend.scrape_url("http://example.com")

    @pytest.mark.asyncio
    async def test_firecrawl_timeout_with_retry(self):
        """Test timeout with retry logic."""
        backend = FirecrawlBackend(api_url="http://localhost:3002", retries=2, mock_mode=False)
        backend._client = MagicMock()
        
        # Fail twice, then succeed
        backend._client.scrape = AsyncMock(
            side_effect=[
                asyncio.TimeoutError("Timeout"),
                asyncio.TimeoutError("Timeout"),
                {"success": True, "content": "Success after retries"}
            ]
        )
        
        result = await backend.scrape_url("http://example.com")
        assert result["success"] is True
        assert backend._client.scrape.call_count == 3


class TestBeautifulSoupBackend:
    """Test BeautifulSoupBackend functionality."""

    @pytest.mark.asyncio
    async def test_beautifulsoup_scrape_url_success(self):
        """Test successful URL scraping with BeautifulSoup."""
        backend = BeautifulSoupBackend(mock_mode=True)
        result = await backend.scrape_url("http://example.com")
        
        assert result["success"] is True
        assert result["backend"] == "beautifulsoup"
        assert "Mock BeautifulSoup content" in result["content"]
        assert "html" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_beautifulsoup_scrape_url_real_html(self):
        """Test scraping real HTML content."""
        backend = BeautifulSoupBackend(mock_mode=False)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Test</h1><script>alert('test')</script></body></html>"
        mock_response.content = mock_response.text.encode()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "http://example.com"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await backend.scrape_url("http://example.com")
            
            assert result["success"] is True
            assert result["backend"] == "beautifulsoup"
            assert "script" not in result["content"]  # Scripts should be removed
            assert "Test" in result["content"]

    @pytest.mark.asyncio
    async def test_beautifulsoup_crawl_site_breadth_first(self):
        """Test site crawling with breadth-first search."""
        backend = BeautifulSoupBackend(mock_mode=True)
        result = await backend.crawl_site("http://example.com", {"limit": 2, "maxDepth": 1})
        
        assert result["success"] is True
        assert result["backend"] == "beautifulsoup"
        assert result["total"] == 1
        assert len(result["pages"]) == 1

    @pytest.mark.asyncio
    async def test_beautifulsoup_extract_structured_data_not_supported(self):
        """Test that structured extraction is not supported."""
        backend = BeautifulSoupBackend(mock_mode=True)
        result = await backend.extract_structured_data("http://example.com", {})
        
        assert result["success"] is False
        assert "requires Firecrawl" in result["error"]

    @pytest.mark.asyncio
    async def test_beautifulsoup_map_urls_with_filter(self):
        """Test URL mapping with pattern filtering."""
        backend = BeautifulSoupBackend(mock_mode=True)
        result = await backend.map_urls("http://example.com", {"search": ".*product.*"})
        
        assert result["success"] is True
        assert result["backend"] == "beautifulsoup"
        assert len(result["urls"]) == 1

    @pytest.mark.asyncio
    async def test_beautifulsoup_health_check_always_healthy(self):
        """Test that health check always returns healthy."""
        backend = BeautifulSoupBackend(mock_mode=False)
        result = await backend.health_check()
        
        assert result["status"] == "healthy"
        assert result["backend"] == "beautifulsoup"

    @pytest.mark.asyncio
    async def test_beautifulsoup_http_error_handling(self):
        """Test HTTP error handling."""
        backend = BeautifulSoupBackend(mock_mode=False)
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = \
                httpx.HTTPStatusError("404 Not Found", request=MagicMock(), response=MagicMock(status_code=404))
            
            result = await backend.scrape_url("http://example.com")
            
            assert result["success"] is False
            assert "404" in result["error"]


class TestWebScrapingService:
    """Test WebScrapingService functionality."""

    @pytest.fixture
    def firecrawl_backend(self):
        """Create FirecrawlBackend for testing."""
        return FirecrawlBackend(api_url="http://localhost:3002", mock_mode=True)

    @pytest.fixture
    def beautifulsoup_backend(self):
        """Create BeautifulSoupBackend for testing."""
        return BeautifulSoupBackend(mock_mode=True)

    @pytest.mark.asyncio
    async def test_service_with_firecrawl_primary(self, firecrawl_backend, beautifulsoup_backend):
        """Test service with Firecrawl as primary backend."""
        service = WebScrapingService(
            primary_backend=firecrawl_backend,
            fallback_backend=beautifulsoup_backend
        )
        
        result = await service.scrape_url("http://example.com")
        
        assert result["success"] is True
        assert result["backend"] == "firecrawl"
        assert service.fallback_count == 0

    @pytest.mark.asyncio
    async def test_service_automatic_fallback(self, firecrawl_backend, beautifulsoup_backend):
        """Test automatic fallback from Firecrawl to BeautifulSoup."""
        # Make Firecrawl fail
        firecrawl_backend.scrape_url = AsyncMock(
            side_effect=FirecrawlUnavailableError("Firecrawl down")
        )
        
        service = WebScrapingService(
            primary_backend=firecrawl_backend,
            fallback_backend=beautifulsoup_backend
        )
        
        result = await service.scrape_url("http://example.com")
        
        assert result["success"] is True
        assert result["backend"] == "beautifulsoup"
        assert service.fallback_count == 1

    @pytest.mark.asyncio
    async def test_service_force_backend(self, firecrawl_backend, beautifulsoup_backend):
        """Test forcing a specific backend."""
        service = WebScrapingService(
            primary_backend=firecrawl_backend,
            fallback_backend=beautifulsoup_backend
        )
        
        result = await service.scrape_url(
            "http://example.com", 
            force_backend="beautifulsoup"
        )
        
        assert result["success"] is True
        assert result["backend"] == "beautifulsoup"

    @pytest.mark.asyncio
    async def test_service_extract_requires_firecrawl(self, beautifulsoup_backend):
        """Test that structured extraction requires Firecrawl."""
        service = WebScrapingService(
            primary_backend=beautifulsoup_backend
        )
        
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = await service.extract_structured_data("http://example.com", schema)
        
        assert result["success"] is False
        assert "requires Firecrawl" in result["error"]

    @pytest.mark.asyncio
    async def test_service_health_check_both_backends(self, firecrawl_backend, beautifulsoup_backend):
        """Test health check with both backends."""
        service = WebScrapingService(
            primary_backend=firecrawl_backend,
            fallback_backend=beautifulsoup_backend
        )
        
        result = await service.health_check()
        
        assert "firecrawl" in result["backends"]
        assert "beautifulsoup" in result["backends"]
        assert result["backends"]["firecrawl"]["status"] == "mock"
        assert result["backends"]["beautifulsoup"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_service_get_backend_info(self, firecrawl_backend, beautifulsoup_backend):
        """Test getting backend information."""
        service = WebScrapingService(
            primary_backend=firecrawl_backend,
            fallback_backend=beautifulsoup_backend
        )
        
        info = service.get_backend_info()
        
        assert info["backend"] == "firecrawl"
        assert "extract" in info["capabilities"]
        assert info["fallback_available"] is True

    @pytest.mark.asyncio
    async def test_service_switch_backend(self, firecrawl_backend, beautifulsoup_backend):
        """Test switching primary backend."""
        service = WebScrapingService(
            primary_backend=firecrawl_backend,
            fallback_backend=beautifulsoup_backend
        )
        
        service.switch_backend(beautifulsoup_backend)
        
        assert service.primary_backend == beautifulsoup_backend

    @pytest.mark.asyncio
    async def test_service_invalid_url_validation(self, firecrawl_backend):
        """Test invalid URL validation."""
        service = WebScrapingService(primary_backend=firecrawl_backend)
        
        with pytest.raises(ValueError) as exc_info:
            await service.crawl_site("ftp://invalid.com")
        
        assert "Invalid URL scheme" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_service_invalid_schema_validation(self, firecrawl_backend):
        """Test invalid schema validation."""
        service = WebScrapingService(primary_backend=firecrawl_backend)
        
        with pytest.raises(ValueError) as exc_info:
            await service.extract_structured_data("http://example.com", "not a dict")
        
        assert "Schema must be a dictionary" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fallback_count_tracking(self, firecrawl_backend, beautifulsoup_backend):
        """Test fallback count tracking."""
        firecrawl_backend.scrape_url = AsyncMock(
            side_effect=FirecrawlUnavailableError("Firecrawl down")
        )
        
        service = WebScrapingService(
            primary_backend=firecrawl_backend,
            fallback_backend=beautifulsoup_backend
        )
        
        # Multiple calls should increment fallback count
        await service.scrape_url("http://example.com")
        await service.scrape_url("http://example.com")
        await service.scrape_url("http://example.com")
        
        assert service.fallback_count == 3

    @pytest.mark.asyncio
    async def test_no_fallback_for_extract_structured_data(self, firecrawl_backend, beautifulsoup_backend):
        """Test that extract_structured_data doesn't fallback."""
        firecrawl_backend.extract_structured_data = AsyncMock(
            side_effect=FirecrawlUnavailableError("Firecrawl down")
        )
        
        service = WebScrapingService(
            primary_backend=firecrawl_backend,
            fallback_backend=beautifulsoup_backend
        )
        
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        
        with pytest.raises(FirecrawlUnavailableError):
            await service.extract_structured_data("http://example.com", schema)


class TestFactoryFunction:
    """Test the create_web_scraping_service factory function."""

    def test_create_service_firecrawl_backend(self, monkeypatch):
        """Test creating service with Firecrawl backend."""
        monkeypatch.setenv("SCRAPING_BACKEND", "firecrawl")
        
        service = create_web_scraping_service()
        
        assert service.primary_backend.backend_name == "firecrawl"
        assert service.fallback_backend is not None
        assert service.fallback_backend.backend_name == "beautifulsoup"

    def test_create_service_beautifulsoup_backend(self, monkeypatch):
        """Test creating service with BeautifulSoup backend."""
        monkeypatch.setenv("SCRAPING_BACKEND", "beautifulsoup")
        
        service = create_web_scraping_service()
        
        assert service.primary_backend.backend_name == "beautifulsoup"
        assert service.fallback_backend is None

    def test_create_service_with_config_service(self, mock_config_service):
        """Test creating service with ConfigService."""
        service = create_web_scraping_service(config_service=mock_config_service)
        
        assert service.primary_backend.backend_name == "firecrawl"
        # Config should be loaded from ConfigService

    def test_create_service_firecrawl_unavailable_fallback(self, monkeypatch):
        """Test fallback when Firecrawl is unavailable."""
        monkeypatch.setenv("SCRAPING_BACKEND", "firecrawl")
        
        with patch('backend.services.web_scraping_service.AsyncFirecrawl', None):
            service = create_web_scraping_service()
            
            # Should fall back to BeautifulSoup
            assert service.primary_backend.backend_name == "beautifulsoup"

    def test_create_service_with_parameter_override(self, monkeypatch):
        """Test backend parameter override."""
        monkeypatch.setenv("SCRAPING_BACKEND", "beautifulsoup")
        
        service = create_web_scraping_service(backend="firecrawl")
        
        assert service.primary_backend.backend_name == "firecrawl"

    def test_create_service_mock_mode(self, monkeypatch):
        """Test creating service in mock mode."""
        monkeypatch.setenv("SCRAPING_MOCK_MODE", "true")
        
        service = create_web_scraping_service()
        
        assert service.primary_backend.mock_mode is True
        if service.fallback_backend:
            assert service.fallback_backend.mock_mode is True

    def test_create_service_with_proxy_config(self, monkeypatch):
        """Test creating service with proxy configuration."""
        monkeypatch.setenv("SCRAPING_BACKEND", "firecrawl")
        monkeypatch.setenv("FIRECRAWL_PROXY_SERVER", "http://proxy.example.com:8080")
        monkeypatch.setenv("FIRECRAWL_PROXY_USERNAME", "user")
        monkeypatch.setenv("FIRECRAWL_PROXY_PASSWORD", "pass")
        
        # Should not raise an error
        service = create_web_scraping_service()
        assert service.primary_backend.backend_name == "firecrawl"

    def test_create_service_openai_config(self, monkeypatch):
        """Test creating service with OpenAI configuration."""
        monkeypatch.setenv("SCRAPING_BACKEND", "firecrawl")
        monkeypatch.setenv("FIRECRAWL_LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        
        service = create_web_scraping_service()
        
        # Should create successfully with OpenAI config
        assert service.primary_backend.backend_name == "firecrawl"


class TestErrorHandling:
    """Test comprehensive error handling."""

    @pytest.mark.asyncio
    async def test_firecrawl_transport_error(self):
        """Test transport error handling."""
        backend = FirecrawlBackend(api_url="http://localhost:3002", mock_mode=False)
        backend._client = MagicMock()
        backend._client.scrape = AsyncMock(side_effect=httpx.TransportError("Transport error"))
        
        with pytest.raises(FirecrawlUnavailableError):
            await backend.scrape_url("http://example.com")

    @pytest.mark.asyncio
    async def test_beautifulsoup_timeout_error(self):
        """Test timeout error handling in BeautifulSoup."""
        backend = BeautifulSoupBackend(mock_mode=False, timeout=0.001)  # Very short timeout
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = \
                httpx.TimeoutException("Timeout")
            
            result = await backend.scrape_url("http://example.com")
            
            assert result["success"] is False
            assert "Timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_service_fallback_when_no_fallback_backend(self):
        """Test service behavior when no fallback backend is available."""
        firecrawl_backend = FirecrawlBackend(api_url="http://localhost:3002", mock_mode=False)
        firecrawl_backend.scrape_url = AsyncMock(
            side_effect=FirecrawlUnavailableError("Firecrawl down")
        )
        
        service = WebScrapingService(primary_backend=firecrawl_backend)
        
        with pytest.raises(FirecrawlUnavailableError):
            await service.scrape_url("http://example.com")

    @pytest.mark.asyncio
    async def test_crawl_site_invalid_url_scheme(self):
        """Test crawl_site with invalid URL scheme."""
        backend = BeautifulSoupBackend(mock_mode=True)
        service = WebScrapingService(primary_backend=backend)
        
        with pytest.raises(ValueError) as exc_info:
            await service.crawl_site("ftp://invalid.com")
        
        assert "Invalid URL scheme" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_structured_data_invalid_schema(self):
        """Test extract_structured_data with invalid schema."""
        backend = FirecrawlBackend(api_url="http://localhost:3002", mock_mode=True)
        service = WebScrapingService(primary_backend=backend)
        
        with pytest.raises(ValueError) as exc_info:
            await service.extract_structured_data("http://example.com", "invalid schema")
        
        assert "Schema must be a dictionary" in str(exc_info.value)
