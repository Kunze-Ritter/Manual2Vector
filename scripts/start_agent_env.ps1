Param(
    [switch]$SkipAPI,
    [switch]$SkipOpenWebUI,
    [switch]$ForceRestartOpenWebUI
)

$ErrorActionPreference = "Stop"

function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor Cyan
}

function Write-WarningMessage($message) {
    Write-Host "[WARN] $message" -ForegroundColor Yellow
}

function Write-ErrorMessage($message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$VenvActivate = Join-Path $RepoRoot ".venv\Scripts\Activate.ps1"

Write-Info "Repository root detected: $RepoRoot"

if (-not $SkipAPI) {
    if (-not (Test-Path $VenvActivate)) {
        Write-WarningMessage ".venv not found. The API will start without virtualenv activation."
    }

    $ApiCmdParts = @()
    $ApiCmdParts += "cd `"$RepoRoot`""
    if (Test-Path $VenvActivate) {
        $ApiCmdParts += ". `\"$VenvActivate`\""
    }
    $ApiCmdParts += "python -m backend.main"

    $ApiCommand = [string]::Join('; ', $ApiCmdParts)
    Write-Info "Starting KR-AI API in new PowerShell window..."
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $ApiCommand
} else {
    Write-Info "Skipping API startup per flag."
}

if (-not $SkipOpenWebUI) {
    $DockerCmd = "docker"
    try {
        & $DockerCmd version | Out-Null
    } catch {
        Write-ErrorMessage "Docker CLI not available. Install Docker Desktop or add docker to PATH."
        exit 1
    }

    $ContainerName = "krai-openwebui"
    $Image = "ghcr.io/open-webui/open-webui:main"
    $PortMapping = "3000:8080"
    $ApiBase = "http://host.docker.internal:8000/v1"
    $ApiKey = "dummy-key"

    $ExistingContainer = (& $DockerCmd ps -a --filter "name=$ContainerName" --format '{{.ID}}')
    if ($ExistingContainer) {
        if ($ForceRestartOpenWebUI) {
            Write-Info "Force restarting existing OpenWebUI container $ContainerName..."
            & $DockerCmd rm -f $ContainerName | Out-Null
        } else {
            $IsRunning = (& $DockerCmd ps --filter "name=$ContainerName" --format '{{.ID}}')
            if (-not $IsRunning) {
                Write-Info "Starting existing OpenWebUI container $ContainerName..."
                & $DockerCmd start $ContainerName | Out-Null
            } else {
                Write-Info "OpenWebUI container $ContainerName already running."
            }
            goto EndOpenWebUI
        }
    }

    Write-Info "Launching OpenWebUI container on http://localhost:3000 ..."
    & $DockerCmd run -d `
        --name $ContainerName `
        -p $PortMapping `
        -e "OPENAI_API_BASE_URLS=$ApiBase" `
        -e "OPENAI_API_KEYS=$ApiKey" `
        $Image | Out-Null

EndOpenWebUI:
    Write-Info "OpenWebUI ready at http://localhost:3000"
    Write-Info "Login, then set OpenAI connection to $ApiBase with API key $ApiKey"
} else {
    Write-Info "Skipping OpenWebUI startup per flag."
}

Write-Info "Startup script completed."
