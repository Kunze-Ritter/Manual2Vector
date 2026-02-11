# KRAI Engine Docker Setup Script (PowerShell)
# Generates all required secrets from .env.example automatically
# For production: Review and customize generated values before deployment
#
# This is the recommended setup script for Windows 10/11 with PowerShell 5+
# For older Windows versions without PowerShell 5+, use setup.bat as fallback

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param(
        [Parameter(Mandatory = $true)][string]$Message
    )
    Write-Host '========================================' -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host '========================================' -ForegroundColor Cyan
    Write-Host ''
}

function Write-Info {
    param(
        [Parameter(Mandatory = $true)][string]$Message
    )
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-WarningMessage {
    param(
        [Parameter(Mandatory = $true)][string]$Message
    )
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-ErrorAndExit {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [int]$Code = 1
    )
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit $Code
}

function Test-RsaExportSupport {
    try {
        $rsa = [System.Security.Cryptography.RSA]::Create(2048)
        try {
            $null = $rsa.ExportPkcs8PrivateKey()
            $null = $rsa.ExportSubjectPublicKeyInfo()
            return $true
        } catch {
            return $false
        } finally {
            $rsa.Dispose()
        }
    } catch {
        return $false
    }
}

function ConvertTo-BigEndianInteger {
    param([byte[]]$LittleEndian)

    if (-not $LittleEndian -or $LittleEndian.Length -eq 0) {
        return [byte[]](0x00)
    }

    $copy = [byte[]]::new($LittleEndian.Length)
    [Array]::Copy($LittleEndian, 0, $copy, 0, $LittleEndian.Length)
    [Array]::Reverse($copy)

    $start = 0
    while (($start -lt $copy.Length - 1) -and $copy[$start] -eq 0) {
        $start++
    }

    if ($start -gt 0) {
        $trimmed = [byte[]]::new($copy.Length - $start)
        [Array]::Copy($copy, $start, $trimmed, 0, $trimmed.Length)
    } else {
        $trimmed = $copy
    }

    if (($trimmed[0] -band 0x80) -ne 0) {
        $prefixed = [byte[]]::new($trimmed.Length + 1)
        $prefixed[0] = 0x00
        [Array]::Copy($trimmed, 0, $prefixed, 1, $trimmed.Length)
        return $prefixed
    }

    return $trimmed
}

function ConvertTo-BigEndianFromInt {
    param([int]$Value)

    if ($Value -eq 0) {
        return [byte[]](0x00)
    }

    $bytes = @()
    $current = [uint32]$Value
    while ($current -gt 0) {
        $bytes = ,([byte]($current -band 0xFF)) + $bytes
        $current = $current -shr 8
    }

    $result = [byte[]]::new($bytes.Count)
    for ($i = 0; $i -lt $bytes.Count; $i++) {
        $result[$i] = $bytes[$i]
    }

    if (($result[0] -band 0x80) -ne 0) {
        $prefixed = [byte[]]::new($result.Length + 1)
        $prefixed[0] = 0x00
        [Array]::Copy($result, 0, $prefixed, 1, $result.Length)
        return $prefixed
    }

    return $result
}

function Join-ByteSegments {
    param([byte[][]]$Segments)

    if (-not $Segments) {
        return [byte[]]::new(0)
    }

    $total = 0
    foreach ($segment in $Segments) {
        if ($segment) {
            $total += $segment.Length
        }
    }

    $result = [byte[]]::new($total)
    $offset = 0
    foreach ($segment in $Segments) {
        if ($segment -and $segment.Length -gt 0) {
            [Array]::Copy($segment, 0, $result, $offset, $segment.Length)
            $offset += $segment.Length
        }
    }

    return $result
}

function New-DerLength {
    param([int]$Length)

    if ($Length -lt 0x80) {
        return [byte[]]([byte]$Length)
    }

    $bytes = @()
    $value = $Length
    while ($value -gt 0) {
        $bytes = ,([byte]($value -band 0xFF)) + $bytes
        $value = $value -shr 8
    }

    $result = [byte[]]::new($bytes.Count + 1)
    $result[0] = 0x80 -bor $bytes.Count
    for ($i = 0; $i -lt $bytes.Count; $i++) {
        $result[$i + 1] = $bytes[$i]
    }

    return $result
}

function New-DerInteger {
    param([byte[]]$LittleEndian)

    $integerBytes = ConvertTo-BigEndianInteger -LittleEndian $LittleEndian
    $lengthBytes = New-DerLength -Length $integerBytes.Length
    $result = [byte[]]::new(1 + $lengthBytes.Length + $integerBytes.Length)
    $result[0] = 0x02
    [Array]::Copy($lengthBytes, 0, $result, 1, $lengthBytes.Length)
    [Array]::Copy($integerBytes, 0, $result, 1 + $lengthBytes.Length, $integerBytes.Length)
    return $result
}

function New-DerIntegerFromInt {
    param([int]$Value)

    $bytes = ConvertTo-BigEndianFromInt -Value $Value
    $lengthBytes = New-DerLength -Length $bytes.Length
    $result = [byte[]]::new(1 + $lengthBytes.Length + $bytes.Length)
    $result[0] = 0x02
    [Array]::Copy($lengthBytes, 0, $result, 1, $lengthBytes.Length)
    [Array]::Copy($bytes, 0, $result, 1 + $lengthBytes.Length, $bytes.Length)
    return $result
}

function New-DerOctetString {
    param([byte[]]$Value)

    $lengthBytes = New-DerLength -Length $Value.Length
    $result = [byte[]]::new(1 + $lengthBytes.Length + $Value.Length)
    $result[0] = 0x04
    [Array]::Copy($lengthBytes, 0, $result, 1, $lengthBytes.Length)
    if ($Value.Length -gt 0) {
        [Array]::Copy($Value, 0, $result, 1 + $lengthBytes.Length, $Value.Length)
    }
    return $result
}

function New-DerBitString {
    param([byte[]]$Value)

    $payload = [byte[]]::new($Value.Length + 1)
    $payload[0] = 0x00
    if ($Value.Length -gt 0) {
        [Array]::Copy($Value, 0, $payload, 1, $Value.Length)
    }

    $lengthBytes = New-DerLength -Length $payload.Length
    $result = [byte[]]::new(1 + $lengthBytes.Length + $payload.Length)
    $result[0] = 0x03
    [Array]::Copy($lengthBytes, 0, $result, 1, $lengthBytes.Length)
    if ($payload.Length -gt 0) {
        [Array]::Copy($payload, 0, $result, 1 + $lengthBytes.Length, $payload.Length)
    }
    return $result
}

function New-DerSequence {
    param([byte[][]]$Elements)

    $payload = Join-ByteSegments -Segments $Elements
    $lengthBytes = New-DerLength -Length $payload.Length
    $result = [byte[]]::new(1 + $lengthBytes.Length + $payload.Length)
    $result[0] = 0x30
    [Array]::Copy($lengthBytes, 0, $result, 1, $lengthBytes.Length)
    if ($payload.Length -gt 0) {
        [Array]::Copy($payload, 0, $result, 1 + $lengthBytes.Length, $payload.Length)
    }
    return $result
}

function ConvertTo-Pkcs8Der {
    param([System.Security.Cryptography.RSAParameters]$Parameters)

    $privateKeySequence = New-DerSequence @(
        (New-DerIntegerFromInt 0),
        (New-DerInteger $Parameters.Modulus),
        (New-DerInteger $Parameters.Exponent),
        (New-DerInteger $Parameters.D),
        (New-DerInteger $Parameters.P),
        (New-DerInteger $Parameters.Q),
        (New-DerInteger $Parameters.DP),
        (New-DerInteger $Parameters.DQ),
        (New-DerInteger $Parameters.InverseQ)
    )

    $algorithmIdentifier = New-DerSequence @(
        [byte[]](0x06,0x09,0x2A,0x86,0x48,0x86,0xF7,0x0D,0x01,0x01,0x01),
        [byte[]](0x05,0x00)
    )

    $version = New-DerIntegerFromInt 0
    $privateKeyOctet = New-DerOctetString $privateKeySequence

    return New-DerSequence @(
        $version,
        $algorithmIdentifier,
        $privateKeyOctet
    )
}

function ConvertTo-SubjectPublicKeyInfoDer {
    param([System.Security.Cryptography.RSAParameters]$Parameters)

    $rsaPublicKey = New-DerSequence @(
        (New-DerInteger $Parameters.Modulus),
        (New-DerInteger $Parameters.Exponent)
    )

    $algorithmIdentifier = New-DerSequence @(
        [byte[]](0x06,0x09,0x2A,0x86,0x48,0x86,0xF7,0x0D,0x01,0x01,0x01),
        [byte[]](0x05,0x00)
    )

    $publicKeyBitString = New-DerBitString $rsaPublicKey

    return New-DerSequence @(
        $algorithmIdentifier,
        $publicKeyBitString
    )
}


function New-RandomSecret {
    param(
        [int]$Length = 32
    )

    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $result = ""
        while ($result.Length -lt $Length) {
            $bytes = New-Object byte[] 48
            $rng.GetBytes($bytes)
            $chunk = [Convert]::ToBase64String($bytes) -replace '[+/=]', ''
            $result += $chunk
        }
        return $result.Substring(0, $Length)
    } finally {
        $rng.Dispose()
    }
}

