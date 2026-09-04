#Requires -Version 5.1
$ErrorActionPreference = "Stop"

& "$PSScriptRoot\compose.ps1" down
if ($LASTEXITCODE -ne 0) { throw "docker compose down failed" }
Write-Host "HRMS Docker services stopped. Persistent data volumes were kept." -ForegroundColor Green
