#!/usr/bin/env bash
# Video 62 homework - a backup you never restored is only a hope. ON THE SERVER:
# the newest dump -> a NEW database -> count the rows -> compare -> drop it again
set -euo pipefail
cd "$(dirname "$0")/.."
set -a                                       # POSTGRES_USER, POSTGRES_DB: the server's .env
# shellcheck disable=SC1091                   # .env exists only on the server
. ./.env
set +a
DIR=${BACKUP_DIR:-$HOME/backups}
dumps=("$DIR"/coursehub-*.dump)
dump=${dumps[-1]}                            # the newest: a glob is sorted by name = by date
DB="docker compose -f compose.yaml exec -T db"
TEST=coursehub_restore_test
psql() { $DB psql -U "$POSTGRES_USER" -d "$1" -tAc "$2"; }

echo "==> restore $(basename "$dump") into $TEST"
$DB dropdb -U "$POSTGRES_USER" --if-exists "$TEST"
$DB createdb -U "$POSTGRES_USER" "$TEST"
$DB pg_restore -U "$POSTGRES_USER" -d "$TEST" --no-owner < "$dump"

live=$(psql "$POSTGRES_DB" "SELECT count(*) FROM courses")
restored=$(psql "$TEST" "SELECT count(*) FROM courses")
revision=$(psql "$TEST" "SELECT version_num FROM alembic_version")
$DB dropdb -U "$POSTGRES_USER" "$TEST"
echo "courses: live $live, restored $restored · alembic revision $revision"
[ "$restored" -gt 0 ] || { echo "!!! the restored database is EMPTY" >&2; exit 1; }
