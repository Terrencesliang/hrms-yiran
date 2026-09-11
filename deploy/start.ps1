#Requires -Version 5.1
<#
.SYNOPSIS
  Start HRMS Docker service on Windows

.EXAMPLE
  .\start.ps1
  .\start.ps1 -Logs
#>
[CmdletBinding()]
param(
    [switch]$Logs
)

$ErrorActionPreference = "Stop"
$DeployDir = $PSScriptRoot
$envFile = Join-Path $DeployDir ".env"
. (Join-Path $DeployDir "scripts\common.ps1")

function Test-DockerReady {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker not found. Install Docker Desktop first."
    }
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running. Start Docker Desktop first."
    }
}

if (-not (Test-Path $envFile)) {
    throw "Missing deploy\.env. Run .\install.ps1 first."
}

Write-Host ""
Write-Host "==> Checking Docker" -ForegroundColor Cyan
Test-DockerReady
Assert-DeployEnvFile -EnvFile $envFile

Push-Location $DeployDir
try {
    Write-Host ""
    Write-Host "==> Starting containers" -ForegroundColor Cyan
    & (Join-Path $DeployDir "compose.ps1") up -d backend nginx
    if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }

    $composeOptions = @(Get-DeployComposeArgs -EnvFile $envFile)
    Wait-DeployBackendRunning -ComposeOptions $composeOptions

    $admin = Get-DeployEnvValue -EnvFile $envFile -Key "ADMIN_PASSWORD" -Default "admin"
    $port = Get-DeployEnvValue -EnvFile $envFile -Key "HTTP_PORT" -Default "8080"

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " HRMS Docker started" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "URL:      http://localhost:$port"
    Write-Host "User:     Administrator"
    Write-Host "Password: $admin"
    Write-Host ""
    Write-Host "Logs:  deploy\logs.ps1"
    Write-Host "Stop:  deploy\stop.ps1"
    Write-Host "========================================" -ForegroundColor Green

    if ($Logs) {
        Write-Host ""
        Write-Host "==> Following logs (Ctrl+C to exit)" -ForegroundColor Cyan
        & (Join-Path $DeployDir "compose.ps1") logs -f backend
    } else {
        Write-Host "First install may take 15-30 minutes. Run .\logs.ps1 to watch progress." -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}
