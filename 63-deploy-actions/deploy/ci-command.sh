#!/usr/bin/env bash
# Video 63 - the ONLY things the CI key can do. One line in ~deploy/.ssh/authorized_keys:
#   restrict,command="/home/deploy/coursehub/deploy/ci-command.sh" ssh-ed25519 AAAA... ci-deploy
# restrict: no shell, no port forwarding, no agent. The client may only ask for:
#   deploy <a 40-character commit>   that commit of the repo -> rollout.sh
#   rollback                         the commit deployed BEFORE the current one
#   status                           the last deploys
set -euo pipefail
REPO_URL=https://github.com/nileshborate/fastapi.git
APP_DIR=63-deploy-actions
# shellcheck disable=SC1091                   # optional, on the server: another repo or folder
[ -f "$HOME/ci-command.env" ] && . "$HOME/ci-command.env"
SRC=$HOME/src
LOG=$HOME/deployed.log                       # one line per deploy: <date> <commit>

deploy() {                                   # $1: a full commit id
    [ -d "$SRC/.git" ] || git clone --quiet --no-checkout "$REPO_URL" "$SRC"
    git -C "$SRC" fetch --quiet origin
    git -C "$SRC" cat-file -e "$1^{commit}"  # unknown commit: stop here (set -e)
    git -C "$SRC" checkout --quiet --force --detach "$1"
    echo "==> commit $1"
    # the same files a laptop deploy copies: .env, certificates and the override stay untouched
    rsync -a --delete --exclude-from="$SRC/$APP_DIR/deploy/rsync-exclude" \
        "$SRC/$APP_DIR/" "$HOME/coursehub/"
    GIT_SHA=$1 "$HOME/coursehub/deploy/rollout.sh"     # the image knows its commit
    echo "$(date -Is) $1" >> "$LOG"           # only a SUCCESSFUL rollout is written down
}

read -r cmd arg extra <<< "${SSH_ORIGINAL_COMMAND:-}"
case "${cmd:-}:${extra:-}" in
    deploy:)
        if ! [[ "${arg:-}" =~ ^[0-9a-f]{40}$ ]]; then
            echo "deploy needs a 40-character commit" >&2; exit 1
        fi
        deploy "$arg" ;;
    rollback:)
        [ -z "${arg:-}" ] || { echo "rollback takes no argument" >&2; exit 1; }
        [ "$(wc -l < "$LOG")" -ge 2 ] || { echo "nothing to roll back to" >&2; exit 1; }
        previous=$(tail -n 2 "$LOG" | head -n 1 | cut -d' ' -f2)
        echo "==> rollback to $previous"
        deploy "$previous" ;;
    status:)
        tail -n 5 "$LOG" ;;
    *)
        echo "not allowed: '${SSH_ORIGINAL_COMMAND:-}'" >&2
        echo "only: deploy <commit> | rollback | status" >&2
        exit 1 ;;
esac
