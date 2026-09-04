#Requires -Version 5.1
<#
.SYNOPSIS
  Start HRMS Docker development mode on Windows.

.EXAMPLE
  .\dev.ps1
  .\dev.ps1 -Logs
  .\dev.ps1 -Migrate
#>
[CmdletBinding()]
param(
    [switch]$Logs,
    [switch]$Migrate,
    [switch]$Recreate
)

$ErrorActionPreference = "Stop"
$DeployDir = $PSScriptRoot
$envFile = Join-Path $DeployDir ".env"

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

$composeOptions = @("-f", "docker-compose.yml", "-f", "docker-compose.dev.yml")
$port = "8080"
$useBundledPostgres = $false
foreach ($line in Get-Content $envFile) {
    if ($line -match '^USE_BUNDLED_POSTGRES=(.+)$' -and $Matches[1].Trim().ToLower() -eq 'true') {
        $composeOptions += @("--profile", "bundled-postgres")
        $useBundledPostgres = $true
    }
    if ($line -match '^USE_BUNDLED_REDIS=(.+)$' -and $Matches[1].Trim().ToLower() -eq 'true') {
        $composeOptions += @("--profile", "bundled-redis")
    }
    if ($line -match '^HTTP_PORT=(.+)$') {
        $port = $Matches[1].Trim().Trim('"')
    }
}

Push-Location $DeployDir
try {
    Write-Host "Starting HRMS development mode..." -ForegroundColor Cyan
    $upOptions = @("up", "-d")
    if ($Recreate) { $upOptions += "--force-recreate" }
    $upOptions += "backend"
    & docker compose @composeOptions @upOptions
    if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }

    Write-Host "Synchronizing mounted source code..."
    & docker compose @composeOptions exec -T backend python /workspace/source/deploy/dev_sync.py --once
    if ($LASTEXITCODE -ne 0) { throw "source synchronization failed" }

    $prepareOptions = @("exec", "-T", "backend", "bash", "/workspace/source/deploy/scripts/prepare_dev.sh")
    if ($useBundledPostgres) { $prepareOptions += "--local-database" }
    if ($Migrate) { $prepareOptions += "--migrate" }
    & docker compose @composeOptions @prepareOptions
    if ($LASTEXITCODE -ne 0) {
        throw "development database preparation failed"
    }

    Write-Host ""
    Write-Host "Development mode is ready: http://localhost:$port" -ForegroundColor Green
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
