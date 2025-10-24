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

    $PythonPathEntries = @()
    $PythonPathEntries += $BackendDir
    $PythonPathEntries += $RepoRoot
    $ExistingPythonPath = [System.Environment]::GetEnvironmentVariable("PYTHONPATH", "Process")
    if (-not [string]::IsNullOrWhiteSpace($ExistingPythonPath)) {
        $PythonPathEntries += $ExistingPythonPath.Split(';')
    }
    $PythonPathValue = ($PythonPathEntries | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique) -join ';'

    $ActivateCommand = ""
    if (Test-Path $VenvActivate) {
        $ActivateCommand = "if (Test-Path '$VenvActivate') { & '$VenvActivate' }"
    }

    $escapedPythonPath = $PythonPathValue -replace "'", "''"
    $ApiCommand = "& { Set-Location -Path '$RepoRoot'; `$env:PYTHONPATH = '$escapedPythonPath'; $ActivateCommand; python -m backend.main }"

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

    try {
        $ExistingContainer = (& $DockerCmd ps -a --filter "name=$ContainerName" --format '{{.ID}}')
    } catch {
        Write-ErrorMessage "Failed to query Docker containers: $($_.Exception.Message)"
        return
    }

    $containerRunning = $false

    if ($ExistingContainer) {
        if ($ForceRestartOpenWebUI) {
            Write-Info "Force restarting existing OpenWebUI container $ContainerName..."
            try {
                & $DockerCmd rm -f $ContainerName | Out-Null
            } catch {
                Write-ErrorMessage "Failed to remove container: $($_.Exception.Message)"
                return
            }
        } else {
            try {
                $IsRunning = (& $DockerCmd ps --filter "name=$ContainerName" --format '{{.ID}}')
            } catch {
                Write-ErrorMessage "Failed to inspect container state: $($_.Exception.Message)"
                return
            }

            if (-not $IsRunning) {
                Write-Info "Starting existing OpenWebUI container $ContainerName..."
                try {
                    & $DockerCmd start $ContainerName | Out-Null
                } catch {
                    Write-ErrorMessage "Failed to start container: $($_.Exception.Message)"
                    return
                }
            } else {
                Write-Info "OpenWebUI container $ContainerName already running."
                $containerRunning = $true
            }
        }
    }

    if (-not $containerRunning) {
        Write-Info "Launching OpenWebUI container on http://localhost:3000 ..."
        try {
            & $DockerCmd run -d `
                --name $ContainerName `
                -p $PortMapping `
                -e "OPENAI_API_BASE_URLS=$ApiBase" `
                -e "OPENAI_API_KEYS=$ApiKey" `
                -e "WEBUI_AUTH=False" `
                $Image | Out-Null
        } catch {
            Write-ErrorMessage "Failed to launch OpenWebUI container: $($_.Exception.Message)"
            Write-ErrorMessage "Is Docker Desktop running?"
            return
        }
    }

    Write-Info "OpenWebUI ready at http://localhost:3000"
    Write-Info "Login, then set OpenAI connection to $ApiBase with API key $ApiKey"
} else {
    Write-Info "Skipping OpenWebUI startup per flag."
}

Write-Info "Startup script completed."
