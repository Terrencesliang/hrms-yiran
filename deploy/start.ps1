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

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-DockerReady {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker not found. Install Docker Desktop first."
    }
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running. Start Docker Desktop first."
    }
}

function Show-AccessInfo {
    $admin = "admin"
    $port = "8080"
    if (Test-Path $envFile) {
        foreach ($line in Get-Content $envFile) {
            if ($line -match '^ADMIN_PASSWORD=(.+)$') { $admin = $Matches[1].Trim().Trim('"') }
            if ($line -match '^HTTP_PORT=(.+)$') { $port = $Matches[1].Trim() }
        }
    }

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
}

if (-not (Test-Path $envFile)) {
    throw "Missing deploy\.env. Run .\install.ps1 first."
}

Write-Step "Checking Docker"
Test-DockerReady

Push-Location $DeployDir
try {
    Write-Step "Starting containers"
    & (Join-Path $DeployDir "compose.ps1") up -d
    if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }

    if ($Logs) {
        Write-Step "Following logs (Ctrl+C to exit)"
        & (Join-Path $DeployDir "compose.ps1") logs -f backend
    } else {
        Show-AccessInfo
        Write-Host "First install may take 15-30 minutes. Run .\logs.ps1 to watch progress." -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}