function Generate-RsaKeys {
    $rsa = [System.Security.Cryptography.RSA]::Create(2048)
    try {
        try {
            $privateBytes = $rsa.ExportPkcs8PrivateKey()
            $publicBytes = $rsa.ExportSubjectPublicKeyInfo()
        } catch {
            $parameters = $rsa.ExportParameters($true)
            $privateBytes = ConvertTo-Pkcs8Der -Parameters $parameters
            $publicBytes = ConvertTo-SubjectPublicKeyInfoDer -Parameters $parameters
        }

        return @{ Private = [Convert]::ToBase64String($privateBytes); Public = [Convert]::ToBase64String($publicBytes) }
    } finally {
        $rsa.Dispose()
    }
}

function Backup-EnvFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = "$Path.bak.$timestamp"
    Copy-Item -LiteralPath $Path -Destination $backupPath -Force
    Write-Info ('📦 Existing .env backed up to {0}' -f $backupPath)
}

function Apply-EnvReplacements {
    param(
        [Parameter(Mandatory = $true)][object]$Lines,
        [Parameter(Mandatory = $true)][hashtable]$Replacements
    )

    if ($Lines -is [System.Collections.IList]) {
        $normalized = @()
        foreach ($item in $Lines) {
            $normalized += [string]$item
        }
        $Lines = $normalized
    } else {
        $Lines = @([string]$Lines)
    }

    $keys = $Replacements.Keys
    for ($i = 0; $i -lt $Lines.Length; $i++) {
        foreach ($key in $keys) {
            if ($Lines[$i] -match "^\s*$key\s*=") {
                $Lines[$i] = "$key=$($Replacements[$key])"
            }
        }
    }

    return ,$Lines
}

