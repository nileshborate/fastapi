#!/usr/bin/env bash
# From your laptop: copy the code, then rollout.sh on the server - and check it
#   DEPLOY_HOST=deploy@203.0.113.10 DOMAIN=api.example.com ./deploy/deploy.sh
set -euo pipefail
: "${DEPLOY_HOST:?set DEPLOY_HOST=deploy@your-server}" "${DOMAIN:?set DOMAIN=your domain}"
cd "$(dirname "$0")/.."

echo "==> copy the code to $DEPLOY_HOST"
# --delete: files you deleted go away on the server too. Excluded files are never touched
rsync -az --delete --exclude-from=deploy/rsync-exclude ./ "$DEPLOY_HOST:coursehub/"

echo "==> on the server: build, migrate, the new api next to the old one (rollout.sh)"
sha=$(git rev-parse HEAD 2>/dev/null || echo laptop)   # GitHub Actions: deploy/ci-command.sh
# shellcheck disable=SC2029                   # $sha: expanded HERE, on purpose
ssh "$DEPLOY_HOST" "test -f coursehub/.env && GIT_SHA=$sha coursehub/deploy/rollout.sh"

echo "==> check it the way a user does: HTTPS, through the domain"
# CHECK_CA: only for a TEST certificate (Let's Encrypt staging) - a real one is trusted
curl -fsS ${CHECK_CA:+--cacert "$CHECK_CA"} "https://$DOMAIN/health/ready"
echo
