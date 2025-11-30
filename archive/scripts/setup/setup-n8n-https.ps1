# ===========================================
# N8N LOKALES HTTPS SETUP
# ===========================================
# Erstellt SSL-Zertifikate und startet n8n mit lokalem HTTPS
# ===========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  n8n mit lokalem HTTPS einrichten" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

# Schritt 1: SSL-Zertifikat erstellen
Write-Host "[SCHRITT 1/4] SSL-Zertifikat erstellen..." -ForegroundColor Yellow
Write-Host ""

$sslDir = Join-Path $projectRoot "nginx\ssl"
$certPath = Join-Path $sslDir "localhost.crt"
$keyPath = Join-Path $sslDir "localhost.key"

if ((Test-Path $certPath) -and (Test-Path $keyPath)) {
    Write-Host "  ✓ Zertifikat existiert bereits" -ForegroundColor Green
    $recreate = Read-Host "  Neues Zertifikat erstellen? (j/n)"
    if ($recreate -eq "j") {
        & "$scriptPath\generate-ssl-cert.ps1"
    }
} else {
    & "$scriptPath\generate-ssl-cert.ps1"
}

if (-not ((Test-Path $certPath) -and (Test-Path $keyPath))) {
    Write-Host ""
    Write-Host "[FEHLER] Zertifikat konnte nicht erstellt werden!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Schritt 2: Zertifikat im Windows Trust Store installieren (optional)
Write-Host "[SCHRITT 2/4] Zertifikat im Windows Trust Store installieren..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Dies ist WICHTIG für Microsoft Teams Integration!" -ForegroundColor Yellow
Write-Host "  Ohne vertrauenswürdiges Zertifikat wird Teams die Verbindung ablehnen." -ForegroundColor Yellow
Write-Host ""

$install = Read-Host "  Zertifikat jetzt installieren? (j/n)"

if ($install -eq "j") {
    Write-Host ""
    Write-Host "  Installiere Zertifikat..." -ForegroundColor Yellow
    
    try {
        # Importiere Zertifikat in Trusted Root Certification Authorities
        $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certPath)
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
        $store.Open("ReadWrite")
        $store.Add($cert)
        $store.Close()
        
        Write-Host "  ✓ Zertifikat erfolgreich installiert!" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Das Zertifikat wurde im 'Vertrauenswürdige Stammzertifizierungsstellen'-Store installiert." -ForegroundColor White
        Write-Host "  Browser und Microsoft Teams werden localhost nun als vertrauenswürdig akzeptieren." -ForegroundColor White
    } catch {
        Write-Host "  ✗ Fehler beim Installieren: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Alternative: Manuelle Installation" -ForegroundColor Yellow
        Write-Host "  1. Rechtsklick auf: $certPath" -ForegroundColor White
        Write-Host "  2. 'Zertifikat installieren...'" -ForegroundColor White
        Write-Host "  3. Speicherort: 'Aktueller Benutzer'" -ForegroundColor White
        Write-Host "  4. 'Alle Zertifikate in folgendem Speicher' -> 'Vertrauenswürdige Stammzertifizierungsstellen'" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "  ⚠️  Zertifikat wurde NICHT installiert" -ForegroundColor Yellow
    Write-Host "  Browser werden eine Sicherheitswarnung anzeigen." -ForegroundColor Yellow
    Write-Host "  Microsoft Teams wird die Verbindung ablehnen." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Um später zu installieren:" -ForegroundColor Cyan
    Write-Host "  1. Rechtsklick auf: $certPath" -ForegroundColor White
    Write-Host "  2. 'Zertifikat installieren...'" -ForegroundColor White
    Write-Host "  3. Speicherort: 'Aktueller Benutzer'" -ForegroundColor White
    Write-Host "  4. 'Alle Zertifikate in folgendem Speicher' -> 'Vertrauenswürdige Stammzertifizierungsstellen'" -ForegroundColor White
}

Write-Host ""

# Schritt 3: Docker-Container starten
Write-Host "[SCHRITT 3/4] Docker-Container starten..." -ForegroundColor Yellow
Write-Host ""

# Prüfe ob Docker läuft
try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FEHLER] Docker läuft nicht!" -ForegroundColor Red
        Write-Host "Bitte starte Docker Desktop" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[FEHLER] Docker nicht gefunden!" -ForegroundColor Red
    exit 1
}

# Stoppe alte Container
Write-Host "  Stoppe alte Container..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null

# Starte Container
Write-Host "  Starte Container..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[FEHLER] Container konnten nicht gestartet werden!" -ForegroundColor Red
    Write-Host "Prüfe Logs: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

# Warte kurz auf Startup
Write-Host "  Warte auf Container-Start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""

# Schritt 4: Verbindung testen
Write-Host "[SCHRITT 4/4] Verbindung testen..." -ForegroundColor Yellow
Write-Host ""

try {
    # Test HTTPS-Verbindung (ignoriere SSL-Warnung für selbst-signierte Zertifikate)
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
    $response = Invoke-WebRequest -Uri "https://localhost" -TimeoutSec 10 -UseBasicParsing
    
    if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 401) {
        Write-Host "  ✓ HTTPS-Verbindung erfolgreich!" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️  HTTPS-Verbindung konnte nicht getestet werden" -ForegroundColor Yellow
    Write-Host "  Dies kann normal sein, wenn n8n noch startet..." -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ Setup abgeschlossen!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "🌐 n8n Interface:" -ForegroundColor Cyan
Write-Host "   https://localhost" -ForegroundColor White
Write-Host ""

Write-Host "🔗 Webhook URLs:" -ForegroundColor Cyan
Write-Host "   https://localhost/webhook/..." -ForegroundColor White
Write-Host ""

Write-Host "🔐 Login-Daten:" -ForegroundColor Cyan
Write-Host "   Benutzer: admin" -ForegroundColor White
Write-Host "   Passwort: krai_chat_agent_2024" -ForegroundColor White
Write-Host ""

Write-Host "📊 Container-Status:" -ForegroundColor Cyan
docker-compose ps
Write-Host ""

Write-Host "📝 Nützliche Befehle:" -ForegroundColor Cyan
Write-Host "   Logs anzeigen:    docker logs krai-n8n-chat-agent -f" -ForegroundColor White
Write-Host "   Nginx logs:       docker logs krai-nginx-ssl -f" -ForegroundColor White
Write-Host "   Container stoppen: docker-compose down" -ForegroundColor White
Write-Host "   Neu starten:      docker-compose restart" -ForegroundColor White
Write-Host ""

if ($install -ne "j") {
    Write-Host "⚠️  WICHTIG für Microsoft Teams:" -ForegroundColor Yellow
    Write-Host "   Installiere das Zertifikat im Windows Trust Store!" -ForegroundColor Yellow
    Write-Host "   Pfad: $certPath" -ForegroundColor White
    Write-Host ""
}

Write-Host "📚 Weitere Infos:" -ForegroundColor Cyan
Write-Host "   docs/setup/N8N_HTTPS_LOCAL_SETUP.md" -ForegroundColor White
Write-Host ""
