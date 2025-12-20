# Web Scraping Service Test Suite

## Überblick

Tests für `WebScrapingService`, `FirecrawlBackend` und `BeautifulSoupBackend` inklusive Proxy, Timeout/Retry, Health-Checks, Backend-Switching, Integration und Performance.

## Test-Dateien

- `test_web_scraping_service.py` – Basis/Service-Tests
- `test_web_scraping_proxy.py` – Proxy-Konfiguration & Auth
- `test_web_scraping_timeout_retry.py` – Timeout-Handling & Retries
- `test_web_scraping_health_checks.py` – Health-Checks
- `test_web_scraping_backend_switching.py` – Backend-Switching & Force-Backend
- `test_web_scraping_integration.py` – Integration mit realem Firecrawl
- `test_web_scraping_performance.py` – Performance-Stubs (`@pytest.mark.slow`)
- `test_fallback_behavior.py` – Fallback-Verhalten

## Ausführung

- Alle Services: `pytest backend/tests/services -v`
- Nur Unit: `pytest backend/tests/services -m "unit and not integration and not slow" -v`
- Proxy: `pytest backend/tests/services -m proxy -v`
- Timeout/Retry: `pytest backend/tests/services -m "timeout or retry" -v`
- Health: `pytest backend/tests/services -m health_check -v`
- Backend Switching: `pytest backend/tests/services -m backend_switching -v`
- Integration (Firecrawl laufend): `pytest backend/tests/services/test_web_scraping_integration.py -m integration -v`
- Performance (langsam): `pytest backend/tests/services/test_web_scraping_performance.py -m slow -v`

## Fixtures (conftest.py)

- `mock_firecrawl_backend`, `mock_beautifulsoup_backend`
- `mock_proxy_config`, `mock_proxy_firecrawl_backend`, `mock_proxy_error`
- `mock_timeout_firecrawl_backend`, `mock_timeout_config`, `mock_slow_response`
- `mock_unhealthy_firecrawl_backend`, `mock_degraded_firecrawl_backend`, `mock_health_check_response`
- `real_firecrawl_service`, `integration_test_urls`, `firecrawl_service_available`
- `mock_switchable_service`, `mock_backend_switch_logger`
- `performance_metrics`, `mock_concurrent_requests`
- `mock_partial_failure_backend`, `mock_rate_limited_backend`, `mock_circuit_breaker`

## Marker

Registriert in `pytest.ini`: `unit`, `integration`, `firecrawl`, `fallback`, `proxy`, `timeout`, `retry`, `health_check`, `backend_switching`, `performance`, `slow`.

## Umgebungsvariablen

```bash
SCRAPING_BACKEND=firecrawl|beautifulsoup
SCRAPING_MOCK_MODE=false
FIRECRAWL_API_URL=http://localhost:9004
FIRECRAWL_PROXY_SERVER=http://proxy.example.com:8080
FIRECRAWL_PROXY_USERNAME=user
FIRECRAWL_PROXY_PASSWORD=pass
```

## Docker Compose (Integration)

Firecrawl starten: `docker-compose -f docker-compose.with-firecrawl.yml up -d`  
Health-Check: `curl http://localhost:9004/health`

## Troubleshooting

- Integration schlägt fehl: Firecrawl-Service prüfen (Compose/Health).
- Timeout-Tests: ggf. Timeouts erhöhen oder `-m "not slow"` nutzen.
- Proxy-Tests: Umgebungsvariablen setzen oder Mocks verwenden.
