#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$RepoUrl = "https://github.com/Terrencesliang/hrms-yiran.git",
    [string]$Branch = "main",
    [string]$AdminPassword = "",
    [string]$DbPassword = "",
    [switch]$SyncLocalData,
    [switch]$SkipLocalData
)

$ErrorActionPreference = "Stop"
$DeployDir = $PSScriptRoot
$RepoRoot = Split-Path $DeployDir -Parent

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

function Ensure-EnvFile {
    $envFile = Join-Path $DeployDir ".env"
    $envExample = Join-Path $DeployDir ".env.example"

    if (-not (Test-Path $envFile)) {
        if (-not (Test-Path $envExample)) {
            throw "Missing $envExample"
        }
        Copy-Item $envExample $envFile
        Write-Step "Created .env from .env.example"
    }

    if ($AdminPassword) {
        (Get-Content $envFile) -replace '^ADMIN_PASSWORD=.*', "ADMIN_PASSWORD=$AdminPassword" | Set-Content $envFile -Encoding UTF8
    }
    if ($DbPassword) {
        (Get-Content $envFile) -replace '^DB_PASSWORD=.*', "DB_PASSWORD=$DbPassword" | Set-Content $envFile -Encoding UTF8
    }
}

function Ensure-Repo {
    $gitDir = Join-Path $RepoRoot ".git"
    if (Test-Path $gitDir) {
        Write-Step "Using repo: $RepoRoot"
        return
    }
    throw "Run this script inside a cloned hrms-yiran repository."
}

function Get-EnvFlag([string]$Key, [bool]$Default = $false) {
    $envFile = Join-Path $DeployDir ".env"
    if (-not (Test-Path $envFile)) { return $Default }
    $pattern = "^" + [regex]::Escape($Key) + "=(.+)$"
    foreach ($line in Get-Content $envFile) {
        if ($line -match $pattern) {
            return ($Matches[1].Trim().ToLower() -eq "true")
        }
    }
    return $Default
}

function Export-LocalDataIfNeeded {
    if ($SkipLocalData) {
        Write-Step "Skipped local data export (-SkipLocalData)"
        return
    }

    $shouldSync = $SyncLocalData.IsPresent -or (Get-EnvFlag "SYNC_LOCAL_DATA" $false)
    if (-not $shouldSync) {
        Write-Step "SYNC_LOCAL_DATA=false, skip local export"
        return
    }

    $exportScript = Join-Path $DeployDir "scripts\export_local_data.ps1"
    if (-not (Test-Path $exportScript)) {
        throw "Missing $exportScript"
    }

    Write-Step "Exporting WSL data to deploy/data/incoming"
    & $exportScript
}

function Show-AccessInfo {
    param([string]$EnvPath)
    $admin = "admin"
    $port = "8080"
    foreach ($line in Get-Content $EnvPath) {
        if ($line -match '^ADMIN_PASSWORD=(.+)$') { $admin = $Matches[1].Trim().Trim('"') }
        if ($line -match '^HTTP_PORT=(.+)$') { $port = $Matches[1].Trim() }
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " HRMS Docker deploy started" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "URL:      http://localhost:$port"
    Write-Host "User:     Administrator"
    Write-Host "Password: $admin"
    Write-Host ""
    Write-Host "Logs: deploy\logs.ps1"
    Write-Host "Stop: deploy\stop.ps1"
    Write-Host "========================================" -ForegroundColor Green
}

Write-Step "Checking Docker"
Test-DockerReady
Ensure-Repo
Ensure-EnvFile
Export-LocalDataIfNeeded

Push-Location $DeployDir
try {
    Write-Step "Starting containers"
    & (Join-Path $DeployDir "compose.ps1") up -d
    if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }
    Show-AccessInfo (Join-Path $DeployDir ".env")
    Write-Host "First install may take 15-30 minutes. Run .\logs.ps1" -ForegroundColor Yellow
}
finally {
    Pop-Location
}
