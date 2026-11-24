#!/usr/bin/env bash
# A real certificate from Let's Encrypt - on the server, as root. Two steps:
#   first:    before the first deploy - nginx isn't running, certbot answers on port 80 itself
#   renewals: after the first deploy  - nginx has port 80: certbot writes into its webroot
#   ssh ubuntu@SERVER_IP "sudo DOMAIN=api.example.com EMAIL=you@example.com bash -s first" \
#       < deploy/certificate.sh
set -euo pipefail
STEP=${1:?usage: certificate.sh first|renewals}
# start with the STAGING server (no rate limits, untrusted certs) - then the real one
ACME_SERVER=${ACME_SERVER:-https://acme-v02.api.letsencrypt.org/directory}
RELOAD="docker compose -f /home/deploy/coursehub/compose.yaml exec -T nginx nginx -s reload"

if [ "$STEP" = first ]; then
    : "${DOMAIN:?set DOMAIN}" "${EMAIL:?set EMAIL}"
    certbot certonly --standalone --non-interactive --agree-tos --email "$EMAIL" \
        --server "$ACME_SERVER" --cert-name coursehub --domain "$DOMAIN"
else
    # webroot + reload nginx after every renewal. reconfigure tests it with a dry run
    certbot reconfigure --non-interactive --cert-name coursehub --webroot \
        --webroot-path /var/www/certbot \
        --deploy-hook "$RELOAD" --server "$ACME_SERVER"
fi
certbot certificates --cert-name coursehub 2>/dev/null | grep -E "Domains|Expiry"
