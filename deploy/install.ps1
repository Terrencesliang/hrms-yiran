#Requires -Version 5.1
<#
.SYNOPSIS
  依然电商 HRMS 一键 Docker 部署（Windows）

.DESCRIPTION
  1. 检查 Docker Desktop
  2. 导出本机 WSL 数据（可选）
  3. docker compose up -d
  4. 容器内自动恢复数据并安装

.EXAMPLE
  .\install.ps1
  .\install.ps1 -SkipLocalData
  .\install.ps1 -AdminPassword "MyPass123"
#>
[CmdletBinding()]
param(
    [string]$RepoUrl = "https://github.com/Terrencesliang/hrms-yiran.git",
    [string]$Branch = "yiran-custom",
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
        throw "未检测到 Docker。请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop/"
    }
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker 未运行。请先启动 Docker Desktop 后重试。"
    }
}

function Ensure-EnvFile {
    $envFile = Join-Path $DeployDir ".env"
    $envExample = Join-Path $DeployDir ".env.example"

    if (-not (Test-Path $envFile)) {
        if (-not (Test-Path $envExample)) {
            throw "缺少 $envExample"
        }
        Copy-Item $envExample $envFile
        Write-Step "已生成 .env（可按需修改密码和端口）"
    }

    if ($AdminPassword) {
        (Get-Content $envFile) -replace '^ADMIN_PASSWORD=.*', "ADMIN_PASSWORD=$AdminPassword" | Set-Content $envFile
    }
    if ($DbPassword) {
        (Get-Content $envFile) -replace '^DB_PASSWORD=.*', "DB_PASSWORD=$DbPassword" | Set-Content $envFile
    }
}

function Ensure-Repo {
    $gitDir = Join-Path $RepoRoot ".git"
    if (Test-Path $gitDir) {
        Write-Step "使用当前目录代码: $RepoRoot"
        return
    }

    $parent = Split-Path $RepoRoot -Parent
    $target = Join-Path $parent "hrms-yiran"
    if (-not (Test-Path $target)) {
        Write-Step "克隆仓库 $RepoUrl ($Branch) ..."
        git clone --branch $Branch --depth 1 $RepoUrl $target
    }
    throw @"
当前目录不是 Git 仓库。
请任选一种方式：
  1) 在已克隆的 hrms-yiran 目录中运行 deploy\install.ps1
  2) 手动克隆: git clone --branch $Branch $RepoUrl
"@
}

function Get-EnvFlag([string]$Key, [bool]$Default = $false) {
    $envFile = Join-Path $DeployDir ".env"
    if (-not (Test-Path $envFile)) { return $Default }
    foreach ($line in Get-Content $envFile) {
        if ($line -match "^${Key}=(.+)$") {
            return ($Matches[1].Trim().ToLower() -eq 'true')
        }
    }
    return $Default
}

function Export-LocalDataIfNeeded {
    if ($SkipLocalData) {
        Write-Step "已跳过本机数据导出 (-SkipLocalData)"
        return
    }

    $shouldSync = $SyncLocalData.IsPresent -or (Get-EnvFlag "SYNC_LOCAL_DATA" $true)
    if (-not $shouldSync) {
        Write-Step "SYNC_LOCAL_DATA=false，跳过本机数据导出"
        return
    }

    $exportScript = Join-Path $DeployDir "scripts\export_local_data.ps1"
    if (-not (Test-Path $exportScript)) {
        throw "缺少 $exportScript"
    }

    Write-Step "导出本机 WSL 数据到 deploy\data\incoming"
    & $exportScript
}

function Show-AccessInfo {
    param([string]$EnvPath)
    $admin = "admin"
    $port = "8080"
    foreach ($line in Get-Content $EnvPath) {
        if ($line -match '^ADMIN_PASSWORD=(.+)$') { $admin = $Matches[1].Trim().Trim('"') }
        if ($line -match '^HTTP_PORT=(.+)$') { $port = $Matches[1] }
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " 部署已启动（首次安装需等待 15-30 分钟）" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "访问地址: http://localhost:$port"
    Write-Host "用户名:   Administrator"
    Write-Host "密码:     $admin"
    Write-Host ""
    Write-Host "查看安装日志: deploy\logs.ps1"
    Write-Host "重新同步数据: deploy\sync-data.ps1"
    Write-Host "停止服务:     deploy\stop.ps1"
    Write-Host "========================================" -ForegroundColor Green
}

Write-Step "检查 Docker 环境"
Test-DockerReady
Ensure-Repo
Ensure-EnvFile
Export-LocalDataIfNeeded

Push-Location $DeployDir
try {
    Write-Step "启动 Docker 容器"
    & (Join-Path $DeployDir "compose.ps1") up -d
    if ($LASTEXITCODE -ne 0) { throw "docker compose up 失败" }
    Show-AccessInfo (Join-Path $DeployDir ".env")
}
finally {
    Pop-Location
}
