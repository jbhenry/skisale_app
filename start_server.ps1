# Starts the waitress production server on Windows.
#
# NOTE: Windows' default PowerShell execution policy blocks running local
# scripts. If this script (or Scripts\Activate.ps1) fails to run, open
# PowerShell as Administrator once and run:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then re-run this script normally.

Set-Location -Path C:\skisale_app
& .\Scripts\Activate.ps1
python serve.py

Read-Host "Press Enter to exit"
