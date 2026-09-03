#Requires -Version 5.1
<#
.SYNOPSIS
  Start HRMS Docker development mode on Windows.

.EXAMPLE
  .\dev.ps1
  .\dev.ps1 -Logs
#>
[CmdletBinding()]
param(
    [switch]$Logs
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
foreach ($line in Get-Content $envFile) {
    if ($line -match '^USE_BUNDLED_POSTGRES=(.+)$' -and $Matches[1].Trim().ToLower() -eq 'true') {
        $composeOptions += @("--profile", "bundled-postgres")
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
    & docker compose @composeOptions up -d --force-recreate backend
    if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }

    Write-Host ""
    Write-Host "Development mode is ready: http://localhost:$port" -ForegroundColor Green
    Write-Host "Source sync: enabled (Windows/macOS polling)"
    Write-Host "Frontend watch: enabled"
    Write-Host "Python reload: enabled"
    Write-Host ""
    Write-Host "Follow logs: .\dev.ps1 -Logs"

    if ($Logs) {
        & docker compose @composeOptions logs -f backend
    }
}
finally {
    Pop-Location
}
