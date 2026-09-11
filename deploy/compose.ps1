param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ComposeArgs
)

$DeployDir = $PSScriptRoot
$envFile = Join-Path $DeployDir ".env"
. (Join-Path $DeployDir "scripts\common.ps1")

$argsList = @("compose")
if (Test-Path $envFile) {
    $argsList += @(Get-DeployComposeArgs -EnvFile $envFile)
}
$argsList += $ComposeArgs

$prevErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"
Push-Location $DeployDir
try {
    & docker @argsList 2>&1 | ForEach-Object { "$_" }
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
    $ErrorActionPreference = $prevErrorAction
}
exit $exitCode
