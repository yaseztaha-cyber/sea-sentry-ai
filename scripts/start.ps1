# start.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $root
Set-Location $root

# free ports
function Stop-Port($port) {
  $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
  }
}
Stop-Port 8000
Stop-Port 5173

$py = "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Start-Process -FilePath $py -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory "$root\backend" -WindowStyle Minimized
Start-Sleep -Seconds 3
Start-Process -FilePath "npm.cmd" -ArgumentList "run","dev" -WorkingDirectory "$root\frontend" -WindowStyle Minimized
Start-Sleep -Seconds 3
Write-Host "Backend: http://127.0.0.1:8000"
Write-Host "Frontend: http://localhost:5173"
Write-Host "API docs: http://127.0.0.1:8000/docs"
