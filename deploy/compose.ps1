param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ComposeArgs
)

$DeployDir = $PSScriptRoot
$envFile = Join-Path $DeployDir ".env"
$useBundledPostgres = $false
$useBundledRedis = $false

if (Test-Path $envFile) {
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^USE_BUNDLED_POSTGRES=(.+)$') {
            $useBundledPostgres = ($Matches[1].Trim().ToLower() -eq 'true')
        }
        if ($line -match '^USE_BUNDLED_REDIS=(.+)$') {
            $useBundledRedis = ($Matches[1].Trim().ToLower() -eq 'true')
        }
    }
}

$argsList = @("compose")
if ($useBundledPostgres) {
    $argsList += @("--profile", "bundled-postgres")
}
if ($useBundledRedis) {
    $argsList += @("--profile", "bundled-redis")
}
$argsList += $ComposeArgs

& docker @argsList