function Test-EnvFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    if (-not (Test-Path $Path)) {
        Write-ErrorAndExit ('❌ Error: .env file not found for validation ({0}).' -f $Path) 1
    }

    $content = Get-Content -Path $Path -Encoding UTF8
    $values = @{}

    foreach ($line in $content) {
        if ($line -match '^[\s#]') {
            continue
        }

        if ($line -match '^\s*([^=\s#]+)\s*=\s*(.*)$') {
            $key = $Matches[1].Trim()
            $value = $Matches[2].Trim()
            $values[$key] = $value
        }
    }

    $requiredKeys = @(
        'DATABASE_PASSWORD',
        'OBJECT_STORAGE_SECRET_KEY',
        'DEFAULT_ADMIN_PASSWORD',
        'JWT_PRIVATE_KEY',
        'JWT_PUBLIC_KEY',
        'N8N_DATABASE_PASSWORD',
        'PGADMIN_DEFAULT_PASSWORD',
        'FIRECRAWL_BULL_AUTH_KEY'
    )

    $missing = @()
    foreach ($key in $requiredKeys) {
        if (-not $values.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($values[$key])) {
            $missing += $key
        }
    }

    if ($missing.Count -gt 0) {
        foreach ($key in $missing) {
            Write-Host ("[ERROR] Missing required variable: {0}" -f $key) -ForegroundColor Red
        }
        return $false
    }

    $optionalKeys = @('YOUTUBE_API_KEY', 'CLOUDFLARE_TUNNEL_TOKEN')
    foreach ($optKey in $optionalKeys) {
        if (-not $values.ContainsKey($optKey) -or [string]::IsNullOrWhiteSpace($values[$optKey])) {
            Write-WarningMessage ("⚠️  Optional variable {0} is not set. Update .env if required." -f $optKey)
        }
    }

    return $true
}

