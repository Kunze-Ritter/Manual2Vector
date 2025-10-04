# ===========================================
# KRAI N8N HTTPS STARTUP SCRIPT
# ===========================================
# Startet n8n mit Cloudflare Tunnel für HTTPS-Zugriff
# Erforderlich für Microsoft Teams Chat-Trigger
# ===========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  KRAI N8N mit HTTPS starten" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob .env existiert
if (-not (Test-Path ".env")) {
    Write-Host "[FEHLER] .env Datei nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte erstelle eine .env Datei basierend auf .env.example" -ForegroundColor Yellow
    exit 1
}

# Prüfe ob CLOUDFLARE_TUNNEL_TOKEN gesetzt ist
$envContent = Get-Content ".env" -Raw
if ($envContent -match "CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token_here" -or $envContent -notmatch "CLOUDFLARE_TUNNEL_TOKEN=eyJ") {
    Write-Host "[WARNUNG] Cloudflare Tunnel Token nicht konfiguriert!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Schritte zum Einrichten:" -ForegroundColor Cyan
    Write-Host "1. Gehe zu: https://one.dash.cloudflare.com/" -ForegroundColor White
    Write-Host "2. Erstelle einen Tunnel unter 'Access' -> 'Tunnels'" -ForegroundColor White
    Write-Host "3. Kopiere den Tunnel-Token" -ForegroundColor White
    Write-Host "4. Trage ihn in die .env Datei ein: CLOUDFLARE_TUNNEL_TOKEN=..." -ForegroundColor White
    Write-Host ""
    Write-Host "Siehe: docs/setup/N8N_HTTPS_SETUP.md für Details" -ForegroundColor Green
    Write-Host ""
    
    $continue = Read-Host "Trotzdem fortfahren (nur HTTP)? (j/n)"
    if ($continue -ne "j") {
        exit 0
    }
}

# Prüfe ob Docker läuft
Write-Host "[CHECK] Prüfe Docker-Status..." -ForegroundColor Yellow
try {
    $dockerCheck = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FEHLER] Docker läuft nicht!" -ForegroundColor Red
        Write-Host "Bitte starte Docker Desktop" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[OK] Docker läuft" -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Docker nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte installiere Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Wechsle ins Hauptverzeichnis
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $scriptPath)

Write-Host ""
Write-Host "[START] Starte n8n mit HTTPS..." -ForegroundColor Yellow

# Stoppe alte Container
Write-Host "[CLEANUP] Stoppe alte Container..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null

# Starte Container
Write-Host "[DOCKER] Starte Container..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✓ N8N erfolgreich gestartet!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Lese Konfiguration
    $n8nHost = ""
    $n8nProtocol = "http"
    
    if ($envContent -match "N8N_HOST=([^\r\n]+)") {
        $n8nHost = $matches[1]
    }
    if ($envContent -match "N8N_PROTOCOL=([^\r\n]+)") {
        $n8nProtocol = $matches[1]
    }
    
    if ($n8nProtocol -eq "https" -and $n8nHost -and $n8nHost -ne "localhost") {
        Write-Host "🌐 n8n Interface (HTTPS):" -ForegroundColor Cyan
        Write-Host "   https://$n8nHost" -ForegroundColor White
        Write-Host ""
        Write-Host "🔗 Webhook URL:" -ForegroundColor Cyan
        Write-Host "   https://$n8nHost/webhook/..." -ForegroundColor White
    } else {
        Write-Host "🌐 n8n Interface (lokal):" -ForegroundColor Cyan
        Write-Host "   http://localhost:5678" -ForegroundColor White
        Write-Host ""
        Write-Host "⚠️  HTTPS ist nicht konfiguriert!" -ForegroundColor Yellow
        Write-Host "   Für Microsoft Teams wird HTTPS benötigt." -ForegroundColor Yellow
        Write-Host "   Siehe: docs/setup/N8N_HTTPS_SETUP.md" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "🔐 Login-Daten:" -ForegroundColor Cyan
    Write-Host "   Benutzer: admin" -ForegroundColor White
    Write-Host "   Passwort: krai_chat_agent_2024" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Container-Status:" -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host "📝 Logs anzeigen:" -ForegroundColor Cyan
    Write-Host "   docker logs krai-n8n-chat-agent -f" -ForegroundColor White
    if ($n8nProtocol -eq "https") {
        Write-Host "   docker logs krai-cloudflare-tunnel -f" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "🛑 Stoppen:" -ForegroundColor Cyan
    Write-Host "   docker-compose down" -ForegroundColor White
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ✗ Fehler beim Starten!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Logs anzeigen:" -ForegroundColor Yellow
    Write-Host "  docker logs krai-n8n-chat-agent" -ForegroundColor White
    Write-Host ""
    exit 1
}
