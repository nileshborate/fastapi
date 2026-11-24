#!/usr/bin/env bash
# Video 62 homework - ON THE SERVER, every night from cron (/etc/cron.d/coursehub-backup):
# one pg_dump file per day, the newest 7 are kept
set -euo pipefail
cd "$(dirname "$0")/.."
set -a                                       # POSTGRES_USER, POSTGRES_DB: the server's .env
# shellcheck disable=SC1091                   # .env exists only on the server
. ./.env
set +a
DIR=${BACKUP_DIR:-$HOME/backups}
KEEP=${BACKUP_KEEP:-7}
mkdir -p "$DIR"
umask 077                                    # the dump has every row: only this user reads it
file="$DIR/coursehub-$(date +%F).dump"

# -Fc: PostgreSQL's custom format - compressed, and pg_restore can restore single tables
docker compose -f compose.yaml exec -T db \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$file.tmp"
mv "$file.tmp" "$file"                       # a half-written dump never looks like a backup

# keep the newest $KEEP - a glob is sorted, and the names sort by date
dumps=("$DIR"/coursehub-*.dump)
if [ "${#dumps[@]}" -gt "$KEEP" ]; then
    rm -- "${dumps[@]:0:${#dumps[@]}-KEEP}"
fi
dumps=("$DIR"/coursehub-*.dump)
echo "$(date -Is) $file $(stat -c %s "$file") bytes - ${#dumps[@]} kept"
