# KRAI Integration Tests Setup Script
# Richtet die Test-Umgebung ein und fuehrt Tests aus

Write-Host "=== KRAI Integration Tests Setup ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python Installation
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK Python found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "  ERROR Python not found! Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# 2. Check Virtual Environment
Write-Host "[2/5] Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "  OK Using existing .venv" -ForegroundColor Green
    $venvPath = ".venv"
}
elseif (Test-Path "venv") {
    Write-Host "  OK Using existing venv" -ForegroundColor Green
    $venvPath = "venv"
}
else {
    Write-Host "  Creating new .venv..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "  OK Virtual environment created" -ForegroundColor Green
    $venvPath = ".venv"
}

# 3. Activate Virtual Environment
Write-Host "[3/5] Activating virtual environment..." -ForegroundColor Yellow
& ".\$venvPath\Scripts\Activate.ps1"
Write-Host "  OK Virtual environment activated" -ForegroundColor Green

# 4. Install/Upgrade Dependencies
Write-Host "[4/5] Installing test dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
python -m pip install pytest pytest-asyncio pytest-benchmark --quiet
python -m pip install -r requirements.txt --quiet

# Check optional dependencies
Write-Host "  Checking optional dependencies..." -ForegroundColor Yellow
try {
    python -c "import firecrawl" 2>$null
    Write-Host "  OK Firecrawl SDK installed" -ForegroundColor Green
}
catch {
    Write-Host "  WARNING Firecrawl SDK not installed (optional)" -ForegroundColor DarkYellow
    Write-Host "    Install with: pip install firecrawl-py" -ForegroundColor DarkGray
}

try {
    python -c "import tavily" 2>$null
    Write-Host "  OK Tavily SDK installed" -ForegroundColor Green
}
catch {
    Write-Host "  WARNING Tavily SDK not installed (optional)" -ForegroundColor DarkYellow
    Write-Host "    Install with: pip install tavily-python" -ForegroundColor DarkGray
}

# 5. Check Environment Configuration
Write-Host "[5/5] Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env.test") {
    Write-Host "  OK .env.test found" -ForegroundColor Green
}
else {
    Write-Host "  WARNING .env.test not found" -ForegroundColor DarkYellow
    if (Test-Path ".env") {
        Write-Host "  Using .env instead" -ForegroundColor DarkYellow
    }
    else {
        Write-Host "  WARNING No environment file found!" -ForegroundColor DarkYellow
        Write-Host "    Create .env.test with required variables" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""

# Show available test commands
Write-Host "Available Test Commands:" -ForegroundColor Cyan
Write-Host "  1. All integration tests:" -ForegroundColor White
Write-Host "     python -m pytest backend/tests/integration/ -v -m integration" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. LinkEnrichmentService E2E:" -ForegroundColor White
Write-Host "     python -m pytest backend/tests/integration/test_link_enrichment_e2e.py -v" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. ProductResearcher integration:" -ForegroundColor White
Write-Host "     python -m pytest backend/tests/integration/test_product_researcher_real.py -v" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Without Firecrawl (BeautifulSoup only):" -ForegroundColor White
Write-Host "     python -m pytest backend/tests/integration/ -v -m 'integration and not firecrawl'" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Fast tests only (exclude slow):" -ForegroundColor White
Write-Host "     python -m pytest backend/tests/integration/ -v -m 'integration and not slow'" -ForegroundColor Gray
Write-Host ""

# Ask user what to run
Write-Host "What would you like to do?" -ForegroundColor Cyan
Write-Host "  [1] Run all integration tests" -ForegroundColor White
Write-Host "  [2] Run LinkEnrichmentService E2E tests" -ForegroundColor White
Write-Host "  [3] Run ProductResearcher integration tests" -ForegroundColor White
Write-Host "  [4] Run tests without Firecrawl" -ForegroundColor White
Write-Host "  [5] Run fast tests only" -ForegroundColor White
Write-Host "  [6] Exit (just setup, do not run tests)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Running all integration tests..." -ForegroundColor Cyan
        python -m pytest backend/tests/integration/ -v -m integration
    }
    "2" {
        Write-Host ""
        Write-Host "Running LinkEnrichmentService E2E tests..." -ForegroundColor Cyan
        python -m pytest backend/tests/integration/test_link_enrichment_e2e.py -v
    }
    "3" {
        Write-Host ""
        Write-Host "Running ProductResearcher integration tests..." -ForegroundColor Cyan
        python -m pytest backend/tests/integration/test_product_researcher_real.py -v
    }
    "4" {
        Write-Host ""
        Write-Host "Running tests without Firecrawl..." -ForegroundColor Cyan
        python -m pytest backend/tests/integration/ -v -m "integration and not firecrawl"
    }
    "5" {
        Write-Host ""
        Write-Host "Running fast tests only..." -ForegroundColor Cyan
        python -m pytest backend/tests/integration/ -v -m "integration and not slow"
    }
    "6" {
        Write-Host ""
        Write-Host "Setup complete. You can run tests manually." -ForegroundColor Green
        Write-Host "Virtual environment is activated." -ForegroundColor Green
    }
    default {
        Write-Host ""
        Write-Host "Invalid choice. Setup complete." -ForegroundColor Yellow
        Write-Host "Run tests manually using the commands above." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Note: Virtual environment is now active in this PowerShell session." -ForegroundColor DarkYellow
Write-Host "To deactivate, run: deactivate" -ForegroundColor DarkGray