try {
    Write-Section '🚀 KRAI Engine Docker Setup'

    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptRoot

    $templatePath = Join-Path $scriptRoot ".env.example"
    $envPath = Join-Path $scriptRoot ".env"

    if (-not (Test-Path $templatePath)) {
        Write-ErrorAndExit ('❌ Error: .env.example not found ({0}).' -f $templatePath) 1
    }

    $psMajor = $PSVersionTable.PSVersion.Major
    if ($psMajor -lt 5) {
        Write-ErrorAndExit ('❌ Error: PowerShell 5.0 or higher is required (detected: {0}).' -f $psMajor) 1
    }

    $supportsNativeRsaExport = Test-RsaExportSupport
    if (-not $supportsNativeRsaExport) {
        Write-WarningMessage 'Compatibility mode: native PKCS8 export unavailable; using managed DER encoder.'
    }

    if (Test-Path $envPath) {
        if ($Force) {
            Backup-EnvFile -Path $envPath
        } else {
            if ($Host.Name -eq "ConsoleHost" -and -not [Console]::IsInputRedirected) {
                $answer = Read-Host '⚠️  .env already exists. Overwrite and create backup? [y/N]:'
                if ($answer -notmatch '^(j|J|y|Y)$') {
                    Write-WarningMessage 'ℹ️  Aborting without modifying .env.'
                    exit 0
                }
                Backup-EnvFile -Path $envPath
            } else {
                Write-ErrorAndExit '❌ Error: .env already exists. Run the script with -Force to overwrite without prompting.' 1
            }
        }
    }

    Write-Info 'Generating cryptographically secure secrets...'

    $secrets = [ordered]@{}
    $secrets.DatabasePassword = New-RandomSecret 32
    $secrets.MinioSecret = New-RandomSecret 32
    $secrets.AdminPassword = New-RandomSecret 32
    $secrets.N8nPassword = New-RandomSecret 32
    $secrets.N8nDbPassword = New-RandomSecret 32
    $secrets.PgadminPassword = New-RandomSecret 32
    $secrets.FirecrawlBullKey = New-RandomSecret 32
    $secrets.TestDatabasePassword = New-RandomSecret 32
    $secrets.TestStorageSecret = New-RandomSecret 32
    $secrets.TestFirecrawlKey = New-RandomSecret 32
    $secrets.TestDatabasePasswordUrl = [System.Uri]::EscapeDataString($secrets.TestDatabasePassword)

    Write-Info 'Generating RSA key pair for JWT...'
    $rsaKeys = Generate-RsaKeys

    $lines = [string[]][System.IO.File]::ReadAllLines($templatePath, [System.Text.Encoding]::UTF8)
    if (-not $lines -or $lines.Length -eq 0) {
        Write-ErrorAndExit '❌ Error: .env.example appears to be empty. Cannot generate .env.' 1
    }
    Write-Info ("Template lines type: {0}" -f $lines.GetType().FullName)
    Write-Info ("Template lines count: {0}" -f $lines.Length)

    $replacements = @{
        "DATABASE_PASSWORD"              = $secrets.DatabasePassword
        "OBJECT_STORAGE_SECRET_KEY"      = $secrets.MinioSecret
        "DEFAULT_ADMIN_PASSWORD"         = $secrets.AdminPassword
        "JWT_PRIVATE_KEY"                = $rsaKeys.Private
        "JWT_PUBLIC_KEY"                 = $rsaKeys.Public
        "PASSWORD_REQUIRE_UPPERCASE"     = "true"
        "PASSWORD_REQUIRE_LOWERCASE"     = "true"
        "PASSWORD_REQUIRE_NUMBER"        = "true"
        "PASSWORD_REQUIRE_SPECIAL"       = "true"
        "PASSWORD_MIN_LENGTH"            = "12"
        "FIRECRAWL_REQUIRE_API_KEY"      = "false"
        "N8N_BASIC_AUTH_PASSWORD"        = $secrets.N8nPassword
        "N8N_DATABASE_PASSWORD"          = $secrets.N8nDbPassword
        "PGADMIN_DEFAULT_PASSWORD"       = $secrets.PgadminPassword
        "FIRECRAWL_BULL_AUTH_KEY"        = $secrets.FirecrawlBullKey
        "TEST_DATABASE_PASSWORD"         = $secrets.TestDatabasePassword
        "TEST_STORAGE_SECRET_KEY"        = $secrets.TestStorageSecret
        "TEST_FIRECRAWL_BULL_AUTH_KEY"   = $secrets.TestFirecrawlKey
    }

    $lines = Apply-EnvReplacements -Lines $lines -Replacements $replacements

    for ($i = 0; $i -lt $lines.Length; $i++) {
        if ($lines[$i] -match "^\s*TEST_DATABASE_URL\s*=") {
            $lines[$i] = "TEST_DATABASE_URL=postgresql://krai_test:$($secrets.TestDatabasePasswordUrl)@postgresql-test:5432/krai_test"
        }
    }

    $requiredPublicUrls = [ordered]@{
        'OBJECT_STORAGE_PUBLIC_URL_DOCUMENTS' = 'http://localhost:9000/documents'
        'OBJECT_STORAGE_PUBLIC_URL_ERROR'     = 'http://localhost:9000/error-images'
        'OBJECT_STORAGE_PUBLIC_URL_PARTS'     = 'http://localhost:9000/parts-images'
    }

    foreach ($publicUrlKey in $requiredPublicUrls.Keys) {
        $present = $false
        foreach ($line in $lines) {
            if ($line -match "^\s*$publicUrlKey\s*=") {
                $present = $true
                break
            }
        }

        if (-not $present) {
            $lines += "{0}={1}" -f $publicUrlKey, $requiredPublicUrls[$publicUrlKey]
        }
    }

    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($envPath, ($lines -join [Environment]::NewLine) + [Environment]::NewLine, $utf8)

    $fileInfo = Get-Item $envPath
    $sizeKb = [Math]::Round($fileInfo.Length / 1KB, 2)
    Write-Info (".env created at {0}" -f $envPath)
    Write-Info ("File size: {0} KB" -f $sizeKb)

    Write-Info '🔍 Validating generated .env file...'
    if (Test-EnvFile -Path $envPath) {
        Write-Host '✅ Validation passed!' -ForegroundColor Green
    } else {
        Write-ErrorAndExit '❌ Validation failed! Please review .env file.' 1
    }

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkCyan
    Write-Host "🔑 GENERATED CREDENTIALS (Keep these secure!)" -ForegroundColor DarkCyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "📊 DATABASE:" -ForegroundColor Green
    Write-Host ("   PostgreSQL Password:     {0}" -f $secrets.DatabasePassword)
    Write-Host ("   n8n Database Password:   {0}" -f $secrets.N8nDbPassword)
    Write-Host ("   Test Database Password:  {0}" -f $secrets.TestDatabasePassword)
    Write-Host ""
    Write-Host "💾 OBJECT STORAGE:" -ForegroundColor Green
    Write-Host ("   MinIO Secret Key:        {0}" -f $secrets.MinioSecret)
    Write-Host ("   Test Storage Key:        {0}" -f $secrets.TestStorageSecret)
    Write-Host ""
    Write-Host "🔐 AUTHENTICATION:" -ForegroundColor Green
    Write-Host ("   Admin Password:          {0}" -f $secrets.AdminPassword)
    Write-Host "   JWT Private Key:         [Generated - see .env]"
    Write-Host "   JWT Public Key:          [Generated - see .env]"
    Write-Host ""
    Write-Host "🐳 DOCKER SERVICES:" -ForegroundColor Green
    Write-Host ("   n8n Password:            {0}" -f $secrets.N8nPassword)
    Write-Host ("   pgAdmin Password:        {0}" -f $secrets.PgadminPassword)
    Write-Host ("   Firecrawl Bull Key:      {0}" -f $secrets.FirecrawlBullKey)
    Write-Host ("   Test Firecrawl Key:      {0}" -f $secrets.TestFirecrawlKey)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "⚠️  IMPORTANT SECURITY NOTES:" -ForegroundColor Yellow
    Write-Host "   - NEVER commit .env to version control (already in .gitignore)"
    Write-Host "   - Store these credentials in a secure password manager"
    Write-Host "   - For production: Review and customize all values in .env"
    Write-Host "   - Rotate secrets regularly (every 90 days recommended)"
    Write-Host ""
    Write-Host "📝 MANUAL CONFIGURATION REQUIRED:" -ForegroundColor Cyan
    Write-Host "   - YOUTUBE_API_KEY: Get from https://console.cloud.google.com/apis/credentials"
    Write-Host "   - CLOUDFLARE_TUNNEL_TOKEN: Get from https://dash.cloudflare.com/"
    Write-Host "   - Review all AI model names in AI SERVICE CONFIGURATION section"
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "📋 NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "   1. Review .env file and customize as needed"
    Write-Host "   2. Start Docker: docker-compose -f docker-compose.simple.yml up -d"
    Write-Host "   3. Check status:  docker-compose -f docker-compose.simple.yml ps"
    Write-Host "   4. View logs:     docker-compose -f docker-compose.simple.yml logs -f"
    Write-Host "   5. Access API:    curl http://localhost:8000/health"
    Write-Host "   6. Access UI:     http://localhost:3000"
    Write-Host ""
    Write-Host "Documentation:" -ForegroundColor Cyan
    Write-Host "   - Full setup guide: DOCKER_SETUP.md"
    Write-Host "   - Deployment guide: DEPLOYMENT.md"
    Write-Host "   - Database schema: DATABASE_SCHEMA.md"
    Write-Host ""
    Write-Host "Setup complete! Your KRAI Engine is ready to start." -ForegroundColor Green

    exit 0

} catch {
    $errorMessage = "[ERROR] {0}" -f $_.Exception.Message
    Write-Host $errorMessage -ForegroundColor Red
    exit 1
}
