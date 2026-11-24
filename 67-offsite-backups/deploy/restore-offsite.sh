#!/usr/bin/env bash
# Video 67 - ON THE SERVER: is the OFF-SITE copy any good? Restore the newest snapshot ...
#   deploy/restore-offsite.sh          ... into a TEST database (restore-test.sh) - every week
#   deploy/restore-offsite.sh --live   ... into the LIVE database (a NEW server, a disaster)
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
# shellcheck disable=SC1091                   # both exist only on the server
. ./.env
# shellcheck disable=SC1091
. "$HOME/restic.env"
set +a
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT                    # the plain dump never stays on the disk

only=(--host coursehub-1 --tag coursehub)    # never "the newest of ANYTHING in the repo"
restic snapshots --compact --latest 3 "${only[@]}"
restic restore latest "${only[@]}" --target "$tmp" | tail -1
dump=$(find "$tmp" -name 'coursehub-*.dump' | sort | tail -1)
echo "==> $(basename "$dump"): $(stat -c %s "$dump") bytes"

if [ "${1:-}" != "--live" ]; then
    exec deploy/restore-test.sh "$dump"
fi
DC="docker compose -f compose.yaml"
echo "==> INTO THE LIVE DATABASE - the api stops for the restore"
$DC stop api
$DC exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner \
    < "$dump"
$DC up -d --wait api 2>&1 | tail -1          # back - and healthy
SQL="SELECT count(*) FROM courses"
count=$($DC exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "$SQL")
echo "courses: $count - back"
