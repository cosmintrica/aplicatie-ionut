[CmdletBinding()]
param([string]$PythonPath, [string]$NodePath)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location -LiteralPath $projectRoot
try {
    if (-not $PythonPath) {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonCommand) { $PythonPath = $pythonCommand.Source }
        else {
            $PythonPath = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        }
    }
    if (-not (Test-Path -LiteralPath $PythonPath)) { throw 'Python 3.12 is required. Pass its executable as -PythonPath.' }
    if (-not $NodePath) { $NodePath = (Get-Command node -ErrorAction Stop).Source }
    $npmCli = Join-Path (Split-Path $NodePath -Parent) 'node_modules\npm\bin\npm-cli.js'
    if (-not (Test-Path -LiteralPath $npmCli)) { throw 'npm must be installed alongside Node.js.' }
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & $PythonPath -m venv '.venv'
        if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
    }
    $projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath 'backend\requirements.lock') {
        & $projectPython -m pip install -r 'backend\requirements.lock'
        if ($LASTEXITCODE -ne 0) { throw 'Locked backend dependency installation failed.' }
        & $projectPython -m pip install --no-deps -e './backend'
    } else {
        & $projectPython -m pip install -e './backend[test]'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Backend installation failed.' }
    Push-Location -LiteralPath (Join-Path $projectRoot 'web')
    try {
        if (Test-Path -LiteralPath 'package-lock.json') { & $NodePath $npmCli ci --no-audit --no-fund --cache '..\var\npm-cache' }
        else { & $NodePath $npmCli install --no-audit --no-fund --cache '..\var\npm-cache' }
        if ($LASTEXITCODE -ne 0) { throw 'Frontend installation failed.' }
        & $NodePath $npmCli run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
    & $projectPython -m app.cli seed
    if ($LASTEXITCODE -ne 0) { throw 'Snapshot import failed.' }
    Write-Output 'Ready. Run .\scripts\Start-Local.ps1 and open http://127.0.0.1:8000.'
} finally { Pop-Location }
