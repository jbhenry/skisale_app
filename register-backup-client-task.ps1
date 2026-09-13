# Run ONCE on each Windows 7 client machine to schedule the download
# backup (backup-client.ps1): every 30 minutes from 3:15 PM to 11:15 PM,
# offset 15 minutes from the server-side backups.
# Uses schtasks.exe rather than the ScheduledTasks module, since that module
# requires PowerShell 3.0+, which Windows 7 doesn't include by default.
#
# Run this from an elevated Command Prompt or PowerShell window
# (Run as Administrator). Safe to re-run; /f replaces an existing task.
#
# Adjust the script path below if your setup differs.
#
# /ri 30 repeats every 30 minutes; /du 08:01 (just over 8 hours) makes sure
# the final 11:15 PM run is included.

schtasks /create /f /tn "SkiSale DB Backup (Client)" /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\skisale_app\backup-client.ps1" /sc daily /st 15:15 /ri 30 /du 08:01
