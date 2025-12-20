import pytest

from services import web_scraping_service as ws


pytestmark = [pytest.mark.unit, pytest.mark.health_check, pytest.mark.firecrawl]


class TestFirecrawlHealthCheck:
    @pytest.mark.asyncio
    async def test_firecrawl_health_check_healthy(self, mock_firecrawl_backend):
        result = await mock_firecrawl_backend.health_check()
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_firecrawl_health_check_degraded(self, mock_degraded_firecrawl_backend):
        result = await mock_degraded_firecrawl_backend.health_check()
        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_firecrawl_health_check_unavailable(self, mock_unhealthy_firecrawl_backend):
        with pytest.raises(ws.FirecrawlUnavailableError):
            await mock_unhealthy_firecrawl_backend.scrape_url("http://example.com")


class TestBeautifulSoupHealthCheck:
    @pytest.mark.asyncio
    async def test_beautifulsoup_health_check_always_healthy(self, mock_beautifulsoup_backend):
        result = await mock_beautifulsoup_backend.health_check()
        assert result["status"] == "healthy"


class TestWebScrapingServiceHealthCheck:
    @pytest.mark.asyncio
    async def test_service_health_check_both_healthy(self, mock_firecrawl_backend, mock_beautifulsoup_backend):
        service = ws.WebScrapingService(primary_backend=mock_firecrawl_backend, fallback_backend=mock_beautifulsoup_backend)
        result = await service.health_check()
        assert result["status"] == "healthy"
        assert "firecrawl" in result["backends"]
        assert "beautifulsoup" in result["backends"]

    @pytest.mark.asyncio
    async def test_service_health_check_primary_unhealthy(self, mock_unhealthy_firecrawl_backend, mock_beautifulsoup_backend):
        service = ws.WebScrapingService(primary_backend=mock_unhealthy_firecrawl_backend, fallback_backend=mock_beautifulsoup_backend)
        result = await service.health_check()
        assert "firecrawl" in result["backends"]
        assert "beautifulsoup" in result["backends"]
        assert result["status"] in {"degraded", "healthy"}
