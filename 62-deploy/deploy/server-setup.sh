#!/usr/bin/env bash
# ONCE, on a fresh Ubuntu 24.04 server - as root, from your laptop:
#   ssh ubuntu@SERVER_IP 'sudo bash -s' < deploy/server-setup.sh
set -euo pipefail

echo "==> 1. packages: Docker + Compose, certbot, the firewall, automatic security updates"
apt-get update -q
DEBIAN_FRONTEND=noninteractive apt-get install -y -q \
    docker.io docker-compose-v2 certbot ufw unattended-upgrades >/dev/null

echo "==> 2. a deploy user: logs in with YOUR key, runs docker - no password, no sudo"
id deploy >/dev/null 2>&1 || adduser --disabled-password --gecos "" deploy >/dev/null
usermod -aG docker deploy                 # the docker group is root-equivalent: guard this key
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
install -m 600 -o deploy -g deploy /home/ubuntu/.ssh/authorized_keys /home/deploy/.ssh/

echo "==> 3. SSH: keys only, no root login"
cat > /etc/ssh/sshd_config.d/99-coursehub.conf <<'CONF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
CONF
sshd -t                                   # a broken sshd config = locked out: test first
systemctl reload ssh 2>/dev/null || kill -HUP "$(cat /run/sshd.pid)"   # no systemd: my stand-in

echo "==> 4. the firewall: SSH FIRST - then 80 + 443 - then enable"
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null
ufw allow OpenSSH >/dev/null
ufw allow 80/tcp >/dev/null               # HTTP: Let's Encrypt's check + the redirect
ufw allow 443/tcp >/dev/null
ufw --force enable

echo "==> 5. the app folder, the challenge folder and .env with a random password"
install -d -o deploy -g deploy /home/deploy/coursehub
install -d /var/www/certbot
if [ ! -f /home/deploy/coursehub/.env ]; then
    umask 077
    printf 'POSTGRES_USER=coursehub\nPOSTGRES_PASSWORD=%s\nPOSTGRES_DB=coursehub\n' \
        "$(openssl rand -hex 24)" > /home/deploy/coursehub/.env
    chown deploy:deploy /home/deploy/coursehub/.env
fi
ufw status verbose | head -4
echo "done: ssh deploy@$(hostname -I | cut -d' ' -f1)"
