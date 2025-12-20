import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from services import web_scraping_service as ws


pytestmark = [pytest.mark.unit, pytest.mark.firecrawl, pytest.mark.timeout, pytest.mark.retry]


class TestFirecrawlTimeoutHandling:
    @pytest.mark.asyncio
    async def test_firecrawl_scrape_timeout_single_attempt(self, mock_timeout_firecrawl_backend):
        result = await mock_timeout_firecrawl_backend.scrape_url("http://example.com")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_firecrawl_crawl_timeout_during_polling(self, mock_timeout_firecrawl_backend):
        mock_timeout_firecrawl_backend._client.start_crawl.side_effect = asyncio.TimeoutError("start timeout")
        result = await mock_timeout_firecrawl_backend.crawl_site("http://example.com")
        assert result["success"] is False


class TestFirecrawlRetryMechanisms:
    @pytest.mark.asyncio
    async def test_firecrawl_retry_on_timeout(self):
        backend = ws.FirecrawlBackend(api_url="http://localhost:3002", retries=2, mock_mode=False)
        backend._client = MagicMock()
        backend._client.scrape = AsyncMock(
            side_effect=[asyncio.TimeoutError("t1"), {"data": {"markdown": "ok"}}]
        )
        result = await backend.scrape_url("http://example.com")
        assert result["success"] is True


class TestBeautifulSoupTimeoutHandling:
    @pytest.mark.asyncio
    async def test_beautifulsoup_scrape_timeout(self):
        backend = ws.BeautifulSoupBackend(timeout=0.001, mock_mode=False)
        with pytest.raises(Exception):
            await backend.scrape_url("http://10.255.255.1")  # unroutable to force timeout


class TestWebScrapingServiceTimeoutFallback:
    @pytest.mark.asyncio
    async def test_service_timeout_triggers_fallback(self, mock_beautifulsoup_backend):
        failing = MagicMock()
        failing.backend_name = "firecrawl"
        failing.scrape_url = AsyncMock(side_effect=ws.FirecrawlUnavailableError("timeout"))
        service = ws.WebScrapingService(primary_backend=failing, fallback_backend=mock_beautifulsoup_backend)
        result = await service.scrape_url("http://example.com")
        assert result["backend"] == "beautifulsoup"
