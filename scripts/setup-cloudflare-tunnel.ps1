# ===========================================
# CLOUDFLARE TUNNEL SETUP FÜR N8N
# ===========================================
# Interaktives Setup-Script für Cloudflare Tunnel
# ===========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Cloudflare Tunnel Setup für n8n" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

# Prüfe ob .env existiert
if (-not (Test-Path ".env")) {
    Write-Host "[FEHLER] .env Datei nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte erstelle eine .env Datei basierend auf .env.example" -ForegroundColor Yellow
    exit 1
}

Write-Host "📋 Anleitung zum Erstellen eines Cloudflare Tunnels" -ForegroundColor Cyan
Write-Host ""
Write-Host "SCHRITT 1: Cloudflare Zero Trust Dashboard öffnen" -ForegroundColor Yellow
Write-Host "  → https://one.dash.cloudflare.com/" -ForegroundColor White
Write-Host ""
Write-Host "SCHRITT 2: Tunnel erstellen" -ForegroundColor Yellow
Write-Host "  1. Navigiere zu: Access → Tunnels" -ForegroundColor White
Write-Host "  2. Klicke: 'Create a tunnel'" -ForegroundColor White
Write-Host "  3. Wähle: 'Cloudflared'" -ForegroundColor White
Write-Host "  4. Name: 'krai-n8n' (oder beliebig)" -ForegroundColor White
Write-Host "  5. KOPIERE das Token (beginnt mit 'eyJ...')" -ForegroundColor White
Write-Host ""
Write-Host "SCHRITT 3: Public Hostname konfigurieren" -ForegroundColor Yellow
Write-Host "  1. Subdomain: dein-name (z.B. 'krai-n8n')" -ForegroundColor White
Write-Host "  2. Domain: Wähle eine Domain ODER nutze *.trycloudflare.com (kostenlos)" -ForegroundColor White
Write-Host "  3. Service Type: HTTP" -ForegroundColor White
Write-Host "  4. URL: krai-n8n-chat-agent:5678" -ForegroundColor White
Write-Host "  5. Speichern" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Frage nach Token
Write-Host "[EINGABE] Bitte füge dein Cloudflare Tunnel Token ein:" -ForegroundColor Yellow
Write-Host "(Das Token beginnt mit 'eyJ...' und ist sehr lang)" -ForegroundColor Gray
Write-Host ""
$tunnelToken = Read-Host "Token"

if ([string]::IsNullOrWhiteSpace($tunnelToken)) {
    Write-Host ""
    Write-Host "[FEHLER] Kein Token eingegeben!" -ForegroundColor Red
    Write-Host "Bitte erstelle zuerst einen Tunnel auf Cloudflare." -ForegroundColor Yellow
    exit 1
}

if (-not $tunnelToken.StartsWith("eyJ")) {
    Write-Host ""
    Write-Host "[WARNUNG] Token sieht nicht korrekt aus!" -ForegroundColor Yellow
    Write-Host "Ein Cloudflare Tunnel Token beginnt normalerweise mit 'eyJ'." -ForegroundColor Gray
    $continue = Read-Host "Trotzdem fortfahren? (j/n)"
    if ($continue -ne "j") {
        exit 0
    }
}

Write-Host ""

# Frage nach Hostname
Write-Host "[EINGABE] Bitte gib deine Tunnel-URL ein:" -ForegroundColor Yellow
Write-Host "(Ohne https://, z.B. 'krai-n8n.trycloudflare.com' oder 'n8n.deine-domain.de')" -ForegroundColor Gray
Write-Host ""
$tunnelHost = Read-Host "URL"

if ([string]::IsNullOrWhiteSpace($tunnelHost)) {
    Write-Host ""
    Write-Host "[FEHLER] Keine URL eingegeben!" -ForegroundColor Red
    exit 1
}

# Entferne https:// falls vorhanden
$tunnelHost = $tunnelHost -replace "^https?://", ""
$tunnelHost = $tunnelHost.TrimEnd('/')

Write-Host ""
Write-Host "[UPDATE] Aktualisiere .env Datei..." -ForegroundColor Yellow

# Lese aktuelle .env
$envContent = Get-Content ".env" -Raw

