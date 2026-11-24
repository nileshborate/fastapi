#!/usr/bin/env bash
# Homework 62.2 - ON THE SERVER: a new api version with ZERO failed requests
#   build -> migrate -> start the NEW api NEXT TO the old one -> wait until healthy
#   -> nginx knows both -> stop the old one. A new api that never gets healthy: old one stays.
set -euo pipefail
cd "$(dirname "$0")/.."
DC="docker compose -f compose.yaml"
WAIT=${ROLLOUT_WAIT:-60}                     # seconds for the new api to become healthy

echo "==> build"
$DC build --quiet api
echo "==> migrate (expand/contract, Video 60: the OLD code must work with the new schema)"
$DC up -d --wait db
$DC run --rm migrate

old=$($DC ps -q api)
if [ -z "$old" ]; then                       # the very first deploy: nothing to replace
    echo "==> first start"
    exec $DC up -d --wait
fi

echo "==> start the new api next to the old one"
$DC up -d --no-deps --no-recreate --scale api=2 api
new=$($DC ps -q api | grep -v "$old")

echo "==> wait until the new api is healthy (at most ${WAIT} s)"
for _ in $(seq "$WAIT"); do
    state=$(docker inspect -f '{{.State.Health.Status}}' "$new")
    [ "$state" = healthy ] && break
    sleep 1
done
if [ "$state" != healthy ]; then
    echo "!!! the new api is '$state' - removing it, the old one keeps serving" >&2
    docker logs --tail 20 "$new" >&2 || true
    docker rm -f "$new" >/dev/null
    exit 1
fi

# nginx is NEVER recreated (Video 62: that cost 12 s). A changed nginx/ folder: test + reload -
# NOW, while both apis run
conf=$(cat nginx/*.conf | sha256sum)
if [ "$conf" != "$(cat "$HOME/.nginx-conf.sha256" 2>/dev/null)" ]; then
    echo "==> nginx: the config changed - test + reload"
    $DC exec -T nginx nginx -t -q && $DC exec -T nginx nginx -s reload 2>/dev/null
    echo "$conf" > "$HOME/.nginx-conf.sha256"
fi
echo "==> nginx: re-resolves 'api' every 10 s (resolver valid=10s) - wait for it"
sleep 11
echo "==> stop the old api (uvicorn finishes its open requests on SIGTERM)"
docker stop "$old" >/dev/null && docker rm "$old" >/dev/null
$DC ps --format 'table {{.Name}}\t{{.Status}}'
