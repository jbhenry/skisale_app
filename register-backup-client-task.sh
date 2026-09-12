#!/bin/bash
# Run ONCE on each Linux client machine to schedule backup-client.sh in the
# current user's crontab: every 30 minutes from 3:15 PM to 11:15 PM, offset
# 15 minutes from the server-side backups.
# Safe to re-run; existing entries for this script are replaced.

SCRIPT="$(cd "$(dirname "$0")" && pwd)/backup-client.sh"

( crontab -l 2>/dev/null | grep -vF "$SCRIPT"
  echo "15,45 15-22 * * * $SCRIPT"
  echo "15 23 * * * $SCRIPT"
) | crontab -

echo "Scheduled $SCRIPT every 30 minutes, 3:15 PM - 11:15 PM. Current crontab:"
crontab -l
