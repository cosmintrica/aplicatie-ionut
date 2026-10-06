[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location -LiteralPath $projectRoot
try {
    & (Join-Path $projectRoot 'tests\Test-MonitorPricesParser.ps1')
    $projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Run Setup-Local.ps1 first.' }
    & $projectPython -m pytest -c backend/pyproject.toml backend/tests tests/test_app_regressions.py
    if ($LASTEXITCODE -ne 0) { throw 'Application regression tests failed.' }
    $nodePath = (Get-Command node -ErrorAction Stop).Source
    $npmCli = Join-Path (Split-Path $nodePath -Parent) 'node_modules\npm\bin\npm-cli.js'
    if (-not (Test-Path -LiteralPath $npmCli)) { throw 'npm must be installed alongside Node.js.' }
    Push-Location -LiteralPath (Join-Path $projectRoot 'web')
    try {
        & $nodePath $npmCli run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
} finally { Pop-Location }
