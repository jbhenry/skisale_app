# Run ONCE on the Windows 10 server machine to schedule the server-side
# backup (backup-server.ps1): every 30 minutes from 3:00 PM to 11:00 PM.
# Requires an elevated PowerShell prompt (Run as Administrator).
# Safe to re-run; -Force replaces an existing task.
#
# Adjust the script path below if your setup differs.

$scriptPath = "C:\skisale_app\backup-server.ps1"

$action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

# Daily trigger at 3:00 PM, repeating every 30 minutes. The duration is just
# over 8 hours so the final 11:00 PM run is included.
$trigger = New-ScheduledTaskTrigger -Daily -At 3pm
$trigger.Repetition = (New-ScheduledTaskTrigger -Once -At 3pm -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Hours 8 -Minutes 1)).Repetition

Register-ScheduledTask -TaskName "SkiSale DB Backup (Server)" -Action $action -Trigger $trigger -Description "SkiSale DB backup every 30 minutes, 3:00 PM - 11:00 PM" -Force

Write-Host "Scheduled task 'SkiSale DB Backup (Server)' created: runs backup-server.ps1 every 30 minutes, 3:00 PM - 11:00 PM."
