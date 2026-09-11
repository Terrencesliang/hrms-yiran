# Shared helpers for deploy/*.ps1 (parity with deploy/scripts/common.sh).

function Get-DeployEnvValue {
    param(
        [Parameter(Mandatory = $true)][string]$EnvFile,
        [Parameter(Mandatory = $true)][string]$Key,
        [string]$Default = ""
    )
    if (-not (Test-Path $EnvFile)) { return $Default }
    $pattern = "^" + [regex]::Escape($Key) + "=(.+)$"
    foreach ($line in Get-Content $EnvFile) {
        if ($line -match $pattern) {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $Default
}

function Assert-DeployEnvFile {
    param([Parameter(Mandatory = $true)][string]$EnvFile)

    if (-not (Test-Path $EnvFile)) {
        throw "Missing deploy\.env. Copy deploy\.env.example to deploy\.env (NOT Desktop or repo root)."
    }

    $dbHost = Get-DeployEnvValue -EnvFile $EnvFile -Key "DB_HOST"
    $redisUrl = Get-DeployEnvValue -EnvFile $EnvFile -Key "REDIS_URL"
    $useBundledPg = (Get-DeployEnvValue -EnvFile $EnvFile -Key "USE_BUNDLED_POSTGRES" -Default "false").ToLower()
    $siteName = Get-DeployEnvValue -EnvFile $EnvFile -Key "SITE_NAME" -Default "hrms.localhost"

    Write-Host "Using env file: $EnvFile"
    Write-Host "  SITE_NAME=$siteName"
    Write-Host "  DB_HOST=$dbHost"
    Write-Host "  REDIS_URL=$redisUrl"
    Write-Host "  USE_BUNDLED_POSTGRES=$useBundledPg"

    if ($useBundledPg -eq "true") {
        if ($dbHost -and $dbHost -ne "postgres") {
            Write-Host "WARNING: USE_BUNDLED_POSTGRES=true but DB_HOST=$dbHost (expected postgres)." -ForegroundColor Yellow
        }
        return
    }

    # Containers cannot reach the Docker host via loopback.
    if ($dbHost -match '^(127\.0\.0\.1|localhost)$') {
        Write-Host ""
        Write-Host "Invalid DB_HOST for Docker: $dbHost" -ForegroundColor Yellow
        Write-Host "Use host.docker.internal when PostgreSQL runs on the same machine as Docker." -ForegroundColor Yellow
        Write-Host "  Edit deploy\.env:" -ForegroundColor Yellow
        Write-Host "    DB_HOST=host.docker.internal" -ForegroundColor Yellow
        Write-Host "When PostgreSQL is on another LAN machine, use that machine IP (e.g. 192.168.1.114)." -ForegroundColor Yellow
        throw "Invalid DB_HOST for Docker on Windows: $dbHost"
    }

    if (-not $dbHost) {
        throw "DB_HOST is empty while USE_BUNDLED_POSTGRES=false."
    }
}

function Get-DeployComposeArgs {
    param(
        [Parameter(Mandatory = $true)][string]$EnvFile,
        [switch]$IncludeDevCompose
    )
    $argsList = @()
    if ($IncludeDevCompose) {
        $argsList += @("-f", "docker-compose.yml", "-f", "docker-compose.dev.yml")
    }
    $useBundledPostgres = ((Get-DeployEnvValue -EnvFile $EnvFile -Key "USE_BUNDLED_POSTGRES" -Default "false").ToLower() -eq "true")
    $useBundledRedis = ((Get-DeployEnvValue -EnvFile $EnvFile -Key "USE_BUNDLED_REDIS" -Default "false").ToLower() -eq "true")
    if ($useBundledPostgres) { $argsList += @("--profile", "bundled-postgres") }
    if ($useBundledRedis) { $argsList += @("--profile", "bundled-redis") }
    return $argsList
}

function Wait-DeployBackendRunning {
    param([string[]]$ComposeOptions = @())

    for ($i = 1; $i -le 45; $i++) {
        $running = & docker compose @ComposeOptions ps --status running --format "{{.Name}}" 2>$null |
            Where-Object { $_ -match "backend" }
        if ($running) { return }

        $all = & docker compose @ComposeOptions ps -a --format "{{.Name}} {{.Status}}" 2>$null
        if ($all -match "backend.*Restarting") {
            Write-Host "Backend is restarting (attempt $i/45)..."
        } else {
            Write-Host "Waiting for backend container (attempt $i/45)..."
        }
        Start-Sleep -Seconds 2
    }

    Write-Host "Backend container did not become ready. Recent logs:" -ForegroundColor Red
    & docker compose @ComposeOptions logs --tail 50 backend
    throw "Backend container did not become ready. Common cause: site db_host=postgres while USE_BUNDLED_POSTGRES=false."
}
