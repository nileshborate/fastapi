#!/usr/bin/env bash
# Homework 62.3 - the ONLY thing the CI key can do. One line in ~deploy/.ssh/authorized_keys:
#   restrict,command="/home/deploy/coursehub/deploy/ci-command.sh" ssh-ed25519 AAAA... ci-deploy
# restrict: no shell, no port forwarding, no agent. The client may only ask for:
#   deploy <a 40-character commit>   -> that commit of the repo, then rollout.sh
set -euo pipefail
REPO_URL=https://github.com/nileshborate/fastapi.git
APP_DIR=62-deploy
# shellcheck disable=SC1091                   # optional, on the server: another repo or folder
[ -f "$HOME/ci-command.env" ] && . "$HOME/ci-command.env"
SRC=$HOME/src

read -r cmd sha extra <<< "${SSH_ORIGINAL_COMMAND:-}"
if [ "${cmd:-}" != deploy ] || [ -n "${extra:-}" ] || ! [[ "${sha:-}" =~ ^[0-9a-f]{40}$ ]]; then
    echo "not allowed: '${SSH_ORIGINAL_COMMAND:-}' - only: deploy <40-character commit>" >&2
    exit 1
fi

[ -d "$SRC/.git" ] || git clone --quiet --no-checkout "$REPO_URL" "$SRC"
git -C "$SRC" fetch --quiet origin
git -C "$SRC" cat-file -e "$sha^{commit}"    # unknown commit: stop here (set -e)
git -C "$SRC" checkout --quiet --force --detach "$sha"
echo "==> commit $sha"
# the same files a laptop deploy copies: .env, certificates and the override stay untouched
rsync -a --delete --exclude-from="$SRC/$APP_DIR/deploy/rsync-exclude" \
    "$SRC/$APP_DIR/" "$HOME/coursehub/"
"$HOME/coursehub/deploy/rollout.sh"
echo "$(date -Is) $sha" >> "$HOME/deployed.log"
