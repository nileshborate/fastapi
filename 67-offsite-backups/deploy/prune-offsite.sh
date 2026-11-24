#!/usr/bin/env bash
# Video 67 - from YOUR LAPTOP, once a week: the app server can't delete (append-only),
# so old snapshots are removed by the OWNER - over SSH, straight on the backup box's disk.
# The password comes from YOUR password manager - it is never stored on the backup box.
#   RESTIC_PASSWORD_COMMAND="pass show coursehub/restic" deploy/prune-offsite.sh
set -euo pipefail
# SSH as the OWNER - not through rest-server:
BOX=sftp:restic@backup.example.net:/srv/restic/coursehub-1
export RESTIC_REPOSITORY=${RESTIC_REPOSITORY:-$BOX}
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune
restic check                                  # are the files that are left OK?
