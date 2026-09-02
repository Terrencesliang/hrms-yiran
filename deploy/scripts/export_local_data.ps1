#Requires -Version 5.1
<#
.SYNOPSIS
  从本机 WSL bench 导出数据到 deploy/data/incoming
#>
[CmdletBinding()]
param(
    [string]$WslDistro = "hrms-dev",
    [string]$WslUser = "dev",
    [string]$LocalSite = "",
    [string]$WslBench = "/home/dev/frappe-bench"
)

$ErrorActionPreference = "Stop"
$DeployDir = Split-Path $PSScriptRoot -Parent
$IncomingDir = Join-Path $DeployDir "data\incoming"
$RepoRoot = Split-Path $DeployDir -Parent

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Get-EnvValue([string]$Key, [string]$Default = "") {
    $envFile = Join-Path $DeployDir ".env"
    if (-not (Test-Path $envFile)) { return $Default }
    foreach ($line in Get-Content $envFile) {
        if ($line -match "^${Key}=(.+)$") {
            return $Matches[1].Trim().Trim('"')
        }
    }
    return $Default
}

if (-not $LocalSite) {
    $LocalSite = Get-EnvValue "LOCAL_SITE" "hrms-test.localhost"
}
$WslDistro = Get-EnvValue "LOCAL_WSL_DISTRO" $WslDistro
$WslBench = Get-EnvValue "LOCAL_WSL_BENCH" $WslBench

New-Item -ItemType Directory -Force -Path $IncomingDir | Out-Null

$winRepo = (Resolve-Path $RepoRoot).Path
$wslRepo = (& wsl -d $WslDistro -u $WslUser wslpath -a $winRepo).Trim()
$wslDeploy = "$wslRepo/deploy"

Write-Step "从 WSL 导出站点 $LocalSite"
$exportCmd = @"
set -euo pipefail
export LOCAL_SITE='$LocalSite'
export LOCAL_BENCH_DIR='$WslBench'
bash '$wslDeploy/scripts/export_local_data.sh'
"@

wsl -d $WslDistro -u $WslUser -e bash -lc $exportCmd
if ($LASTEXITCODE -ne 0) {
    throw "本机数据导出失败。请确认 WSL 中 bench 站点 $LocalSite 可访问。"
}

Write-Step "备份已写入 deploy\data\incoming"
Get-ChildItem $IncomingDir | Format-Table Name, Length, LastWriteTime
