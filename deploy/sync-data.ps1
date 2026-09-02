#Requires -Version 5.1
<#
.SYNOPSIS
  重新同步本机数据到已运行的 Docker 部署
#>
[CmdletBinding()]
param(
    [string]$WslDistro = "hrms-dev",
    [string]$WslUser = "dev"
)

$ErrorActionPreference = "Stop"
$DeployDir = $PSScriptRoot

& (Join-Path $DeployDir "scripts\export_local_data.ps1") -WslDistro $WslDistro -WslUser $WslUser

Write-Host ""
Write-Host "==> 恢复数据到 Docker 容器..." -ForegroundColor Cyan
Push-Location $DeployDir
try {
    & (Join-Path $DeployDir "compose.ps1") exec -T backend bash /workspace/source/deploy/scripts/restore_backup.sh
    if ($LASTEXITCODE -ne 0) { throw "容器内数据恢复失败" }
    & (Join-Path $DeployDir "compose.ps1") exec -T backend bash -lc "cd /home/frappe/frappe-bench && bench build --app hrms --app employee_roster && bench --site hrms.localhost clear-cache"
    Write-Host ""
    Write-Host "数据同步完成。" -ForegroundColor Green
}
finally {
    Pop-Location
}
