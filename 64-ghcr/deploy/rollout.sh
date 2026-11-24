#!/usr/bin/env bash
# ON THE SERVER: a new api version with ZERO failed requests (Video 62 homework)
#   pull -> migrate -> start the NEW api NEXT TO the old one -> wait until healthy
#   -> nginx knows both -> stop the old one. A new api that never gets healthy: old one stays.
# Video 64: no build here any more - the image CI built and pushed for THIS commit
set -euo pipefail
cd "$(dirname "$0")/.."
DC="docker compose -f compose.yaml"
WAIT=${ROLLOUT_WAIT:-60}                     # seconds for the new api to become healthy
KEEP=${KEEP_IMAGES:-5}                       # images kept on the server - older ones: pruned
GOOD="$HOME/.nginx-good"                     # homework 64: the last nginx config that worked
: "${GIT_SHA:?the commit whose image CI pushed - ci-command.sh sets it}"
export GIT_SHA

echo "==> pull the image of ${GIT_SHA:0:12} (built once, by CI)"
start=$SECONDS
$DC pull --quiet api          # nothing is stopped yet: a failed pull changes nothing
echo "    $((SECONDS - start)) s"
echo "==> migrate (expand/contract, Video 60: the OLD code must work with the new schema)"
$DC up -d --wait db
$DC run --rm migrate

old=$($DC ps -q api)
if [ -z "$old" ]; then                       # the very first deploy: nothing to replace
    echo "==> first start"
    $DC up -d --wait
    mkdir -p "$GOOD" && cp nginx/*.conf "$GOOD/"
    exit 0
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
# homework 64: check the path a USER takes - through nginx - right after the reload,
# while the old api still runs
echo "==> check through nginx: https://localhost/health/ready - 5 times, all must answer"
sleep 2                    # "nginx -s reload" returns BEFORE the new workers take requests
ok=0
for _ in 1 2 3 4 5; do
    curl -fsSk -o /dev/null https://localhost/health/ready && ok=$((ok + 1))
    sleep 0.5
done
if [ "$ok" -lt 5 ]; then
    echo "!!! $ok of 5 through nginx - back to the last good nginx config, old api stays" >&2
    if [ -d "$GOOD" ]; then
        cp "$GOOD"/*.conf nginx/
        $DC exec -T nginx nginx -s reload 2>/dev/null
        cat nginx/*.conf | sha256sum > "$HOME/.nginx-conf.sha256"
    fi
    docker rm -f "$new" >/dev/null
    exit 1
fi
cp nginx/*.conf "$GOOD/" 2>/dev/null || { mkdir -p "$GOOD" && cp nginx/*.conf "$GOOD/"; }

echo "==> nginx: re-resolves 'api' every 10 s (resolver valid=10s) - wait for it"
sleep 11
echo "==> stop the old api (uvicorn finishes its open requests on SIGTERM)"
docker stop "$old" >/dev/null && docker rm "$old" >/dev/null
$DC ps --format 'table {{.Name}}\t{{.Status}}'

echo "==> keep the $KEEP newest images (a rollback further back pulls again)"
# grep -m1 would stop reading early: compose gets SIGPIPE, exits 255 -> pipefail -> "failed"
image=$($DC config --images | grep ":$GIT_SHA$" | sort -u)     # api + migrate: the same image
repo=${image%:*}                             # ghcr.io/nileshborate/coursehub
$DC rm -f migrate >/dev/null 2>&1 || true    # a STOPPED migrate container still holds its image
# newest first (by build time). The RUNNING image can't be removed: docker refuses - fine
docker image ls "$repo" --format '{{.Repository}}:{{.Tag}}' | tail -n +"$((KEEP + 1))" \
    | xargs -r docker rmi >/dev/null 2>&1 || true
docker image ls "$repo" --format '{{.Tag}}  {{.Size}}'   # no head: it stops reading early too
