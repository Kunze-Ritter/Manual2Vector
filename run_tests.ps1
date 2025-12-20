# Quick Test Runner for KRAI Integration Tests
# Einfaches Script zum schnellen Ausführen von Tests

param(
    [Parameter(Position=0)]
    [ValidateSet("all", "link", "product", "fast", "no-firecrawl", "help")]
    [string]$TestType = "help"
)

# Activate virtual environment if exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
}

Write-Host "=== KRAI Integration Tests ===" -ForegroundColor Cyan
Write-Host ""

switch ($TestType) {
    "all" {
        Write-Host "Running ALL integration tests..." -ForegroundColor Yellow
        python -m pytest backend/tests/integration/ -v -m integration
    }
    "link" {
        Write-Host "Running LinkEnrichmentService tests..." -ForegroundColor Yellow
        python -m pytest backend/tests/integration/test_link_enrichment_e2e.py backend/tests/integration/test_link_enrichment_error_handling.py -v
    }
    "product" {
        Write-Host "Running ProductResearcher tests..." -ForegroundColor Yellow
        python -m pytest backend/tests/integration/test_product_researcher_real.py -v
    }
    "fast" {
        Write-Host "Running fast tests (excluding slow)..." -ForegroundColor Yellow
        python -m pytest backend/tests/integration/ -v -m "integration and not slow"
    }
    "no-firecrawl" {
        Write-Host "Running tests without Firecrawl (BeautifulSoup only)..." -ForegroundColor Yellow
        python -m pytest backend/tests/integration/ -v -m "integration and not firecrawl"
    }
    "help" {
        Write-Host "Usage: .\run_tests.ps1 [test-type]" -ForegroundColor White
        Write-Host ""
        Write-Host "Available test types:" -ForegroundColor Cyan
        Write-Host "  all          - Run all integration tests" -ForegroundColor White
        Write-Host "  link         - Run LinkEnrichmentService tests only" -ForegroundColor White
        Write-Host "  product      - Run ProductResearcher tests only" -ForegroundColor White
        Write-Host "  fast         - Run fast tests (exclude slow)" -ForegroundColor White
        Write-Host "  no-firecrawl - Run without Firecrawl (BeautifulSoup)" -ForegroundColor White
        Write-Host "  help         - Show this help message" -ForegroundColor White
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Cyan
        Write-Host "  .\run_tests.ps1 all" -ForegroundColor Gray
        Write-Host "  .\run_tests.ps1 link" -ForegroundColor Gray
        Write-Host "  .\run_tests.ps1 fast" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Direct pytest commands:" -ForegroundColor Cyan
        Write-Host "  python -m pytest backend/tests/integration/ -v -m integration" -ForegroundColor Gray
    }
}
