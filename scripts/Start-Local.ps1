[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Run .\scripts\Setup-Local.ps1 first.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'web\dist\index.html'))) { throw 'Build the interface with .\scripts\Setup-Local.ps1 first.' }
Push-Location -LiteralPath $projectRoot
try {
    Write-Output 'Local app: http://127.0.0.1:8000 - Ctrl+C to stop.'
    & $projectPython -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
    if ($LASTEXITCODE -ne 0) { throw 'Application server stopped with an error.' }
} finally { Pop-Location }
