#!/bin/bash
# Runs ON the Linux server machine (where the app itself runs).
# Triggers the server-side backup, which saves a timestamped copy of the
# database into var/app-instance/backups/ on this same machine.

LOG_FOLDER="$HOME/skisale_backups"
mkdir -p "$LOG_FOLDER"

if curl -sf -X POST http://localhost:5000/admin/backup-db -o /dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') OK: server-side backup triggered" >> "$LOG_FOLDER/backup.log"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') FAILED: server unreachable, no backup triggered" >> "$LOG_FOLDER/backup.log"
fi
