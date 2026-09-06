# Starts the waitress production server on Windows.
#
# NOTE: Windows' default PowerShell execution policy blocks running local
# scripts. If this script (or Scripts\Activate.ps1) fails to run, open
# PowerShell as Administrator once and run:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then re-run this script normally.

Write-Host "===================================================" -ForegroundColor Yellow
Write-Host " SkiSale App server is running." -ForegroundColor Yellow
Write-Host " DO NOT CLOSE THIS WINDOW - it will stop the server." -ForegroundColor Yellow
Write-Host " Press Ctrl-C to stop the server." -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Yellow
Write-Host ""

Set-Location -Path C:\skisale_app
& .\Scripts\Activate.ps1

try {
    python serve.py
} finally {
    Read-Host "Press Enter to exit"
}
