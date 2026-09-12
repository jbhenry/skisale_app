#!/bin/bash
# Runs ON a Linux client machine. Downloads a snapshot of the database
# from the server's /admin/download-db endpoint and saves it locally.
#
# BEFORE FIRST USE:
#   - Replace SERVER-IP-OR-HOSTNAME below with the server's actual LAN
#     address (find it on the server with ip addr or hostname -I).
#   - Replace DEST_FOLDER if it doesn't match where you want backups saved.

SERVER_ADDRESS="SERVER-IP-OR-HOSTNAME"
DEST_FOLDER="$HOME/skisale_backups"

mkdir -p "$DEST_FOLDER"

STAMP=$(date +%Y%m%d_%H%M%S)
DEST="$DEST_FOLDER/skisale_backup_${STAMP}.db"

if curl -sf -o "$DEST" "http://${SERVER_ADDRESS}:5000/admin/download-db"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') OK: saved $DEST" >> "$DEST_FOLDER/backup.log"
else
    rm -f "$DEST"
    echo "$(date '+%Y-%m-%d %H:%M:%S') FAILED: server unreachable, no backup saved" >> "$DEST_FOLDER/backup.log"
fi
