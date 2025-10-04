# ===========================================
# SSL ZERTIFIKAT GENERATOR FÜR LOCALHOST
# ===========================================
# Erstellt ein selbst-signiertes SSL-Zertifikat für lokales HTTPS
# ===========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SSL-Zertifikat für localhost erstellen" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Erstelle nginx/ssl Verzeichnis falls nicht vorhanden
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$sslDir = Join-Path $projectRoot "nginx\ssl"

if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Path $sslDir -Force | Out-Null
    Write-Host "[OK] SSL-Verzeichnis erstellt: $sslDir" -ForegroundColor Green
} else {
    Write-Host "[OK] SSL-Verzeichnis existiert: $sslDir" -ForegroundColor Green
}

# Prüfe ob OpenSSL verfügbar ist
Write-Host ""
Write-Host "[CHECK] Prüfe OpenSSL..." -ForegroundColor Yellow

$opensslPath = $null

# Versuche OpenSSL zu finden
$possiblePaths = @(
    "C:\Program Files\Git\usr\bin\openssl.exe",
    "C:\Program Files (x86)\Git\usr\bin\openssl.exe",
    "C:\OpenSSL-Win64\bin\openssl.exe",
    "C:\Program Files\OpenSSL-Win64\bin\openssl.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $opensslPath = $path
        break
    }
}

# Prüfe auch im PATH
if (-not $opensslPath) {
    try {
        $opensslCheck = Get-Command openssl -ErrorAction Stop
        $opensslPath = $opensslCheck.Source
    } catch {
        # OpenSSL nicht im PATH gefunden
    }
}

if (-not $opensslPath) {
    Write-Host "[INFO] OpenSSL nicht gefunden. Nutze Docker-basierte Lösung..." -ForegroundColor Yellow
    Write-Host ""
    
    # Erstelle Zertifikat mit Docker
    Write-Host "[CREATE] Erstelle Zertifikat mit Docker..." -ForegroundColor Yellow
    
    $certPath = Join-Path $sslDir "localhost.crt"
    $keyPath = Join-Path $sslDir "localhost.key"
    
    # Erstelle OpenSSL-Konfigurationsdatei
    $opensslConf = @"
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
C = DE
ST = Germany
L = Local
O = KRAI Development
OU = Development
CN = localhost

[v3_req]
subjectAltName = @alt_names
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
"@
    
    $confPath = Join-Path $sslDir "openssl.cnf"
    $opensslConf | Out-File -FilePath $confPath -Encoding ASCII
    
    # Erstelle Zertifikat mit Docker
    docker run --rm -v "${sslDir}:/ssl" alpine/openssl req `
        -x509 `
        -nodes `
        -days 365 `
        -newkey rsa:2048 `
        -keyout /ssl/localhost.key `
        -out /ssl/localhost.crt `
        -config /ssl/openssl.cnf
    
    # Lösche Konfigurationsdatei
    Remove-Item $confPath -Force
    
} else {
    Write-Host "[OK] OpenSSL gefunden: $opensslPath" -ForegroundColor Green
    Write-Host ""
    
    # Erstelle Zertifikat mit lokalem OpenSSL
    Write-Host "[CREATE] Erstelle Zertifikat..." -ForegroundColor Yellow
    
    $certPath = Join-Path $sslDir "localhost.crt"
    $keyPath = Join-Path $sslDir "localhost.key"
    
    # Erstelle OpenSSL-Konfigurationsdatei
    $opensslConf = @"
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
C = DE
ST = Germany
L = Local
O = KRAI Development
OU = Development
CN = localhost

[v3_req]
subjectAltName = @alt_names
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
"@
    
    $confPath = Join-Path $sslDir "openssl.cnf"
    $opensslConf | Out-File -FilePath $confPath -Encoding ASCII
    
    # Generiere Zertifikat
    & $opensslPath req -x509 -nodes -days 365 -newkey rsa:2048 `
        -keyout $keyPath `
        -out $certPath `
        -config $confPath
    
    # Lösche Konfigurationsdatei
    Remove-Item $confPath -Force
}

# Prüfe ob Zertifikat erstellt wurde
if ((Test-Path $certPath) -and (Test-Path $keyPath)) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✓ Zertifikat erfolgreich erstellt!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📄 Zertifikat: $certPath" -ForegroundColor White
    Write-Host "🔑 Private Key: $keyPath" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  WICHTIG: Selbst-signierte Zertifikate" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Browser werden eine Warnung anzeigen, da das Zertifikat" -ForegroundColor White
    Write-Host "nicht von einer vertrauenswürdigen CA signiert ist." -ForegroundColor White
    Write-Host ""
    Write-Host "Um die Warnung zu vermeiden:" -ForegroundColor Cyan
    Write-Host "1. Chrome/Edge: Klicke 'Erweitert' -> 'Weiter zu localhost'" -ForegroundColor White
    Write-Host "2. ODER: Installiere das Zertifikat im Windows Trust Store" -ForegroundColor White
    Write-Host "   (Rechtsklick auf .crt -> 'Zertifikat installieren')" -ForegroundColor White
    Write-Host ""
    Write-Host "Microsoft Teams benötigt ein vertrauenswürdiges Zertifikat!" -ForegroundColor Yellow
    Write-Host "Für Teams-Integration installiere das Zertifikat im Trust Store." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📚 Siehe: docs/setup/N8N_HTTPS_LOCAL_SETUP.md" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ✗ Fehler beim Erstellen!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Bitte prüfe:" -ForegroundColor Yellow
    Write-Host "- Docker läuft (für Docker-basierte Erstellung)" -ForegroundColor White
    Write-Host "- Schreibrechte für $sslDir" -ForegroundColor White
    Write-Host ""
    exit 1
}
