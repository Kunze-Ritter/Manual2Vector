import pytest

from services import web_scraping_service as ws


pytestmark = [pytest.mark.integration, pytest.mark.firecrawl]


@pytest.fixture
def real_service(real_firecrawl_service):
    """Use real Firecrawl backend with BeautifulSoup fallback for integration tests."""
    bs = ws.BeautifulSoupBackend(mock_mode=False)
    return ws.WebScrapingService(primary_backend=real_firecrawl_service, fallback_backend=bs)


class TestFirecrawlIntegrationScraping:
    @pytest.mark.asyncio
    async def test_real_firecrawl_scrape_url(self, real_service, integration_test_urls):
        result = await real_service.scrape_url(integration_test_urls["example"])
        assert result["success"] is True
        assert result["backend"] == "firecrawl"


class TestFirecrawlIntegrationHealthCheck:
    @pytest.mark.asyncio
    async def test_real_firecrawl_health_check(self, real_firecrawl_service):
        result = await real_firecrawl_service.health_check()
        assert result["backend"] == "firecrawl"
        assert result["status"] in {"healthy", "mock"}
