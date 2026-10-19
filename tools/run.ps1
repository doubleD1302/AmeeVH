param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$ToolArgs
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
try {
    & python (Join-Path $PSScriptRoot 'localize.py') @ToolArgs
    $ToolExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $ToolExitCode
