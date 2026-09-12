# Run ONCE on the Windows 10 server machine to schedule the daily server-side
# backup (backup-server.ps1). Requires an elevated PowerShell prompt
# (Run as Administrator).
#
# Adjust -At and the script path below if your setup differs.

$scriptPath = "C:\skisale_app\backup-server.ps1"

$action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At 6pm
Register-ScheduledTask -TaskName "SkiSale DB Backup (Server)" -Action $action -Trigger $trigger -Description "Nightly server-side SkiSale DB backup"

Write-Host "Scheduled task 'SkiSale DB Backup (Server)' created: runs backup-server.ps1 daily at 6:00 PM."
