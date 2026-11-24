#!/usr/bin/env bash
# Video 67 - ONCE, on the BACKUP BOX: a small server at ANOTHER provider (not the app's).
#   ssh root@backup.example.net 'bash -s' < deploy/backup-box-setup.sh
# rest-server: restic's own server. --append-only: the app server can ADD backups -
# it can never delete or change one. A hacked server can't take its backups with it.
set -euo pipefail
V=0.14.0
URL=https://github.com/restic/rest-server/releases/download/v$V
SHA=$(curl -fsSL "$URL/SHA256SUMS" | grep "rest-server_${V}_linux_amd64.tar.gz")
curl -fsSLo /tmp/rs.tgz "$URL/rest-server_${V}_linux_amd64.tar.gz"
echo "${SHA%% *}  /tmp/rs.tgz" | sha256sum -c -          # the checksum - or nothing
tar -xzf /tmp/rs.tgz -C /tmp
install -m 755 "/tmp/rest-server_${V}_linux_amd64/rest-server" /usr/local/bin/

id restic >/dev/null 2>&1 || adduser --system --group --home /srv/restic restic
apt-get install -y -q apache2-utils >/dev/null           # htpasswd
# ONE user per app server - --private-repos: coursehub-1 sees only /coursehub-1/
htpasswd -B -c /srv/restic/.htpasswd coursehub-1         # asks for the password
chown restic:restic /srv/restic/.htpasswd && chmod 600 /srv/restic/.htpasswd

cat > /etc/systemd/system/rest-server.service <<'UNIT'
[Unit]
Description=restic rest-server (append-only)
After=network-online.target
[Service]
User=restic
ExecStart=/usr/local/bin/rest-server --path /srv/restic --listen :8000 --append-only \
    --private-repos --tls --tls-cert /etc/rest-server/cert.pem \
    --tls-key /etc/rest-server/key.pem
Restart=always
[Install]
WantedBy=multi-user.target
UNIT
echo "next: a certificate in /etc/rest-server (certbot)"
echo "then: systemctl enable --now rest-server"
