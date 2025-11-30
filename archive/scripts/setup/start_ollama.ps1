# Start Ollama with optimized settings for 8GB VRAM
# This script loads settings from .env.ai and starts Ollama

Write-Host "Starting Ollama with optimized settings..." -ForegroundColor Cyan

# Load .env.ai if it exists
$envFile = Join-Path $PSScriptRoot "..\\.env.ai"
if (Test-Path $envFile) {
    Write-Host "Loading settings from .env.ai..." -ForegroundColor Yellow
    
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            
            # Only set Ollama-related env vars
            if ($name -like "OLLAMA_*") {
                [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
                Write-Host "  OK: $name = $value" -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "WARNING: .env.ai not found, using defaults" -ForegroundColor Yellow
    # Set defaults
    [System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_CTX", "8192", "Process")
    Write-Host "  OK: OLLAMA_NUM_CTX = 8192 (default)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting Ollama server..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start Ollama
ollama serve
