# test.ps1
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $root
Set-Location $root
$py = "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
& $py -c "import cv2, fastapi, ultralytics, sqlalchemy; print('imports ok')"
cd frontend
npm run build
cd $root
Write-Host "Tests done."
