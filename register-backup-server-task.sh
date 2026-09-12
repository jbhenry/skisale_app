#!/bin/bash
# Run ONCE on the Linux server machine to schedule backup-server.sh in the
# current user's crontab: every 30 minutes from 3:00 PM to 11:00 PM.
# Safe to re-run; existing entries for this script are replaced.

SCRIPT="$(cd "$(dirname "$0")" && pwd)/backup-server.sh"

( crontab -l 2>/dev/null | grep -vF "$SCRIPT"
  echo "0,30 15-22 * * * $SCRIPT"
  echo "0 23 * * * $SCRIPT"
) | crontab -

echo "Scheduled $SCRIPT every 30 minutes, 3:00 PM - 11:00 PM. Current crontab:"
crontab -l
