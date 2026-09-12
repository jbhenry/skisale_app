# Runs ON the Windows 10 server machine (where the app itself runs).
# Triggers the server-side backup, which saves a timestamped copy of the
# database into var\app-instance\backups\ on this same machine.
#
# Requires PowerShell 3.0+ (standard on Windows 10).

$logFolder = "C:\SkiSaleBackups"
if (-not (Test-Path $logFolder)) {
    New-Item -ItemType Directory -Path $logFolder | Out-Null
}
$logFile = Join-Path $logFolder "backup.log"

try {
    Invoke-WebRequest -Uri "http://localhost:5000/admin/backup-db" -Method POST -UseBasicParsing | Out-Null
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') OK: server-side backup triggered" | Add-Content $logFile
} catch {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') FAILED: server unreachable, no backup triggered" | Add-Content $logFile
}
