# setup.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $root
Set-Location $root
if (-not (Test-Path "backend\.venv")) {
  python -m venv backend\.venv
}
& "backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "backend\.venv\Scripts\pip.exe" install -r backend\requirements.txt
Set-Location frontend
npm install
Set-Location $root
New-Item -ItemType Directory -Force -Path data | Out-Null
New-Item -ItemType Directory -Force -Path data\evidence | Out-Null
Write-Host "Setup complete."
