# Run ONCE on each Windows 7 client machine to schedule the daily download
# backup (backup-client.ps1). Uses schtasks.exe rather than the
# ScheduledTasks module, since that module requires PowerShell 3.0+, which
# Windows 7 doesn't include by default.
#
# Run this from an elevated Command Prompt or PowerShell window
# (Run as Administrator).
#
# Adjust the time (/st) and script path below if your setup differs.

schtasks /create /tn "SkiSale DB Backup (Client)" /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\skisale_app\backup-client.ps1" /sc daily /st 18:15
