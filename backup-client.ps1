# Runs ON a Windows 7 client machine. Downloads a snapshot of the database
# from the server's /admin/download-db endpoint and saves it locally.
#
# Uses System.Net.WebClient (not Invoke-WebRequest) for PowerShell 2.0
# compatibility, since Windows 7 does not include PS 3.0+ by default.
#
# BEFORE FIRST USE:
#   - Replace SERVER-IP-OR-HOSTNAME below with the Win10 server's actual
#     LAN address (find it on the server with ipconfig).
#   - Replace the destination folder if D:\SkiSaleBackups doesn't exist
#     on this machine, or create that folder first.

$serverAddress = "SERVER-IP-OR-HOSTNAME"
$destFolder    = "D:\SkiSaleBackups"

if (-not (Test-Path $destFolder)) {
    New-Item -ItemType Directory -Path $destFolder | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$dest  = Join-Path $destFolder "skisale_backup_$stamp.db"

$logFile = Join-Path $destFolder "backup.log"

$wc = New-Object System.Net.WebClient
try {
    $wc.DownloadFile("http://${serverAddress}:5000/admin/download-db", $dest)
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') OK: saved $dest" | Add-Content $logFile
} catch {
    if (Test-Path $dest) {
        Remove-Item $dest -Force
    }
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') FAILED: server unreachable, no backup saved" | Add-Content $logFile
}
