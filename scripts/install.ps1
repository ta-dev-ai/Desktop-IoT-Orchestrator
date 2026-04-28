$ErrorActionPreference = "Stop"

Write-Host "Desktop IoT Orchestrator - installation automatique" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$venvPath = Join-Path $projectRoot ".venv"
$localTemp = Join-Path $projectRoot "temp_local"
$python = "python"
$venvSitePackages = Join-Path $venvPath "Lib\site-packages"

function Write-Step($message) {
    Write-Host "`n==> $message" -ForegroundColor Yellow
}

Write-Step "Verification de Python"
try {
    $pythonVersion = & $python --version
    Write-Host "Python detecte: $pythonVersion" -ForegroundColor Green
} catch {
    throw "Python n'est pas disponible dans le PATH."
}

Write-Step "Creation du venv"
if (-not (Test-Path $localTemp)) {
    New-Item -ItemType Directory -Force $localTemp | Out-Null
}

if (-not (Test-Path $venvPath)) {
    & $python -m venv $venvPath
    Write-Host "Venv cree dans $venvPath" -ForegroundColor Green
} else {
    Write-Host "Venv deja present: $venvPath" -ForegroundColor Green
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Impossible de trouver Python dans le venv."
}

Write-Step "Preparation de l'environnement local"
$env:TEMP = $localTemp
$env:TMP = $localTemp
$env:TMPDIR = $localTemp

Write-Step "Installation de pip et des outils dans le venv"
& $python -m pip install --upgrade --target $venvSitePackages pip setuptools wheel

Write-Step "Installation des dependances"
& $python -m pip install --upgrade --target $venvSitePackages -r (Join-Path $projectRoot "requirements.txt")

Write-Step "Reparation de click"
$clickSource = & $python -c "import click, pathlib; print(pathlib.Path(click.__file__).resolve().parent)"
$clickTarget = Join-Path $venvSitePackages "click"
if (Test-Path $clickTarget) {
    Remove-Item -Recurse -Force $clickTarget
}
Copy-Item -Recurse -Force $clickSource $clickTarget
Write-Host "click copie depuis le Python systeme vers le venv." -ForegroundColor Green

Write-Host "`nInstallation terminee avec succes." -ForegroundColor Green
Write-Host "Pour activer le venv: .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "Pour lancer le backend: .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload" -ForegroundColor Cyan
