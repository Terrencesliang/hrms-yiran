#Requires -Version 5.1
<#
.SYNOPSIS
  Start HRMS Docker development mode on Windows.

.EXAMPLE
  .\dev.ps1
  .\dev.ps1 -Logs
  .\dev.ps1 -Migrate
  .\dev.ps1 -ForceMigrate
#>
[CmdletBinding()]
param(
    [switch]$Logs,
    [switch]$Migrate,
    [switch]$ForceMigrate,
    [switch]$Recreate,
    [ValidateRange(10, 300)]
    [int]$TimeoutSeconds = 55
)

$ErrorActionPreference = "Stop"
$DeployDir = $PSScriptRoot
$envFile = Join-Path $DeployDir ".env"
. (Join-Path $DeployDir "scripts\common.ps1")

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker not found. Install Docker Desktop first."
}
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker is not running. Start Docker Desktop first."
}
if (-not (Test-Path $envFile)) {
    throw "Missing deploy\.env. Run .\install.ps1 first."
}

Assert-DeployEnvFile -EnvFile $envFile

$composeOptions = @(Get-DeployComposeArgs -EnvFile $envFile -IncludeDevCompose)
$port = Get-DeployEnvValue -EnvFile $envFile -Key "HTTP_PORT" -Default "8080"
$useBundledPostgres = ((Get-DeployEnvValue -EnvFile $envFile -Key "USE_BUNDLED_POSTGRES" -Default "false").ToLower() -eq "true")

Push-Location $DeployDir
try {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    Write-Host "Starting HRMS development mode..." -ForegroundColor Cyan
    $upOptions = @("up", "-d")
    if ($Recreate) { $upOptions += "--force-recreate" }
    $upOptions += @("backend", "nginx")
    & docker compose @composeOptions @upOptions
    if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }

    Write-Host "Waiting for backend container..."
    Wait-DeployBackendRunning -ComposeOptions $composeOptions

    Write-Host "Synchronizing mounted source code..."
    & docker compose @composeOptions exec -T backend python /workspace/source/deploy/dev_sync.py --once
    if ($LASTEXITCODE -ne 0) { throw "source synchronization failed" }

    Write-Host "Waiting for the development server (max $($TimeoutSeconds)s)..."
    & docker compose @composeOptions exec -T backend bash /workspace/source/deploy/scripts/wait_dev_ready.sh $TimeoutSeconds
    if ($LASTEXITCODE -ne 0) {
        throw "development server did not become ready within $($TimeoutSeconds)s"
    }

    if ($Migrate -or $ForceMigrate) {
        Write-Host "Applying requested schema preparation (this may exceed the fast-start target)..."
        $prepareOptions = @("exec", "-T", "backend", "bash", "/workspace/source/deploy/scripts/prepare_dev.sh")
        if ($useBundledPostgres) { $prepareOptions += "--local-database" }
        if ($ForceMigrate) {
            $prepareOptions += "--force-migrate"
        } else {
            $prepareOptions += "--migrate"
        }
        & docker compose @composeOptions @prepareOptions
        if ($LASTEXITCODE -ne 0) {
            throw "development database preparation failed"
        }
    }

    $stopwatch.Stop()
    Write-Host ""
    Write-Host "Development mode is ready in $([Math]::Round($stopwatch.Elapsed.TotalSeconds, 1))s: http://localhost:$port" -ForegroundColor Green
    Write-Host "Source sync: enabled (Windows/macOS polling)"
    Write-Host "Frontend watch: enabled"
    Write-Host "Watched apps: hrms, employee_roster (ERPNext excluded)"
    Write-Host "Python reload: enabled"
    Write-Host "Arco org_ui watch: enabled"
    Write-Host ""
    Write-Host "Follow logs: .\dev.ps1 -Logs"
    Write-Host "Stop: .\stop.ps1"

    if ($Logs) {
        & docker compose @composeOptions logs -f backend
    }
}
finally {
    Pop-Location
}
