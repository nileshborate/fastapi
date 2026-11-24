#!/usr/bin/env sh
# LAPTOP ONLY - development certificates in the SAME layout as certbot on the server:
#   certs/live/coursehub/fullchain.pem + privkey.pem  (compose.override.yaml mounts certs/)
# The server gets a real certificate from Let's Encrypt: deploy/get-certificate.sh
# certs/ is in .gitignore - a private key is never committed.
set -eu
cd "$(dirname "$0")/.."
mkdir -p certs/live/coursehub certs/acme && cd certs

# 1. the CA - trust ca.crt (curl --cacert, or import it into your browser)
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=Course Hub dev CA" \
    -keyout ca.key -out ca.crt

# 2. the server key + a request, 3. signed by the CA - browsers only read subjectAltName
openssl req -newkey rsa:2048 -nodes -subj "/CN=localhost" -keyout live/coursehub/privkey.pem \
    -out server.csr
printf "subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n" > server.ext
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 90 \
    -extfile server.ext -out live/coursehub/fullchain.pem

rm -f server.csr server.ext ca.srl
echo "certs/: ca.crt (trust this) · live/coursehub/fullchain.pem + privkey.pem (for nginx)"