# Ersetze Token
if ($envContent -match "CLOUDFLARE_TUNNEL_TOKEN=.*") {
    $envContent = $envContent -replace "CLOUDFLARE_TUNNEL_TOKEN=.*", "CLOUDFLARE_TUNNEL_TOKEN=$tunnelToken"
} else {
    $envContent += "`nCLOUDFLARE_TUNNEL_TOKEN=$tunnelToken"
}

# Ersetze Host
if ($envContent -match "N8N_HOST=.*") {
    $envContent = $envContent -replace "N8N_HOST=.*", "N8N_HOST=$tunnelHost"
} else {
    $envContent += "`nN8N_HOST=$tunnelHost"
}

# Ersetze Webhook URL
if ($envContent -match "WEBHOOK_URL=.*") {
    $envContent = $envContent -replace "WEBHOOK_URL=.*", "WEBHOOK_URL=https://$tunnelHost/"
} else {
    $envContent += "`nWEBHOOK_URL=https://$tunnelHost/"
}

# Speichere .env
$envContent | Out-File ".env" -Encoding UTF8 -NoNewline

Write-Host "  ✓ .env aktualisiert" -ForegroundColor Green
Write-Host ""

# Prüfe Docker
Write-Host "[CHECK] Prüfe Docker..." -ForegroundColor Yellow
try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FEHLER] Docker läuft nicht!" -ForegroundColor Red
        Write-Host "Bitte starte Docker Desktop" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  ✓ Docker läuft" -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Docker nicht gefunden!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Starte Container
Write-Host "[START] Starte Container..." -ForegroundColor Yellow
Write-Host ""

# Stoppe alte Container
docker-compose down 2>&1 | Out-Null

# Starte neu
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[FEHLER] Container konnten nicht gestartet werden!" -ForegroundColor Red
    Write-Host "Prüfe: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

# Warte auf Startup
Write-Host "  Warte auf Container-Start..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ Setup abgeschlossen!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "🌐 n8n ist jetzt erreichbar über:" -ForegroundColor Cyan
Write-Host "   https://$tunnelHost" -ForegroundColor White
Write-Host ""

Write-Host "🔗 Webhook URLs:" -ForegroundColor Cyan
Write-Host "   https://$tunnelHost/webhook/..." -ForegroundColor White
Write-Host ""

Write-Host "🔐 Login-Daten:" -ForegroundColor Cyan
Write-Host "   Benutzer: admin" -ForegroundColor White
Write-Host "   Passwort: krai_chat_agent_2024" -ForegroundColor White
Write-Host ""

Write-Host "✅ Vorteile von Cloudflare Tunnel:" -ForegroundColor Cyan
Write-Host "   • SSL-Zertifikat automatisch vertrauenswürdig" -ForegroundColor Green
Write-Host "   • Keine manuelle Zertifikat-Installation nötig" -ForegroundColor Green
Write-Host "   • Microsoft Teams akzeptiert Webhooks sofort" -ForegroundColor Green
Write-Host "   • Von überall erreichbar (auch mobil)" -ForegroundColor Green
Write-Host ""

Write-Host "📊 Container-Status:" -ForegroundColor Cyan
docker-compose ps
Write-Host ""

Write-Host "📝 Nützliche Befehle:" -ForegroundColor Cyan
Write-Host "   Logs anzeigen:     docker logs krai-n8n-chat-agent -f" -ForegroundColor White
Write-Host "   Tunnel-Logs:       docker logs krai-cloudflare-tunnel -f" -ForegroundColor White
Write-Host "   Container stoppen: docker-compose down" -ForegroundColor White
Write-Host "   Neu starten:       docker-compose restart" -ForegroundColor White
Write-Host ""

Write-Host "🎯 Nächste Schritte:" -ForegroundColor Cyan
Write-Host "   1. Öffne https://$tunnelHost im Browser" -ForegroundColor White
Write-Host "   2. Erstelle einen Webhook in n8n" -ForegroundColor White
Write-Host "   3. Nutze die Webhook-URL in Microsoft Teams" -ForegroundColor White
Write-Host ""

Write-Host "📚 Weitere Infos: docs/setup/N8N_CLOUDFLARE_TUNNEL_SETUP.md" -ForegroundColor Green
Write-Host ""
