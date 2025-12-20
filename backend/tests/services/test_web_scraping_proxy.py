import pytest


pytestmark = [pytest.mark.unit, pytest.mark.proxy, pytest.mark.firecrawl]


class TestFirecrawlProxyConfiguration:
    @pytest.mark.asyncio
    async def test_firecrawl_with_proxy_server(self, mock_proxy_firecrawl_backend, mock_proxy_config):
        assert mock_proxy_firecrawl_backend.proxy == mock_proxy_config

    @pytest.mark.asyncio
    async def test_firecrawl_with_proxy_authentication(self, mock_proxy_firecrawl_backend, mock_proxy_config):
        assert mock_proxy_firecrawl_backend.proxy.get("username") == mock_proxy_config["username"]


class TestBeautifulSoupProxyConfiguration:
    def test_beautifulsoup_with_proxy_not_supported(self, mock_beautifulsoup_backend):
        assert not getattr(mock_beautifulsoup_backend, "proxy", {})


class TestWebScrapingServiceProxyFallback:
    @pytest.mark.asyncio
    async def test_service_proxy_error_triggers_fallback(self, mock_switchable_service, mock_proxy_error):
        mock_switchable_service.primary_backend.scrape_url.side_effect = mock_proxy_error
        result = await mock_switchable_service.scrape_url("http://example.com")
        assert result["backend"] == "beautifulsoup"


class TestProxyFactoryConfiguration:
    def test_create_service_with_proxy_env_vars(self, monkeypatch):
        monkeypatch.setenv("SCRAPING_BACKEND", "firecrawl")
        monkeypatch.setenv("FIRECRAWL_PROXY_SERVER", "http://proxy.example.com:8080")
        monkeypatch.setenv("FIRECRAWL_PROXY_USERNAME", "user")
        monkeypatch.setenv("FIRECRAWL_PROXY_PASSWORD", "pass")
        from services.web_scraping_service import create_web_scraping_service

        service = create_web_scraping_service()
        assert service.primary_backend.proxy["server"] == "http://proxy.example.com:8080"
