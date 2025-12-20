import pytest

from services import web_scraping_service as ws


pytestmark = [pytest.mark.unit, pytest.mark.backend_switching, pytest.mark.firecrawl]


class TestBackendSwitching:
    @pytest.mark.asyncio
    async def test_switch_from_firecrawl_to_beautifulsoup(self, mock_firecrawl_backend, mock_beautifulsoup_backend):
        service = ws.WebScrapingService(primary_backend=mock_firecrawl_backend, fallback_backend=mock_beautifulsoup_backend)
        service.switch_backend(mock_beautifulsoup_backend)
        assert service.primary_backend.backend_name == "beautifulsoup"

    def test_switch_backend_preserves_fallback(self, mock_switchable_service, mock_firecrawl_backend):
        mock_switchable_service.switch_backend(mock_firecrawl_backend)
        assert mock_switchable_service.fallback_backend is not None


class TestForceBackendSelection:
    @pytest.mark.asyncio
    async def test_force_backend_firecrawl(self, mock_switchable_service):
        result = await mock_switchable_service.scrape_url("http://example.com", force_backend="firecrawl")
        assert result["backend"] == "firecrawl"

    def test_force_backend_invalid_raises_error(self, mock_switchable_service):
        with pytest.raises(ValueError):
            _ = mock_switchable_service._resolve_backend("invalid")


class TestBackendCapabilities:
    def test_get_backend_info_firecrawl(self, mock_switchable_service):
        info = mock_switchable_service.get_backend_info()
        assert "scrape" in info["capabilities"]
        assert info["fallback_available"] is True
