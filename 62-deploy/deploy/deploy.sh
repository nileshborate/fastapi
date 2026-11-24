#!/usr/bin/env bash
# From your laptop: copy the code, build on the server, migrate, start, wait - and check it
#   DEPLOY_HOST=deploy@203.0.113.10 DOMAIN=api.example.com ./deploy/deploy.sh
set -euo pipefail
: "${DEPLOY_HOST:?set DEPLOY_HOST=deploy@your-server}" "${DOMAIN:?set DOMAIN=your domain}"
cd "$(dirname "$0")/.."

echo "==> copy the code to $DEPLOY_HOST"
# --delete: files you deleted go away on the server too. Excluded files are never touched
rsync -az --delete --exclude-from=deploy/rsync-exclude ./ "$DEPLOY_HOST:coursehub/"

echo "==> build, migrate, start - and wait until everything is healthy"
# -f compose.yaml: ONLY the production file, never a compose.override.yaml
ssh "$DEPLOY_HOST" "cd coursehub && test -f .env && \
    docker compose -f compose.yaml up -d --build --wait --remove-orphans"

echo "==> check it the way a user does: HTTPS, through the domain"
# CHECK_CA: only for a TEST certificate (Let's Encrypt staging) - a real one is trusted
curl -fsS ${CHECK_CA:+--cacert "$CHECK_CA"} "https://$DOMAIN/health/ready"
echo
