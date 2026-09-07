#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$Down
)

$ErrorActionPreference = "Stop"

if ($Down) {
    & "$PSScriptRoot\compose.ps1" down
    if ($LASTEXITCODE -ne 0) { throw "docker compose down failed" }
    Write-Host "HRMS Docker containers and network removed. Persistent data volumes were kept." -ForegroundColor Green
} else {
    & "$PSScriptRoot\compose.ps1" stop
    if ($LASTEXITCODE -ne 0) { throw "docker compose stop failed" }
    Write-Host "HRMS Docker services stopped and kept for a faster next start." -ForegroundColor Green
}
